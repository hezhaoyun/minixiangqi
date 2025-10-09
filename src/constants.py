# -*- coding: utf-8 -*-
'''
定义项目全局常量的模块。

该模块集中管理项目中使用的所有硬编码值，便于维护和调整。
'''

# --- 棋子常量 ---
# 使用唯一的整数来表示每一种棋子。
# 负数代表黑方，正数代表红方。

# 黑方 (Black)
B_KING, B_GUARD, B_BISHOP, B_HORSE, B_ROOK, B_CANNON, B_PAWN = -1, -2, -3, -4, -5, -6, -7
# 红方 (Red)
R_KING, R_GUARD, R_BISHOP, R_HORSE, R_ROOK, R_CANNON, R_PAWN = 1, 2, 3, 4, 5, 6, 7
# 空白位置
EMPTY = 0

# --- 玩家常量 ---
PLAYER_R = 1  # 红方
PLAYER_B = -1  # 黑方

# --- 搜索与评估常量 ---
MATE_VALUE = 10000  # 表示“将死”的评估分值，一个足够大的数
DRAW_VALUE = 0      # 表示“和棋”的评估分值

# --- 棋子基础价值 ---
# 注意：这里的价值与 `evaluate.py` 中的定义重复，未来可以考虑统一。
# 此处的定义可能用于其他非核心评估的场景。
PIECE_VALUES = {
    B_KING: 0, B_GUARD: -100, B_BISHOP: -100, B_HORSE: -450, B_ROOK: -900, B_CANNON: -500, B_PAWN: -100,
    R_KING: 0, R_GUARD: 100, R_BISHOP: 100, R_HORSE: 450, R_ROOK: 900, R_CANNON: 500, R_PAWN: 100,
    EMPTY: 0
}
