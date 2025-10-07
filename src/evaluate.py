# -*- coding: utf-8 -*-

"""
中国象棋评估函数 - 位棋盘版本
"""
import copy
from typing import List, Tuple

from src.bitboard import Bitboard, PIECE_TO_BB_INDEX, BB_INDEX_TO_PIECE
from src.constants import *
from src.moves import get_rook_moves_bb, get_cannon_moves_bb, HORSE_ATTACKS, HORSE_LEGS, SQUARE_MASKS

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
PAWN_PST_EG = [
    [20, 20, 20, 25, 30, 25, 20, 20, 20], [40, 50, 60, 70, 75, 70, 60, 50, 40],
    [40, 50, 60, 65, 70, 65, 60, 50, 40], [40, 50, 55, 60, 60, 60, 55, 50, 40],
    [30, 40, 45, 50, 50, 50, 45, 40, 30], [15, 20, 25, 30, 30, 30, 25, 20, 15],
    [10, 15, 20, 20, 20, 20, 20, 15, 10], [5, 5, 5, 5, 5, 5, 5, 5, 5],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
]
# fmt: on

PST_MG = { B_KING: KING_PST_MG, B_GUARD: GUARD_PST_MG, B_BISHOP: BISHOP_PST_MG, B_HORSE: HORSE_PST_MG, B_ROOK: ROOK_PST_MG, B_CANNON: CANNON_PST_MG, B_PAWN: PAWN_PST_MG, R_KING: KING_PST_MG, R_GUARD: GUARD_PST_MG, R_BISHOP: BISHOP_PST_MG, R_HORSE: HORSE_PST_MG, R_ROOK: ROOK_PST_MG, R_CANNON: CANNON_PST_MG, R_PAWN: PAWN_PST_MG,}
PST_EG = copy.deepcopy(PST_MG)
PST_EG[R_PAWN] = PAWN_PST_EG
PST_EG[B_PAWN] = PAWN_PST_EG

OPENING_PHASE_MATERIAL = (90 + 40 + 45) * 2
MOBILITY_BONUS = {R_ROOK: 1, R_HORSE: 3, R_CANNON: 1,}
MOBILITY_PIECES = {R_ROOK, R_HORSE, R_CANNON}
KING_SAFETY_PENALTY = 15
PATTERN_BONUS = {'BOTTOM_CANNON': 80, 'PALACE_HEART_HORSE': 70, 'CONNECTED_HORSES': 30, 'ROOK_ON_RIB_FILE': 20,}
DYNAMIC_BONUS = {'ATTACK_PER_MISSING_DEFENDER': 15,}

def popcount(bb: int) -> int:
    return bin(bb).count('1')

def calculate_mobility_score(bb: Bitboard) -> int:
    mobility_score = 0
    occupied = bb.occupied_bitboard

    for player in [PLAYER_R, PLAYER_B]:
        player_idx = 0 if player == PLAYER_R else 1
        own_pieces_bb = bb.color_bitboards[player_idx]
        
        # Rook mobility
        rook_piece = R_ROOK if player == PLAYER_R else B_ROOK
        rooks_bb = bb.piece_bitboards[PIECE_TO_BB_INDEX[rook_piece]]
        temp_rooks = rooks_bb
        while temp_rooks:
            sq = (temp_rooks & -temp_rooks).bit_length() - 1
            moves_bb = get_rook_moves_bb(sq, occupied) & ~own_pieces_bb
            mobility_score += popcount(moves_bb) * MOBILITY_BONUS[R_ROOK] * player
            temp_rooks &= temp_rooks - 1

        # Horse mobility
        horse_piece = R_HORSE if player == PLAYER_R else B_HORSE
        horses_bb = bb.piece_bitboards[PIECE_TO_BB_INDEX[horse_piece]]
        temp_horses = horses_bb
        while temp_horses:
            sq = (temp_horses & -temp_horses).bit_length() - 1
            potential_moves = HORSE_ATTACKS[sq] & ~own_pieces_bb
            temp_moves = potential_moves
            while temp_moves:
                to_sq = (temp_moves & -temp_moves).bit_length() - 1
                leg_sq = HORSE_LEGS[sq][to_sq]
                if not (occupied & SQUARE_MASKS[leg_sq]):
                    mobility_score += MOBILITY_BONUS[R_HORSE] * player
                temp_moves &= temp_moves - 1
            temp_horses &= temp_horses - 1

        # Cannon mobility
        cannon_piece = R_CANNON if player == PLAYER_R else B_CANNON
        cannons_bb = bb.piece_bitboards[PIECE_TO_BB_INDEX[cannon_piece]]
        temp_cannons = cannons_bb
        while temp_cannons:
            sq = (temp_cannons & -temp_cannons).bit_length() - 1
            moves_bb = get_cannon_moves_bb(sq, occupied) & ~own_pieces_bb
            mobility_score += popcount(moves_bb) * MOBILITY_BONUS[R_CANNON] * player
            temp_cannons &= temp_cannons - 1
            
    return mobility_score

def evaluate(bb: Bitboard) -> int:
    material_score = 0
    pst_score = 0

    # 1. Calculate material score efficiently using popcount
    for piece_type, value in PIECE_VALUES.items():
        if piece_type == EMPTY:
            continue
        count = popcount(bb.piece_bitboards[PIECE_TO_BB_INDEX[piece_type]])
        material_score += count * value

    # 2. Determine game phase for tapered evaluation
    current_phase_material = 0
    major_pieces = {R_ROOK, R_HORSE, R_CANNON, R_GUARD, R_BISHOP}
    for piece_type in major_pieces:
        # Consider both sides for phase calculation
        current_phase_material += popcount(bb.piece_bitboards[PIECE_TO_BB_INDEX[piece_type]]) * abs(PIECE_VALUES[piece_type])
        current_phase_material += popcount(bb.piece_bitboards[PIECE_TO_BB_INDEX[-piece_type]]) * abs(PIECE_VALUES[piece_type])
    phase_weight = min(1.0, current_phase_material / OPENING_PHASE_MATERIAL)

    # 3. Calculate PST score
    for piece_bb_idx, piece_bb in enumerate(bb.piece_bitboards):
        temp_bb = piece_bb
        piece_type = BB_INDEX_TO_PIECE[piece_bb_idx]
        player = Bitboard.get_player(piece_type)
        
        while temp_bb:
            sq = (temp_bb & -temp_bb).bit_length() - 1
            r, c = sq // 9, sq % 9
            
            # Always lookup from Red's perspective
            pst_r, pst_c = (9 - r, 8 - c) if player == PLAYER_R else (r, c)
            
            mg_pst = PST_MG[piece_type][pst_r][pst_c]
            eg_pst = PST_EG[piece_type][pst_r][pst_c]
            
            pst = mg_pst * phase_weight + eg_pst * (1 - phase_weight)
            
            if player == PLAYER_R:
                pst_score += pst
            else:
                pst_score -= pst

            temp_bb &= temp_bb - 1

    # --- Final Score ---
    mobility_score = calculate_mobility_score(bb)
    # The score is from Red's perspective. We adjust it for the current player.
    final_score = material_score + pst_score + mobility_score
    
    # Return score from the perspective of the current player to move
    return int(final_score * bb.player_to_move)