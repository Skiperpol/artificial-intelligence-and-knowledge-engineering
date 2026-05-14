import random
from typing import List

from _setup import Runner

from engine.board import BOARD_SIZE, Board
from players.players import FirstPlayer, Player, SecondPlayer


def random_board(seed: int, n_pieces_each: int = 5) -> Board:
    """Deterministic random mid-game position avoiding goal rows."""
    rng = random.Random(seed)
    grid: List[List[str]] = [["_"] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    inner_cells = [
        (r, c)
        for r in range(1, BOARD_SIZE - 1)
        for c in range(BOARD_SIZE)
    ]
    rng.shuffle(inner_cells)

    for r, c in inner_cells[:n_pieces_each]:
        grid[r][c] = "B"
    for r, c in inner_cells[n_pieces_each : 2 * n_pieces_each]:
        grid[r][c] = "W"

    return Board(grid)


def both_players() -> list[Player]:
    return [FirstPlayer(), SecondPlayer()]


def mate_in_one_board_for_black() -> Board:
    lines = [
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ B _ _ _ _",
        "_ _ _ _ _ _ _ _",
    ]
    return Board.from_lines(lines)


def mate_in_one_board_for_white() -> Board:
    lines = [
        "_ _ _ _ _ _ _ _",
        "_ _ _ W _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
    ]
    return Board.from_lines(lines)


def capture_or_lose_board() -> Board:
    """It is B's turn. W is one move from winning (W at row 1 reaches row 0
    next ply). B has two pieces sitting at row 0 that can capture W
    diagonally. Not capturing means W reaches its goal row and B loses.
    """
    lines = [
        "_ _ B _ B _ _ _",
        "_ _ _ W _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
    ]
    return Board.from_lines(lines)
