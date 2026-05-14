import random
from typing import List

from _setup import Runner

from engine.board import Board
from players.players import FirstPlayer, Player, SecondPlayer

TEST_ROWS = 8
TEST_COLS = 8


def random_board(seed: int, n_pieces_each: int = 5) -> Board:
    rng = random.Random(seed)
    grid: List[List[str]] = [["_"] * TEST_COLS for _ in range(TEST_ROWS)]
    inner_cells = [
        (r, c)
        for r in range(1, TEST_ROWS - 1)
        for c in range(TEST_COLS)
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
