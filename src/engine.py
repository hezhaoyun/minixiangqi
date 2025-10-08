# -*- coding: utf-8 -*-
"""
象棋引擎核心，负责搜索和评估。

该模块包含了Engine类，它是驱动象棋AI的核心。它实现了基于Alpha-Beta剪枝的
负极大值（Negamax）搜索算法，并融合了多种现代象棋引擎优化技术，例如：
- 置换表 (Transposition Tables)
- 静默搜索 (Quiescence Search)
- 空着裁剪 (Null Move Pruning)
- 后期走法裁减 (Late Move Reductions)
- 历史启发 (History Heuristic)
- 开局库 (Opening Book)
"""

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

# 置换表条目的标志 (Flags for Transposition Table entries)
TT_EXACT = 0  # 精确值 (Exact score)
TT_LOWER = 1  # 下界值 (Lower bound, alpha)
TT_UPPER = 2  # 上界值 (Upper bound, beta)


class StopSearchException(Exception):
    """当搜索时间超过限制时抛出此异常。"""
    pass


class Engine:
    """
    象棋AI引擎类。

    Attributes:
        transposition_table (Dict): 置换表，用于缓存已计算过的局面的评估值和最佳走法。
        nodes_searched (int): 当前搜索访问的节点总数。
        start_time (float): 搜索开始的时间戳。
        time_limit (float): 单次搜索的时间限制（秒）。
        opening_book (Dict): 开局库，存储从JSON文件中加载的开局走法。
        history_table (list): 历史启发表，用于走法排序，优先考虑在其他分支中表现好的走法。
    """

    def __init__(self):
        """初始化引擎。"""
        self.transposition_table: Dict = {}
        self.nodes_searched = 0
        self.start_time = 0
        self.time_limit = 0
        self.opening_book = None
        self.book_random = random.Random()
        self.history_table = [[0] * 90 for _ in range(14)]
        self._load_opening_book()

    def _clear_history_table(self):
        """清空历史启发表。"""
        self.history_table = [[0] * 90 for _ in range(14)]

    def _load_opening_book(self):
        """从 '''opening_book.json''' 文件加载开局库。"""
        try:
            with open('''opening_book.json''', 'r') as f:
                book_str_keys = json.load(f)
                self.opening_book = {int(k): [tuple(map(tuple, move)) for move in v] for k, v in book_str_keys.items()}
            print('开局库加载成功。')
        except FileNotFoundError:
            print('未找到开局库文件, 将不使用开局库。')

    def query_opening_book(self, bb: Bitboard) -> Optional[Move]:
        """
        查询开局库。

        Args:
            bb (Bitboard): 当前棋盘局面。

        Returns:
            Optional[Move]: 如果当前局面在开局库中，则返回一个推荐走法；否则返回None。
        """
        if not self.opening_book:
            return None

        if bb.hash_key in self.opening_book:
            return self.book_random.choice(self.opening_book[bb.hash_key])

        return None

    def _quiescence_search(self, bb: Bitboard, alpha: float, beta: float) -> float:
        """
        静默搜索。

        在达到常规搜索深度后，继续搜索所有吃子走法，直到局面“平静”下来，
        以避免因未解决的战术组合而对局面做出错误评估（“地平线效应”）。

        Args:
            bb (Bitboard): 当前棋盘局面。
            alpha (float): Alpha值（当前搜索窗口的下界）。
            beta (float): Beta值（当前搜索窗口的上界）。

        Returns:
            float: 局面的评估值。
        """
        self.nodes_searched += 1
        self._check_time()

        score = evaluate(bb)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

        # 只生成并搜索吃子走法
        all_legal_moves = moves.generate_moves(bb)
        capture_moves = []
        opponent_idx = 1 - Bitboard.get_player_bb_idx(bb.player_to_move)
        opponent_pieces_bb = bb.color_bitboards[opponent_idx]
        for from_sq, to_sq in all_legal_moves:
            if (opponent_pieces_bb >> to_sq) & 1:
                capture_moves.append((from_sq, to_sq))

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
        """
        检查搜索是否超时。
        每搜索2048个节点检查一次，以减少时间检查的开销。
        """
        if (self.nodes_searched & 2047) == 0:
            if self.time_limit > 0 and time.time() - self.start_time >= self.time_limit:
                raise StopSearchException()

    def _negamax(self, bb: Bitboard, depth: int, alpha: float, beta: float, allow_null: bool = True) -> Tuple[float, Optional[Move]]:
        """
        核心搜索函数，实现了带有多种优化的负极大值算法。

        Args:
            bb (Bitboard): 当前棋盘局面。
            depth (int): 剩余搜索深度。
            alpha (float): 当前搜索窗口的下界。
            beta (float): 当前搜索窗口的上界。
            allow_null (bool): 是否允许在此节点进行空着裁剪。

        Returns:
            Tuple[float, Optional[Move]]: 返回评估分数和最佳走法。
        """
        self.nodes_searched += 1
        self._check_time()

        # --- 重复局面检测 ---
        # 如果当前局面在历史中重复出现，认为是和棋。
        if depth > 0 and bb.history.count(bb.hash_key) > 2:
            return 0, None

        # --- 置换表查询 ---
        # 尝试从置换表中获取当前局面的缓存信息，如果缓存的深度足够，则可以直接使用。
        original_alpha = alpha
        tt_entry = self.transposition_table.get(bb.hash_key)

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

        # --- 到达搜索深度叶子节点 ---
        # 到达常规搜索深度后，转入静默搜索。
        if depth <= 0:
            return self._quiescence_search(bb, alpha, beta), None

        # --- 空着裁剪 (Null Move Pruning) ---
        # 假设当前方放弃一步棋，如果局面评估值仍然很高（>= beta），
        # 那么可以认为当前局面本身就很好，可以提前剪枝。
        # R是裁剪的深度，自适应调整，深度越深，裁剪得越狠。
        R = 3 + depth // 6
        major_pieces_count = 0
        player_idx = Bitboard.get_player_bb_idx(bb.player_to_move)
        if player_idx == 0:  # Red
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[R_ROOK]]).count('1')
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[R_HORSE]]).count('1')
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[R_CANNON]]).count('1')
        else:  # Black
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[B_ROOK]]).count('1')
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[B_HORSE]]).count('1')
            major_pieces_count += bin(bb.piece_bitboards[PIECE_TO_BB_INDEX[B_CANNON]]).count('1')

        is_in_check = moves.is_check(bb, bb.player_to_move)

        if allow_null and not is_in_check and depth >= 3 and major_pieces_count > 1:
            bb.player_to_move *= -1
            bb.hash_key ^= zobrist_player
            null_move_score, _ = self._negamax(bb, depth - 1 - R, -beta, -beta + 1, allow_null=False)
            null_move_score = -null_move_score
            bb.player_to_move *= -1
            bb.hash_key ^= zobrist_player
            if null_move_score >= beta:
                self.transposition_table[bb.hash_key] = {'depth': depth, 'score': beta, 'flag': TT_LOWER, 'best_move': None}
                return beta, None

        best_value = -math.inf
        best_move = None

        def sq_to_coord(sq: int) -> tuple[int, int]:
            return sq // 9, sq % 9

        # --- 走法生成与排序 ---
        legal_moves = moves.generate_moves(bb)

        if not legal_moves:
            if is_in_check:
                # 被将死，返回一个与深度相关的负无穷大值，倾向于选择能更快将死对方的路径。
                return -MATE_VALUE + depth, None
            # 逼和
            return DRAW_VALUE, None

        # 走法排序：优先搜索吃子走法（按MVV-LVA思想估分），然后是历史表启发的好走法。
        move_scores = []
        for from_sq, to_sq in legal_moves:
            score = 0
            captured_piece = bb.get_piece_on_square(to_sq)
            if captured_piece != EMPTY:
                moving_piece = bb.get_piece_on_square(from_sq)
                score = 1000 + abs(PIECE_VALUES.get(captured_piece, 0)) - abs(PIECE_VALUES.get(moving_piece, 0))
            else:
                moving_piece = bb.get_piece_on_square(from_sq)
                if moving_piece != EMPTY:
                    piece_idx = Bitboard.piece_to_zobrist_idx(moving_piece)
                    score = self.history_table[piece_idx][to_sq]
            move_scores.append(((from_sq, to_sq), score))

        sorted_moves = sorted(move_scores, key=lambda x: x[1], reverse=True)

        # --- 遍历走法进行搜索 ---
        move_index = 0
        for move, _ in sorted_moves:
            move_index += 1
            from_sq, to_sq = move

            captured_piece_on_sq = bb.get_piece_on_square(to_sq)
            is_quiet = captured_piece_on_sq == EMPTY

            # --- 后期走法裁减 (Late Move Reduction - LMR) ---
            # 对排序靠后的安静走法，我们认为它们大概率不是好棋，
            # 因此用一个较浅的深度去搜索它们，以节省时间。
            reduction = 0
            if depth >= 3 and move_index > 4 and is_quiet and not is_in_check:
                reduction = 1

            captured_piece = bb.move_piece(from_sq, to_sq)

            # 使用缩减后的深度进行搜索
            child_value, _ = self._negamax(bb, depth - 1 - reduction, -beta, -alpha, allow_null=True)

            # 如果缩减深度的搜索结果意外地好（突破了alpha），
            # 那说明这个走法可能是个“漏网之鱼”，需要用完整深度重新搜索一次。
            if reduction > 0 and -child_value > alpha:
                child_value, _ = self._negamax(bb, depth - 1, -beta, -alpha, allow_null=True)

            bb.unmove_piece(from_sq, to_sq, captured_piece)

            if child_value is None:
                continue

            current_score = -child_value

            if current_score > best_value:
                best_value = current_score
                best_move = (sq_to_coord(from_sq), sq_to_coord(to_sq))

            alpha = max(alpha, best_value)

            # --- Alpha-Beta 剪枝 ---
            if alpha >= beta:
                # 如果一个安静走法（非吃子）导致了beta剪枝，
                # 那么它是一个“好”走法，我们增加它在历史表中的权重。
                if is_quiet:
                    moving_piece = bb.get_piece_on_square(from_sq)
                    if moving_piece != EMPTY:
                        piece_idx = Bitboard.piece_to_zobrist_idx(moving_piece)
                        self.history_table[piece_idx][to_sq] += depth * depth
                break

        # --- 置换表存储 ---
        # 将当前节点的搜索结果存入置换表，以便后续使用。
        flag = TT_EXACT
        if best_value <= original_alpha:
            flag = TT_UPPER
        elif best_value >= beta:
            flag = TT_LOWER

        self.transposition_table[bb.hash_key] = {
            'depth': depth, 'score': best_value, 'flag': flag, 'best_move': best_move,
        }

        return best_value, best_move

    def search_by_time(self, bb: Bitboard, time_limit_seconds: float) -> Tuple[float, Optional[Move]]:
        """
        在给定的时间内进行搜索。

        采用迭代加深（Iterative Deepening）的方式，从深度1开始，
        逐步增加深度进行搜索，直到时间耗尽。

        Args:
            bb (Bitboard): 初始棋盘局面。
            time_limit_seconds (float): 搜索时间限制（秒）。

        Returns:
            Tuple[float, Optional[Move]]: 返回最终评估分数和找到的最佳走法。
        """
        board_copy = bb.copy()
        book_move = self.query_opening_book(board_copy)
        if book_move:
            return 0, book_move

        self.transposition_table.clear()
        self._clear_history_table()
        self.start_time = time.time()
        self.time_limit = time_limit_seconds
        self.nodes_searched = 0
        last_completed_move = None

        try:
            # 迭代加深搜索
            for i in range(1, 64):
                score, move = self._negamax(board_copy, i, -MATE_VALUE, MATE_VALUE, allow_null=True)
                if move is not None:
                    last_completed_move = move

                # 如果找到杀棋，提前终止搜索
                if abs(score) > (MATE_VALUE - 100):
                    break
        except StopSearchException:
            pass

        end_time = time.time()
        time_taken = end_time - self.start_time

        print(f"Score: {score}, depth: {i}, time: {time_taken:.2f}, nodes: {self.nodes_searched}")

        return 0, last_completed_move

    def search_by_depth(self, bb: Bitboard, depth: int) -> Tuple[float, Optional[Move]]:
        """
        搜索指定的深度。

        同样采用迭代加深，但会一直搜索到指定的深度。

        Args:
            bb (Bitboard): 初始棋盘局面。
            depth (int): 目标搜索深度。

        Returns:
            Tuple[float, Optional[Move]]: 返回最终评估分数和找到的最佳走法。
        """
        board_copy = bb.copy()
        book_move = self.query_opening_book(board_copy)
        if book_move:
            return 0, book_move

        self.transposition_table.clear()
        self._clear_history_table()
        score, move = -math.inf, None
        last_good_move = None
        for i in range(1, depth + 1):
            score, move = self._negamax(board_copy, i, -MATE_VALUE, MATE_VALUE, allow_null=True)
            if move is not None:
                last_good_move = move
            if abs(score) > (MATE_VALUE - 100):  # Stop if a mate is found
                break

        return score, last_good_move
