from board import Board, Move
from engine import Engine


from constants import (
    EMPTY, B_KING, B_GUARD, B_BISHOP, B_HORSE, B_ROOK, B_CANNON, B_PAWN,
    R_KING, R_GUARD, R_BISHOP, R_HORSE, R_ROOK, R_CANNON, R_PAWN
)


def print_board_text(board: Board, last_move: Move = None):
    '''以文本形式打印棋盘,并用颜色区分红黑双方'''

    # ANSI color codes
    END_COLOR = '\033[0m'
    RED_COLOR = '\033[31m'
    BLUE_COLOR = '\033[34m'
    HL_RED_COLOR = '\033[31m\033[47m'
    HL_BLUE_COLOR = '\033[34m\033[47m'
    HL_END_COLOR = '\033[0m\033[47m'

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

            hl = (fp == (r, c) or tp == (r, c))
            if hl:
                pass
            color = HL_END_COLOR if hl else END_COLOR

            if piece > 0:
                color = HL_RED_COLOR if hl else RED_COLOR
            elif piece < 0:
                color = HL_BLUE_COLOR if hl else BLUE_COLOR

            row_items.append(f'{color}{char}{END_COLOR}')

        print(' '.join(row_items))

    print('-----------------------------')


def main():
    '''主函数, 模拟对局'''

    SIMULATE_STEPS = 24

    game_board = Board()
    engine = Engine()

    print_board_text(game_board)

    for i in range(SIMULATE_STEPS):
        # 使用按时间限制的搜索
        final_score, best_move = engine.search_by_time(game_board, 2.0)
        print(f'\n思考时间: {2.0}s, 评估分数: {final_score}，最佳着法是: {best_move}')

        # 使用按深度限制的搜索
        # final_score, best_move = engine.search_by_depth(game_board, 5)
        # print(f'\n思考深度: 5, 评估分数: {final_score}，最佳着法是: {best_move}')

        if best_move is None:
            print('无棋可走, 游戏结束.')
            break

        game_board.make_move(best_move)
        print_board_text(game_board, best_move)


if __name__ == '__main__':
    main()
