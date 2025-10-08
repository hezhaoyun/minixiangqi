# -*- coding: utf-8 -*-
"""
位棋盘 (Bitboard) 走法生成与合法性检测模块。

该模块负责象棋引擎中所有与走法生成相关的功能。它完全基于位棋盘实现，
以追求最高的性能。主要功能包括：
- 为所有棋子类型生成伪合法走法 (Pseudo-legal moves)。
- 检测特定棋盘位置是否被某一方攻击。
- 判断某一方是否被将军。
- 生成当前局面的所有合法走法。

为了提升性能，模块在启动时会预先计算并缓存所有棋子的基本攻击模式。
"""

from typing import List
from src.bitboard import Bitboard, SQUARE_MASKS, PIECE_TO_BB_INDEX, BB_INDEX_TO_PIECE
from src.constants import *

Move = tuple[int, int]  # 使用整数表示棋盘位置，而非坐标元组

# --- 棋盘区域掩码 (Masks) ---
# 用于兵、象等棋子过河或区域限制
RED_SIDE_MASK = 0x000000000001FFFFFFFFFFF  # 红方兵、象的移动区域 (黑方半盘)
BLACK_SIDE_MASK = 0x3FFFFFFFFFFE00000000000  # 黑方兵、象的移动区域 (红方半盘)

# --- 预计算攻击表 (Pre-calculated Attack Tables) ---
# 这些表在模块加载时一次性计算，之后在走法生成中可以快速查询。
KING_ATTACKS = [0] * 90   # 帅/将 的攻击范围
GUARD_ATTACKS = [0] * 90  # 仕/士 的攻击范围
BISHOP_ATTACKS = [0] * 90  # 象/相 的攻击范围 (不考虑塞象眼)
BISHOP_LEGS = {}          # 记录象/相的象眼位置
HORSE_ATTACKS = [0] * 90  # 马 的攻击范围 (不考虑蹩马腿)
HORSE_LEGS = {}           # 记录马的马腿位置
PAWN_ATTACKS = [[0] * 90, [0] * 90]  # 兵/卒 的攻击范围 [player_idx][square]

# --- 预计算辅助函数 ---


def _sq(r, c):
    """将行列坐标转换为棋盘位置索引 (0-89)。"""
    return r * 9 + c


def _is_valid(r, c):
    """检查坐标 (r, c) 是否在棋盘范围内。"""
    return 0 <= r < 10 and 0 <= c < 9


def _precompute_king_guard_attacks():
    """预计算帅/将和仕/士的攻击位棋盘。"""
    for r in range(10):
        for c in range(9):
            sq = _sq(r, c)
            # 帅/将的走法 (九宫格内的直线移动)
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                # 限制在九宫格内
                if not (3 <= nc <= 5 and (0 <= nr <= 2 or 7 <= nr <= 9)):
                    continue
                KING_ATTACKS[sq] |= SQUARE_MASKS[_sq(nr, nc)]
            # 仕/士的走法 (九宫格内的斜线移动)
            for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nr, nc = r + dr, c + dc
                # 限制在九宫格内
                if not (3 <= nc <= 5 and (0 <= nr <= 2 or 7 <= nr <= 9)):
                    continue
                GUARD_ATTACKS[sq] |= SQUARE_MASKS[_sq(nr, nc)]


def _precompute_bishop_horse_attacks():
    """预计算象/相和马的攻击位棋盘及阻挡位置。"""
    for r in range(10):
        for c in range(9):
            from_sq = _sq(r, c)
            BISHOP_LEGS[from_sq] = {}
            HORSE_LEGS[from_sq] = {}

            # 象/相的走法 ("田"字)
            for dr, dc in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
                nr, nc = r + dr, c + dc
                if not _is_valid(nr, nc):
                    continue
                to_sq = _sq(nr, nc)
                BISHOP_ATTACKS[from_sq] |= SQUARE_MASKS[to_sq]
                # 记录象眼位置
                leg_r, leg_c = r + dr // 2, c + dc // 2
                BISHOP_LEGS[from_sq][to_sq] = _sq(leg_r, leg_c)

            # 马的走法 ("日"字)
            for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
                nr, nc = r + dr, c + dc
                if not _is_valid(nr, nc):
                    continue
                to_sq = _sq(nr, nc)
                HORSE_ATTACKS[from_sq] |= SQUARE_MASKS[to_sq]
                # 记录马腿位置
                leg_r, leg_c = r, c
                if abs(dr) == 2:
                    leg_r += dr // 2
                else:
                    leg_c += dc // 2
                HORSE_LEGS[from_sq][to_sq] = _sq(leg_r, leg_c)


def _precompute_pawn_attacks():
    """预计算兵/卒的攻击位棋盘。"""
    for r in range(10):
        for c in range(9):
            sq = _sq(r, c)

            # 红兵走法
            if _is_valid(r - 1, c):
                PAWN_ATTACKS[0][sq] |= SQUARE_MASKS[_sq(r - 1, c)]  # 向前

            if r < 5:  # 过河后
                if _is_valid(r, c - 1):
                    PAWN_ATTACKS[0][sq] |= SQUARE_MASKS[_sq(r, c - 1)]  # 向左
                if _is_valid(r, c + 1):
                    PAWN_ATTACKS[0][sq] |= SQUARE_MASKS[_sq(r, c + 1)]  # 向右

            # 黑卒走法
            if _is_valid(r + 1, c):
                PAWN_ATTACKS[1][sq] |= SQUARE_MASKS[_sq(r + 1, c)]  # 向前

            if r > 4:  # 过河后
                if _is_valid(r, c - 1):
                    PAWN_ATTACKS[1][sq] |= SQUARE_MASKS[_sq(r, c - 1)]  # 向左
                if _is_valid(r, c + 1):
                    PAWN_ATTACKS[1][sq] |= SQUARE_MASKS[_sq(r, c + 1)]  # 向右


# --- 模块加载时执行预计算 ---
_precompute_king_guard_attacks()
_precompute_bishop_horse_attacks()
_precompute_pawn_attacks()


# --- Ray-Attack Pre-calculation for Sliding Pieces ---

# Directions: 0:N, 1:E, 2:S, 3:W
RAYS = [[0] * 90, [0] * 90, [0] * 90, [0] * 90]

def _precompute_rays():
    """预计算所有位置在四个基本方向上的射线。"""
    for sq in range(90):
        r, c = sq // 9, sq % 9
        # North (Up)
        for i in range(r - 1, -1, -1):
            RAYS[0][sq] |= SQUARE_MASKS[_sq(i, c)]
        # East (Right)
        for i in range(c + 1, 9):
            RAYS[1][sq] |= SQUARE_MASKS[_sq(r, i)]
        # South (Down)
        for i in range(r + 1, 10):
            RAYS[2][sq] |= SQUARE_MASKS[_sq(i, c)]
        # West (Left)
        for i in range(c - 1, -1, -1):
            RAYS[3][sq] |= SQUARE_MASKS[_sq(r, i)]

_precompute_rays()

def get_rook_moves_bb(sq: int, occupied: int) -> int:
    """
    获取车在给定位置的走法位棋盘 (使用射线预计算)。
    """
    final_attacks = 0
    
    # North (decreasing index) -> MSB
    ray = RAYS[0][sq]
    blockers = occupied & ray
    if blockers:
        first_blocker = blockers.bit_length() - 1
        final_attacks |= (ray ^ RAYS[0][first_blocker]) | SQUARE_MASKS[first_blocker]
    else:
        final_attacks |= ray

    # East (increasing index) -> LSB
    ray = RAYS[1][sq]
    blockers = occupied & ray
    if blockers:
        first_blocker = (blockers & -blockers).bit_length() - 1
        final_attacks |= (ray ^ RAYS[1][first_blocker]) | SQUARE_MASKS[first_blocker]
    else:
        final_attacks |= ray

    # South (increasing index) -> LSB
    ray = RAYS[2][sq]
    blockers = occupied & ray
    if blockers:
        first_blocker = (blockers & -blockers).bit_length() - 1
        final_attacks |= (ray ^ RAYS[2][first_blocker]) | SQUARE_MASKS[first_blocker]
    else:
        final_attacks |= ray

    # West (decreasing index) -> MSB
    ray = RAYS[3][sq]
    blockers = occupied & ray
    if blockers:
        first_blocker = blockers.bit_length() - 1
        final_attacks |= (ray ^ RAYS[3][first_blocker]) | SQUARE_MASKS[first_blocker]
    else:
        final_attacks |= ray
        
    return final_attacks


def get_cannon_moves_bb(sq: int, occupied: int) -> int:
    """
    获取炮在给定位置的走法位棋盘 (使用射线预计算)。
    """
    attacks = 0
    
    # North (decreasing index) -> MSB
    ray = RAYS[0][sq]
    blockers = occupied & ray
    if blockers:
        screen = blockers.bit_length() - 1
        attacks |= ray ^ RAYS[0][screen] ^ SQUARE_MASKS[screen] # Empty squares before screen
        remaining_blockers = blockers ^ SQUARE_MASKS[screen]
        if remaining_blockers:
            target = remaining_blockers.bit_length() - 1
            attacks |= SQUARE_MASKS[target]
    else:
        attacks |= ray

    # East (increasing index) -> LSB
    ray = RAYS[1][sq]
    blockers = occupied & ray
    if blockers:
        screen = (blockers & -blockers).bit_length() - 1
        attacks |= ray ^ RAYS[1][screen] ^ SQUARE_MASKS[screen]
        remaining_blockers = blockers ^ SQUARE_MASKS[screen]
        if remaining_blockers:
            target = (remaining_blockers & -remaining_blockers).bit_length() - 1
            attacks |= SQUARE_MASKS[target]
    else:
        attacks |= ray

    # South (increasing index) -> LSB
    ray = RAYS[2][sq]
    blockers = occupied & ray
    if blockers:
        screen = (blockers & -blockers).bit_length() - 1
        attacks |= ray ^ RAYS[2][screen] ^ SQUARE_MASKS[screen]
        remaining_blockers = blockers ^ SQUARE_MASKS[screen]
        if remaining_blockers:
            target = (remaining_blockers & -remaining_blockers).bit_length() - 1
            attacks |= SQUARE_MASKS[target]
    else:
        attacks |= ray

    # West (decreasing index) -> MSB
    ray = RAYS[3][sq]
    blockers = occupied & ray
    if blockers:
        screen = blockers.bit_length() - 1
        attacks |= ray ^ RAYS[3][screen] ^ SQUARE_MASKS[screen]
        remaining_blockers = blockers ^ SQUARE_MASKS[screen]
        if remaining_blockers:
            target = remaining_blockers.bit_length() - 1
            attacks |= SQUARE_MASKS[target]
    else:
        attacks |= ray
        
    return attacks


def generate_all_moves(bb: Bitboard, player: int) -> List[Move]:
    """
    为指定方生成所有伪合法走法。

    伪合法走法是指不考虑走棋后是否会被将军的所有可能走法。

    Args:
        bb (Bitboard): 当前棋盘局面。
        player (int): 要生成走法的一方 (PLAYER_R 或 PLAYER_B)。

    Returns:
        List[Move]: 一个包含所有伪合法走法的列表。
    """
    moves = []
    player_idx = 0 if player == PLAYER_R else 1
    own_pieces_bb = bb.color_bitboards[player_idx]
    occupied = bb.occupied_bitboard

    # 遍历该方的每一种棋子
    for piece_bb_idx in range(14):
        piece_type = BB_INDEX_TO_PIECE[piece_bb_idx]
        if Bitboard.get_player(piece_type) != player:
            continue

        # 遍历该类型棋子的每一个棋子
        piece_bb = bb.piece_bitboards[piece_bb_idx]
        temp_piece_bb = piece_bb
        while temp_piece_bb:
            from_sq = (temp_piece_bb & -temp_piece_bb).bit_length() - 1
            moves_bb = 0

            # --- 根据棋子类型生成走法位棋盘 ---
            if piece_type in (R_KING, B_KING):
                moves_bb = KING_ATTACKS[from_sq]
            elif piece_type in (R_GUARD, B_GUARD):
                moves_bb = GUARD_ATTACKS[from_sq]
            elif piece_type in (R_BISHOP, B_BISHOP):
                side_mask = BLACK_SIDE_MASK if piece_type == R_BISHOP else RED_SIDE_MASK
                potential_moves = BISHOP_ATTACKS[from_sq] & side_mask
                temp_moves = potential_moves
                while temp_moves:
                    to_sq = (temp_moves & -temp_moves).bit_length() - 1
                    leg_sq = BISHOP_LEGS[from_sq][to_sq]
                    if not (occupied & SQUARE_MASKS[leg_sq]):  # 检查象眼
                        moves_bb |= SQUARE_MASKS[to_sq]
                    temp_moves &= temp_moves - 1
            elif piece_type in (R_HORSE, B_HORSE):
                potential_moves = HORSE_ATTACKS[from_sq]
                temp_moves = potential_moves
                while temp_moves:
                    to_sq = (temp_moves & -temp_moves).bit_length() - 1
                    leg_sq = HORSE_LEGS[from_sq][to_sq]
                    if not (occupied & SQUARE_MASKS[leg_sq]):  # 检查马腿
                        moves_bb |= SQUARE_MASKS[to_sq]
                    temp_moves &= temp_moves - 1
            elif piece_type in (R_PAWN, B_PAWN):
                moves_bb = PAWN_ATTACKS[player_idx][from_sq]
            elif piece_type in (R_ROOK, B_ROOK):
                moves_bb = get_rook_moves_bb(from_sq, occupied)
            elif piece_type in (R_CANNON, B_CANNON):
                moves_bb = get_cannon_moves_bb(from_sq, occupied)

            # 排除走到己方棋子上的走法
            valid_moves_bb = moves_bb & ~own_pieces_bb

            # 从走法位棋盘中提取单个走法
            temp_valid_moves = valid_moves_bb
            while temp_valid_moves:
                to_sq = (temp_valid_moves & -temp_valid_moves).bit_length() - 1
                moves.append((from_sq, to_sq))
                temp_valid_moves &= temp_valid_moves - 1

            temp_piece_bb &= temp_piece_bb - 1

    return moves


def is_square_attacked_by(bb: Bitboard, sq: int, attacker_player: int) -> bool:
    """
    检查指定位置 `sq` 是否被 `attacker_player` 方攻击。

    Args:
        bb (Bitboard): 当前棋盘局面。
        sq (int): 要检查的棋盘位置。
        attacker_player (int): 攻击方。

    Returns:
        bool: 如果位置被攻击，则返回True；否则返回False。
    """
    occupied = bb.occupied_bitboard
    attacker_idx = 0 if attacker_player == PLAYER_R else 1

    # 检查兵/卒的攻击
    pawn_attacks = PAWN_ATTACKS[attacker_idx][sq]
    pawn_piece = R_PAWN if attacker_player == PLAYER_R else B_PAWN
    if pawn_attacks & bb.piece_bitboards[PIECE_TO_BB_INDEX[pawn_piece]]:
        return True

    # 检查马的攻击 (需要检查马腿)
    horse_attacks = HORSE_ATTACKS[sq]
    horse_piece = R_HORSE if attacker_player == PLAYER_R else B_HORSE
    potential_horses = horse_attacks & bb.piece_bitboards[PIECE_TO_BB_INDEX[horse_piece]]
    if potential_horses:
        temp_horses = potential_horses
        while temp_horses:
            from_sq = (temp_horses & -temp_horses).bit_length() - 1
            leg_sq = HORSE_LEGS[from_sq][sq]
            if not (occupied & SQUARE_MASKS[leg_sq]):
                return True
            temp_horses &= temp_horses - 1

    # 检查象/相的攻击 (需要检查象眼)
    bishop_attacks = BISHOP_ATTACKS[sq]
    bishop_piece = R_BISHOP if attacker_player == PLAYER_R else B_BISHOP
    potential_bishops = bishop_attacks & bb.piece_bitboards[PIECE_TO_BB_INDEX[bishop_piece]]
    if potential_bishops:
        side_mask = BLACK_SIDE_MASK if attacker_player == PLAYER_R else RED_SIDE_MASK
        if side_mask & SQUARE_MASKS[sq]:  # 象/相不能过河
            temp_bishops = potential_bishops
            while temp_bishops:
                from_sq = (temp_bishops & -temp_bishops).bit_length() - 1
                leg_sq = BISHOP_LEGS[from_sq][sq]
                if not (occupied & SQUARE_MASKS[leg_sq]):
                    return True
                temp_bishops &= temp_bishops - 1

    # 检查帅/将的攻击 (包括将帅对脸的情况)
    king_attacks = KING_ATTACKS[sq]
    king_piece = R_KING if attacker_player == PLAYER_R else B_KING
    if king_attacks & bb.piece_bitboards[PIECE_TO_BB_INDEX[king_piece]]:
        return True

    # 检查车和炮的攻击 (复用走法生成函数以提高性能)
    rook_piece = R_ROOK if attacker_player == PLAYER_R else B_ROOK
    if get_rook_moves_bb(sq, occupied) & bb.piece_bitboards[PIECE_TO_BB_INDEX[rook_piece]]:
        return True

    cannon_piece = R_CANNON if attacker_player == PLAYER_R else B_CANNON
    if get_cannon_moves_bb(sq, occupied) & bb.piece_bitboards[PIECE_TO_BB_INDEX[cannon_piece]]:
        return True

    return False


def is_check(bb: Bitboard, player: int) -> bool:
    """
    检查指定方 `player` 是否被将军。

    Args:
        bb (Bitboard): 当前棋盘局面。
        player (int): 要检查的一方。

    Returns:
        bool: 如果被将军，则返回True；否则返回False。
    """
    king_piece = R_KING if player == PLAYER_R else B_KING
    king_sq_bb = bb.piece_bitboards[PIECE_TO_BB_INDEX[king_piece]]
    if not king_sq_bb:
        return True  # 棋盘上没有将/帅，理论上不应发生
    king_sq = (king_sq_bb & -king_sq_bb).bit_length() - 1

    # 1. 检查是否被对方棋子攻击
    if is_square_attacked_by(bb, king_sq, -player):
        return True

    # 2. 检查是否满足“将帅对脸”的条件
    opponent_player = -player
    opponent_king_piece = R_KING if opponent_player == PLAYER_R else B_KING
    opponent_king_sq_bb = bb.piece_bitboards[PIECE_TO_BB_INDEX[opponent_king_piece]]
    if not opponent_king_sq_bb:
        return False  # 没有对方将/帅，则安全

    opponent_king_sq = (opponent_king_sq_bb & -opponent_king_sq_bb).bit_length() - 1

    # a. 必须在同一列
    if king_sq % 9 != opponent_king_sq % 9:
        return False

    # b. 两者之间不能有任何棋子
    occupied = bb.occupied_bitboard
    min_sq, max_sq = min(king_sq, opponent_king_sq), max(king_sq, opponent_king_sq)

    # 构造两者之间所有格子的掩码
    between_mask = 0
    # 从min_sq的下一行开始，到max_sq之前
    for s in range(min_sq + 9, max_sq, 9):
        between_mask |= SQUARE_MASKS[s]

    if not (occupied & between_mask):
        return True  # 将帅对脸，构成将军

    return False


def generate_moves(bb: Bitboard) -> List[Move]:
    """
    为当前走棋方生成所有合法的走法。

    这个函数是最终的走法生成接口。它首先生成所有伪合法走法，
    然后对每一个走法进行验证，确保走棋后己方将/帅不会处于被攻击状态。

    Args:
        bb (Bitboard): 当前棋盘局面。

    Returns:
        List[Move]: 一个包含所有合法走法的列表。
    """
    legal_moves = []
    player = bb.player_to_move

    # 1. 生成所有不考虑将军的“伪合法”走法
    pseudo_legal_moves = generate_all_moves(bb, player)

    # 2. 对每个伪合法走法进行验证
    for from_sq, to_sq in pseudo_legal_moves:
        # a. 模拟走一步
        captured = bb.move_piece(from_sq, to_sq)
        # b. 检查走棋后，自己的王是否被攻击
        if not is_check(bb, player):
            legal_moves.append((from_sq, to_sq))
        # c. 撤销走法，恢复局面
        bb.unmove_piece(from_sq, to_sq, captured)

    return legal_moves
