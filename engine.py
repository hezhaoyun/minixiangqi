# -*- coding: utf-8 -*-

import math
from typing import Dict, Optional, Tuple

import board as b
import evaluate
import moves_gen
import tools

# 置换表条目的标志
TT_EXACT = 0  # 精确值 (PV-Node)
TT_LOWER = 1  # Alpha值 (Fail-High)
TT_UPPER = 2  # Beta值 (Fail-Low)


class Engine:
    def __init__(self):
        # 使用一个字典作为置换表
        self.tt: Dict = {}

    def _quiescence_search(self, board: b.Board, alpha: float, beta: float) -> Tuple[float, Optional[b.Move]]:
        """
        静态搜索, 用于处理不稳定的局面 (主要指吃子), 以避免地平线效应.
        """
        stand_pat_score = evaluate.evaluate(board) * board.player

        if stand_pat_score >= beta:
            return stand_pat_score, None

        alpha = max(alpha, stand_pat_score)

        capture_moves = moves_gen.generate_capture_moves(board)
        ordered_moves = moves_gen.order_moves(board.board, capture_moves, None)

        for move in ordered_moves:
            captured_piece = board.make_move(move)
            score, _ = self._quiescence_search(board, -beta, -alpha)
            score = -score
            board.unmake_move(move, captured_piece)

            if score >= beta:
                # 返回一个下界值, 因为实际值可能更高
                return score, None

            if score > alpha:
                alpha = score

        return alpha, None

    def _negamax(self, board: b.Board, depth: int, alpha: float, beta: float) -> Tuple[float, Optional[b.Move]]:
        """
        使用 Negamax 算法结合 Alpha-Beta 剪枝和置换表来搜索. 
        """
        original_alpha = alpha
        tt_entry = self.tt.get(board.hash_key)

        if tt_entry and tt_entry['depth'] >= depth:
            score = tt_entry['score']
            flag = tt_entry['flag']
            best_move = tt_entry.get('best_move')

            if flag == TT_EXACT:
                return score, best_move
            elif flag == TT_LOWER:
                alpha = max(alpha, score)
            elif flag == TT_UPPER:
                beta = min(beta, score)

            if alpha >= beta:
                return score, best_move

        if depth == 0:
            return self._quiescence_search(board, alpha, beta)

        best_value, best_move = -math.inf, None
        best_move_from_tt = tt_entry.get('best_move') if tt_entry else None

        moves = moves_gen.generate_moves(board)
        ordered_moves = moves_gen.order_moves(board.board, moves, best_move_from_tt)

        if not ordered_moves:
            # 如果没有合法走法, 意味着被将死或困毙
            # 对于被将死的情况, 返回一个极小值
            return -math.inf, None

        for move in ordered_moves:
            captured_piece = board.make_move(move)

            # 检查重复局面, 避免无限循环
            if board.history.count(board.hash_key) > 1:
                current_score = 0  # 和棋分数为0
            else:
                child_value, _ = self._negamax(board, depth - 1, -beta, -alpha)
                current_score = -child_value

            board.unmake_move(move, captured_piece)

            if current_score > best_value:
                best_value = current_score
                best_move = move

            alpha = max(alpha, best_value)

            if alpha >= beta:
                break

        # 如果没有找到任何大于-inf的走法 (比如所有走法都导致重复局面),
        # best_value 可能是-inf, 此时不应存入置换表
        if best_value == -math.inf:
            return -math.inf, None

        # 存入置换表
        flag = TT_EXACT
        if best_value <= original_alpha:
            flag = TT_UPPER
        elif best_value >= beta:
            flag = TT_LOWER

        self.tt[board.hash_key] = {
            'depth': depth,
            'score': best_value,
            'flag': flag,
            'best_move': best_move
        }

        return best_value, best_move

    def search(self, board: b.Board, depth: int) -> Tuple[float, Optional[b.Move]]:
        """
        执行迭代深化搜索.
        从深度1开始, 迭代搜索到指定的深度.
        这样可以更好地利用置换表, 并允许未来的时间控制.
        """
        self.tt.clear()

        best_move = None
        final_score = -math.inf

        for i in range(1, depth + 1):
            score, move = self._negamax(board, i, -math.inf, math.inf)

            # 只有在搜索成功返回一个有效走法时才更新最佳走法
            if move:
                best_move = move
            final_score = score

        return final_score, best_move
