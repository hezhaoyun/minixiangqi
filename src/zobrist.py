# -*- coding: utf-8 -*-
"""
Zobrist 哈希实现模块。

Zobrist哈希是一种将棋盘上每个可能的局面都映射到一个唯一的（或极少碰撞的）
哈希值的技术。它通过为棋盘上每个位置的每一种棋子预先生成一个随机数来实现。
一个局面的哈希值就是当前局面中所有棋子对应随机数的异或（XOR）总和。

这种方法的巧妙之处在于，当棋盘上只有一个棋子移动时，我们不需要重新计算
整个棋盘的哈希。新的哈希值可以通过以下方式增量更新：
`new_hash = old_hash ^ piece_at_from_sq_key ^ piece_at_to_sq_key`

这使得哈希计算非常高效，是实现置换表（Transposition Table）等高级
象棋引擎技术的基础。
"""

import random

# --- Zobrist 哈希键 ---

# 14种棋子 (7种红棋, 7种黑棋) 在90个位置上的随机数
# 结构: zobrist_keys[piece_idx][row][col]
zobrist_keys = [[[0] * 9 for _ in range(10)] for _ in range(14)]

# 用于切换走棋方的随机数
zobrist_player = 0


def _initialize_zobrist_keys():
    """
    初始化Zobrist哈希所需的所有随机数。

    此函数在模块加载时被调用一次。为了保证每次运行程序时生成的哈希键都相同，
    使用了固定的随机种子。
    """
    global zobrist_player
    # 使用固定种子以确保每次生成的随机数都一样
    random.seed(826)

    for i in range(14):
        for r in range(10):
            for c in range(9):
                zobrist_keys[i][r][c] = random.getrandbits(64)

    zobrist_player = random.getrandbits(64)


# --- 模块加载时执行初始化 ---
_initialize_zobrist_keys()
