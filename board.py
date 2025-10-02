# -*- coding: utf-8 -*-

"""
中国象棋棋盘 - 面向对象版本
"""
from zobrist import zobrist_keys, zobrist_player

# 定义棋子常量
# 黑方 (Black)
B_KING = -1
B_GUARD = -2
B_BISHOP = -3
B_HORSE = -4
B_ROOK = -5
B_CANNON = -6
B_PAWN = -7

# 红方 (Red)
R_KING = 1
R_GUARD = 2
R_BISHOP = 3
R_HORSE = 4
R_ROOK = 5
R_CANNON = 6
R_PAWN = 7

# 空白位置
EMPTY = 0

# 棋子基础价值
PIECE_VALUES = {
    B_KING: -10000, B_GUARD: -100, B_BISHOP: -100, B_HORSE: -450, B_ROOK: -900, B_CANNON: -500, B_PAWN: -100,
    R_KING: 10000, R_GUARD: 100, R_BISHOP: 100, R_HORSE: 450, R_ROOK: 900, R_CANNON: 500, R_PAWN: 100,
    EMPTY: 0
}

# 棋子到Zobrist数组索引的映射
# B_KING(-1) -> 0, B_GUARD(-2) -> 1, ..., B_PAWN(-7) -> 6
# R_KING(1) -> 7, R_GUARD(2) -> 8, ..., R_PAWN(7) -> 13
def piece_to_zobrist_idx(piece):
    if piece < 0:
        return abs(piece) - 1
    elif piece > 0:
        return piece + 6
    return -1 # Should not happen for actual pieces

class Board:
    def __init__(self, fen=None):
        if fen:
            self.board, self.player = self._from_fen(fen)
        else:
            self.board = self._get_initial_board()
            self.player = 1  # Red starts
        
        self.hash_key = self._calculate_initial_hash()

    def _get_initial_board(self):
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

    def _from_fen(self, fen):
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
        
        player = 1 if player_char == 'w' else -1
        return board, player

    def to_fen(self):
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
        side = 'w' if self.player == 1 else 'b'
        fen += f" {side} - - 0 1"
        return fen

    def _calculate_initial_hash(self):
        h = 0
        for r in range(10):
            for c in range(9):
                piece = self.board[r][c]
                if piece != EMPTY:
                    idx = piece_to_zobrist_idx(piece)
                    h ^= zobrist_keys[idx][r][c]
        if self.player == -1: # If black to move
            h ^= zobrist_player
        return h

    def make_move(self, move):
        from_r, from_c = move[0]
        to_r, to_c = move[1]

        moving_piece = self.board[from_r][from_c]
        captured_piece = self.board[to_r][to_c]

        # Update hash key
        # 1. XOR out the moving piece from its original position
        moving_idx = piece_to_zobrist_idx(moving_piece)
        self.hash_key ^= zobrist_keys[moving_idx][from_r][from_c]

        # 2. If a piece is captured, XOR it out from the destination
        if captured_piece != EMPTY:
            captured_idx = piece_to_zobrist_idx(captured_piece)
            self.hash_key ^= zobrist_keys[captured_idx][to_r][to_c]

        # 3. XOR in the moving piece at its new position
        self.hash_key ^= zobrist_keys[moving_idx][to_r][to_c]
        
        # 4. Flip side to move
        self.hash_key ^= zobrist_player

        # Update board state
        self.board[to_r][to_c] = moving_piece
        self.board[from_r][from_c] = EMPTY
        
        # Update player
        self.player *= -1
        
        return captured_piece

    def unmake_move(self, move, captured_piece):
        from_r, from_c = move[0]
        to_r, to_c = move[1]
        
        moving_piece = self.board[to_r][to_c]

        # The hash key update is the same as make_move, because XORing twice restores the original value
        # 1. Flip side to move back
        self.hash_key ^= zobrist_player

        # 2. XOR out the moving piece from its new position
        moving_idx = piece_to_zobrist_idx(moving_piece)
        self.hash_key ^= zobrist_keys[moving_idx][to_r][to_c]

        # 3. If a piece was captured, XOR it back in at the destination
        if captured_piece != EMPTY:
            captured_idx = piece_to_zobrist_idx(captured_piece)
            self.hash_key ^= zobrist_keys[captured_idx][to_r][to_c]

        # 4. XOR in the moving piece at its original position
        self.hash_key ^= zobrist_keys[moving_idx][from_r][from_c]

        # Restore board state
        self.board[from_r][from_c] = moving_piece
        self.board[to_r][to_c] = captured_piece
        
        # Restore player
        self.player *= -1

# --- PST tables and other constants remain the same ---
# (For brevity, they are omitted here but should be kept in the file)

# 将/帅
KING_PST = [
    [0, 0, 0, 8, 8, 8, 0, 0, 0], [0, 0, 0, 8, 8, 8, 0, 0, 0], [0, 0, 0, 6, 6, 6, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 6, 6, 6, 0, 0, 0], [0, 0, 0, 8, 8, 8, 0, 0, 0],
    [0, 0, 0, 8, 8, 8, 0, 0, 0],
]
# 士/仕
GUARD_PST = [
    [0, 0, 0, 20, 0, 20, 0, 0, 0], [0, 0, 0, 0, 23, 0, 0, 0, 0], [0, 0, 0, 20, 0, 20, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 20, 0, 20, 0, 0, 0], [0, 0, 0, 0, 23, 0, 0, 0, 0],
    [0, 0, 0, 20, 0, 20, 0, 0, 0],
]
# 象/相
BISHOP_PST = [
    [0, 0, 20, 0, 0, 0, 20, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 23, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 20, 0, 0, 0, 20, 0, 0], [0, 0, 20, 0, 0, 0, 20, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 23, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 20, 0, 0, 0, 20, 0, 0],
]
# 马
HORSE_PST = [
    [90, 90, 90, 96, 90, 96, 90, 90, 90], [90, 96, 103, 97, 94, 97, 103, 96, 90],
    [92, 98, 99, 103, 99, 103, 99, 98, 92], [93, 108, 100, 107, 100, 107, 100, 108, 93],
    [90, 100, 99, 103, 104, 103, 99, 100, 90], [90, 98, 101, 102, 103, 102, 101, 98, 90],
    [92, 94, 98, 95, 98, 95, 98, 94, 92], [93, 92, 94, 95, 92, 95, 94, 92, 93],
    [85, 90, 92, 93, 78, 93, 92, 90, 85], [88, 85, 90, 88, 90, 88, 90, 85, 88],
]
# 车
ROOK_PST = [
    [206, 208, 207, 213, 214, 213, 207, 208, 206], [206, 212, 209, 216, 233, 216, 209, 212, 206],
    [206, 208, 207, 214, 216, 214, 207, 208, 206], [206, 213, 213, 216, 216, 216, 213, 213, 206],
    [208, 211, 211, 214, 215, 214, 211, 211, 208], [208, 212, 212, 214, 215, 214, 212, 212, 208],
    [204, 209, 204, 212, 214, 212, 204, 209, 204], [198, 208, 204, 212, 212, 212, 204, 208, 198],
    [200, 208, 206, 212, 200, 212, 206, 208, 200], [194, 206, 204, 212, 200, 212, 204, 206, 194],
]
# 炮
CANNON_PST = [
    [100, 100, 96, 91, 90, 91, 96, 100, 100], [98, 98, 96, 92, 89, 92, 96, 98, 98],
    [97, 97, 96, 91, 92, 91, 96, 97, 97], [96, 99, 99, 98, 100, 98, 99, 99, 96],
    [96, 96, 96, 96, 100, 96, 96, 96, 96], [95, 96, 99, 96, 100, 96, 99, 96, 95],
    [96, 96, 96, 96, 96, 96, 96, 96, 96], [97, 96, 100, 99, 101, 99, 100, 96, 97],
    [96, 97, 98, 98, 98, 98, 98, 97, 96], [96, 96, 97, 99, 99, 99, 97, 96, 96],
]
# 兵/卒
PAWN_PST = [
    [9, 9, 9, 11, 13, 11, 9, 9, 9], [19, 24, 34, 42, 44, 42, 34, 24, 19],
    [19, 24, 32, 37, 37, 37, 32, 24, 19], [19, 23, 27, 29, 30, 29, 27, 23, 19],
    [14, 18, 20, 27, 29, 27, 20, 18, 14], [7, 0, 13, 0, 16, 0, 13, 0, 7],
    [7, 0, 7, 0, 15, 0, 7, 0, 7], [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0],
]

PST = {
    B_KING: KING_PST, B_GUARD: GUARD_PST, B_BISHOP: BISHOP_PST, B_HORSE: HORSE_PST, B_ROOK: ROOK_PST, B_CANNON: CANNON_PST, B_PAWN: PAWN_PST,
    R_KING: KING_PST, R_GUARD: GUARD_PST, R_BISHOP: BISHOP_PST, R_HORSE: HORSE_PST, R_ROOK: ROOK_PST, R_CANNON: CANNON_PST, R_PAWN: PAWN_PST,
}