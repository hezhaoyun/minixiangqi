# -*- coding: utf-8 -*- 

"""
中国象棋走法生成器
"""

from typing import List, Optional

import board as b
import evaluate
from board import get_player
from constants import (
    EMPTY, PLAYER_B, PLAYER_R, R_BISHOP, R_CANNON, R_GUARD, R_HORSE, R_KING,
    R_PAWN, R_ROOK
)


def is_valid_pos(r: int, c: int) -> bool:
    """检查位置是否在棋盘内 (0-9, 0-8)"""
    return 0 <= r <= 9 and 0 <= c <= 8


def generate_moves(board: b.Board) -> List[b.Move]:
    """
    为指定玩家生成所有合法走法
    :param board: Board 对象
    :return: 一个包含所有走法的列表
    """
    moves = []
    board_state = board.board
    player = board.player

    for r, c in board.piece_list[player]:
        moves.extend(get_piece_moves(board_state, r, c))

    return moves


def get_piece_moves(board_state: b.BoardState, r: int, c: int) -> List[b.Move]:
    """获取单个棋子的所有走法"""
    piece = board_state[r][c]
    piece_type = abs(piece)

    if piece_type == R_KING:
        return get_king_moves(board_state, r, c)
    if piece_type == R_GUARD:
        return get_guard_moves(board_state, r, c)
    if piece_type == R_BISHOP:
        return get_bishop_moves(board_state, r, c)
    if piece_type == R_HORSE:
        return get_horse_moves(board_state, r, c)
    if piece_type == R_ROOK:
        return get_rook_moves(board_state, r, c)
    if piece_type == R_CANNON:
        return get_cannon_moves(board_state, r, c)
    if piece_type == R_PAWN:
        return get_pawn_moves(board_state, r, c)

    return []


def get_king_moves(board_state: b.BoardState, r: int, c: int) -> List[b.Move]:
    moves = []
    player = get_player(board_state[r][c])

    palace_r = (0, 3) if player == PLAYER_B else (7, 10)
    palace_c = (3, 6)

    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = r + dr, c + dc
        if palace_r[0] <= nr < palace_r[1] and palace_c[0] <= nc < palace_c[1]:
            target_piece = board_state[nr][nc]
            if target_piece == EMPTY or get_player(target_piece) != player:
                moves.append(((r, c), (nr, nc)))

    # 将帅对脸规则
    opponent_king_pos = None
    for i in range(10):
        for j in range(9):
            if board_state[i][j] == -player * R_KING:
                opponent_king_pos = (i, j)
                break
        if opponent_king_pos:
            break

    if opponent_king_pos and opponent_king_pos[1] == c:
        is_clear = True
        for i in range(min(r, opponent_king_pos[0]) + 1, max(r, opponent_king_pos[0])):
            if board_state[i][c] != EMPTY:
                is_clear = False
                break
        if is_clear:
            nr, nc = opponent_king_pos
            if get_player(board_state[nr][nc]) != player:
                moves.append(((r, c), (nr, nc)))

    return moves


def get_guard_moves(board_state: b.BoardState, r: int, c: int) -> List[b.Move]:
    moves = []
    player = get_player(board_state[r][c])
    palace_r = (0, 3) if player == PLAYER_B else (7, 10)
    palace_c = (3, 6)

    for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nr, nc = r + dr, c + dc
        if palace_r[0] <= nr < palace_r[1] and palace_c[0] <= nc < palace_c[1]:
            target_piece = board_state[nr][nc]
            if target_piece == EMPTY or get_player(target_piece) != player:
                moves.append(((r, c), (nr, nc)))
    return moves


def get_bishop_moves(board_state: b.BoardState, r: int, c: int) -> List[b.Move]:
    moves = []
    player = get_player(board_state[r][c])
    river_r = 4 if player == PLAYER_B else 5

    for dr, dc in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
        nr, nc = r + dr, c + dc
        if not is_valid_pos(nr, nc):
            continue

        if (player == PLAYER_B and nr > river_r) or (player == PLAYER_R and nr < river_r):
            continue

        eye_r, eye_c = r + dr // 2, c + dc // 2
        if board_state[eye_r][eye_c] == EMPTY:
            target_piece = board_state[nr][nc]
            if target_piece == EMPTY or get_player(target_piece) != player:
                moves.append(((r, c), (nr, nc)))
    return moves


def get_horse_moves(board_state: b.BoardState, r: int, c: int) -> List[b.Move]:
    moves = []
    player = get_player(board_state[r][c])

    for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
        nr, nc = r + dr, c + dc
        if not is_valid_pos(nr, nc):
            continue

        leg_r, leg_c = r, c
        if abs(dr) == 2:
            leg_r += dr // 2
        else:
            leg_c += dc // 2

        if board_state[leg_r][leg_c] == EMPTY:
            target_piece = board_state[nr][nc]
            if target_piece == EMPTY or get_player(target_piece) != player:
                moves.append(((r, c), (nr, nc)))

    return moves


def get_rook_moves(board_state: b.BoardState, r: int, c: int) -> List[b.Move]:
    moves = []
    player = get_player(board_state[r][c])

    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        for i in range(1, 10):
            nr, nc = r + dr * i, c + dc * i
            if not is_valid_pos(nr, nc):
                break

            target_piece = board_state[nr][nc]
            if target_piece == EMPTY:
                moves.append(((r, c), (nr, nc)))
            else:
                if get_player(target_piece) != player:
                    moves.append(((r, c), (nr, nc)))
                break

    return moves


def get_cannon_moves(board_state: b.BoardState, r: int, c: int) -> List[b.Move]:
    moves = []
    player = get_player(board_state[r][c])

    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        has_jumped = False
        for i in range(1, 10):
            nr, nc = r + dr * i, c + dc * i
            if not is_valid_pos(nr, nc):
                break

            target_piece = board_state[nr][nc]
            if not has_jumped:
                if target_piece == EMPTY:
                    moves.append(((r, c), (nr, nc)))
                else:
                    has_jumped = True
            else:
                if target_piece != EMPTY:
                    if get_player(target_piece) != player:
                        moves.append(((r, c), (nr, nc)))
                    break

    return moves


def get_pawn_moves(board_state: b.BoardState, r: int, c: int) -> List[b.Move]:
    moves = []
    player = get_player(board_state[r][c])
    forward_dr = 1 if player == PLAYER_B else -1

    nr, nc = r + forward_dr, c
    if is_valid_pos(nr, nc):
        target_piece = board_state[nr][nc]
        if target_piece == EMPTY or get_player(target_piece) != player:
            moves.append(((r, c), (nr, nc)))

    river_r = 4 if player == PLAYER_B else 5
    if (player == PLAYER_B and r > river_r) or (player == PLAYER_R and r < river_r):
        for dc in [-1, 1]:
            nr, nc = r, c + dc
            if is_valid_pos(nr, nc):
                target_piece = board_state[nr][nc]
                if target_piece == EMPTY or get_player(target_piece) != player:
                    moves.append(((r, c), (nr, nc)))

    return moves


def order_moves(board_state: b.BoardState, moves: List[b.Move], best_move_from_tt: Optional[b.Move] = None) -> List[b.Move]:
    """
    对着法列表进行排序，以优化Alpha-Beta剪枝效率。
    """
    move_scores = {}
    CAPTURE_BONUS = 10000

    for move in moves:
        score = 0
        from_r, from_c = move[0]
        to_r, to_c = move[1]

        if move == best_move_from_tt:
            score = 100000
        else:
            captured_piece = board_state[to_r][to_c]
            if captured_piece != EMPTY:
                moving_piece = board_state[from_r][from_c]
                victim_value = abs(evaluate.PIECE_VALUES.get(captured_piece, 0))
                attacker_value = abs(evaluate.PIECE_VALUES.get(moving_piece, 0))
                score = CAPTURE_BONUS + victim_value - attacker_value

        move_scores[move] = score

    return sorted(moves, key=lambda m: move_scores[m], reverse=True)


if __name__ == '__main__':
    initial_board = b.Board()
    red_moves = generate_moves(initial_board)
    print(f"初始局面, 红方共有 {len(red_moves)} 种走法:")
    for move in red_moves[:10]:
        print(f"  棋子 {initial_board.board[move[0][0]][move[0][1]]} 从 {move[0]} 移动到 {move[1]}")

    initial_board.player = PLAYER_B
    black_moves = generate_moves(initial_board)
    print(f"\n初始局面, 黑方共有 {len(black_moves)} 种走法:")
    for move in black_moves[:10]:
        print(f"  棋子 {initial_board.board[move[0][0]][move[0][1]]} 从 {move[0]} 移动到 {move[1]}")