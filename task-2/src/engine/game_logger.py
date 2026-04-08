
from __future__ import annotations

from engine.board import Board, Move
from players.players import Player

class GameLogger:
    def __init__(self, output_path: str) -> None:
        self.output_path = output_path
        with open(self.output_path, "w", encoding="utf-8") as log_file:
            log_file.write("====== GAME LOG ======\n")

    def _write_board(self, board: Board, log_file) -> None:
        for line in board.to_lines():
            log_file.write(f"{line}\n")

    def log_initial_board(self, board: Board) -> None:
        with open(self.output_path, "a", encoding="utf-8") as log_file:
            log_file.write("\n--- START BOARD ---\n")
            self._write_board(board, log_file)

    def log_turn(
        self,
        round_no: int,
        player: Player,
        move: Move,
        heuristic_name: str,
        visited_nodes: int,
        elapsed_seconds: float,
        board_after_move: Board,
    ) -> None:
        with open(self.output_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n--- ROUND {round_no} ---\n")
            log_file.write(f"player={player.name} symbol={player.symbol}\n")
            log_file.write(
                "move="
                f"({move.from_row},{move.from_col})->({move.to_row},{move.to_col}) "
                f"capture={move.is_capture}\n"
            )
            log_file.write(
                f"heuristic={heuristic_name} visited_nodes={visited_nodes} "
                f"time_s={elapsed_seconds:.6f}\n"
            )
            self._write_board(board_after_move, log_file)

    def log_end(self, rounds: int, winner_name: str | None) -> None:
        with open(self.output_path, "a", encoding="utf-8") as log_file:
            log_file.write("\n--- GAME END ---\n")
            log_file.write(f"rounds={rounds}\n")
            log_file.write(f"winner={winner_name if winner_name else 'brak'}\n")
