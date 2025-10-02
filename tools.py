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

    for i, row in enumerate(board):
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


def print_search_result(final_score, best_move, board_obj):

    print(f"\n评估分数 (从当前玩家角度): {final_score}，", end="")

    if best_move:
        from_pos, to_pos = best_move
        piece = board_obj.board[from_pos[0]][from_pos[1]]

        piece_map = {
            B_KING: '將', B_GUARD: '士', B_BISHOP: '象', B_HORSE: '馬', B_ROOK: '車', B_CANNON: '砲', B_PAWN: '卒',
            R_KING: '帥', R_GUARD: '仕', R_BISHOP: '相', R_HORSE: '傌', R_ROOK: '俥', R_CANNON: '炮', R_PAWN: '兵',
        }
        piece_name = piece_map.get(piece, f"Unknown({piece})")

        print(f"最佳着法是: {piece_name} 从 {from_pos} 移动到 {to_pos}，", end='')

        board_obj.make_move(best_move)

        print("应用推荐着法后：")
        print_board_text(board_obj.board)

    else:
        print("没有找到最佳着法.")
