from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence
from players.players import Player


BOARD_SIZE = 8
EMPTY = "_"
LAST_MOVE_FROM = "o"


@dataclass(frozen=True)
class Move:
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    is_capture: bool

class Board:
    # [Punkt 1] Poprawne zdefiniowanie stanu gry.
    def __init__(self, grid: Sequence[Sequence[str]] | None = None) -> None:
        if grid is None:
            self.grid = self._default_start_position()
        else:
            self.grid = []
            for row in grid:
                new_row = list(row)
                self.grid.append(new_row)
            self._validate_grid()

    @staticmethod
    def _default_start_position() -> List[List[str]]:
        grid = []

        for _ in range(BOARD_SIZE):
            row = [EMPTY] * BOARD_SIZE
            grid.append(row)

        for row in (0, 1):
            for col in range(BOARD_SIZE):
                grid[row][col] = "B"
        for row in (BOARD_SIZE - 2, BOARD_SIZE - 1):
            for col in range(BOARD_SIZE):
                grid[row][col] = "W"
        return grid

    def _validate_grid(self) -> None:
        if len(self.grid) != BOARD_SIZE:
            raise ValueError("Board must have exactly " + str(BOARD_SIZE) + " rows.")
        for row in self.grid:
            if len(row) != BOARD_SIZE:
                raise ValueError("Each row must have exactly " + str(BOARD_SIZE) + " columns.")
            for cell in row:
                if cell not in {"B", "W", EMPTY, LAST_MOVE_FROM}:
                    raise ValueError(f"Invalid board token: {cell}")

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    @staticmethod
    def _is_empty(cell: str) -> bool:
        return cell in {EMPTY, LAST_MOVE_FROM}

    def get_legal_moves(self, player: Player) -> List[Move]:
        # [Punkt 1] Funkcja generująca możliwe ruchy dla danego stanu i gracza.
        moves: List[Move] = []
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.grid[row][col] != player.symbol:
                    continue

                next_row = row + player.direction
                if not (0 <= next_row < BOARD_SIZE):
                    continue

                if self._is_empty(self.grid[next_row][col]):
                    moves.append(Move(row, col, next_row, col, False))

                for delta_col in (-1, 1):
                    next_col = col + delta_col
                    if not self._in_bounds(next_row, next_col):
                        continue

                    destination = self.grid[next_row][next_col]
                    if self._is_empty(destination):
                        moves.append(Move(row, col, next_row, next_col, False))
                    elif destination == player.opponent_symbol():
                        moves.append(Move(row, col, next_row, next_col, True))

        return moves

    def _clear_last_move_marker(self) -> None:
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                if self.grid[row][col] == LAST_MOVE_FROM:
                    self.grid[row][col] = EMPTY

    def apply_move(self, move: Move, player: Player) -> None:
        if self.grid[move.from_row][move.from_col] != player.symbol:
            raise ValueError("Invalid move source for given player.")

        self._clear_last_move_marker()
        self.grid[move.from_row][move.from_col] = LAST_MOVE_FROM
        self.grid[move.to_row][move.to_col] = player.symbol

    def has_player_won(self, player: Player) -> bool:
        meta_player = self.grid[player.goal_row]
        
        for cell in meta_player:
            if cell == player.symbol:
                return True
                
        return False      

    def to_lines(self) -> List[str]:
        result = []
        
        for row in self.grid:
            joined_row = " ".join(row)
            result.append(joined_row)
            
        return result

    @classmethod
    def from_lines(cls, lines: Sequence[str]) -> "Board":
        if len(lines) != BOARD_SIZE:
            raise ValueError(f"Board must have exactly {BOARD_SIZE} lines.")

        grid_data = []
        for line in lines:
            cells = line.split()
            if len(cells) != BOARD_SIZE:
                raise ValueError(f"Each board row must have exactly {BOARD_SIZE} cells.")
            grid_data.append(cells)

        return cls(grid_data)
