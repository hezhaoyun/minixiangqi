# -*- coding: utf-8 -*-

"""
位棋盘 (Bitboard) 实现, 包含Zobrist哈希
"""

from typing import Optional
from src.constants import *
from src.zobrist import zobrist_keys, zobrist_player

# --- Pre-calculated Masks and Mappings ---

SQUARE_MASKS = [1 << i for i in range(90)]
CLEAR_MASKS = [~m for m in SQUARE_MASKS]

FEN_MAP = {
    'k': B_KING, 'a': B_GUARD, 'b': B_BISHOP, 'n': B_HORSE, 'r': B_ROOK, 'c': B_CANNON, 'p': B_PAWN,
    'K': R_KING, 'A': R_GUARD, 'B': R_BISHOP, 'N': R_HORSE, 'R': R_ROOK, 'C': R_CANNON, 'P': R_PAWN,
}
PIECE_TO_FEN_CHAR = {v: k for k, v in FEN_MAP.items()}

PIECE_TO_BB_INDEX = {
    R_KING: 0, R_GUARD: 1, R_BISHOP: 2, R_HORSE: 3, R_ROOK: 4, R_CANNON: 5, R_PAWN: 6,
    B_KING: 7, B_GUARD: 8, B_BISHOP: 9, B_HORSE: 10, B_ROOK: 11, B_CANNON: 12, B_PAWN: 13,
}
BB_INDEX_TO_PIECE = {v: k for k, v in PIECE_TO_BB_INDEX.items()}

def piece_to_zobrist_idx(piece: int) -> int:
    if piece < 0: return abs(piece) - 1
    elif piece > 0: return piece + 6
    return -1

def get_player(piece: int) -> int:
    return PLAYER_R if piece > 0 else PLAYER_B

class Bitboard:
    def __init__(self, fen: Optional[str] = None):
        self.piece_bitboards = [0] * 14
        self.color_bitboards = [0] * 2
        self.player_to_move = PLAYER_R
        self.hash_key = 0
        self.history = []

        if fen:
            self.parse_fen(fen)
        else:
            self.setup_default_position()
        
        self.history.append(self.hash_key)

    def get_player_bb_idx(self, player: int) -> int:
        return 0 if player == PLAYER_R else 1

    def parse_fen(self, fen: str):
        parts = fen.split(' ')
        fen_board, player_char = parts[0], parts[1]

        # Reset state
        self.piece_bitboards = [0] * 14
        self.color_bitboards = [0] * 2
        self.hash_key = 0

        # Set pieces
        for r, row_str in enumerate(fen_board.split('/')):
            c = 0
            for char in row_str:
                if char.isdigit():
                    c += int(char)
                else:
                    piece_type = FEN_MAP.get(char)
                    if piece_type:
                        sq = r * 9 + c
                        self._set_piece(piece_type, sq)
                    c += 1
        
        # Set player and update hash
        self.player_to_move = PLAYER_R if player_char == 'w' else PLAYER_B
        if self.player_to_move == PLAYER_B:
            self.hash_key ^= zobrist_player

    def setup_default_position(self):
        self.parse_fen("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1")

    def _set_piece(self, piece_type: int, sq: int):
        mask = SQUARE_MASKS[sq]
        player = get_player(piece_type)
        r, c = sq // 9, sq % 9
        
        self.piece_bitboards[PIECE_TO_BB_INDEX[piece_type]] |= mask
        self.color_bitboards[self.get_player_bb_idx(player)] |= mask
        self.hash_key ^= zobrist_keys[piece_to_zobrist_idx(piece_type)][r][c]

    def move_piece(self, from_sq: int, to_sq: int) -> int:
        moving_piece = self.get_piece_on_square(from_sq)
        if moving_piece == EMPTY:
            # This should not happen with legal move generation, but as a safeguard:
            print(f"Warning: Attempted to move from an empty square: {from_sq}")
            return EMPTY

        captured_piece = self.get_piece_on_square(to_sq)
        r_from, c_from = from_sq // 9, from_sq % 9
        r_to, c_to = to_sq // 9, to_sq % 9

        # 1. Update hash for moving piece
        moving_z_idx = piece_to_zobrist_idx(moving_piece)
        self.hash_key ^= zobrist_keys[moving_z_idx][r_from][c_from]
        self.hash_key ^= zobrist_keys[moving_z_idx][r_to][c_to]

        # 2. Update bitboards for moving piece
        move_mask = SQUARE_MASKS[from_sq] | SQUARE_MASKS[to_sq]
        self.piece_bitboards[PIECE_TO_BB_INDEX[moving_piece]] ^= move_mask
        self.color_bitboards[self.get_player_bb_idx(self.player_to_move)] ^= move_mask

        # 3. Handle capture
        if captured_piece != EMPTY:
            captured_z_idx = piece_to_zobrist_idx(captured_piece)
            self.hash_key ^= zobrist_keys[captured_z_idx][r_to][c_to]
            capture_mask = CLEAR_MASKS[to_sq]
            self.piece_bitboards[PIECE_TO_BB_INDEX[captured_piece]] &= capture_mask
            self.color_bitboards[self.get_player_bb_idx(get_player(captured_piece))] &= capture_mask

        # 4. Update player and hash
        self.player_to_move *= -1
        self.hash_key ^= zobrist_player
        self.history.append(self.hash_key)
        
        return captured_piece

    def unmove_piece(self, from_sq: int, to_sq: int, captured_piece: int):
        self.history.pop()
        moving_piece = self.get_piece_on_square(to_sq) # Piece is at its new location
        r_from, c_from = from_sq // 9, from_sq % 9
        r_to, c_to = to_sq // 9, to_sq % 9
        r_to, c_to = to_sq // 9, to_sq % 9

        # 1. Update player and hash
        self.player_to_move *= -1
        self.hash_key ^= zobrist_player # Revert player hash

        # 2. Revert moving piece bitboards
        move_mask = SQUARE_MASKS[from_sq] | SQUARE_MASKS[to_sq]
        self.piece_bitboards[PIECE_TO_BB_INDEX[moving_piece]] ^= move_mask
        self.color_bitboards[self.get_player_bb_idx(self.player_to_move)] ^= move_mask

        # 3. Revert moving piece hash
        moving_z_idx = piece_to_zobrist_idx(moving_piece)
        self.hash_key ^= zobrist_keys[moving_z_idx][r_from][c_from]
        self.hash_key ^= zobrist_keys[moving_z_idx][r_to][c_to]

        # 4. If there was a capture, restore the captured piece
        if captured_piece != EMPTY:
            capture_mask = SQUARE_MASKS[to_sq]
            self.piece_bitboards[PIECE_TO_BB_INDEX[captured_piece]] |= capture_mask
            self.color_bitboards[self.get_player_bb_idx(get_player(captured_piece))] |= capture_mask
            captured_z_idx = piece_to_zobrist_idx(captured_piece)
            self.hash_key ^= zobrist_keys[captured_z_idx][r_to][c_to]

    def get_piece_on_square(self, sq: int) -> int:
        mask = SQUARE_MASKS[sq]
        for i in range(14):
            if self.piece_bitboards[i] & mask: return BB_INDEX_TO_PIECE[i]
        return EMPTY

    @property
    def occupied_bitboard(self) -> int:
        return self.color_bitboards[0] | self.color_bitboards[1]

    def __str__(self) -> str:
        builder = []
        for r in range(10):
            row_str = [PIECE_TO_FEN_CHAR.get(self.get_piece_on_square(r * 9 + c), '.') for c in range(9)]
            builder.append(" ".join(row_str))
        return "\n".join(builder)

    def copy(self):
        new_bb = Bitboard()
        new_bb.piece_bitboards = self.piece_bitboards[:]
        new_bb.color_bitboards = self.color_bitboards[:]
        new_bb.player_to_move = self.player_to_move
        new_bb.hash_key = self.hash_key
        new_bb.history = self.history[:]
        return new_bb