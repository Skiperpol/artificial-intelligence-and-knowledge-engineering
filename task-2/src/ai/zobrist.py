import random
from typing import Dict, Tuple

from engine.board import Board, EMPTY, LAST_MOVE_FROM
from players.players import Player

_PIECE_CODES = ("_", "B", "W", "o")
_rng = random.Random(0xB7E4A7E0)


def _init_keys(rows: int, cols: int) -> Dict[Tuple[int, int, str], int]:
    keys: Dict[Tuple[int, int, str], int] = {}
    for row in range(rows):
        for col in range(cols):
            for piece in _PIECE_CODES:
                keys[(row, col, piece)] = _rng.getrandbits(64)
    return keys


_KEYS_CACHE: Dict[Tuple[int, int], Dict[Tuple[int, int, str], int]] = {}


def _keys_for_board(board: Board) -> Dict[Tuple[int, int, str], int]:
    size = (board.rows, board.cols)
    if size not in _KEYS_CACHE:
        _KEYS_CACHE[size] = _init_keys(board.rows, board.cols)
    return _KEYS_CACHE[size]


def _cell_code(cell: str) -> str:
    if cell in {EMPTY, LAST_MOVE_FROM}:
        return "_"
    return cell


def hash_board(board: Board, side_to_move: Player) -> int:
    keys = _keys_for_board(board)
    value = 0
    for row in range(board.rows):
        for col in range(board.cols):
            code = _cell_code(board.grid[row][col])
            value ^= keys[(row, col, code)]
    if side_to_move.symbol == "W":
        value ^= _SIDE_KEY
    return value


_SIDE_KEY = _rng.getrandbits(64)
