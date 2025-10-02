# -*- coding: utf-8 -*-

import math
import copy

from board import *
from evaluate import evaluate
from moves_gen import *


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

# Negamax + α-β剪枝实现


def negamax(board, depth, alpha, beta, player):
    """
    使用 Negamax 算法结合 Alpha-Beta 剪枝来搜索最佳着法和分数.

    参数:
    board (list): 当前棋盘状态.
    depth (int): 剩余搜索深度.
    alpha (float): Alpha值.
    beta (float): Beta值.
    player (int): 当前玩家 (1 for Red, -1 for Black).

    返回:
    tuple: (最佳分数, 最佳着法).
    """
    # 1. 到达叶子节点(递归终点), 返回局面评估分数.
    # 分数需要根据当前玩家的视角进行调整.
    if depth == 0:
        score = evaluate(board) * player
        return score, None

    # 2. 初始化最佳分数和最佳着法.
    best_value = -math.inf
    best_move = None

    # 3. 遍历所有子节点 (即所有可能的着法).
    moves = generate_moves(board, player)

    # 如果没有合法走法 (被将死或困毙), 这是一个输棋局面
    if not moves:
        return -math.inf, None  # 返回一个极低分

    for move in moves:
        # 4. 为每个走法创建一个新的棋盘状态
        new_board = apply_move(board, move)

        # 5. 递归调用negamax, 注意参数的变化:
        # - 深度-1.
        # - 交换alpha和beta, 并都取反.
        # - 切换玩家.
        child_value, _ = negamax(new_board, depth - 1, -beta, -alpha, -player)

        # 从子节点返回的是"对手"的分数, 需要取反转换成"我方"的分数.
        current_score = -child_value

        # 6. 如果当前分数更好, 则更新最佳分数和最佳着法.
        if current_score > best_value:
            best_value = current_score
            best_move = move

        # 7. 更新alpha值 (我方能保证的最低分数).
        alpha = max(alpha, best_value)

        # 8. Alpha-Beta 剪枝.
        if alpha >= beta:
            break  # 剪枝

    return best_value, best_move


def search(board, depth, player):
    """
    开始搜索
    :param board: 初始棋盘
    :param depth: 搜索深度
    :param player: 开始玩家
    """
    print("="*20 + f" 开始为玩家 {player} 搜索 (深度: {depth}) " + "="*20)
    final_score, best_move = negamax(board, depth, -math.inf, math.inf, player)
    print("="*20 + " 搜索结束 " + "="*20)

    print(f"\n最终评估分数 (从当前玩家角度): {final_score}")
    if best_move:
        from_pos, to_pos = best_move
        piece = board[from_pos[0]][from_pos[1]]
        print(f"最佳着法是: 棋子 {piece} 从 {from_pos} 移动到 {to_pos}")
    else:
        print("没有找到最佳着法.")


if __name__ == "__main__":
    initial_board = get_initial_board()

    # 示例: 为红方搜索, 搜索深度为3
    # 注意: 深度为3可能需要几秒钟, 深度为4或更高会非常慢
    search(initial_board, depth=3, player=PLAYER_R)
