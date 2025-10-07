# -*- coding: utf-8 -*-

'''
中国象棋走法生成器
'''

from typing import List, Optional

from src.board import BoardState, Board, Move, get_player, is_valid_pos, piece_to_zobrist_idx
from src.constants import *


def generate_moves(board: Board) -> List[Move]:
    '''
    为指定玩家生成所有合法走法
    :param board: Board 对象
    :return: 一个包含所有走法的列表
    '''
    pseudo_legal_moves = []
    board_state = board.board
    player = board.player

    for r, c in board.piece_list[player]:
        pseudo_legal_moves.extend(get_piece_moves(board_state, r, c))

    legal_moves = []
    for move in pseudo_legal_moves:
        captured_piece = board.make_move(move)

        # 切换到对手视角来检查攻击
        board.player *= -1

        if not board.is_check():
            legal_moves.append(move)

        # 切换回原来玩家
        board.player *= -1

        board.unmake_move(move, captured_piece)

    return legal_moves


def get_piece_moves(board_state: BoardState, r: int, c: int) -> List[Move]:
    '''获取单个棋子的所有走法'''
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


def get_king_moves(board_state: BoardState, r: int, c: int) -> List[Move]:
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


def get_guard_moves(board_state: BoardState, r: int, c: int) -> List[Move]:
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


def get_bishop_moves(board_state: BoardState, r: int, c: int) -> List[Move]:
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


def get_horse_moves(board_state: BoardState, r: int, c: int) -> List[Move]:
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


def get_rook_moves(board_state: BoardState, r: int, c: int) -> List[Move]:
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


def get_cannon_moves(board_state: BoardState, r: int, c: int) -> List[Move]:
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


def get_pawn_moves(board_state: BoardState, r: int, c: int) -> List[Move]:
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


def order_moves(board_state: BoardState, moves: List[Move], best_move_from_tt: Optional[Move], history_table: List[List[int]]) -> List[Move]:
    '''
    对着法列表进行排序，以优化Alpha-Beta剪枝效率。
    排序优先级: 置换表最佳走法 > 吃子走法(MVV-LVA) > 历史启发 > 普通走法
    '''
    move_scores = {}
    CAPTURE_BONUS = 1000000  # 确保吃子走法优先于历史启发

    for move in moves:
        score = 0
        from_r, from_c = move[0]
        to_r, to_c = move[1]

        moving_piece = board_state[from_r][from_c]
        captured_piece = board_state[to_r][to_c]

        if move == best_move_from_tt:
            score = 10 * CAPTURE_BONUS # 最高优先级
        elif captured_piece != EMPTY:
            # MVV-LVA (Most Valuable Victim - Least Valuable Attacker)
            victim_value = abs(PIECE_VALUES.get(captured_piece, 0))
            attacker_value = abs(PIECE_VALUES.get(moving_piece, 0))
            score = CAPTURE_BONUS + victim_value - attacker_value
        else:
            # 历史启发分数
            piece_idx = piece_to_zobrist_idx(moving_piece)
            to_sq_idx = to_r * 9 + to_c
            score = history_table[piece_idx][to_sq_idx]

        move_scores[move] = score

    return sorted(moves, key=lambda m: move_scores[m], reverse=True)


def generate_capture_moves(board: Board) -> List[Move]:
    '''
    为指定玩家生成所有只吃子的走法
    '''
    capture_moves = []
    board_state = board.board

    for r, c in board.piece_list[board.player]:
        piece_moves = get_piece_moves(board_state, r, c)
        for move in piece_moves:
            to_r, to_c = move[1]
            if board_state[to_r][to_c] != EMPTY:
                # 确保是合法的吃子
                captured_piece = board.make_move(move)
                board.player *= -1
                if not board.is_check():
                    capture_moves.append(move)
                board.player *= -1
                board.unmake_move(move, captured_piece)

    return capture_moves


if __name__ == '__main__':
    initial_board = Board()
    red_moves = generate_moves(initial_board)
    print(f'初始局面, 红方共有 {len(red_moves)} 种走法:')
    for move in red_moves[:10]:
        print(f'  棋子 {initial_board.board[move[0][0]][move[0][1]]} 从 {move[0]} 移动到 {move[1]}')

    initial_board.player = PLAYER_B
    black_moves = generate_moves(initial_board)
    print(f'\n初始局面, 黑方共有 {len(black_moves)} 种走法:')
    for move in black_moves[:10]:
        print(f'  棋子 {initial_board.board[move[0][0]][move[0][1]]} 从 {move[0]} 移动到 {move[1]}')