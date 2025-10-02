# -*- coding: utf-8 -*-

import math
from board import *
from evaluate import evaluate
from moves_gen import generate_moves, order_moves
from tools import print_board_text, print_search_result

# --- 置换表 (Transposition Table) ---
# 使用一个简单的字典作为置换表
tt = {}

# 置换表条目的标志
TT_EXACT = 0  # 精确值 (PV-Node)
TT_LOWER = 1  # Alpha值 (Fail-High)
TT_UPPER = 2  # Beta值 (Fail-Low)


def negamax(board, depth, alpha, beta):
    """
    使用 Negamax 算法结合 Alpha-Beta 剪枝和置换表来搜索.
    """
    # --- 1. 置换表查询 ---
    original_alpha = alpha
    tt_entry = tt.get(board.hash_key)

    if tt_entry and tt_entry['depth'] >= depth:
        score = tt_entry['score']
        flag = tt_entry['flag']

        if flag == TT_EXACT:
            return score, tt_entry['best_move']
        elif flag == TT_LOWER:
            alpha = max(alpha, score)
        elif flag == TT_UPPER:
            beta = min(beta, score)

        if alpha >= beta:
            return score, tt_entry['best_move']

    # --- 2. 到达叶子节点 ---
    if depth == 0:
        score = evaluate(board.board) * board.player
        return score, None

    # --- 3. 遍历所有子节点 ---
    best_value, best_move = -math.inf, None

    best_move_from_tt = tt_entry.get('best_move') if tt_entry else None

    moves = generate_moves(board.board, board.player)
    ordered_moves = order_moves(board.board, moves, best_move_from_tt)

    if not ordered_moves:
        return -math.inf, None

    # 追踪是否已经搜索过PV节点
    is_pv_node = True

    for move in ordered_moves:
        # 做出走法
        captured_piece = board.make_move(move)

        # 递归调用, 注意参数的变化
        child_value, _ = negamax(board, depth - 1, -beta, -alpha)
        current_score = -child_value

        # 撤销走法
        board.unmake_move(move, captured_piece)

        # 更新最佳分数和最佳着法
        if current_score > best_value:
            best_value = current_score
            best_move = move

        alpha = max(alpha, best_value)

        if alpha >= beta:
            break  # 剪枝

    # --- 4. 置换表存储 ---
    flag = TT_EXACT
    if best_value <= original_alpha:
        flag = TT_UPPER  # Fail-Low, 得到的是上限
    elif best_value >= beta:
        flag = TT_LOWER  # Fail-High, 得到的是下限

    tt[board.hash_key] = {
        'depth': depth,
        'score': best_value,
        'flag': flag,
        'best_move': best_move
    }

    return best_value, best_move


def search(fen_string, depth, show_init_board=False):
    board_obj = Board(fen=fen_string)

    if show_init_board:
        print(f"初始棋盘 ({fen_string})：")
        print_board_text(board_obj.board)

    # 清空上一轮搜索的置换表，或者可以根据需要保留
    tt.clear()

    final_score, best_move = negamax(board_obj, depth, -math.inf, math.inf)
    print_search_result(final_score, best_move, board_obj)

    return board_obj.to_fen() if best_move else None


if __name__ == "__main__":
    # 从初始局面开始
    board = Board()
    init_fen = board.to_fen()

    for s in range(6):
        result_fen = search(
            init_fen, 4, show_init_board=(s == 0))  # 增加一点深度以体现性能
        if result_fen is None:
            print("对局结束")
            break
        init_fen = result_fen
