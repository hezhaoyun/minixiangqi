# -*- coding: utf-8 -*-

import math
import time
import json
import random
from typing import Dict, Optional, Tuple

# --- New Bitboard Imports ---
from src.bitboard import Bitboard, PIECE_TO_BB_INDEX
from src.evaluate import evaluate
import src.moves_gen_bitboard as bb_moves

# --- Old Board for API compatibility ---


from src.constants import *

# --- Type Hint for Move ---
Move = tuple[tuple[int, int], tuple[int, int]]

# 置换表条目的标志
TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2


class StopSearchException(Exception):
    pass


class Engine:
    def __init__(self):
        self.tt: Dict = {}
        self.nodes_searched = 0
        self.start_time = 0
        self.time_limit = 0
        self.opening_book = None
        self.book_random = random.Random()
        self.history_table = [[0] * 90 for _ in range(14)]
        self._load_opening_book()

    def _clear_history_table(self):
        self.history_table = [[0] * 90 for _ in range(14)]

    def _load_opening_book(self):
        try:
            with open('opening_book.json', 'r') as f:
                book_str_keys = json.load(f)
                self.opening_book = {int(k): [tuple(map(tuple, move)) for move in v] for k, v in book_str_keys.items()}
            print('开局库加载成功。')
        except FileNotFoundError:
            print('未找到开局库文件, 将不使用开局库。')

    def query_opening_book(self, bb: Bitboard) -> Optional[Move]:
        if not self.opening_book:
            return None
        if bb.hash_key in self.opening_book:
            # TODO: Validate book moves against new move generator
            return self.book_random.choice(self.opening_book[bb.hash_key])
        return None

    def _check_time(self):
        if (self.nodes_searched & 2047) == 0:
            if self.time_limit > 0 and time.time() - self.start_time >= self.time_limit:
                raise StopSearchException()

    def _negamax(self, bb: Bitboard, depth: int, alpha: float, beta: float) -> Tuple[float, Optional[Move]]:
        self.nodes_searched += 1
        self._check_time()

        original_alpha = alpha
        tt_entry = self.tt.get(bb.hash_key)

        if tt_entry and tt_entry['depth'] >= depth:
            score, flag, best_move = tt_entry['score'], tt_entry['flag'], tt_entry.get('best_move')
            if flag == TT_EXACT:
                return score, best_move
            elif flag == TT_LOWER:
                alpha = max(alpha, score)
            elif flag == TT_UPPER:
                beta = min(beta, score)
            if alpha >= beta:
                return score, best_move

        if depth == 0:
            # Quiescence search would go here
            return evaluate(bb) * bb.player_to_move, None

        best_value, best_move = -math.inf, None

        def sq_to_coord(sq: int) -> tuple[int, int]:
            return sq // 9, sq % 9

        # Generate legal moves
        legal_moves = bb_moves.generate_moves(bb)

        # TODO: Implement move ordering with history heuristic for bitboard moves

        if not legal_moves:
            if bb_moves.is_check(bb, bb.player_to_move):
                return -MATE_VALUE, None  # Checkmate
            return DRAW_VALUE, None  # Stalemate

        for from_sq, to_sq in legal_moves:
            captured_piece = bb.move_piece(from_sq, to_sq)

            if bb.history.count(bb.hash_key) > 1:
                current_score = 0
            else:
                child_value, _ = self._negamax(bb, depth - 1, -beta, -alpha)
                current_score = -child_value

            if current_score > best_value:
                best_value = current_score
                best_move = (sq_to_coord(from_sq), sq_to_coord(to_sq))

            bb.unmove_piece(from_sq, to_sq, captured_piece)

            alpha = max(alpha, best_value)

            if alpha >= beta:
                if captured_piece == EMPTY:
                    # After unmove, the piece is back at from_sq
                    moving_piece = bb.get_piece_on_square(from_sq)
                    if moving_piece != EMPTY:
                        piece_idx = Bitboard.piece_to_zobrist_idx(moving_piece)
                        self.history_table[piece_idx][to_sq] += depth * depth
                break

        flag = TT_EXACT
        if best_value <= original_alpha:
            flag = TT_UPPER
        elif best_value >= beta:
            flag = TT_LOWER

        self.tt[bb.hash_key] = {'depth': depth, 'score': best_value, 'flag': flag, 'best_move': best_move}
        return best_value, best_move

    def search_by_time(self, bb: Bitboard, time_limit_seconds: float) -> Tuple[float, Optional[Move]]:
        board_copy = bb.copy()
        book_move = self.query_opening_book(board_copy)
        if book_move:
            return 0, book_move

        self.tt.clear()
        self._clear_history_table()
        self.start_time = time.time()
        self.time_limit = time_limit_seconds
        self.nodes_searched = 0
        last_completed_move = None

        try:
            for i in range(1, 64):
                score, move = self._negamax(board_copy, i, -math.inf, math.inf)
                if move:
                    last_completed_move = move
                if abs(score) > (MATE_VALUE / 2):
                    break
        except StopSearchException:
            pass
        return 0, last_completed_move

    def search_by_depth(self, bb: Bitboard, depth: int) -> Tuple[float, Optional[Move]]:
        board_copy = bb.copy()
        book_move = self.query_opening_book(board_copy)
        if book_move:
            return 0, book_move

        self.tt.clear()
        self._clear_history_table()
        score, move = -math.inf, None
        for i in range(1, depth + 1):
            score, move = self._negamax(board_copy, i, -math.inf, math.inf)
        return score, move
