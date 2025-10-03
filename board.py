# -*- coding: utf-8 -*-

"""
中国象棋棋盘 - 面向对象版本
"""
from typing import List, Optional, Tuple

import zobrist
from constants import (B_BISHOP, B_CANNON, B_GUARD, B_HORSE, B_KING, B_PAWN,
                       B_ROOK, EMPTY, PLAYER_B, PLAYER_R, R_BISHOP, R_CANNON,
                       R_GUARD, R_HORSE, R_KING, R_PAWN, R_ROOK)

# 类型别名
Move = Tuple[Tuple[int, int], Tuple[int, int]]
BoardState = List[List[int]]


def get_player(piece: int) -> int:
    """根据棋子判断玩家"""
    return PLAYER_R if piece > 0 else PLAYER_B


def piece_to_zobrist_idx(piece: int) -> int:
    """
    棋子到Zobrist数组索引的映射
    B_KING(-1) -> 0, B_GUARD(-2) -> 1, ..., B_PAWN(-7) -> 6
    R_KING(1) -> 7, R_GUARD(2) -> 8, ..., R_PAWN(7) -> 13
    """
    if piece < 0:
        return abs(piece) - 1
    elif piece > 0:
        return piece + 6
    return -1  # Should not happen


class Board:
    def __init__(self, fen: Optional[str] = None):
        if fen:
            self.board, self.player = self._from_fen(fen)
        else:
            self.board: BoardState = self._get_initial_board()
            self.player: int = PLAYER_R  # Red starts

        self._initialize_piece_list()
        self.hash_key: int = self._calculate_initial_hash()
        self.history: List[int] = [self.hash_key]  # 跟踪历史局面

    def copy(self):
        """创建并返回当前局面的一个深拷贝."""
        new_b = object.__new__(Board)  # 创建一个空对象,避免调用__init__
        new_b.board = [row[:] for row in self.board]
        new_b.player = self.player
        new_b.piece_list = {
            PLAYER_R: self.piece_list[PLAYER_R][:],
            PLAYER_B: self.piece_list[PLAYER_B][:]
        }
        new_b.hash_key = self.hash_key
        new_b.history = self.history[:]
        return new_b

    def _initialize_piece_list(self):
        self.piece_list = {PLAYER_R: [], PLAYER_B: []}
        for r in range(10):
            for c in range(9):
                piece = self.board[r][c]
                if piece != EMPTY:
                    player = get_player(piece)
                    self.piece_list[player].append((r, c))

    def _get_initial_board(self) -> BoardState:
        return [
            [B_ROOK, B_HORSE, B_BISHOP, B_GUARD, B_KING, B_GUARD, B_BISHOP, B_HORSE, B_ROOK],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, B_CANNON, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, B_CANNON, EMPTY],
            [B_PAWN, EMPTY, B_PAWN, EMPTY, B_PAWN, EMPTY, B_PAWN, EMPTY, B_PAWN],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [R_PAWN, EMPTY, R_PAWN, EMPTY, R_PAWN, EMPTY, R_PAWN, EMPTY, R_PAWN],
            [EMPTY, R_CANNON, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, R_CANNON, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [R_ROOK, R_HORSE, R_BISHOP, R_GUARD, R_KING, R_GUARD, R_BISHOP, R_HORSE, R_ROOK],
        ]

    def _from_fen(self, fen: str) -> Tuple[BoardState, int]:
        fen_map = {
            'k': B_KING, 'a': B_GUARD, 'b': B_BISHOP, 'n': B_HORSE, 'r': B_ROOK, 'c': B_CANNON, 'p': B_PAWN,
            'K': R_KING, 'A': R_GUARD, 'B': R_BISHOP, 'N': R_HORSE, 'R': R_ROOK, 'C': R_CANNON, 'P': R_PAWN,
        }
        parts = fen.split(' ')
        fen_board = parts[0]
        player_char = parts[1]

        board = []
        rows = fen_board.split('/')
        for row_str in rows:
            row = []
            for char in row_str:
                if char.isdigit():
                    row.extend([EMPTY] * int(char))
                else:
                    row.append(fen_map.get(char, EMPTY))
            board.append(row)

        player = PLAYER_R if player_char == 'w' else PLAYER_B
        return board, player

    def to_fen(self) -> str:
        fen_char_map = {
            B_KING: 'k', B_GUARD: 'a', B_BISHOP: 'b', B_HORSE: 'n', B_ROOK: 'r', B_CANNON: 'c', B_PAWN: 'p',
            R_KING: 'K', R_GUARD: 'A', R_BISHOP: 'B', R_HORSE: 'N', R_ROOK: 'R', R_CANNON: 'C', R_PAWN: 'P'
        }
        fen = ''
        for row in self.board:
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
        side = 'w' if self.player == PLAYER_R else 'b'
        fen += f" {side} - - 0 1"
        return fen

    def _calculate_initial_hash(self) -> int:
        h = 0
        for r in range(10):
            for c in range(9):
                piece = self.board[r][c]
                if piece != EMPTY:
                    idx = piece_to_zobrist_idx(piece)
                    h ^= zobrist.zobrist_keys[idx][r][c]

        if self.player == PLAYER_B:
            h ^= zobrist.zobrist_player
        return h

    def make_move(self, move: Move) -> int:
        from_r, from_c = move[0]
        to_r, to_c = move[1]

        moving_piece = self.board[from_r][from_c]
        captured_piece = self.board[to_r][to_c]
        moving_player = get_player(moving_piece)

        # Update piece list
        self.piece_list[moving_player].remove((from_r, from_c))
        self.piece_list[moving_player].append((to_r, to_c))
        if captured_piece != EMPTY:
            captured_player = get_player(captured_piece)
            self.piece_list[captured_player].remove((to_r, to_c))

        # Update hash key
        moving_idx = piece_to_zobrist_idx(moving_piece)
        self.hash_key ^= zobrist.zobrist_keys[moving_idx][from_r][from_c]

        if captured_piece != EMPTY:
            captured_idx = piece_to_zobrist_idx(captured_piece)
            self.hash_key ^= zobrist.zobrist_keys[captured_idx][to_r][to_c]

        self.hash_key ^= zobrist.zobrist_keys[moving_idx][to_r][to_c]
        self.hash_key ^= zobrist.zobrist_player

        # Update board state
        self.board[to_r][to_c] = moving_piece
        self.board[from_r][from_c] = EMPTY
        self.player *= -1
        self.history.append(self.hash_key)

        return captured_piece

    def unmake_move(self, move: Move, captured_piece: int):
        self.history.pop()

        from_r, from_c = move[0]
        to_r, to_c = move[1]
        moving_piece = self.board[to_r][to_c]
        moving_player = get_player(moving_piece)

        # Restore piece list
        self.piece_list[moving_player].remove((to_r, to_c))
        self.piece_list[moving_player].append((from_r, from_c))
        if captured_piece != EMPTY:
            captured_player = get_player(captured_piece)
            self.piece_list[captured_player].append((to_r, to_c))

        # XORing twice restores the original value
        self.hash_key ^= zobrist.zobrist_player
        moving_idx = piece_to_zobrist_idx(moving_piece)
        self.hash_key ^= zobrist.zobrist_keys[moving_idx][to_r][to_c]

        if captured_piece != EMPTY:
            captured_idx = piece_to_zobrist_idx(captured_piece)
            self.hash_key ^= zobrist.zobrist_keys[captured_idx][to_r][to_c]

        self.hash_key ^= zobrist.zobrist_keys[moving_idx][from_r][from_c]

        # Restore board state
        self.board[from_r][from_c] = moving_piece
        self.board[to_r][to_c] = captured_piece
        self.player *= -1