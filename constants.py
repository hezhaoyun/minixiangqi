# -*- coding: utf-8 -*-

'''
全局常量
'''

# 棋子常量
# 黑方 (Black)
B_KING, B_GUARD, B_BISHOP, B_HORSE, B_ROOK, B_CANNON, B_PAWN = -1, -2, -3, -4, -5, -6, -7
# 红方 (Red)
R_KING, R_GUARD, R_BISHOP, R_HORSE, R_ROOK, R_CANNON, R_PAWN = 1, 2, 3, 4, 5, 6, 7
# 空白位置
EMPTY = 0

# 玩家常量
PLAYER_R = 1  # 红方
PLAYER_B = -1  # 黑方

# 胜负判断
MATE_VALUE = 10000
DRAW_VALUE = 0

# 棋子基础价值
PIECE_VALUES = {
    B_KING: -10000, B_GUARD: -100, B_BISHOP: -100, B_HORSE: -450, B_ROOK: -900, B_CANNON: -500, B_PAWN: -100,
    R_KING: 10000, R_GUARD: 100, R_BISHOP: 100, R_HORSE: 450, R_ROOK: 900, R_CANNON: 500, R_PAWN: 100,
    EMPTY: 0
}
