"""Solver końcówki — pełne przeszukanie przy małej liczbie pionów."""

from __future__ import annotations

from math import inf
from time import perf_counter
from typing import Dict, Optional, Tuple

from engine.board import Board, Move
from players.players import Player, get_opponent
from ai.minimax import copy_board, MATE_SCORE
from ai.strategy import order_moves
from ai.tactics import (
    apply_tactical_constraints,
    find_best_capture,
    find_immediate_win,
    prioritize_tactical_moves,
)
from ai.zobrist import hash_board

ENDGAME_PIECE_THRESHOLD = 12
MAX_ENDGAME_NODES = 20_000
MAX_ENDGAME_TIME_S = 0.12


def total_pieces(board: Board) -> int:
    return board.count_pieces("B") + board.count_pieces("W")


def is_endgame(board: Board, player: Player | None = None) -> bool:
    """Pełny solver tylko przy małej liczbie pionów (turniej: limit czasu 1 s)."""
    return total_pieces(board) <= ENDGAME_PIECE_THRESHOLD


def _terminal_score(board: Board, root: Player, side: Player) -> Optional[float]:
    if board.has_player_won(root):
        return MATE_SCORE
    if board.has_player_won(get_opponent(root)):
        return -MATE_SCORE
    if not board.get_legal_moves(side):
        if side.symbol == root.symbol:
            return -MATE_SCORE
        return MATE_SCORE
    opponent = get_opponent(side)
    if not board.get_legal_moves(opponent):
        if side.symbol == root.symbol:
            return MATE_SCORE
        return -MATE_SCORE
    return None


def _negamax(
    board: Board,
    side: Player,
    root: Player,
    alpha: float,
    beta: float,
    deadline: float,
    counters: Dict[str, int],
    tt: Dict[int, Tuple[int, float]],
) -> float:
    counters["nodes"] += 1
    if counters["nodes"] > MAX_ENDGAME_NODES or perf_counter() >= deadline:
        return 0.0

    terminal = _terminal_score(board, root, side)
    if terminal is not None:
        return terminal

    tt_key = hash_board(board, side)
    cached = tt.get(tt_key)
    if cached is not None:
        return cached[1]

    legal = board.get_legal_moves(side)
    legal = prioritize_tactical_moves(legal, board=board, player=side)
    legal = order_moves(board, legal, side, heuristic_name="breakthrough")

    maximizing = side.symbol == root.symbol
    if maximizing:
        value = -inf
    else:
        value = inf

    opponent = get_opponent(side)
    for move in legal:
        child = copy_board(board)
        child.apply_move(move, side)
        score = _negamax(child, opponent, root, alpha, beta, deadline, counters, tt)
        if maximizing:
            value = max(value, score)
            alpha = max(alpha, value)
        else:
            value = min(value, score)
            beta = min(beta, value)
        if beta <= alpha:
            break

    tt[tt_key] = (1, value)
    return value


def solve_endgame(
    board: Board,
    player: Player,
    time_limit_s: float,
) -> Tuple[Optional[Move], int]:
    if not is_endgame(board, player):
        return None, 0

    instant = find_immediate_win(board, player)
    if instant is not None:
        return instant, 1

    capture = find_best_capture(board, player)
    if capture is not None:
        return capture, 1

    legal = apply_tactical_constraints(board, player, board.get_legal_moves(player))
    if not legal:
        return None, 0

    deadline = perf_counter() + min(time_limit_s, MAX_ENDGAME_TIME_S)
    counters = {"nodes": 0}
    tt: Dict[int, Tuple[int, float]] = {}

    best_move: Optional[Move] = None
    best_score = -inf

    for move in prioritize_tactical_moves(legal, board=board, player=player):
        trial = copy_board(board)
        trial.apply_move(move, player)
        score = _negamax(
            trial,
            get_opponent(player),
            player,
            -inf,
            inf,
            deadline,
            counters,
            tt,
        )
        if score > best_score:
            best_score = score
            best_move = move
        if perf_counter() >= deadline:
            break

    return best_move, counters["nodes"]
