# -*- coding: utf-8 -*-

import math
import time
import json
import random
from typing import Dict, Optional, Tuple

# --- New Bitboard Imports ---
from src.bitboard import Bitboard, PIECE_TO_BB_INDEX
from src.evaluate import evaluate
import src.moves as moves
from src.zobrist import zobrist_player


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

    def _quiescence_search(self, bb: Bitboard, alpha: float, beta: float) -> float:
        self.nodes_searched += 1
        self._check_time()

        score = evaluate(bb)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

        all_legal_moves = moves.generate_moves(bb)
        capture_moves = []
        opponent_idx = 1 - bb.get_player_bb_idx(bb.player_to_move)
        opponent_pieces_bb = bb.color_bitboards[opponent_idx]
        for from_sq, to_sq in all_legal_moves:
            if (opponent_pieces_bb >> to_sq) & 1:
                capture_moves.append((from_sq, to_sq))

        # TODO: Implement MVV-LVA move ordering here for captures

        for from_sq, to_sq in capture_moves:
            captured_piece = bb.move_piece(from_sq, to_sq)
            score = -self._quiescence_search(bb, -beta, -alpha)
            bb.unmove_piece(from_sq, to_sq, captured_piece)

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def _check_time(self):
        if (self.nodes_searched & 2047) == 0:
            if self.time_limit > 0 and time.time() - self.start_time >= self.time_limit:
                raise StopSearchException()

    def _negamax(self, bb: Bitboard, depth: int, alpha: float, beta: float, allow_null: bool = True) -> Tuple[float, Optional[Move]]:
        self.nodes_searched += 1
        self._check_time()

        # Repetition check
        if bb.history.count(bb.hash_key) > 1:
            return 0, None

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

        if depth <= 0:
            return self._quiescence_search(bb, alpha, beta), None

        # --- Null Move Pruning ---
        R = 2  # Depth reduction factor, reduced from 3 to 2

        # Endgame check for NMP: disable if few major pieces are left
        major_pieces_count = 0
        player_idx = bb.get_player_bb_idx(bb.player_to_move)
        if player_idx == 0: # Red
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[R_ROOK]]).count('1')
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[R_HORSE]]).count('1')
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[R_CANNON]]).count('1')
        else: # Black
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[B_ROOK]]).count('1')
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[B_HORSE]]).count('1')
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[B_CANNON]]).count('1')

        if allow_null and depth >= 3 and not moves.is_check(bb, bb.player_to_move) and major_pieces_count > 1:
            # Make a null move
            bb.player_to_move *= -1
            bb.hash_key ^= zobrist_player

            null_move_score, _ = self._negamax(bb, depth - 1 - R, -beta, -beta + 1, allow_null=False)
            null_move_score = -null_move_score

            # Unmake the null move
            bb.player_to_move *= -1
            bb.hash_key ^= zobrist_player

            if null_move_score >= beta:
                # Store TT entry for null move cutoff
                self.tt[bb.hash_key] = {'depth': depth, 'score': beta, 'flag': TT_LOWER, 'best_move': None}
                return beta, None
        # --- End Null Move Pruning ---

        best_value, best_move = -math.inf, None

        def sq_to_coord(sq: int) -> tuple[int, int]:
            return sq // 9, sq % 9

        legal_moves = moves.generate_moves(bb)

        if not legal_moves:
            if moves.is_check(bb, bb.player_to_move):
                return -MATE_VALUE, None  # Checkmate
            return DRAW_VALUE, None  # Stalemate

        move_scores = []
        for from_sq, to_sq in legal_moves:
            score = 0
            captured_piece = bb.get_piece_on_square(to_sq)
            if captured_piece != EMPTY:
                moving_piece = bb.get_piece_on_square(from_sq)
                score = 1000 + abs(PIECE_VALUES.get(captured_piece, 0)) - abs(PIECE_VALUES.get(moving_piece, 0))
            else:
                # Use history table for quiet moves
                moving_piece = bb.get_piece_on_square(from_sq)
                if moving_piece != EMPTY:
                    piece_idx = Bitboard.piece_to_zobrist_idx(moving_piece)
                    score = self.history_table[piece_idx][to_sq]
            move_scores.append(((from_sq, to_sq), score))

        sorted_moves = sorted(move_scores, key=lambda x: x[1], reverse=True)

        for move, _ in sorted_moves:
            from_sq, to_sq = move
            captured_piece = bb.move_piece(from_sq, to_sq)

            child_value, _ = self._negamax(bb, depth - 1, -beta, -alpha, allow_null=True)
            current_score = -child_value

            bb.unmove_piece(from_sq, to_sq, captured_piece)

            if current_score > best_value:
                best_value = current_score
                best_move = (sq_to_coord(from_sq), sq_to_coord(to_sq))

            alpha = max(alpha, best_value)

            if alpha >= beta:
                if captured_piece == EMPTY:
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
                score, move = self._negamax(board_copy, i, -math.inf, math.inf, allow_null=True)
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
        last_good_move = None
        for i in range(1, depth + 1):
            score, move = self._negamax(board_copy, i, -math.inf, math.inf, allow_null=True)
            if move is not None:
                last_good_move = move
        return score, last_good_move