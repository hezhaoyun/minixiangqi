# -*- coding: utf-8 -*-

import random

# 棋盘维度
BOARD_HEIGHT = 10
BOARD_WIDTH = 9

# 棋子类型数量 (14种棋子 + 1个空位)
PIECE_COUNT = 15

# 初始化Zobrist键表
# zobrist_keys[piece_type][row][col]
zobrist_keys = [[[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)] for _ in range(PIECE_COUNT)]

# 用于标识轮到哪一方走棋的Zobrist键
zobrist_player = 0


def init_zobrist():
    """
    初始化Zobrist键表, 为每个位置上的每个棋子类型生成一个唯一的64位随机数
    """
    global zobrist_player
    # 使用固定的种子以保证每次运行生成的随机数相同，方便调试
    # 在最终版本中可以移除种子，或使用更随机的种子
    random.seed(0)

    for i in range(PIECE_COUNT):
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                zobrist_keys[i][r][c] = random.getrandbits(64)

    zobrist_player = random.getrandbits(64)


# 在模块加载时自动初始化
init_zobrist()
