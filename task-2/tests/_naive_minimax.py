from math import inf
from typing import Callable

from _setup import Runner

from ai.minimax import copy_board
from engine.board import Board
from players.players import Player, get_opponent


WIN_SCORE = 10_000.0


def naive_minimax(
    board: Board,
    depth: int,
    current_player: Player,
    root_player: Player,
    heuristic: Callable[[Board, Player], float],
) -> float:
    if board.has_player_won(root_player):
        return WIN_SCORE
    if board.has_player_won(get_opponent(root_player)):
        return -WIN_SCORE

    legal = board.get_legal_moves(current_player)
    if not legal:
        return -WIN_SCORE if current_player.symbol == root_player.symbol else WIN_SCORE

    if depth == 0:
        return heuristic(board, root_player)

    is_max = current_player.symbol == root_player.symbol
    next_player = get_opponent(current_player)
    best = -inf if is_max else inf

    for move in legal:
        nb = copy_board(board)
        nb.apply_move(move, current_player)
        v = naive_minimax(nb, depth - 1, next_player, root_player, heuristic)
        best = max(best, v) if is_max else min(best, v)

    return best
