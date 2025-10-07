
import cProfile
import pstats
from src.bitboard import Bitboard
from src.engine import Engine


def profile_search():
    engine = Engine()
    # Disable opening book for profiling search performance
    engine.opening_book = None
    print("Opening book disabled for profiling.")

    # Use the default starting position FEN
    fen = "rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"
    board = Bitboard(fen=fen)
    print("Starting search to depth 5...")
    engine.search_by_depth(board, 5)
    print("Search finished.")


if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.run('profile_search()')

    print("\n--- Profiling Results ---")
    stats = pstats.Stats(profiler)
    stats.sort_stats(pstats.SortKey.CUMULATIVE)
    stats.print_stats(20)
