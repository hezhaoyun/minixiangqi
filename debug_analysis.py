# -*- coding: utf-8 -*-

"""
Engine Debugging and Analysis Script
"""

from src.bitboard import Bitboard
from src.engine import Engine

def main():
    # A simple tactical position where Red can capture a Black knight.
    # The best move should be the rook at (7,0) capturing the knight at (4,4).
    # In square indices, this is move (63, 40).
    test_fen = "4k4/9/9/9/4n4/9/9/R8/9/4K4 w - - 0 1"

    print(f"Analyzing FEN: {test_fen}")
    
    board = Bitboard(fen=test_fen)
    engine = Engine()

    # Analyze the position to a depth of 3 (which is search depth 4 for the moves)
    engine.debug_analyze_position(board, 3)


if __name__ == "__main__":
    main()
