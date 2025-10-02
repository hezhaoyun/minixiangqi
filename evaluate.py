# -*- coding: utf-8 -*-

"""
中国象棋评估函数
"""

from board import *


def evaluate(board):
    """
    评估函数
    :param board: 10x9 的二维列表, 表示棋盘状态
    :return: 局面的评估分数, 正数表示红方优势, 负数表示黑方优势
    """
    score = 0
    for r in range(10):
        for c in range(9):
            piece = board[r][c]
            if piece != EMPTY:
                # 加上棋子本身的基础价值
                score += PIECE_VALUES[piece]

                # 加上棋子的位置价值
                if piece > 0:  # 红方
                    # 红方PST需要垂直翻转
                    score += PST[piece][9 - r][8 - c]
                else:  # 黑方
                    score -= PST[piece][r][c]
    return score


if __name__ == '__main__':
    # 示例: 评估初始局面
    initial_board = Board()
    initial_score = evaluate(initial_board.board)

    print("初始局面评估分数:", initial_score)
    # 初始局面双方均等, 分数应该接近0 (由于位置价值不对称, 不会完全为0)

    # 示例: 红方拿掉黑方一个车
    board_without_b_rook = Board()
    board_without_b_rook.board[0][0] = EMPTY
    score_after_capture = evaluate(board_without_b_rook.board)

    print("红方拿掉黑方一个车后的评估分数:", score_after_capture)
    # 分数应该显著为正, 表示红方巨大优势
