# -*- coding: utf-8 -*-

"""
位棋盘 (Bitboard) 走法生成器 (已修复)
"""

from typing import List
from src.bitboard import Bitboard, get_player, SQUARE_MASKS, PIECE_TO_BB_INDEX, BB_INDEX_TO_PIECE
from src.constants import *

Move = tuple[tuple[int, int], tuple[int, int]]

# --- Masks ---
RED_SIDE_MASK = 0x1FFFFFFFFFFFF  # Bits 0-44 (Black's side for Red to cross)
BLACK_SIDE_MASK = 0x3FFFFFFFFFFFFFFFFFFFFF000000000000 # Bits 45-89

# --- Pre-calculated Attack Tables ---
KING_ATTACKS = [0] * 90
GUARD_ATTACKS = [0] * 90
BISHOP_ATTACKS = [0] * 90
BISHOP_LEGS = {} # from_sq -> to_sq -> leg_sq
HORSE_ATTACKS = [0] * 90
HORSE_LEGS = {} # from_sq -> to_sq -> leg_sq
PAWN_ATTACKS = [[0] * 90, [0] * 90]

# --- Helper functions for pre-computation ---

def _sq(r, c): return r * 9 + c
def _is_valid(r, c): return 0 <= r < 10 and 0 <= c < 9

def _precompute_king_guard_attacks():
    for r in range(10):
        for c in range(9):
            sq = _sq(r, c)
            # King
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                nr, nc = r + dr, c + dc
                if not (3 <= nc <= 5 and (0 <= nr <= 2 or 7 <= nr <= 9)): continue
                KING_ATTACKS[sq] |= SQUARE_MASKS[_sq(nr, nc)]
            # Guard
            for dr, dc in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                nr, nc = r + dr, c + dc
                if not (3 <= nc <= 5 and (0 <= nr <= 2 or 7 <= nr <= 9)): continue
                GUARD_ATTACKS[sq] |= SQUARE_MASKS[_sq(nr, nc)]

def _precompute_bishop_horse_attacks():
    for r in range(10):
        for c in range(9):
            from_sq = _sq(r, c)
            BISHOP_LEGS[from_sq] = {}
            HORSE_LEGS[from_sq] = {}
            # Bishop
            for dr, dc in [(2,2), (2,-2), (-2,2), (-2,-2)]:
                nr, nc = r + dr, c + dc
                if not _is_valid(nr, nc): continue
                to_sq = _sq(nr, nc)
                BISHOP_ATTACKS[from_sq] |= SQUARE_MASKS[to_sq]
                leg_r, leg_c = r + dr // 2, c + dc // 2
                BISHOP_LEGS[from_sq][to_sq] = _sq(leg_r, leg_c)
            # Horse
            for dr, dc in [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]:
                nr, nc = r + dr, c + dc
                if not _is_valid(nr, nc): continue
                to_sq = _sq(nr, nc)
                HORSE_ATTACKS[from_sq] |= SQUARE_MASKS[to_sq]
                leg_r, leg_c = r, c
                if abs(dr) == 2: leg_r += dr // 2
                else: leg_c += dc // 2
                HORSE_LEGS[from_sq][to_sq] = _sq(leg_r, leg_c)

def _precompute_pawn_attacks():
    for r in range(10):
        for c in range(9):
            sq = _sq(r, c)
            # Red Pawns (player_idx 0)
            if _is_valid(r - 1, c): PAWN_ATTACKS[0][sq] |= SQUARE_MASKS[_sq(r - 1, c)]
            if r < 5:
                if _is_valid(r, c - 1): PAWN_ATTACKS[0][sq] |= SQUARE_MASKS[_sq(r, c - 1)]
                if _is_valid(r, c + 1): PAWN_ATTACKS[0][sq] |= SQUARE_MASKS[_sq(r, c + 1)]
            # Black Pawns (player_idx 1)
            if _is_valid(r + 1, c): PAWN_ATTACKS[1][sq] |= SQUARE_MASKS[_sq(r + 1, c)]
            if r > 4:
                if _is_valid(r, c - 1): PAWN_ATTACKS[1][sq] |= SQUARE_MASKS[_sq(r, c - 1)]
                if _is_valid(r, c + 1): PAWN_ATTACKS[1][sq] |= SQUARE_MASKS[_sq(r, c + 1)]

_precompute_king_guard_attacks()
_precompute_bishop_horse_attacks()
_precompute_pawn_attacks()

def get_rook_moves_bb(sq: int, occupied: int) -> int:
    r, c = sq // 9, sq % 9
    attacks = 0
    for nc in range(c + 1, 9): 
        s = _sq(r, nc); attacks |= SQUARE_MASKS[s]
        if occupied & SQUARE_MASKS[s]: break
    for nc in range(c - 1, -1, -1):
        s = _sq(r, nc); attacks |= SQUARE_MASKS[s]
        if occupied & SQUARE_MASKS[s]: break
    for nr in range(r + 1, 10):
        s = _sq(nr, c); attacks |= SQUARE_MASKS[s]
        if occupied & SQUARE_MASKS[s]: break
    for nr in range(r - 1, -1, -1):
        s = _sq(nr, c); attacks |= SQUARE_MASKS[s]
        if occupied & SQUARE_MASKS[s]: break
    return attacks

def get_cannon_moves_bb(sq: int, occupied: int) -> int:
    r, c = sq // 9, sq % 9
    attacks = 0
    screen = False
    for nc in range(c + 1, 9):
        s = _sq(r, nc)
        if not screen:
            if not (occupied & SQUARE_MASKS[s]): attacks |= SQUARE_MASKS[s]
            else: screen = True
        else:
            if occupied & SQUARE_MASKS[s]:
                attacks |= SQUARE_MASKS[s]; break
    screen = False
    for nc in range(c - 1, -1, -1):
        s = _sq(r, nc)
        if not screen:
            if not (occupied & SQUARE_MASKS[s]): attacks |= SQUARE_MASKS[s]
            else: screen = True
        else:
            if occupied & SQUARE_MASKS[s]:
                attacks |= SQUARE_MASKS[s]; break
    screen = False
    for nr in range(r + 1, 10):
        s = _sq(nr, c)
        if not screen:
            if not (occupied & SQUARE_MASKS[s]): attacks |= SQUARE_MASKS[s]
            else: screen = True
        else:
            if occupied & SQUARE_MASKS[s]:
                attacks |= SQUARE_MASKS[s]; break
    screen = False
    for nr in range(r - 1, -1, -1):
        s = _sq(nr, c)
        if not screen:
            if not (occupied & SQUARE_MASKS[s]): attacks |= SQUARE_MASKS[s]
            else: screen = True
        else:
            if occupied & SQUARE_MASKS[s]:
                attacks |= SQUARE_MASKS[s]; break
    return attacks

def generate_all_moves(bb: Bitboard, player: int) -> List[Move]:
    moves = []
    player_idx = 0 if player == PLAYER_R else 1
    own_pieces_bb = bb.color_bitboards[player_idx]
    occupied = bb.occupied_bitboard

    for piece_bb_idx in range(14):
        piece_type = BB_INDEX_TO_PIECE[piece_bb_idx]
        if get_player(piece_type) != player: continue

        piece_bb = bb.piece_bitboards[piece_bb_idx]
        temp_piece_bb = piece_bb
        while temp_piece_bb:
            from_sq = (temp_piece_bb & -temp_piece_bb).bit_length() - 1
            moves_bb = 0

            if piece_type in (R_KING, B_KING):
                moves_bb = KING_ATTACKS[from_sq]
            elif piece_type in (R_GUARD, B_GUARD):
                moves_bb = GUARD_ATTACKS[from_sq]
            elif piece_type == R_BISHOP:
                potential_moves = BISHOP_ATTACKS[from_sq] & BLACK_SIDE_MASK
                temp_moves = potential_moves
                while temp_moves:
                    to_sq = (temp_moves & -temp_moves).bit_length() - 1
                    leg_sq = BISHOP_LEGS[from_sq][to_sq]
                    if not (occupied & SQUARE_MASKS[leg_sq]): moves_bb |= SQUARE_MASKS[to_sq]
                    temp_moves &= temp_moves - 1
            elif piece_type == B_BISHOP:
                potential_moves = BISHOP_ATTACKS[from_sq] & RED_SIDE_MASK
                temp_moves = potential_moves
                while temp_moves:
                    to_sq = (temp_moves & -temp_moves).bit_length() - 1
                    leg_sq = BISHOP_LEGS[from_sq][to_sq]
                    if not (occupied & SQUARE_MASKS[leg_sq]): moves_bb |= SQUARE_MASKS[to_sq]
                    temp_moves &= temp_moves - 1
            elif piece_type in (R_HORSE, B_HORSE):
                potential_moves = HORSE_ATTACKS[from_sq]
                temp_moves = potential_moves
                while temp_moves:
                    to_sq = (temp_moves & -temp_moves).bit_length() - 1
                    leg_sq = HORSE_LEGS[from_sq][to_sq]
                    if not (occupied & SQUARE_MASKS[leg_sq]): moves_bb |= SQUARE_MASKS[to_sq]
                    temp_moves &= temp_moves - 1
            elif piece_type in (R_PAWN, B_PAWN):
                moves_bb = PAWN_ATTACKS[player_idx][from_sq]
            elif piece_type in (R_ROOK, B_ROOK):
                moves_bb = get_rook_moves_bb(from_sq, occupied)
            elif piece_type in (R_CANNON, B_CANNON):
                moves_bb = get_cannon_moves_bb(from_sq, occupied)

            valid_moves_bb = moves_bb & ~own_pieces_bb
            temp_valid_moves = valid_moves_bb
            while temp_valid_moves:
                to_sq = (temp_valid_moves & -temp_valid_moves).bit_length() - 1
                moves.append(((_sq_to_coord(from_sq)), (_sq_to_coord(to_sq))))
                temp_valid_moves &= temp_valid_moves - 1

            temp_piece_bb &= temp_piece_bb - 1
    return moves

def _sq_to_coord(sq: int) -> tuple[int, int]:
    return sq // 9, sq % 9

def is_square_attacked_by(bb: Bitboard, sq: int, attacker_player: int) -> bool:
    occupied = bb.occupied_bitboard
    attacker_idx = 0 if attacker_player == PLAYER_R else 1
    
    # Pawn attacks
    pawn_attacks = PAWN_ATTACKS[1 - attacker_idx][sq]
    pawn_piece = R_PAWN if attacker_player == PLAYER_R else B_PAWN
    if pawn_attacks & bb.piece_bitboards[PIECE_TO_BB_INDEX[pawn_piece]]:
        return True

    # Knight attacks
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

    # Rook and Cannon attacks (sliders)
    rook_piece = R_ROOK if attacker_player == PLAYER_R else B_ROOK
    cannon_piece = R_CANNON if attacker_player == PLAYER_R else B_CANNON
    
    # Horizontal and Vertical
    for get_moves_func, piece_type in [(get_rook_moves_bb, rook_piece), (get_cannon_moves_bb, cannon_piece)] :
        attacks = get_moves_func(sq, occupied)
        if attacks & bb.piece_bitboards[PIECE_TO_BB_INDEX[piece_type]]:
            return True

    # King attacks
    king_attacks = KING_ATTACKS[sq]
    king_piece = R_KING if attacker_player == PLAYER_R else B_KING
    if king_attacks & bb.piece_bitboards[PIECE_TO_BB_INDEX[king_piece]]:
        return True
        
    return False

def is_check(bb: Bitboard, player: int) -> bool:
    king_piece = R_KING if player == PLAYER_R else B_KING
    king_sq_bb = bb.piece_bitboards[PIECE_TO_BB_INDEX[king_piece]]
    if not king_sq_bb:
        return True # Should not happen in a legal game
    king_sq = (king_sq_bb & -king_sq_bb).bit_length() - 1
    
    return is_square_attacked_by(bb, king_sq, -player)

def generate_moves(bb: Bitboard) -> List[Move]:
    """
    Generates all legal moves for the current player.
    """
    legal_moves = []
    player = bb.player_to_move
    
    pseudo_legal_moves = generate_all_moves(bb, player)

    for move in pseudo_legal_moves:
        from_r, from_c = move[0]
        to_r, to_c = move[1]
        from_sq, to_sq = from_r * 9 + from_c, to_r * 9 + to_c
        
        captured = bb.move_piece(from_sq, to_sq)
        if not is_check(bb, player):
            legal_moves.append(move)
        bb.unmove_piece(from_sq, to_sq, captured)
        
    return legal_moves