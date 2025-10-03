# -*- coding: utf-8 -*-

import math
import time
from typing import Dict, Optional, Tuple

import board as b
import evaluate
import moves_gen
import tools

# 置换表条目的标志
TT_EXACT = 0  # 精确值 (PV-Node)
TT_LOWER = 1  # Alpha值 (Fail-High)
TT_UPPER = 2  # Beta值 (Fail-Low)


class StopSearchException(Exception):
    """自定义异常, 用于在时间用尽时中止搜索."""
    pass


class Engine:
    def __init__(self):
        self.tt: Dict = {}
        self.nodes_searched = 0
        self.start_time = 0
        self.time_limit = 0

    def _check_time(self):
        """每隔2048个节点检查一次时间, 如果超时则抛出异常."""
        if (self.nodes_searched & 2047) == 0:  # 高效的取模操作
            if time.time() - self.start_time >= self.time_limit:
                raise StopSearchException()

    def _quiescence_search(self, board: b.Board, alpha: float, beta: float) -> Tuple[float, Optional[b.Move]]:
        """
        静态搜索, 用于处理不稳定的局面 (主要指吃子), 以避免地平线效应.
        """
        self.nodes_searched += 1
        self._check_time()

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
                return score, None

            if score > alpha:
                alpha = score

        return alpha, None

    def _negamax(self, board: b.Board, depth: int, alpha: float, beta: float) -> Tuple[float, Optional[b.Move]]:
        """
        使用 Negamax 算法结合 Alpha-Beta 剪枝和置换表来搜索. 
        """
        self.nodes_searched += 1
        self._check_time()

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
            return -math.inf, None

        for move in ordered_moves:
            captured_piece = board.make_move(move)

            if board.history.count(board.hash_key) > 1:
                current_score = 0
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

        if best_value == -math.inf:
            return -math.inf, None

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

    def search_by_depth(self, board: b.Board, depth: int) -> Tuple[float, Optional[b.Move]]:
        """
        执行迭代深化搜索.
        从深度1开始, 迭代搜索到指定的深度.
        这样可以更好地利用置换表, 并允许未来的时间控制.
        """
        board_copy = board.copy()
        self.tt.clear()
        best_move = None
        final_score = -math.inf

        for i in range(1, depth + 1):
            score, move = self._negamax(board_copy, i, -math.inf, math.inf)

            if move:
                best_move = move
            final_score = score

        return final_score, best_move

    def search_by_time(self, board: b.Board, time_limit_seconds: float) -> Tuple[float, Optional[b.Move]]:
        """
        执行基于时间限制的迭代深化搜索.
        """
        board_copy = board.copy()
        self.tt.clear()
        self.start_time = time.time()
        self.time_limit = time_limit_seconds
        self.nodes_searched = 0

        last_completed_score = -math.inf
        last_completed_move = None

        try:
            for i in range(1, 64):
                current_score, current_move = self._negamax(board_copy, i, -math.inf, math.inf)

                last_completed_score = current_score
                last_completed_move = current_move

                if abs(current_score) > (10000 / 2):
                    break
        except StopSearchException:
            pass

        return last_completed_score, last_completed_move
