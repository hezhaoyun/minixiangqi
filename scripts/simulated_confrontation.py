# -*- coding: utf-8 -*-
'''
引擎自我对弈模拟脚本。

该脚本让引擎自己与自己下棋，用于测试引擎的稳定性和棋力。
它会在终端中以文本形式打印出每一步的棋盘状态。

注意：此脚本使用了旧的Board类，与当前项目的Bitboard不兼容。
在运行前需要确保有 `src.board` 模块或将其适配为 `src.bitboard`。
'''

from src.constants import *
from src.engine import Engine
from src.board import Board, Move


def print_board_text(board: Board, last_move: Move = None):
    '''
    以文本形式在终端打印棋盘,并用颜色区分红黑双方。
    使用ANSI转义序列来显示颜色。
    '''

    # ANSI 颜色代码
    END_COLOR = '\033[0m'      # 重置颜色
    RED_COLOR = '\033[31m'     # 红色
    BLUE_COLOR = '\033[34m'    # 蓝色 (代替黑色以便在深色背景下显示)
    HL_RED_COLOR = '\033[31m\033[47m'   # 高亮红色 (红棋白底)
    HL_BLUE_COLOR = '\033[34m\033[47m'  # 高亮蓝色 (黑棋白底)
    HL_END_COLOR = '\033[0m\033[47m'    # 高亮背景色重置

    piece_map = {
        B_KING: '將', B_GUARD: '士', B_BISHOP: '象', B_HORSE: '馬', B_ROOK: '車', B_CANNON: '砲', B_PAWN: '卒',
        R_KING: '帥', R_GUARD: '仕', R_BISHOP: '相', R_HORSE: '傌', R_ROOK: '俥', R_CANNON: '炮', R_PAWN: '兵',
        EMPTY: '・'
    }

    fp, tp = (last_move[0], last_move[1]) if last_move else (None, None)

    print('\n   0  1  2  3  4  5  6  7  8')
    print('-----------------------------')

    for r, row in enumerate(board.board):
        row_items = [f'{r}|']

        for c, piece in enumerate(row):
            char = piece_map[piece]

            # 判断是否需要高亮
            is_highlighted = (fp == (r, c) or tp == (r, c))

            color = END_COLOR
            if is_highlighted:
                if piece > 0:
                    color = HL_RED_COLOR
                elif piece < 0:
                    color = HL_BLUE_COLOR
                else:
                    color = HL_END_COLOR
            else:
                if piece > 0:
                    color = RED_COLOR
                elif piece < 0:
                    color = BLUE_COLOR

            row_items.append(f'{color}{char}{END_COLOR}')

        print(' '.join(row_items))

    print('-----------------------------')


def main():
    '''
    主函数, 模拟引擎自我对弈。
    '''
    SIMULATE_STEPS = 24  # 模拟的总步数（半回合）

    game_board = Board()
    engine = Engine()

    print('--- 引擎自我对弈开始 ---')
    print_board_text(game_board)

    for i in range(SIMULATE_STEPS):
        print(f'\n--- 第 {i+1} 回合 ---')
        player_name = '红方' if game_board.player_to_move == PLAYER_R else '黑方'
        print(f'轮到 {player_name} 走棋...')

        # --- 调用引擎进行搜索 ---
        # 可以选择按时间限制或按深度限制
        final_score, best_move = engine.search_by_time(game_board, 2.0)
        print(f'思考时间: {2.0}s, 评估分数: {final_score}，最佳着法是: {best_move}')

        # final_score, best_move = engine.search_by_depth(game_board, 5)
        # print(f'思考深度: 5, 评估分数: {final_score}，最佳着法是: {best_move}')

        if best_move is None:
            print('引擎返回无棋可走, 游戏结束.')
            break

        # 执行走法并打印棋盘
        game_board.make_move(best_move)
        print_board_text(game_board, best_move)


if __name__ == '__main__':
    main()
