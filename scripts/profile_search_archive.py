# -*- coding: utf-8 -*-
'''
引擎性能分析脚本。

该脚本使用 Python 内置的 cProfile 和 pstats 模块来分析
引擎核心搜索函数 `search_by_depth` 的性能。

它会从一个固定的初始局面开始，搜索指定深度，然后打印出
耗时最长的函数调用，帮助开发者定位性能瓶颈。
'''
from src.engine import Engine
from src.bitboard import Bitboard
import pstats
import cProfile
import sys
import os
# 将项目根目录添加到Python路径中，以确保可以正确导入src模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def profile_search():
    '''
    执行搜索并进行性能分析的函数。
    '''
    engine = Engine()
    # 禁用开局库，以确保我们分析的是纯粹的搜索性能
    engine.opening_book = None
    print('Opening book disabled for profiling.')

    # 从标准开局局面开始
    # fen = 'rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1'
    fen = 'rnbakCb1r/9/7c1/p1p1p1p1p/9/9/P1P1P1P1P/1C7/9/RcBAKABNR b - - 0 1'
    board = Bitboard(fen=fen)

    # print('Starting search to depth 5...')
    # score, move = engine.search_by_depth(board, 5)
    print('Starting search time limit 3s...')
    score, move = engine.search_by_time(board, 3.0)
    print(f'Search finished. Score: {score}, Move: {move}')


if __name__ == '__main__':
    # 创建性能分析器
    profiler = cProfile.Profile()
    # 运行目标函数
    profiler.run('profile_search()')

    # 打印性能分析结果
    print('\n--- Profiling Results ---')
    stats = pstats.Stats(profiler)
    # 按累计耗时排序
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    # 打印前20个耗时最长的函数
    stats.print_stats(20)
