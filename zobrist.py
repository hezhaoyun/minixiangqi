# -*- coding: utf-8 -*-

import random
from typing import List

# 棋盘维度
BOARD_HEIGHT = 10
BOARD_WIDTH = 9

# 棋子类型数量 (14种不同的棋子)
# 注意：这里不包括空位，因为Zobrist哈希不为空位生成键
PIECE_TYPE_COUNT = 14

# 初始化Zobrist键表
# zobrist_keys[piece_type_idx][row][col]
zobrist_keys: List[List[List[int]]] = [[[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)] for _ in range(PIECE_TYPE_COUNT)]

# 用于标识轮到哪一方走棋的Zobrist键
zobrist_player: int = 0

def init_zobrist():
    """
    初始化Zobrist键表, 为每个位置上的每个棋子类型生成一个唯一的64位随机数
    """
    global zobrist_player, zobrist_keys
    # 使用固定的种子以保证每次运行生成的随机数相同，方便调试
    random.seed(0)

    for i in range(PIECE_TYPE_COUNT):
        for r in range(BOARD_HEIGHT):
            for c in range(BOARD_WIDTH):
                zobrist_keys[i][r][c] = random.getrandbits(64)

    zobrist_player = random.getrandbits(64)

# 在模块加载时自动初始化
init_zobrist()