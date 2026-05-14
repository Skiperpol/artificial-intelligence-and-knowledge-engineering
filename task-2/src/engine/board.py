from dataclasses import dataclass
from typing import List, Sequence
from players.players import Player


DEFAULT_ROWS = 8
DEFAULT_COLS = 8
# Zachowane dla testów i kodu zakładającego planszę 8×8.
BOARD_SIZE = DEFAULT_ROWS

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
    def __init__(
        self,
        grid: Sequence[Sequence[str]] | None = None,
        rows: int | None = None,
        cols: int | None = None,
    ) -> None:
        if grid is None:
            r = DEFAULT_ROWS if rows is None else rows
            c = DEFAULT_COLS if cols is None else cols
            self.grid = self._default_start_position(r, c)
        else:
            self.grid = []
            for row in grid:
                new_row = list(row)
                self.grid.append(new_row)
            self._validate_grid()

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0]) if self.grid else 0

    @staticmethod
    def _default_start_position(rows: int, cols: int) -> List[List[str]]:
        if rows < 2:
            raise ValueError("Plansza musi mieć co najmniej 2 wiersze.")
        if cols < 1:
            raise ValueError("Plansza musi mieć co najmniej 1 kolumnę.")

        grid: List[List[str]] = [[EMPTY] * cols for _ in range(rows)]
        setup_depth = min(2, rows // 2)
        for r in range(setup_depth):
            for c in range(cols):
                grid[r][c] = "B"
        for r in range(rows - setup_depth, rows):
            for c in range(cols):
                grid[r][c] = "W"
        return grid

    def _validate_grid(self) -> None:
        if self.rows < 2:
            raise ValueError("Plansza musi mieć co najmniej 2 wiersze.")
        w = len(self.grid[0])
        if w < 1:
            raise ValueError("Plansza musi mieć co najmniej 1 kolumnę.")
        for row in self.grid:
            if len(row) != w:
                raise ValueError("Wszystkie wiersze muszą mieć tę samą liczbę kolumn.")
            for cell in row:
                if cell not in {"B", "W", EMPTY, LAST_MOVE_FROM}:
                    raise ValueError(f"Invalid board token: {cell}")

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    @staticmethod
    def _is_empty(cell: str) -> bool:
        return cell in {EMPTY, LAST_MOVE_FROM}

    def get_legal_moves(self, player: Player) -> List[Move]:
        # [Punkt 1] Funkcja generująca możliwe ruchy dla danego stanu i gracza.
        moves: List[Move] = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] != player.symbol:
                    continue

                next_row = row + player.direction
                if not (0 <= next_row < self.rows):
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
        for row in range(self.rows):
            for col in range(self.cols):
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
        stripped = [line.rstrip("\n\r") for line in lines]
        if not stripped:
            raise ValueError("Brak linii opisujących planszę.")

        grid_data: List[List[str]] = []
        expected_width: int | None = None
        for line in stripped:
            cells = line.split()
            if expected_width is None:
                expected_width = len(cells)
            elif len(cells) != expected_width:
                raise ValueError(
                    f"Każdy wiersz musi mieć tę samą liczbę pól (oczekiwano {expected_width}, "
                    f"dostano {len(cells)})."
                )
            grid_data.append(cells)

        return cls(grid_data)
