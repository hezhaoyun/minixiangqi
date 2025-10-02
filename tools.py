from board import *


def print_board_text(board):
    """以文本形式打印棋盘,并用颜色区分红黑双方"""

    # ANSI color codes
    RED_COLOR = '\033[91m'
    YELLOW_COLOR = '\033[93m'  # For Black pieces
    END_COLOR = '\033[0m'

    piece_map = {
        B_KING: '將', B_GUARD: '士', B_BISHOP: '象', B_HORSE: '馬', B_ROOK: '車', B_CANNON: '砲', B_PAWN: '卒',
        R_KING: '帥', R_GUARD: '仕', R_BISHOP: '相', R_HORSE: '傌', R_ROOK: '俥', R_CANNON: '炮', R_PAWN: '兵',
        EMPTY: '・'
    }

    print("\n   0  1  2  3  4  5  6  7  8")
    print("-----------------------------")

    for i, row in enumerate(board.board):
        row_items = [f"{i}|"]

        for piece in row:
            char = piece_map[piece]
            if piece > 0:  # Red piece
                row_items.append(f"{RED_COLOR}{char}{END_COLOR}")
            elif piece < 0:  # Black piece
                row_items.append(f"{YELLOW_COLOR}{char}{END_COLOR}")
            else:  # Empty
                row_items.append(char)

        print(" ".join(row_items))

    print("-----------------------------")
