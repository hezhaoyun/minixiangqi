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


def print_board_text(board):
    """以文本形式打印棋盘,并区分颜色"""
    piece_map = {
        B_KING: '將', B_GUARD: '士', B_BISHOP: '象', B_HORSE: '馬', B_ROOK: '車', B_CANNON: '砲', B_PAWN: '卒',
        R_KING: '帥', R_GUARD: '仕', R_BISHOP: '相', R_HORSE: '傌', R_ROOK: '俥', R_CANNON: '炮', R_PAWN: '兵',
        EMPTY: '・'
    }
    print("\n   0  1  2  3  4  5  6  7  8")
    print("-----------------------------")
    for i, row in enumerate(board):
        row_items = [f"{i}|"]
        for piece in row:
            row_items.append(piece_map[piece])
        print(" ".join(row_items))
    print("-----------------------------")


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
    return final_score, best_move


if __name__ == "__main__":
    initial_board = board_from_fen(
        "rCbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/7C1/9/RNBAKABNR b - - 0 1"
    )

    print("初始棋盘:")
    print_board_text(initial_board)

    # 示例: 为红方搜索, 搜索深度为3
    # 注意: 深度为3可能需要几秒钟, 深度为4或更高会非常慢
    depth = 3
    player = 1  # Red is 1, Black is -1
    final_score, best_move = search(initial_board, depth=depth, player=player)

    print(f"\n最终评估分数 (从当前玩家角度): {final_score}")
    if best_move:
        from_pos, to_pos = best_move
        piece = initial_board[from_pos[0]][from_pos[1]]

        piece_map = {
            B_KING: '將', B_GUARD: '士', B_BISHOP: '象', B_HORSE: '馬', B_ROOK: '車', B_CANNON: '砲', B_PAWN: '卒',
            R_KING: '帥', R_GUARD: '仕', R_BISHOP: '相', R_HORSE: '傌', R_ROOK: '俥', R_CANNON: '炮', R_PAWN: '兵',
        }
        piece_name = piece_map.get(piece, f"Unknown({piece})")

        print(f"最佳着法是: {piece_name} 从 {from_pos} 移动到 {to_pos}")

        new_board = apply_move(initial_board, best_move)

        print("\n推荐走法后的棋盘:")
        print_board_text(new_board)

        next_player = -player
        new_fen = board_to_fen(new_board, next_player)
        print(f"\n新棋盘的FEN字符串: {new_fen}")

    else:
        print("没有找到最佳着法.")
