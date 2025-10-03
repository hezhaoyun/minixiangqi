# -*- coding: utf-8 -*-

import unittest

import board
import evaluate
import moves_gen
from constants import PLAYER_B, PLAYER_R


class TestRefactor(unittest.TestCase):

    def setUp(self):
        """在每个测试前设置好初始棋盘"""
        self.initial_board = board.Board()

    def test_initial_evaluation(self):
        """测试初始局面的评估分数是否与重构前一致"""
        # 这个值是在重构前从旧代码的输出中获得的
        expected_score = 115
        actual_score = evaluate.evaluate(self.initial_board)
        self.assertEqual(expected_score, actual_score)

    def test_initial_move_generation(self):
        """测试初始局面双方的合法走法数量"""
        # 1. 测试红方
        self.initial_board.player = PLAYER_R
        red_moves = moves_gen.generate_moves(self.initial_board)
        # 这个值是在重构前从旧代码的输出中获得的
        self.assertEqual(len(red_moves), 44)

        # 2. 测试黑方
        self.initial_board.player = PLAYER_B
        black_moves = moves_gen.generate_moves(self.initial_board)
        # 这个值是在重构前从旧代码的输出中获得的
        self.assertEqual(len(black_moves), 44)


if __name__ == '__main__':
    unittest.main()
