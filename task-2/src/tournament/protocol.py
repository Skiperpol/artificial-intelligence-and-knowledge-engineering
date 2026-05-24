from __future__ import annotations

import sys
from typing import Tuple

from engine.board import Board, Move


def read_line() -> str:
    line = sys.stdin.readline()
    if line == "":
        raise EOFError("Tournament closed stdin.")
    return line.rstrip("\n\r")


def is_coordinate_move(line: str) -> bool:
    parts = line.split()
    if len(parts) != 4:
        return False
    try:
        for part in parts:
            int(part)
    except ValueError:
        return False
    return True


def is_full_board_line(line: str, cols: int, rows: int) -> bool:
    return len(line.split()) == cols * rows


def parse_coordinate_move(line: str) -> Tuple[int, int, int, int]:
    x0, y0, x1, y1 = (int(value) for value in line.split())
    return x0, y0, x1, y1


def tournament_to_internal_move(
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    rows: int,
    board: Board | None = None,
    player_symbol: str | None = None,
) -> Move:
    from_row = rows - 1 - y0
    to_row = rows - 1 - y1
    is_capture = False
    if board is not None and player_symbol is not None:
        if board._in_bounds(to_row, x1):
            destination = board.grid[to_row][x1]
            is_capture = destination == (
                "W" if player_symbol == "B" else "B"
            )
    return Move(
        from_row=from_row,
        from_col=x0,
        to_row=to_row,
        to_col=x1,
        is_capture=is_capture,
    )


def format_move_for_tournament(move: Move, rows: int) -> str:
    y0 = rows - 1 - move.from_row
    y1 = rows - 1 - move.to_row
    return f"{move.from_col} {y0} {move.to_col} {y1}"


def emit_move(move: Move, rows: int) -> None:
    print(format_move_for_tournament(move, rows), flush=True)


def apply_tournament_move(board: Board, line: str, rows: int, player_symbol: str) -> None:
    from players.players import Player, TournamentBlack, TournamentWhite

    x0, y0, x1, y1 = parse_coordinate_move(line)
    move = tournament_to_internal_move(
        x0, y0, x1, y1, rows, board=board, player_symbol=player_symbol
    )
    if player_symbol == "B":
        mover: Player = TournamentWhite(rows)
    else:
        mover = TournamentBlack(rows)
    board.apply_move(move, mover)
