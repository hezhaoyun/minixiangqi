# -*- coding: utf-8 -*-
"""
游戏主程序模块。

该模块使用 Pygame 库创建图形用户界面 (GUI)，并处理用户输入，
驱动游戏主循环。它负责：
- 绘制棋盘和棋子。
- 接收并处理用户的鼠标点击和键盘事件（如悔棋、重开）。
- 调用引擎进行思考并执行引擎的走法。
- 判断游戏是否结束（将死或和棋）。
"""

import pygame
import sys
import os
from src.bitboard import Bitboard as Board
from src.engine import Engine
from src.moves import generate_moves, is_check
from src.constants import PLAYER_B
import pygame.gfxdraw

# --- 游戏界面常量 ---
SCREEN_WIDTH = 540
SCREEN_HEIGHT = 600
BOARD_COLOR = (240, 217, 181)  # 棋盘米色
LINE_COLOR = (0, 0, 0)
PIECE_RADIUS = 25

# --- Pygame 初始化 ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Mini Xiangqi (R: Resart, U: Undo, T: Test FEN)')
# 加载中文字体
font_path = os.path.join(os.path.dirname(__file__), "assets", "SimHei.ttf")
font = pygame.font.Font(font_path, 24)

# --- 游戏核心状态变量 ---
board = Board()  # 棋盘对象
engine = Engine()  # AI引擎对象
selected_piece_pos = None  # 玩家选中的棋子坐标 (r, c)
last_move = None  # 上一步走法，用于高亮显示
move_history = []  # 记录走法历史，用于悔棋
game_over = False  # 游戏是否结束的标志
game_result_message = ''  # 游戏结束时显示的信息


def draw_board():
    """绘制棋盘的网格、河流和九宫。"""
    screen.fill(BOARD_COLOR)
    # 绘制棋盘网格线
    for i in range(10):
        pygame.draw.aaline(screen, LINE_COLOR, (30, 30 + i * 60), (510, 30 + i * 60))
    for i in range(9):
        pygame.draw.aaline(screen, LINE_COLOR, (30 + i * 60, 30), (30 + i * 60, 570))

    # 绘制楚河汉界
    pygame.draw.rect(screen, BOARD_COLOR, (31, 271, 479, 59))
    river_text = font.render('楚 河      漢 界', True, LINE_COLOR)
    screen.blit(river_text, (180, 285))

    # 绘制九宫格斜线
    pygame.draw.aaline(screen, LINE_COLOR, (210, 30), (330, 150))
    pygame.draw.aaline(screen, LINE_COLOR, (330, 30), (210, 150))
    pygame.draw.aaline(screen, LINE_COLOR, (210, 450), (330, 570))
    pygame.draw.aaline(screen, LINE_COLOR, (330, 450), (210, 570))


def draw_pieces():
    """根据当前棋盘状态绘制所有棋子。"""
    piece_map = {
        1: '帅', 2: '仕', 3: '相', 4: '马', 5: '车', 6: '炮', 7: '兵',
        -1: '将', -2: '士', -3: '象', -4: '马', -5: '车', -6: '炮', -7: '卒',
    }
    color_map = {1: (255, 0, 0), -1: (0, 0, 0)}  # 红黑双方棋子颜色

    for r in range(10):
        for c in range(9):
            piece = board.get_piece_on_square(r * 9 + c)
            if piece != 0:
                player = 1 if piece > 0 else -1
                x, y = 30 + c * 60, 30 + r * 60

                # 绘制棋子背景，如果被选中则高亮
                fill_color = (255, 255, 255)
                if (r, c) == selected_piece_pos:
                    fill_color = (173, 216, 230)  # 淡蓝色

                pygame.gfxdraw.filled_circle(screen, x, y, PIECE_RADIUS, fill_color)
                pygame.gfxdraw.aacircle(screen, x, y, PIECE_RADIUS, LINE_COLOR)

                # 绘制棋子文字
                text = font.render(piece_map[piece], True, color_map[player])
                text_rect = text.get_rect(center=(x, y))
                screen.blit(text, text_rect)


def draw_last_move():
    """高亮显示上一步走法。"""
    if last_move:
        from_r, from_c = last_move[0]
        to_r, to_c = last_move[1]
        # 在起始和目标位置绘制标记
        pygame.gfxdraw.filled_circle(screen, from_c * 60 + 30, from_r * 60 + 30, 10, (0, 128, 0, 200))
        pygame.gfxdraw.filled_circle(screen, to_c * 60 + 30, to_r * 60 + 30, 5, (0, 128, 0, 200))


def is_game_over(board):
    """
    检查游戏是否结束。

    Returns:
        str: 如果游戏结束，返回结果信息 (如 '红方胜')；否则返回 None。
    """
    # 如果当前方没有合法走法
    if len(generate_moves(board)) == 0:
        if is_check(board, board.player_to_move):
            # 被将死
            return '红方胜' if board.player_to_move == PLAYER_B else '黑方胜'
        else:
            # 逼和
            return '和棋'
    return None


def main():
    """游戏主循环。"""
    global selected_piece_pos, board, last_move, move_history, game_over, game_result_message
    running = True
    while running:
        # --- 事件处理循环 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # --- 键盘事件处理 ---
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_t:  # T键: 加载测试FEN局面
                    board = Board('3aka2r/4n4/9/p5p1p/c1R1p4/4P1P2/P7P/N1CnB4/4C4/2BAKA3 w - - 0 1')
                    selected_piece_pos = None
                    last_move = None
                    move_history = []
                    game_over = False
                    game_result_message = ''
                if event.key == pygame.K_r:  # R键: 重新开始
                    board = Board()
                    selected_piece_pos = None
                    last_move = None
                    move_history = []
                    game_over = False
                    game_result_message = ''
                if event.key == pygame.K_u:  # U键: 悔棋 (撤销两步)
                    if len(move_history) >= 2:
                        # 撤销引擎的走法
                        move, captured = move_history.pop()
                        from_r, from_c = move[0]
                        to_r, to_c = move[1]
                        board.unmove_piece(from_r * 9 + from_c, to_r * 9 + to_c, captured)
                        # 撤销玩家的走法
                        move, captured = move_history.pop()
                        from_r, from_c = move[0]
                        to_r, to_c = move[1]
                        board.unmove_piece(from_r * 9 + from_c, to_r * 9 + to_c, captured)
                        last_move = None
                        selected_piece_pos = None

            # --- 鼠标点击事件处理 ---
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                c = (event.pos[0] - 30 + 30) // 60
                r = (event.pos[1] - 30 + 30) // 60

                if not (0 <= r < 10 and 0 <= c < 9):
                    continue

                if selected_piece_pos:
                    # --- 第二次点击：尝试走棋 ---
                    from_r, from_c = selected_piece_pos
                    to_r, to_c = r, c

                    from_sq, to_sq = from_r * 9 + from_c, to_r * 9 + to_c

                    # 检查走法是否合法
                    if (from_sq, to_sq) in generate_moves(board):
                        # 执行玩家走法
                        captured_piece = board.move_piece(from_sq, to_sq)
                        coord_move = ((from_r, from_c), (to_r, to_c))
                        move_history.append((coord_move, captured_piece))
                        last_move = coord_move
                        selected_piece_pos = None

                        # 立即重绘棋盘以显示玩家的走法
                        draw_board()
                        draw_pieces()
                        draw_last_move()
                        pygame.display.flip()

                        # 检查游戏是否结束
                        result_message = is_game_over(board)
                        if result_message:
                            game_over = True
                            game_result_message = result_message
                        else:
                            # --- 轮到引擎走棋 ---
                            pygame.time.wait(300)  # 短暂延迟，改善体验

                            # 显示“引擎思考中”的提示
                            overlay = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
                            overlay.fill((255, 255, 255, 220))
                            screen.blit(overlay, (0, SCREEN_HEIGHT / 2 - 100 / 2))
                            think_text = font.render('Engine is thinking...', True, (0, 0, 0))
                            text_rect = think_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                            screen.blit(think_text, text_rect)
                            pygame.display.flip()

                            # 调用引擎进行搜索
                            _, engine_move = engine.search_by_time(board, 3.0)
                            if engine_move:
                                from_r, from_c = engine_move[0]
                                to_r, to_c = engine_move[1]
                                from_sq, to_sq = from_r * 9 + from_c, to_r * 9 + to_c
                                captured_piece = board.move_piece(from_sq, to_sq)
                                move_history.append((engine_move, captured_piece))
                                last_move = engine_move

                                # 检查游戏是否结束
                                result_message = is_game_over(board)
                                if result_message:
                                    game_over = True
                                    game_result_message = result_message
                    else:
                        # 走法不合法，取消选择
                        selected_piece_pos = None
                else:
                    # --- 第一次点击：选择棋子 ---
                    piece = board.get_piece_on_square(r * 9 + c)
                    # 只能选择轮到自己走的棋子
                    if piece != 0 and (piece > 0 and board.player_to_move == 1 or piece < 0 and board.player_to_move == -1):
                        selected_piece_pos = (r, c)

        # --- 循环末尾的重绘 ---
        draw_board()
        draw_pieces()
        draw_last_move()

        # 如果游戏结束，显示结果
        if game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 220))
            screen.blit(overlay, (0, SCREEN_HEIGHT / 2 - 100 / 2))
            result_text = font.render(game_result_message, True, (0, 0, 0))
            text_rect = result_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
            screen.blit(result_text, text_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
