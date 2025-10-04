import os
import re
import json
from typing import Optional, List
from board import Board, Move
import moves_gen
from constants import (
    PLAYER_R, PLAYER_B, EMPTY,
    R_KING, B_KING, R_GUARD, B_GUARD, R_BISHOP, B_BISHOP,
    R_HORSE, B_HORSE, R_ROOK, B_ROOK, R_CANNON, B_CANNON, R_PAWN, B_PAWN
)

# 开局库数据源目录
DATA_SOURCE_DIR = 'xq_data/data/opening'
# 生成的开局库文件名
OUTPUT_FILE = 'opening_book.json'
# 开局库记录的最大步数
MAX_PLY = 20


def parse_movelist(content: str) -> list[str]:
    '''从文件内容中解析出所有走法列表.'''
    movelists = []
    content = content.replace('\r', '').replace('\n', '')

    # 匹配主走法列表
    main_move_match = re.search(r'\[DhtmlXQ_movelist\](.*?)\[/DhtmlXQ_movelist\]', content, re.DOTALL)
    if main_move_match:
        movelists.append(main_move_match.group(1).strip())

    # 匹配所有变着
    variation_matches = re.findall(r'\[DhtmlXQ_move_\d+_\d+_\d+\](.*?)\[/DhtmlXQ_move_\d+_\d+_\d+\]', content, re.DOTALL)
    for var in variation_matches:
        movelists.append(var.strip())

    return movelists


def parse_move_str(move_str: str) -> Optional[Move]:
    '''
    将4位数字的走法字符串转换为绝对坐标走法 ((from_r, from_c), (to_r, to_c))。
    格式: c1r1c2r2
    '''
    if len(move_str) != 4 or not move_str.isdigit():
        return None
    c1, r1, c2, r2 = map(int, list(move_str))
    return ((r1, c1), (r2, c2))


def build_book():
    '''
    构建开局库。
    '''
    opening_book = {}
    file_count = 0

    print(f'开始从 {DATA_SOURCE_DIR} 目录扫描棋谱文件...')

    for root, _, files in os.walk(DATA_SOURCE_DIR):
        for filename in files:
            # 忽略非棋谱文件
            if filename.endswith(('.md', '.json', '.png', '.gif', 'README.md', 'register.json')):
                continue

            file_path = os.path.join(root, filename)
            # 调试: 打印正在处理的文件名
            # print(f'正在处理: {file_path}')

            try:
                with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                print(f'无法读取文件 {file_path}: {e}')
                continue

            movelists = parse_movelist(content)
            if not movelists:
                # print(f'文件 {file_path} 中未找到走法列表')
                continue

            file_count += 1
            if file_count % 1000 == 0:
                print(f'已处理 {file_count} 个文件...')

            for movelist_str in movelists:
                board = Board()
                # print(f'处理走法字符串: {movelist_str}')
                # 将走法字符串分割成4个字符一组的列表
                moves_str_list = [movelist_str[i:i+4] for i in range(0, len(movelist_str), 4)]

                for i, move_str in enumerate(moves_str_list):
                    if i >= MAX_PLY:
                        break

                    zobrist_key = board.hash_key
                    legal_moves = moves_gen.generate_moves(board)

                    move = parse_move_str(move_str)

                    if move is None or move not in legal_moves:
                        # print(f'非法走法或转换失败: {move_str}, 转换结果: {move}')
                        break

                    if zobrist_key not in opening_book:
                        opening_book[zobrist_key] = []

                    # 使用列表推导式简化坐标格式
                    simple_move = [list(move[0]), list(move[1])]

                    if simple_move not in opening_book[zobrist_key]:
                        opening_book[zobrist_key].append(simple_move)

                    board.make_move(move)

    print(f'处理完成！共处理 {file_count} 个棋谱文件。')
    print(f'开局库中包含 {len(opening_book)} 个局面。')

    # 保存开局库到JSON文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(opening_book, f)  # , indent=2)

    print(f'开局库已成功保存到 {OUTPUT_FILE}')


if __name__ == '__main__':
    build_book()
