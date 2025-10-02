# -*- coding: utf-8 -*-

import math

from board import *
from evaluate import evaluate
from moves_gen import *
from printer import print_board_text


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


def search(fen_string, depth, show_init_board=False):
    initial_board = board_from_fen(fen_string)

    # Determine player from FEN string
    player_char = fen_string.split(' ')[1]
    player = 1 if player_char == 'w' else -1

    if show_init_board:
        print(f"初始棋盘 ({fen_string})：")
        print_board_text(initial_board)

    final_score, best_move = negamax(
        initial_board, depth, -math.inf, math.inf, player)

    print(f"评估分数 (从当前玩家角度): {final_score}，", end="")

    if best_move:
        from_pos, to_pos = best_move
        piece = initial_board[from_pos[0]][from_pos[1]]

        piece_map = {
            B_KING: '將', B_GUARD: '士', B_BISHOP: '象', B_HORSE: '馬', B_ROOK: '車', B_CANNON: '砲', B_PAWN: '卒',
            R_KING: '帥', R_GUARD: '仕', R_BISHOP: '相', R_HORSE: '傌', R_ROOK: '俥', R_CANNON: '炮', R_PAWN: '兵',
        }
        piece_name = piece_map.get(piece, f"Unknown({piece})")

        print(f"最佳着法是: {piece_name} 从 {from_pos} 移动到 {to_pos}，", end='')

        new_board = apply_move(initial_board, best_move)

        print("应用推荐着法后：")
        print_board_text(new_board)

        next_player = -player
        new_fen = board_to_fen(new_board, next_player)
        return new_fen

    print("没有找到最佳着法.")
    return None


if __name__ == "__main__":

    init_fen = board_to_fen(get_initial_board(), 1)

    for s in range(6):
        result_fen = search(init_fen, 4, show_init_board=(s == 0))
        if result_fen is None:
            break

        init_fen = result_fen
