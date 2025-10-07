# -*- coding: utf-8 -*-
"""
开局库生成脚本。

该脚本会扫描指定目录下的棋谱文件（特定格式），解析出其中的走法，
并构建一个开局库。开局库是一个字典，键是局面的Zobrist哈希值，
值是该局面下所有出现过的、合法的后继走法列表。

生成的开局库将保存为 JSON 文件，供引擎在开局阶段查询使用。
"""

import os
import re
import json
from typing import Optional, List
# 注意：此脚本使用了旧的Board类，与当前项目的Bitboard不兼容。
# 在运行前需要确保有 `src.board` 模块或将其适配为 `src.bitboard`。
from src.board import Board, Move
from src.moves_gen import generate_moves
from src.constants import *

# --- 配置 ---
DATA_SOURCE_DIR = 'external/xq_data/data/opening'  # 开局库数据源目录
OUTPUT_FILE = 'opening_book.json'  # 生成的开局库文件名
MAX_PLY = 20  # 开局库记录的最大步数（半回合）


def parse_movelist(content: str) -> list[str]:
    """
    从文件内容中解析出所有走法列表（包括主变着和所有变着）。
    文件格式是DhtmlXQ使用的格式。
    """
    movelists = []
    content = content.replace('\r', '').replace('\n', '')

    # 1. 匹配主走法列表
    main_move_match = re.search(
        r'\[DhtmlXQ_movelist\](.*?)?\[/DhtmlXQ_movelist\]', content, re.DOTALL)
    if main_move_match:
        movelists.append(main_move_match.group(1).strip())

    # 2. 匹配所有变着
    # 格式如: [DhtmlXQ_move_0_1_1]...[/DhtmlXQ_move_0_1_1]
    variation_matches = re.findall(
        r'\[DhtmlXQ_move_\d+_\d+_\d+\](.*?)?\[/DhtmlXQ_move_\d+_\d+_\d+\]', content, re.DOTALL)
    for var in variation_matches:
        movelists.append(var.strip())

    return movelists


def parse_move_str(move_str: str) -> Optional[Move]:
    """
    将4位数字的走法字符串转换为绝对坐标走法 ((from_r, from_c), (to_r, to_c))。
    格式: c1r1c2r2 (列1行1列2行2)
    """
    if len(move_str) != 4 or not move_str.isdigit():
        return None
    c1, r1, c2, r2 = map(int, list(move_str))
    return ((r1, c1), (r2, c2))


def build_book():
    """
    扫描棋谱文件，构建并保存开局库。
    """
    opening_book = {}
    file_count = 0

    print(f'开始从 {DATA_SOURCE_DIR} 目录扫描棋谱文件...')

    for root, _, files in os.walk(DATA_SOURCE_DIR):
        for filename in files:
            # 忽略非棋谱文件
            if filename.endswith(('.md', '.json', '.png', '.gif', 'README.md', 'register.json')):
                continue

            file_path = os.path.join(root, filename)

            try:
                # 棋谱文件通常使用GBK编码
                with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                print(f'无法读取文件 {file_path}: {e}')
                continue

            movelists = parse_movelist(content)
            if not movelists:
                continue

            file_count += 1
            if file_count % 1000 == 0:
                print(f'已处理 {file_count} 个文件...')

            # 遍历棋谱中的每一个变着
            for movelist_str in movelists:
                board = Board()  # 每个变着都从初始局面开始

                # 将走法字符串分割成4个字符一组的列表
                moves_str_list = [movelist_str[i:i+4]
                                  for i in range(0, len(movelist_str), 4)]

                for i, move_str in enumerate(moves_str_list):
                    if i >= MAX_PLY:
                        break

                    zobrist_key = board.hash_key
                    legal_moves = generate_moves(board)

                    move = parse_move_str(move_str)

                    # 校验解析出的走法是否合法
                    if move is None or move not in legal_moves:
                        break

                    if zobrist_key not in opening_book:
                        opening_book[zobrist_key] = []

                    # 存储为JSON兼容的列表格式
                    simple_move = [list(move[0]), list(move[1])]

                    if simple_move not in opening_book[zobrist_key]:
                        opening_book[zobrist_key].append(simple_move)

                    board.make_move(move)

    print(f'处理完成！共处理 {file_count} 个棋谱文件。')
    print(f'开局库中包含 {len(opening_book)} 个局面。')

    # 保存开局库到JSON文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(opening_book, f)

    print(f'开局库已成功保存到 {OUTPUT_FILE}')


if __name__ == '__main__':
    build_book()
