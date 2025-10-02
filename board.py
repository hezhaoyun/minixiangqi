# -*- coding: utf-8 -*-

"""
中国象棋棋盘
"""

import copy

# 定义棋子常量
# 黑方 (Black)
B_KING = -1
B_GUARD = -2
B_BISHOP = -3
B_HORSE = -4
B_ROOK = -5
B_CANNON = -6
B_PAWN = -7

# 红方 (Red)
R_KING = 1
R_GUARD = 2
R_BISHOP = 3
R_HORSE = 4
R_ROOK = 5
R_CANNON = 6
R_PAWN = 7

# 空白位置
EMPTY = 0

# 棋子基础价值
PIECE_VALUES = {
    B_KING: -10000,
    B_GUARD: -100,
    B_BISHOP: -100,
    B_HORSE: -450,
    B_ROOK: -900,
    B_CANNON: -500,
    B_PAWN: -100,
    R_KING: 10000,
    R_GUARD: 100,
    R_BISHOP: 100,
    R_HORSE: 450,
    R_ROOK: 900,
    R_CANNON: 500,
    R_PAWN: 100,
    EMPTY: 0
}

# 棋子位置价值表 (Piece-Square Tables, PST)
# 数组是旋转180度的, 以匹配黑方的视角
# 红方使用时需要翻转

# 将/帅
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

# 士/仕
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

# 象/相
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

# 马
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

# 车
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

# 炮
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

# 兵/卒
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

# 将所有PST存储在一个字典中，方便访问
PST = {
    B_KING: KING_PST,
    B_GUARD: GUARD_PST,
    B_BISHOP: BISHOP_PST,
    B_HORSE: HORSE_PST,
    B_ROOK: ROOK_PST,
    B_CANNON: CANNON_PST,
    B_PAWN: PAWN_PST,
    R_KING: KING_PST,
    R_GUARD: GUARD_PST,
    R_BISHOP: BISHOP_PST,
    R_HORSE: HORSE_PST,
    R_ROOK: ROOK_PST,
    R_CANNON: CANNON_PST,
    R_PAWN: PAWN_PST,
}


def apply_move(board, move):
    """
    执行一个走法, 返回新的棋盘状态
    :param board: 当前棋盘
    :param move: 要执行的走法 ((from_r, from_c), (to_r, to_c))
    :return: 新的棋盘
    """
    new_board = copy.deepcopy(board)
    from_r, from_c = move[0]
    to_r, to_c = move[1]

    piece = new_board[from_r][from_c]
    new_board[to_r][to_c] = piece
    new_board[from_r][from_c] = EMPTY
    return new_board


def get_initial_board():
    """
    返回中国象棋的初始棋盘布局
    """
    return [
        [B_ROOK, B_HORSE, B_BISHOP, B_GUARD, B_KING,
            B_GUARD, B_BISHOP, B_HORSE, B_ROOK],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
        [EMPTY, B_CANNON, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, B_CANNON, EMPTY],
        [B_PAWN, EMPTY, B_PAWN, EMPTY, B_PAWN, EMPTY, B_PAWN, EMPTY, B_PAWN],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
        [R_PAWN, EMPTY, R_PAWN, EMPTY, R_PAWN, EMPTY, R_PAWN, EMPTY, R_PAWN],
        [EMPTY, R_CANNON, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, R_CANNON, EMPTY],
        [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
        [R_ROOK, R_HORSE, R_BISHOP, R_GUARD, R_KING,
            R_GUARD, R_BISHOP, R_HORSE, R_ROOK],
    ]


def board_from_fen(fen):
    """
    从FEN字符串创建棋盘
    FEN standard for Xiangqi (from https://www.wxf-xiangqi.org/images/doc/wxf-fen-v1.0.pdf)
    Piece representation:
    Red: K, A, B, N, R, C, P
    Black: k, a, b, n, r, c, p
    """
    fen_map = {
        'k': B_KING, 'a': B_GUARD, 'b': B_BISHOP, 'n': B_HORSE, 'r': B_ROOK, 'c': B_CANNON, 'p': B_PAWN,
        'K': R_KING, 'A': R_GUARD, 'B': R_BISHOP, 'N': R_HORSE, 'R': R_ROOK, 'C': R_CANNON, 'P': R_PAWN,
    }

    board = []
    fen_board = fen.split(' ')[0]
    rows = fen_board.split('/')

    for row_str in rows:
        row = []
        for char in row_str:
            if char.isdigit():
                row.extend([EMPTY] * int(char))
            else:
                row.append(fen_map.get(char, EMPTY))
        board.append(row)
    return board


def board_to_fen(board, player_to_move):
    """
    将棋盘状态转换为FEN字符串。
    """
    fen_char_map = {
        B_KING: 'k', B_GUARD: 'a', B_BISHOP: 'b', B_HORSE: 'n', B_ROOK: 'r', B_CANNON: 'c', B_PAWN: 'p',
        R_KING: 'K', R_GUARD: 'A', R_BISHOP: 'B', R_HORSE: 'N', R_ROOK: 'R', R_CANNON: 'C', R_PAWN: 'P'
    }

    fen = ''
    for row in board:
        empty_count = 0
        for piece in row:
            if piece == EMPTY:
                empty_count += 1
            else:
                if empty_count > 0:
                    fen += str(empty_count)
                    empty_count = 0
                fen += fen_char_map.get(piece, '')
        if empty_count > 0:
            fen += str(empty_count)
        fen += '/'

    fen = fen[:-1]

    side = 'w' if player_to_move == 1 else 'b'

    fen += f" {side} - - 0 1"

    return fen
