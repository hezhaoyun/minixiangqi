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
            score = evaluate.evaluate(board) * board.player
            return score, None

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
        self.tt.clear()
        return self._negamax(board, depth, -math.inf, math.inf)
