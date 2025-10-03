from board import Board
from engine import Engine
from tools import print_board_text


def main():
    """主函数, 模拟对局"""

    SIMULATE_STEPS = 24

    game_board = Board()
    engine = Engine()

    print_board_text(game_board)

    for i in range(SIMULATE_STEPS):
        # 使用按时间限制的搜索
        final_score, best_move = engine.search_by_time(game_board, 2.0)
        print(f"\n思考时间: {2.0}s, 评估分数: {final_score}，最佳着法是: {best_move}")

        # 使用按深度限制的搜索
        # final_score, best_move = engine.search_by_depth(game_board, 5)
        # print(f"\n思考深度: 5, 评估分数: {final_score}，最佳着法是: {best_move}")

        if best_move is None:
            print("无棋可走, 游戏结束.")
            break

        game_board.make_move(best_move)
        print_board_text(game_board, best_move)


if __name__ == "__main__":
    main()
