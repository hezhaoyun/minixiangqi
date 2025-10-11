
# -*- coding: utf-8 -*-
"""
Textual-based GUI for Mini Xiangqi.
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Label, Input, Button
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.message import Message

from src.bitboard import Bitboard as Board
from src.engine import Engine
from src.moves import generate_moves, is_check
from src.constants import PLAYER_B, PLAYER_R


class FenInputScreen(Screen):
    """Screen for FEN input."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Enter FEN string:"),
            Input(placeholder="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1"),
            Button("Load", variant="primary"),
            Button("Cancel"),
            id="fen-dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.variant == "primary":
            input_widget = self.query_one(Input)
            self.dismiss(input_widget.value)
        else:
            self.dismiss(None)


class XiangqiBoard(Static):
    """A widget to display the Xiangqi board."""

    class PieceSelected(Message):
        """Message sent when a piece is selected."""

        def __init__(self, r: int, c: int) -> None:
            self.r = r
            self.c = c
            super().__init__()

    def __init__(self, board: Board) -> None:
        self.board = board
        self.selected_piece_pos = None
        self.last_move = None
        super().__init__()

    def on_mount(self) -> None:
        self.update_display()

    def on_click(self, event) -> None:
        # Each cell is 3 chars wide, row label is 3 chars wide
        c = (event.x - 3) // 3
        # Column labels are on the first row
        r = event.y - 1

        if not (0 <= r < 10 and 0 <= c < 9):
            return

        self.post_message(self.PieceSelected(r, c))

    def update_display(self):
        """Updates the board display from the internal board state."""
        piece_map = {
            1: '帅', 2: '仕', 3: '相', 4: '马', 5: '车', 6: '炮', 7: '兵',
            -1: '将', -2: '士', -3: '象', -4: '马', -5: '车', -6: '炮', -7: '卒',
        }

        board_rows = []
        # Add column labels, each padded to 3 spaces
        board_rows.append("   " + "".join([f" {c} " for c in range(9)]))

        for r in range(10):
            row_display = [f"{r:2d} "]  # 3 chars for row label
            for c in range(9):
                piece = self.board.get_piece_on_square(r * 9 + c)

                content = ""
                if piece == 0:
                    content = "・ "
                else:
                    player = 1 if piece > 0 else -1
                    color = "red" if player == PLAYER_R else "white"
                    piece_char = piece_map.get(piece, ' ')
                    # Pad CJK character with a space to make it 3-wide
                    content = f"[{color}]{piece_char}[/{color}] "

                is_last_move_sq = False
                if self.last_move:
                    from_sq, to_sq = self.last_move
                    from_r, from_c = from_sq // 9, from_sq % 9
                    to_r, to_c = to_sq // 9, to_sq % 9
                    if (r, c) == (from_r, from_c) or (r, c) == (to_r, to_c):
                        is_last_move_sq = True

                if self.selected_piece_pos and self.selected_piece_pos == (r, c):
                    row_display.append(f"[reverse]{content}[/reverse]")
                elif is_last_move_sq:
                    row_display.append(f"[on green]{content}[/on green]")
                else:
                    row_display.append(content)

            board_rows.append("".join(row_display))

        self.update("\n".join(board_rows))


class TextualUI(App):
    """A Textual app for Mini Xiangqi."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("r", "reset_game", "Reset Game"),
        ("u", "undo_move", "Undo Move"),
        ("t", "load_fen", "Load FEN"),
    ]

    def __init__(self):
        super().__init__()
        self.board = Board()
        self.engine = Engine()
        self.xiangqi_board = XiangqiBoard(self.board)
        self.status_label = Label("Welcome to Mini Xiangqi! Your turn.")
        self.selected_piece_pos = None
        self.game_over = False
        self.move_history = []
        self.last_move = None
        self.dark = False

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Container(self.status_label, self.xiangqi_board)
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_reset_game(self) -> None:
        """Resets the game to the initial state."""
        self.board = Board()
        self.xiangqi_board.board = self.board
        self.selected_piece_pos = None
        self.game_over = False
        self.move_history = []
        self.last_move = None
        self.xiangqi_board.last_move = None
        self.status_label.update("Game reset. Your turn.")
        self.xiangqi_board.update_display()

    def action_undo_move(self) -> None:
        """Undoes the last player and engine move."""
        if len(self.move_history) >= 2:
            # Undo engine move
            move, captured = self.move_history.pop()
            self.board.unmove_piece(move[0], move[1], captured)
            # Undo player move
            move, captured = self.move_history.pop()
            self.board.unmove_piece(move[0], move[1], captured)

            self.game_over = False
            self.selected_piece_pos = None
            self.xiangqi_board.selected_piece_pos = None
            self.last_move = self.move_history[-1][0] if self.move_history else None
            self.xiangqi_board.last_move = self.last_move
            self.status_label.update("Undo successful. Your turn.")
            self.xiangqi_board.update_display()
        else:
            self.status_label.update("Not enough moves to undo.")

    def action_load_fen(self) -> None:
        """Opens a screen to load a FEN."""
        def _load_fen_callback(fen: str):
            if fen:
                try:
                    self.board = Board(fen)
                    self.xiangqi_board.board = self.board
                    self.selected_piece_pos = None
                    self.game_over = False
                    self.move_history = []
                    self.last_move = None
                    self.xiangqi_board.last_move = None
                    self.status_label.update(f"Loaded FEN. {self.board.player_to_move} to move.")
                    self.xiangqi_board.update_display()
                except Exception as e:
                    self.status_label.update(f"Invalid FEN string: {e}")

        self.push_screen(FenInputScreen(), _load_fen_callback)

    def on_xiangqi_board_piece_selected(self, message: XiangqiBoard.PieceSelected) -> None:
        if self.game_over:
            return

        r, c = message.r, message.c

        if self.selected_piece_pos:
            from_r, from_c = self.selected_piece_pos
            from_sq, to_sq = from_r * 9 + from_c, r * 9 + c

            if (from_sq, to_sq) in generate_moves(self.board):
                captured_piece = self.board.move_piece(from_sq, to_sq)
                self.last_move = (from_sq, to_sq)
                self.move_history.append((self.last_move, captured_piece))
                self.selected_piece_pos = None
                self.xiangqi_board.selected_piece_pos = None
                self.xiangqi_board.last_move = self.last_move
                self.xiangqi_board.update_display()
                self.check_game_over()

                if not self.game_over:
                    self.status_label.update("Engine is thinking...")
                    self.set_timer(0.1, self.engine_move)
            else:
                self.selected_piece_pos = None
                self.xiangqi_board.selected_piece_pos = None
                self.status_label.update("Invalid move. Your turn.")
        else:
            piece = self.board.get_piece_on_square(r * 9 + c)
            if piece != 0 and (piece > 0 and self.board.player_to_move == 1 or piece < 0 and self.board.player_to_move == -1):
                self.selected_piece_pos = (r, c)
                self.xiangqi_board.selected_piece_pos = (r, c)
                self.status_label.update(f"Piece at ({r}, {c}) selected. Choose destination.")
            else:
                self.status_label.update("Select one of your pieces. Your turn.")

        self.xiangqi_board.update_display()

    def engine_move(self):
        _, engine_move = self.engine.search_by_time(self.board, 1.0)
        if engine_move:
            from_r, from_c = engine_move[0]
            to_r, to_c = engine_move[1]
            from_sq, to_sq = from_r * 9 + from_c, to_r * 9 + to_c
            captured_piece = self.board.move_piece(from_sq, to_sq)
            self.last_move = (from_sq, to_sq)
            self.move_history.append((self.last_move, captured_piece))
            self.xiangqi_board.last_move = self.last_move
            self.xiangqi_board.update_display()
            self.check_game_over()
            if not self.game_over:
                self.status_label.update("Your turn.")
        else:
            self.status_label.update("Engine has no moves. It might be a draw or an error.")
            self.game_over = True

    def check_game_over(self):
        if len(generate_moves(self.board)) == 0:
            if is_check(self.board, self.board.player_to_move):
                winner = "Red" if self.board.player_to_move == PLAYER_B else "Black"
                self.status_label.update(f"Checkmate! {winner} wins.")
            else:
                self.status_label.update("Stalemate! It's a draw.")
            self.game_over = True


if __name__ == '__main__':
    app = TextualUI()
    app.run()
