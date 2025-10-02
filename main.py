# -*- coding: utf-8 -*-

import math
from board import *
from evaluate import evaluate
from moves_gen import generate_moves, order_moves
from tools import print_board_text

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

        # --- 重复局面检测 ---
        # 如果一个局面在历史中出现过（算上当前这次至少2次），则认为是和棋
        # 注意：更严格的规则是三次重复，但两次重复已经有强烈的和棋倾向
        # 在搜索中，我们将其视为和棋(0分)，以避开或寻求和棋
        if board.history.count(board.hash_key) > 1:
            current_score = 0
        else:
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


def search(board, depth):

    # 清空上一轮搜索的置换表，或者可以根据需要保留
    tt.clear()

    return negamax(board, depth, -math.inf, math.inf)


if __name__ == "__main__":
    # 创建一个贯穿整局游戏的棋盘对象
    game_board = Board()

    # 打印开始局面
    print_board_text(game_board)

    # 模拟对局
    for i in range(10):
        final_score, best_move = search(game_board, 4)
        print(f"\n评估分数 (从当前玩家角度): {final_score}，最佳着法是: {best_move}")

        if best_move is None:
            break

        # 将最佳着法应用到主棋盘上，保留历史记录
        game_board.make_move(best_move)
        print_board_text(game_board)
