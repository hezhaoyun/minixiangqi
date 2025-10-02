# -*- coding: utf-8 -*-

from board import *

"""
中国象棋走法生成器
"""

# 定义玩家常量, 方便代码阅读
PLAYER_R = 1  # 红方
PLAYER_B = -1 # 黑方

def get_player(piece):
    """根据棋子判断玩家"""
    return PLAYER_R if piece > 0 else PLAYER_B

def is_valid_pos(r, c):
    """检查位置是否在棋盘内 (0-9, 0-8)"""
    return 0 <= r <= 9 and 0 <= c <= 8

def generate_moves(board, player):
    """
    为指定玩家生成所有合法走法
    :param board: 10x9 的棋盘
    :param player: 玩家 (PLAYER_R or PLAYER_B)
    :return: 一个包含所有走法的列表, 每个走法为 ((from_r, from_c), (to_r, to_c))
    """
    moves = []
    for r in range(10):
        for c in range(9):
            piece = board[r][c]
            if piece != EMPTY and get_player(piece) == player:
                moves.extend(get_piece_moves(board, r, c))
    return moves

def get_piece_moves(board, r, c):
    """获取单个棋子的所有走法"""
    piece = board[r][c]
    piece_type = abs(piece)

    if piece_type == R_KING:
        return get_king_moves(board, r, c)
    if piece_type == R_GUARD:
        return get_guard_moves(board, r, c)
    if piece_type == R_BISHOP:
        return get_bishop_moves(board, r, c)
    if piece_type == R_HORSE:
        return get_horse_moves(board, r, c)
    if piece_type == R_ROOK:
        return get_rook_moves(board, r, c)
    if piece_type == R_CANNON:
        return get_cannon_moves(board, r, c)
    if piece_type == R_PAWN:
        return get_pawn_moves(board, r, c)
    return []

def get_king_moves(board, r, c):
    moves = []
    player = get_player(board[r][c])
    
    # 九宫格范围
    palace_r = (0, 3) if player == PLAYER_B else (7, 10)
    palace_c = (3, 6)

    # 上下左右移动
    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        nr, nc = r + dr, c + dc
        if palace_r[0] <= nr < palace_r[1] and palace_c[0] <= nc < palace_c[1]:
            target_piece = board[nr][nc]
            if target_piece == EMPTY or get_player(target_piece) != player:
                moves.append(((r, c), (nr, nc)))

    # 将帅对脸规则
    opponent_king_pos = None
    for i in range(10):
        for j in range(9):
            if board[i][j] == -player * R_KING:
                opponent_king_pos = (i, j)
                break
        if opponent_king_pos:
            break
    
    if opponent_king_pos and opponent_king_pos[1] == c:
        is_clear = True
        for i in range(min(r, opponent_king_pos[0]) + 1, max(r, opponent_king_pos[0])):
            if board[i][c] != EMPTY:
                is_clear = False
                break
        if is_clear:
            # 找到一个可以飞过去的格子
            nr, nc = opponent_king_pos
            if get_player(board[nr][nc]) != player:
                 # 实际上不能走到那个格子，但是这是一个合法的将军/应将走法
                 # 在实际的走法生成中，我们不直接添加这个走法，
                 # 而是通过检查这个局面是否合法来过滤走法。
                 # 为简化，此处不生成飞将走法，但在之后的合法性检查中需要考虑。
                 pass

    return moves

def get_guard_moves(board, r, c):
    moves = []
    player = get_player(board[r][c])
    palace_r = (0, 3) if player == PLAYER_B else (7, 10)
    palace_c = (3, 6)

    for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        nr, nc = r + dr, c + dc
        if palace_r[0] <= nr < palace_r[1] and palace_c[0] <= nc < palace_c[1]:
            target_piece = board[nr][nc]
            if target_piece == EMPTY or get_player(target_piece) != player:
                moves.append(((r, c), (nr, nc)))
    return moves

def get_bishop_moves(board, r, c):
    moves = []
    player = get_player(board[r][c])
    river_r = 4 if player == PLAYER_B else 5 # 不能过河

    for dr, dc in [(2, 2), (2, -2), (-2, 2), (-2, -2)]:
        nr, nc = r + dr, c + dc
        if not is_valid_pos(nr, nc): continue
        
        # 不能过河
        if (player == PLAYER_B and nr > river_r) or (player == PLAYER_R and nr < river_r):
            continue

        # 象眼被塞
        eye_r, eye_c = r + dr // 2, c + dc // 2
        if board[eye_r][eye_c] == EMPTY:
            target_piece = board[nr][nc]
            if target_piece == EMPTY or get_player(target_piece) != player:
                moves.append(((r, c), (nr, nc)))
    return moves

def get_horse_moves(board, r, c):
    moves = []
    player = get_player(board[r][c])
    
    # 8个方向的日字
    for dr, dc in [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]:
        nr, nc = r + dr, c + dc
        if not is_valid_pos(nr, nc): continue

        # 蹩马腿
        leg_r, leg_c = r, c
        if abs(dr) == 2: leg_r += dr // 2
        else: leg_c += dc // 2
        
        if board[leg_r][leg_c] == EMPTY:
            target_piece = board[nr][nc]
            if target_piece == EMPTY or get_player(target_piece) != player:
                moves.append(((r, c), (nr, nc)))
    return moves

def get_rook_moves(board, r, c):
    moves = []
    player = get_player(board[r][c])

    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # 四个方向
        for i in range(1, 10):
            nr, nc = r + dr * i, c + dc * i
            if not is_valid_pos(nr, nc): break
            
            target_piece = board[nr][nc]
            if target_piece == EMPTY:
                moves.append(((r, c), (nr, nc)))
            else:
                if get_player(target_piece) != player:
                    moves.append(((r, c), (nr, nc))) # 吃子
                break # 被挡住
    return moves

def get_cannon_moves(board, r, c):
    moves = []
    player = get_player(board[r][c])

    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]: # 四个方向
        has_jumped = False
        for i in range(1, 10):
            nr, nc = r + dr * i, c + dc * i
            if not is_valid_pos(nr, nc): break

            target_piece = board[nr][nc]
            if not has_jumped:
                if target_piece == EMPTY:
                    moves.append(((r, c), (nr, nc))) # 移动
                else:
                    has_jumped = True # 遇到第一个棋子, 成为炮架
            else:
                if target_piece != EMPTY:
                    if get_player(target_piece) != player:
                        moves.append(((r, c), (nr, nc))) # 吃子
                    break # 被挡住
    return moves

def get_pawn_moves(board, r, c):
    moves = []
    player = get_player(board[r][c])
    
    # 前进方向
    forward_dr = 1 if player == PLAYER_B else -1
    
    # 前进一步
    nr, nc = r + forward_dr, c
    if is_valid_pos(nr, nc):
        target_piece = board[nr][nc]
        if target_piece == EMPTY or get_player(target_piece) != player:
            moves.append(((r, c), (nr, nc)))

    # 过河后可以横走
    river_r = 4 if player == PLAYER_B else 5
    if (player == PLAYER_B and r > river_r) or (player == PLAYER_R and r < river_r):
        for dc in [-1, 1]: # 左右
            nr, nc = r, c + dc
            if is_valid_pos(nr, nc):
                target_piece = board[nr][nc]
                if target_piece == EMPTY or get_player(target_piece) != player:
                    moves.append(((r, c), (nr, nc)))
    return moves

def order_moves(board, moves, best_move_from_tt=None):
    """
    对着法列表进行排序，以优化Alpha-Beta剪枝效率。
    排序策略:
    1. 置换表中的最佳着法
    2. MVV-LVA (最有价值的被攻击者 - 最低价值的攻击者)
    """
    move_scores = {}
    # 为吃子动作设置一个高的基础分，确保它们排在非吃子动作前面
    CAPTURE_BONUS = 10000

    for move in moves:
        score = 0
        from_r, from_c = move[0]
        to_r, to_c = move[1]

        # 1. 如果是置换表中的最佳着法，给予最高分
        if move == best_move_from_tt:
            score = 100000
        else:
            # 2. 评估吃子着法
            captured_piece = board[to_r][to_c]
            if captured_piece != EMPTY:
                moving_piece = board[from_r][from_c]
                # 使用棋子价值的绝对值进行MVV-LVA评分
                victim_value = abs(PIECE_VALUES.get(captured_piece, 0))
                attacker_value = abs(PIECE_VALUES.get(moving_piece, 0))
                score = CAPTURE_BONUS + victim_value - attacker_value
        
        move_scores[move] = score

    # 按分数降序排序
    return sorted(moves, key=lambda m: move_scores[m], reverse=True)


if __name__ == '__main__':
    # 示例: 测试初始棋盘红方的走法
    initial_board = get_initial_board()
    red_moves = generate_moves(initial_board, PLAYER_R)
    
    print(f"初始局面, 红方共有 {len(red_moves)} 种走法:")
    # 打印部分走法
    for move in red_moves[:10]:
        print(f"  棋子 {initial_board[move[0][0]][move[0][1]]} 从 {move[0]} 移动到 {move[1]}")

    # 示例: 测试黑方
    black_moves = generate_moves(initial_board, PLAYER_B)
    print(f"\n初始局面, 黑方共有 {len(black_moves)} 种走法:")
    for move in black_moves[:10]:
        print(f"  棋子 {initial_board[move[0][0]][move[0][1]]} 从 {move[0]} 移动到 {move[1]}")
