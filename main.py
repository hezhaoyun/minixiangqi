from board import Board
from engine import Engine
from tools import print_board_text


def main():
    """主函数, 模拟对局"""

    SEARCH_DEPTH = 5
    SIMULATE_STEPS = 24

    game_board = Board()
    engine = Engine()

    print_board_text(game_board)

    for i in range(SIMULATE_STEPS):
        final_score, best_move = engine.search(game_board, SEARCH_DEPTH)
        print(f"\n评估分数 (从当前玩家角度): {final_score}，最佳着法是: {best_move}")

        if best_move is None:
            print("无棋可走, 游戏结束.")
            break

        game_board.make_move(best_move)
        print_board_text(game_board, best_move)


if __name__ == "__main__":
    main()
