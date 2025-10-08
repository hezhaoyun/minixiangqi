# -*- coding: utf-8 -*-
"""
位棋盘 (Bitboard) 数据结构实现。

该模块定义了 `Bitboard` 类，它是整个引擎的棋盘表示核心。
一个位棋盘使用一个整数（在Python中是任意精度的长整数）来表示棋盘上的状态，
其中每一个比特位对应棋盘上的一个位置。由于中国象棋有90个位置，这里使用的整数会超过标准的64位。这种表示方法使得棋子的移动、
吃子和攻击检测等操作可以通过高效的位运算来完成。

该实现还包含了Zobrist哈希，用于快速地为每个棋盘局面生成一个唯一的哈希值，
这对于置换表的实现至关重要。
"""

from typing import Optional
from src.constants import *
from src.zobrist import zobrist_keys, zobrist_player

# --- 预计算的掩码和映射表 ---

# SQUARE_MASKS[i] 是一个整数，只有第i位是1，用于定位棋盘上的单个位置。
SQUARE_MASKS = [1 << i for i in range(90)]
# CLEAR_MASKS[i] 是一个整数，只有第i位是0，用于从位棋盘中移除一个棋子。
CLEAR_MASKS = [~m for m in SQUARE_MASKS]

# FEN字符与棋子整数表示的映射
FEN_MAP = {
    'k': B_KING, 'a': B_GUARD, 'b': B_BISHOP, 'n': B_HORSE, 'r': B_ROOK, 'c': B_CANNON, 'p': B_PAWN,
    'K': R_KING, 'A': R_GUARD, 'B': R_BISHOP, 'N': R_HORSE, 'R': R_ROOK, 'C': R_CANNON, 'P': R_PAWN,
}
PIECE_TO_FEN_CHAR = {v: k for k, v in FEN_MAP.items()}

# 棋子整数表示与其在位棋盘数组中索引的映射
PIECE_TO_BB_INDEX = {
    R_KING: 0, R_GUARD: 1, R_BISHOP: 2, R_HORSE: 3, R_ROOK: 4, R_CANNON: 5, R_PAWN: 6,
    B_KING: 7, B_GUARD: 8, B_BISHOP: 9, B_HORSE: 10, B_ROOK: 11, B_CANNON: 12, B_PAWN: 13,
}
BB_INDEX_TO_PIECE = {v: k for k, v in PIECE_TO_BB_INDEX.items()}


class Bitboard:
    """
    象棋位棋盘数据结构。

    使用一组整数来表示棋盘状态，使得操作可以通过高效的位运算完成。

    Attributes:
        piece_bitboards (list[int]): 14个位棋盘，每种特定类型的棋子一个 (例如, 红车、黑马)。数组索引由 `PIECE_TO_BB_INDEX` 决定。
        color_bitboards (list[int]): 2个位棋盘，一个用于红方所有棋子，一个用于黑方所有棋子。
        player_to_move (int): 当前走棋方 (PLAYER_R 或 PLAYER_B)。
        hash_key (int): 当前局面的Zobrist哈希值。
        history (list[int]): 记录历史Zobrist哈希值的列表，用于检测重复局面。
    """
    @staticmethod
    def get_player(piece: int) -> int:
        """根据棋子的整数表示获取其所属玩家。"""
        return PLAYER_R if piece > 0 else PLAYER_B

    @staticmethod
    def piece_to_zobrist_idx(piece: int) -> int:
        """将棋子整数表示转换为其在Zobrist键数组中的索引。"""
        if piece < 0:
            return abs(piece) - 1  # 黑方棋子索引 0-6
        elif piece > 0:
            return piece + 6      # 红方棋子索引 7-13
        return -1  # 不应发生

    def __init__(self, fen: Optional[str] = None):
        """
        初始化位棋盘。

        可以从一个FEN字符串初始化，或者创建一个默认的开局局面。
        """
        self.piece_bitboards = [0] * 14
        self.color_bitboards = [0] * 2
        self.player_to_move = PLAYER_R
        self.hash_key = 0
        self.history = []
        self.board = [EMPTY] * 90

        if fen:
            self.parse_fen(fen)
        else:
            self.setup_default_position()

        # 将初始局面的哈希值存入历史记录
        self.history.append(self.hash_key)

    def get_player_bb_idx(self, player: int) -> int:
        """获取玩家在 `color_bitboards` 数组中的索引 (0 for Red, 1 for Black)。"""
        return 0 if player == PLAYER_R else 1

    def parse_fen(self, fen: str):
        """
        从FEN (Forsyth-Edwards Notation) 字符串解析棋盘局面。
        """
        parts = fen.split(' ')
        fen_board, player_char = parts[0], parts[1]

        # 重置棋盘状态
        self.piece_bitboards = [0] * 14
        self.color_bitboards = [0] * 2
        self.hash_key = 0
        self.board = [EMPTY] * 90

        # 根据FEN字符串设置棋子
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

        # 设置当前走棋方并更新哈希值
        self.player_to_move = PLAYER_R if player_char == 'w' else PLAYER_B
        if self.player_to_move == PLAYER_B:
            self.hash_key ^= zobrist_player

    def setup_default_position(self):
        """设置中国象棋的默认开局局面。"""
        self.parse_fen("rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1")

    def _set_piece(self, piece_type: int, sq: int):
        """
        在指定位置放置一个棋子，并更新所有相关的位棋盘和Zobrist哈希值。
        这是一个内部辅助函数，主要用于初始化。
        """
        mask = SQUARE_MASKS[sq]
        player = Bitboard.get_player(piece_type)
        r, c = sq // 9, sq % 9

        # 更新棋盘数组
        self.board[sq] = piece_type
        # 更新棋子位棋盘
        self.piece_bitboards[PIECE_TO_BB_INDEX[piece_type]] |= mask
        # 更新颜色位棋盘
        self.color_bitboards[self.get_player_bb_idx(player)] |= mask
        # 更新Zobrist哈希
        self.hash_key ^= zobrist_keys[Bitboard.piece_to_zobrist_idx(piece_type)][r][c]

    def move_piece(self, from_sq: int, to_sq: int) -> int:
        """
        在棋盘上执行一步走法。

        这会更新所有位棋盘和Zobrist哈希值。这是一个增量更新，比重新计算整个
        哈希值要快得多。

        Args:
            from_sq (int): 起始位置。
            to_sq (int): 目标位置。

        Returns:
            int: 被吃掉的棋子类型，如果没有吃子则返回EMPTY。
        """
        moving_piece = self.board[from_sq]
        if moving_piece == EMPTY:
            return EMPTY

        captured_piece = self.board[to_sq]
        r_from, c_from = from_sq // 9, from_sq % 9
        r_to, c_to = to_sq // 9, to_sq % 9

        # 1. 更新棋盘数组
        self.board[from_sq] = EMPTY
        self.board[to_sq] = moving_piece

        # 2. 更新移动棋子的Zobrist哈希
        # 异或操作相当于：从哈希中移除起始位置的棋子，再在目标位置添加该棋子
        moving_z_idx = Bitboard.piece_to_zobrist_idx(moving_piece)
        self.hash_key ^= zobrist_keys[moving_z_idx][r_from][c_from]
        self.hash_key ^= zobrist_keys[moving_z_idx][r_to][c_to]

        # 3. 更新移动棋子的位棋盘
        # 异或一个包含起始和目标位置的掩码，相当于将棋子从from_sq移动到to_sq
        move_mask = SQUARE_MASKS[from_sq] | SQUARE_MASKS[to_sq]
        self.piece_bitboards[PIECE_TO_BB_INDEX[moving_piece]] ^= move_mask
        self.color_bitboards[self.get_player_bb_idx(self.player_to_move)] ^= move_mask

        # 4. 如果有吃子，处理被吃掉的棋子
        if captured_piece != EMPTY:
            # 从哈希中移除被吃掉的棋子
            captured_z_idx = Bitboard.piece_to_zobrist_idx(captured_piece)
            self.hash_key ^= zobrist_keys[captured_z_idx][r_to][c_to]
            # 从位棋盘中移除被吃掉的棋子
            capture_mask = CLEAR_MASKS[to_sq]
            self.piece_bitboards[PIECE_TO_BB_INDEX[captured_piece]] &= capture_mask
            self.color_bitboards[self.get_player_bb_idx(Bitboard.get_player(captured_piece))] &= capture_mask

        # 5. 切换走棋方并更新哈希
        self.player_to_move *= -1
        self.hash_key ^= zobrist_player
        self.history.append(self.hash_key)

        return captured_piece

    def unmove_piece(self, from_sq: int, to_sq: int, captured_piece: int):
        """
        撤销一步走法。

        这是 `move_piece` 的逆操作，用于在搜索中恢复棋盘状态。
        撤销的顺序与执行走法的顺序严格相反。
        """
        self.history.pop()
        moving_piece = self.board[to_sq] # 使用邮箱快速查找
        r_from, c_from = from_sq // 9, from_sq % 9
        r_to, c_to = to_sq // 9, to_sq % 9

        # 1. 恢复走棋方 (必须在所有棋子哈希操作之前完成)
        self.player_to_move *= -1
        self.hash_key ^= zobrist_player

        # 2. 恢复棋盘数组
        self.board[from_sq] = moving_piece
        self.board[to_sq] = captured_piece

        # 3. 将移动的棋子从 to_sq 移回 from_sq
        move_mask = SQUARE_MASKS[from_sq] | SQUARE_MASKS[to_sq]
        self.piece_bitboards[PIECE_TO_BB_INDEX[moving_piece]] ^= move_mask
        self.color_bitboards[self.get_player_bb_idx(self.player_to_move)] ^= move_mask
        # 恢复Zobrist哈希
        moving_z_idx = Bitboard.piece_to_zobrist_idx(moving_piece)
        self.hash_key ^= zobrist_keys[moving_z_idx][r_from][c_from]
        self.hash_key ^= zobrist_keys[moving_z_idx][r_to][c_to]

        # 4. 如果有吃子，将被吃的棋子放回 to_sq
        if captured_piece != EMPTY:
            capture_mask = SQUARE_MASKS[to_sq]
            captured_player = Bitboard.get_player(captured_piece)
            self.piece_bitboards[PIECE_TO_BB_INDEX[captured_piece]] |= capture_mask
            self.color_bitboards[self.get_player_bb_idx(captured_player)] |= capture_mask
            # 恢复被吃棋子的Zobrist哈希
            captured_z_idx = Bitboard.piece_to_zobrist_idx(captured_piece)
            self.hash_key ^= zobrist_keys[captured_z_idx][r_to][c_to]

    def get_piece_on_square(self, sq: int) -> int:
        """获取指定位置上的棋子。"""
        return self.board[sq]

    @property
    def occupied_bitboard(self) -> int:
        """返回一个表示所有棋子位置的位棋盘。"""
        return self.color_bitboards[0] | self.color_bitboards[1]

    def __str__(self) -> str:
        """返回一个用于调试的、人类可读的棋盘字符串表示。"""
        builder = []
        for r in range(10):
            row_str = [PIECE_TO_FEN_CHAR.get(self.get_piece_on_square(r * 9 + c), '.') for c in range(9)]
            builder.append(" ".join(row_str))
        return "\n".join(builder)

    def to_fen(self) -> str:
        """将当前棋盘局面转换为FEN字符串。"""
        fen_parts = []
        for r in range(10):
            empty_count = 0
            row_str = ""
            for c in range(9):
                piece = self.get_piece_on_square(r * 9 + c)
                if piece == EMPTY:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += PIECE_TO_FEN_CHAR[piece]
            if empty_count > 0:
                row_str += str(empty_count)
            fen_parts.append(row_str)

        board_fen = "/".join(fen_parts)
        player_fen = 'w' if self.player_to_move == PLAYER_R else 'b'
        # 注意：这里的步数、吃子等信息是占位符
        return f"{board_fen} {player_fen} - - 0 1"

    def copy(self):
        """创建一个当前Bitboard对象的深拷贝。"""
        new_bb = Bitboard()
        new_bb.piece_bitboards = self.piece_bitboards[:]
        new_bb.color_bitboards = self.color_bitboards[:]
        new_bb.player_to_move = self.player_to_move
        new_bb.hash_key = self.hash_key
        new_bb.history = self.history[:]
        return new_bb
