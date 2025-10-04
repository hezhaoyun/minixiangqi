# -*- coding: utf-8 -*-

'''
中国象棋评估函数
'''
from typing import List

from src.board import Board
from src.constants import *
from src.moves_gen import get_piece_moves

# --- Piece-Square Tables (PST) ---
# fmt: off
KING_PST = [
    [0, 0, 0, 8, 8, 8, 0, 0, 0],
    [0, 0, 0, 8, 8, 8, 0, 0, 0],
    [0, 0, 0, 6, 6, 6, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 6, 6, 6, 0, 0, 0],
    [0, 0, 0, 8, 8, 8, 0, 0, 0],
    [0, 0, 0, 8, 8, 8, 0, 0, 0],
]
GUARD_PST = [
    [0, 0, 0, 20, 0, 20, 0, 0, 0],
    [0, 0, 0, 0, 23, 0, 0, 0, 0],
    [0, 0, 0, 20, 0, 20, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 20, 0, 20, 0, 0, 0],
    [0, 0, 0, 0, 23, 0, 0, 0, 0],
    [0, 0, 0, 20, 0, 20, 0, 0, 0],
]
BISHOP_PST = [
    [0, 0, 20, 0, 0, 0, 20, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 23, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 20, 0, 0, 0, 20, 0, 0],
    [0, 0, 20, 0, 0, 0, 20, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 23, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 20, 0, 0, 0, 20, 0, 0],
]
HORSE_PST = [
    [90, 90, 90, 96, 90, 96, 90, 90, 90],
    [90, 96, 103, 97, 94, 97, 103, 96, 90],
    [92, 98, 99, 103, 99, 103, 99, 98, 92],
    [93, 108, 100, 107, 100, 107, 100, 108, 93],
    [90, 100, 99, 103, 104, 103, 99, 100, 90],
    [90, 98, 101, 102, 103, 102, 101, 98, 90],
    [92, 94, 98, 95, 98, 95, 98, 94, 92],
    [93, 92, 94, 95, 92, 95, 94, 92, 93],
    [85, 90, 92, 93, 78, 93, 92, 90, 85],
    [88, 85, 90, 88, 90, 88, 90, 85, 88],
]
ROOK_PST = [
    [206, 208, 207, 213, 214, 213, 207, 208, 206],
    [206, 212, 209, 216, 233, 216, 209, 212, 206],
    [206, 208, 207, 214, 216, 214, 207, 208, 206],
    [206, 213, 213, 216, 216, 216, 213, 213, 206],
    [208, 211, 211, 214, 215, 214, 211, 211, 208],
    [208, 212, 212, 214, 215, 214, 212, 212, 208],
    [204, 209, 204, 212, 214, 212, 204, 209, 204],
    [198, 208, 204, 212, 212, 212, 204, 208, 198],
    [200, 208, 206, 212, 200, 212, 206, 208, 200],
    [194, 206, 204, 212, 200, 212, 204, 206, 194],
]
CANNON_PST = [
    [100, 100, 96, 91, 90, 91, 96, 100, 100],
    [98, 98, 96, 92, 89, 92, 96, 98, 98],
    [97, 97, 96, 91, 92, 91, 96, 97, 97],
    [96, 99, 99, 98, 100, 98, 99, 99, 96],
    [96, 96, 96, 96, 100, 96, 96, 96, 96],
    [95, 96, 99, 96, 100, 96, 99, 96, 95],
    [96, 96, 96, 96, 96, 96, 96, 96, 96],
    [97, 96, 100, 99, 101, 99, 100, 96, 97],
    [96, 97, 98, 98, 98, 98, 98, 97, 96],
    [96, 96, 97, 99, 99, 99, 97, 96, 96],
]
PAWN_PST = [
    [9, 9, 9, 11, 13, 11, 9, 9, 9],
    [19, 24, 34, 42, 44, 42, 34, 24, 19],
    [19, 24, 32, 37, 37, 37, 32, 24, 19],
    [19, 23, 27, 29, 30, 29, 27, 23, 19],
    [14, 18, 20, 27, 29, 27, 20, 18, 14],
    [7, 0, 13, 0, 16, 0, 13, 0, 7],
    [7, 0, 7, 0, 15, 0, 7, 0, 7],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
]
# fmt: on

PST = {
    B_KING: KING_PST, B_GUARD: GUARD_PST, B_BISHOP: BISHOP_PST, B_HORSE: HORSE_PST,
    B_ROOK: ROOK_PST, B_CANNON: CANNON_PST, B_PAWN: PAWN_PST,
    R_KING: KING_PST, R_GUARD: GUARD_PST, R_BISHOP: BISHOP_PST, R_HORSE: HORSE_PST,
    R_ROOK: ROOK_PST, R_CANNON: CANNON_PST, R_PAWN: PAWN_PST,
}

# 机动性奖励: key 为棋子类型, value 为每一步合法移动的奖励分数
MOBILITY_BONUS = {
    R_ROOK: 2,
    R_HORSE: 3,
    R_CANNON: 1,
}
# 需要计算机动性的棋子类型
MOBILITY_PIECES = {R_ROOK, R_HORSE, R_CANNON}


def evaluate(current_board: Board) -> int:
    '''
    评估函数
    :param current_board: Board 对象
    :return: 局面的评估分数, 正数表示红方优势, 负数表示黑方优势
    '''
    score = 0
    board_state = current_board.board

    # 通过遍历 piece_list 来优化, 而不是遍历整个棋盘
    # 红方
    for r, c in current_board.piece_list[PLAYER_R]:
        piece = board_state[r][c]
        piece_type = abs(piece)

        # 1. 子力价值
        score += PIECE_VALUES[piece]
        # 2. 棋子位置价值
        score += PST[piece][9 - r][8 - c]
        # 3. 棋子机动性
        if piece_type in MOBILITY_PIECES:
            moves = get_piece_moves(board_state, r, c)
            score += len(moves) * MOBILITY_BONUS.get(piece_type, 0)

    # 黑方
    for r, c in current_board.piece_list[PLAYER_B]:
        piece = board_state[r][c]
        piece_type = abs(piece)

        # 1. 子力价值
        score += PIECE_VALUES[piece]
        # 2. 棋子位置价值
        score -= PST[piece][r][c]
        # 3. 棋子机动性
        if piece_type in MOBILITY_PIECES:
            moves = get_piece_moves(board_state, r, c)
            score -= len(moves) * MOBILITY_BONUS.get(piece_type, 0)

    return score


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
