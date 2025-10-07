# -*- coding: utf-8 -*-

'''
中国象棋评估函数
'''
import copy
from typing import List, Tuple

from src.board import Board
from src.constants import *
from src.moves_gen import get_piece_moves

# --- Midgame Piece-Square Tables (PST_MG) ---
# fmt: off
KING_PST_MG = [
    [0, 0, 0, 8, 8, 8, 0, 0, 0], [0, 0, 0, 8, 8, 8, 0, 0, 0], [0, 0, 0, 6, 6, 6, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 6, 6, 6, 0, 0, 0], [0, 0, 0, 8, 8, 8, 0, 0, 0],
    [0, 0, 0, 8, 8, 8, 0, 0, 0],
]
GUARD_PST_MG = [
    [0, 0, 0, 20, 0, 20, 0, 0, 0], [0, 0, 0, 0, 23, 0, 0, 0, 0], [0, 0, 0, 20, 0, 20, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 20, 0, 20, 0, 0, 0], [0, 0, 0, 0, 23, 0, 0, 0, 0],
    [0, 0, 0, 20, 0, 20, 0, 0, 0],
]
BISHOP_PST_MG = [
    [0, 0, 20, 0, 0, 0, 20, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 23, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 20, 0, 0, 0, 20, 0, 0], [0, 0, 20, 0, 0, 0, 20, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 23, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 20, 0, 0, 0, 20, 0, 0],
]
HORSE_PST_MG = [
    [90, 90, 90, 96, 90, 96, 90, 90, 90], [90, 96, 103, 97, 94, 97, 103, 96, 90],
    [92, 98, 99, 103, 99, 103, 99, 98, 92], [93, 108, 100, 107, 100, 107, 100, 108, 93],
    [90, 100, 99, 103, 104, 103, 99, 100, 90], [90, 98, 101, 102, 103, 102, 101, 98, 90],
    [92, 94, 98, 95, 98, 95, 98, 94, 92], [93, 92, 94, 95, 92, 95, 94, 92, 93],
    [85, 90, 92, 93, 78, 93, 92, 90, 85], [88, 85, 90, 88, 90, 88, 90, 85, 88],
]
ROOK_PST_MG = [
    [206, 208, 207, 213, 214, 213, 207, 208, 206], [206, 212, 209, 216, 233, 216, 209, 212, 206],
    [206, 208, 207, 214, 216, 214, 207, 208, 206], [206, 213, 213, 216, 216, 216, 213, 213, 206],
    [208, 211, 211, 214, 215, 214, 211, 211, 208], [208, 212, 212, 214, 215, 214, 212, 212, 208],
    [204, 209, 204, 212, 214, 212, 204, 209, 204], [198, 208, 204, 212, 212, 212, 204, 208, 198],
    [200, 208, 206, 212, 200, 212, 206, 208, 200], [194, 206, 204, 212, 200, 212, 204, 206, 194],
]
CANNON_PST_MG = [
    [100, 100, 96, 91, 90, 91, 96, 100, 100], [98, 98, 96, 92, 89, 92, 96, 98, 98],
    [97, 97, 96, 91, 92, 91, 96, 97, 97], [96, 99, 99, 98, 100, 98, 99, 99, 96],
    [96, 96, 96, 96, 100, 96, 96, 96, 96], [95, 96, 99, 96, 100, 96, 99, 96, 95],
    [96, 96, 96, 96, 96, 96, 96, 96, 96], [97, 96, 100, 99, 101, 99, 100, 96, 97],
    [96, 97, 98, 98, 98, 98, 98, 97, 96], [96, 96, 97, 99, 99, 99, 97, 96, 96],
]
PAWN_PST_MG = [
    [9, 9, 9, 11, 13, 11, 9, 9, 9], [19, 24, 34, 42, 44, 42, 34, 24, 19],
    [19, 24, 32, 37, 37, 37, 32, 24, 19], [19, 23, 27, 29, 30, 29, 27, 23, 19],
    [14, 18, 20, 27, 29, 27, 20, 18, 14], [7, 0, 13, 0, 16, 0, 13, 0, 7],
    [7, 0, 7, 0, 15, 0, 7, 0, 7], [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
]
# --- Endgame Piece-Square Tables (PST_EG) ---
# 残局时, 兵的价值被大幅提升
PAWN_PST_EG = [
    [20, 20, 20, 25, 30, 25, 20, 20, 20], [40, 50, 60, 70, 75, 70, 60, 50, 40],
    [40, 50, 60, 65, 70, 65, 60, 50, 40], [40, 50, 55, 60, 60, 60, 55, 50, 40],
    [30, 40, 45, 50, 50, 50, 45, 40, 30], [15, 20, 25, 30, 30, 30, 25, 20, 15],
    [10, 15, 20, 20, 20, 20, 20, 15, 10], [5, 5, 5, 5, 5, 5, 5, 5, 5],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
]
# fmt: on

PST_MG = {
    B_KING: KING_PST_MG, B_GUARD: GUARD_PST_MG, B_BISHOP: BISHOP_PST_MG, B_HORSE: HORSE_PST_MG,
    B_ROOK: ROOK_PST_MG, B_CANNON: CANNON_PST_MG, B_PAWN: PAWN_PST_MG,
    R_KING: KING_PST_MG, R_GUARD: GUARD_PST_MG, R_BISHOP: BISHOP_PST_MG, R_HORSE: HORSE_PST_MG,
    R_ROOK: ROOK_PST_MG, R_CANNON: CANNON_PST_MG, R_PAWN: PAWN_PST_MG,
}
# 在残局表中, 除了兵, 其他棋子的位置价值与中局相同
PST_EG = copy.deepcopy(PST_MG)
PST_EG[R_PAWN] = PAWN_PST_EG
PST_EG[B_PAWN] = PAWN_PST_EG

# --- Tapered Eval Constants ---
# 开局时, 主要子力 (车马炮) 的总价值
# 2 * (ROOK + HORSE + CANNON)
OPENING_PHASE_MATERIAL = (90 + 40 + 45) * 2
# 机动性奖励
MOBILITY_BONUS = {R_ROOK: 1, R_HORSE: 3, R_CANNON: 1, }  # 调整了车马炮的机动性奖励
MOBILITY_PIECES = {R_ROOK, R_HORSE, R_CANNON}
# 将/帅安全惩罚
KING_SAFETY_PENALTY = 15

# --- 新增: 特殊棋型和动态评估奖励 ---
PATTERN_BONUS = {
    'BOTTOM_CANNON': 80,          # 沉底炮
    'PALACE_HEART_HORSE': 70,     # 卧心马
    'CONNECTED_HORSES': 30,       # 连环马
    'ROOK_ON_RIB_FILE': 20,       # 车占肋
}
DYNAMIC_BONUS = {
    'ATTACK_PER_MISSING_DEFENDER': 15,  # 每缺少一个防守子(士象), 攻击子(车马炮)的额外奖励
}


def _calculate_king_safety_score(current_board: Board) -> int:
    '''计算将/帅安全分数'''
    king_safety_score = 0
    PALACE_ZONES = {
        PLAYER_R: [(r, c) for r in range(7, 10) for c in range(3, 6)],
        PLAYER_B: [(r, c) for r in range(0, 3) for c in range(3, 6)]
    }
    # 检查黑方九宫格是否被红方攻击
    for pos in PALACE_ZONES[PLAYER_B]:
        if current_board.is_square_attacked_by(pos, PLAYER_R):
            king_safety_score += KING_SAFETY_PENALTY  # 黑方危险, 对红方有利

    # 检查红方九宫格是否被黑方攻击
    for pos in PALACE_ZONES[PLAYER_R]:
        if current_board.is_square_attacked_by(pos, PLAYER_B):
            king_safety_score -= KING_SAFETY_PENALTY  # 红方危险, 对红方不利

    return king_safety_score


def _calculate_pattern_and_dynamic_score(current_board: Board) -> int:
    '''计算特殊棋型和动态奖励分数'''
    score = 0
    board_state = current_board.board

    # --- 1. 单个棋子的棋型评估 ---
    for player in [PLAYER_R, PLAYER_B]:
        for r, c in current_board.piece_list[player]:
            piece = board_state[r][c]
            piece_type = abs(piece)

            # 红方评估
            if player == PLAYER_R:
                # 沉底炮
                if piece_type == R_CANNON and r == 0:
                    score += PATTERN_BONUS['BOTTOM_CANNON']
                # 卧心马
                if piece_type == R_HORSE and r == 1 and c == 4:
                    score += PATTERN_BONUS['PALACE_HEART_HORSE']
                # 车占肋
                if piece_type == R_ROOK and r < 5 and (c == 3 or c == 5):
                    score += PATTERN_BONUS['ROOK_ON_RIB_FILE']
            # 黑方评估
            else:
                # 沉底炮
                if piece_type == B_CANNON and r == 9:
                    score -= PATTERN_BONUS['BOTTOM_CANNON']
                # 卧心马
                if piece_type == B_HORSE and r == 8 and c == 4:
                    score -= PATTERN_BONUS['PALACE_HEART_HORSE']
                # 车占肋
                if piece_type == B_ROOK and r > 4 and (c == 3 or c == 5):
                    score -= PATTERN_BONUS['ROOK_ON_RIB_FILE']

    # --- 2. 多个棋子协作的棋型评估 (连环马) ---
    r_horses = [pos for pos in current_board.piece_list[PLAYER_R] if board_state[pos[0]][pos[1]] == R_HORSE]
    if len(r_horses) > 1:
        for i in range(len(r_horses)):
            for j in range(i + 1, len(r_horses)):
                r1, c1 = r_horses[i]
                r2, c2 = r_horses[j]
                if abs((r1 - r2) * (c1 - c2)) == 2:  # 互为马腿
                    score += PATTERN_BONUS['CONNECTED_HORSES']

    b_horses = [pos for pos in current_board.piece_list[PLAYER_B] if board_state[pos[0]][pos[1]] == B_HORSE]
    if len(b_horses) > 1:
        for i in range(len(b_horses)):
            for j in range(i + 1, len(b_horses)):
                r1, c1 = b_horses[i]
                r2, c2 = b_horses[j]
                if abs((r1 - r2) * (c1 - c2)) == 2:  # 互为马腿
                    score -= PATTERN_BONUS['CONNECTED_HORSES']

    # --- 3. 动态子力评估 ---
    num_r_guards = len([p for p in current_board.piece_list[PLAYER_R] if board_state[p[0]][p[1]] == R_GUARD])
    num_r_bishops = len([p for p in current_board.piece_list[PLAYER_R] if board_state[p[0]][p[1]] == R_BISHOP])
    num_b_guards = len([p for p in current_board.piece_list[PLAYER_B] if board_state[p[0]][p[1]] == B_GUARD])
    num_b_bishops = len([p for p in current_board.piece_list[PLAYER_B] if board_state[p[0]][p[1]] == B_BISHOP])

    r_attackers = len([p for p in current_board.piece_list[PLAYER_R] if abs(board_state[p[0]][p[1]]) in {R_ROOK, R_HORSE, R_CANNON}])
    b_attackers = len([p for p in current_board.piece_list[PLAYER_B] if abs(board_state[p[0]][p[1]]) in {B_ROOK, B_HORSE, B_CANNON}])

    # 红方攻击力加成
    missing_b_defenders = (2 - num_b_guards) + (2 - num_b_bishops)
    score += r_attackers * missing_b_defenders * DYNAMIC_BONUS['ATTACK_PER_MISSING_DEFENDER']

    # 黑方攻击力加成
    missing_r_defenders = (2 - num_r_guards) + (2 - num_r_bishops)
    score -= b_attackers * missing_r_defenders * DYNAMIC_BONUS['ATTACK_PER_MISSING_DEFENDER']

    return score


def evaluate(current_board: Board) -> int:
    '''
    评估函数
    :param current_board: Board 对象
    :return: 局面的评估分数, 正数表示红方优势, 负数表示黑方优势
    '''
    score = 0
    board_state = current_board.board

    # --- 计算棋局阶段 ---
    current_phase_material = 0
    major_pieces = {R_ROOK, R_HORSE, R_CANNON, R_GUARD, R_BISHOP}
    for piece_type in major_pieces:
        # 使用 piece_list 优化计数
        current_phase_material += len([p for p in current_board.piece_list[PLAYER_R] if abs(board_state[p[0]][p[1]]) == piece_type]) * PIECE_VALUES[piece_type]
        current_phase_material += len([p for p in current_board.piece_list[PLAYER_B] if abs(board_state[p[0]][p[1]]) == piece_type]) * PIECE_VALUES[piece_type]

    # 阶段权重, 范围从1.0 (开局) 到 0.0 (残局)
    phase_weight = min(1.0, current_phase_material / OPENING_PHASE_MATERIAL)

    # --- 遍历棋子计算分数 ---
    # 使用 piece_list 优化遍历
    for player in [PLAYER_R, PLAYER_B]:
        for r, c in current_board.piece_list[player]:
            piece = board_state[r][c]
            piece_type = abs(piece)

            # 1. 子力价值
            score += PIECE_VALUES[piece]

            # 2. 棋子位置价值 (渐进式)
            if player == PLAYER_R:
                mg_pst = PST_MG[piece][9 - r][8 - c]
                eg_pst = PST_EG[piece][9 - r][8 - c]
                pst_score = mg_pst * phase_weight + eg_pst * (1 - phase_weight)
                score += pst_score
            else:  # PLAYER_B
                mg_pst = PST_MG[piece][r][c]
                eg_pst = PST_EG[piece][r][c]
                pst_score = mg_pst * phase_weight + eg_pst * (1 - phase_weight)
                score -= pst_score

            # 3. 棋子机动性
            if piece_type in MOBILITY_PIECES:
                moves = get_piece_moves(board_state, r, c)
                mobility_score = len(moves) * MOBILITY_BONUS.get(piece_type, 0)
                if player == PLAYER_R:
                    score += mobility_score
                else:
                    score -= mobility_score

    # 4. 计算将/帅安全分数
    score += _calculate_king_safety_score(current_board)

    # 5. 新增: 计算特殊棋型和动态奖励分数
    score += _calculate_pattern_and_dynamic_score(current_board)

    return int(score)


if __name__ == '__main__':
    # 示例: 评估初始局面
    initial_board = Board()
    initial_score = evaluate(initial_board)
    print('初始局面评估分数:', initial_score)

    # 示例: 红方开局左炮打马后评估分数
    board_without_b_rook = Board()
    board_without_b_rook.make_move(((7, 1), (0, 1)))
    score_after_capture = evaluate(board_without_b_rook)
    print('红方开局左炮打马后评估分数:', score_after_capture)

    # 示例: 残局评估
    endgame_board = Board('4k4/9/9/9/9/9/9/9/4p4/3K5 w - - 0 1')
    endgame_score = evaluate(endgame_board)
    print('残局局面评估分数:', endgame_score)

    # 示例: 沉底炮局面
    bottom_cannon_board = Board('1rbakab2/9/1c2n4/p1p1p1p1p/9/9/P1P1P1P1P/1C2N4/9/2BAKABR1 w - - 0 1')
    print('沉底炮局面评估分数:', evaluate(bottom_cannon_board))
