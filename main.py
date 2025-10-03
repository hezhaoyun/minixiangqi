from board import Board
from engine import Engine
from tools import print_board_text


def main():
    """主函数, 模拟对局"""

    TIME_LIMIT_SECONDS = 3.0  # 每一步的思考时间
    SIMULATE_STEPS = 24

    game_board = Board()
    engine = Engine()

    print_board_text(game_board)

    for i in range(SIMULATE_STEPS):
        # 使用按时间限制的搜索
        final_score, best_move = engine.search_by_time(game_board, TIME_LIMIT_SECONDS)
        print(f"\n思考时间: {TIME_LIMIT_SECONDS}s, 评估分数: {final_score}，最佳着法是: {best_move}")

        if best_move is None:
            print("无棋可走, 游戏结束.")
            break

        game_board.make_move(best_move)
        print_board_text(game_board, best_move)


if __name__ == "__main__":
    main()
