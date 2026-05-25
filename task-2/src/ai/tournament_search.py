"""Jednolity wybór ruchu turniejowego: book → solver → MCTS + minimax."""

from __future__ import annotations

import os
from time import perf_counter

from engine.board import Board, Move
from players.players import Player

from ai.endgame import is_endgame, solve_endgame, total_pieces
from ai.minimax import choose_best_move_timed
from ai.mcts import mcts_choose_move
from ai.opening_book import lookup_opening_move
from ai.strategy import has_capture_moves, order_moves
from ai.tactics import (
    filter_safe_root_moves,
    find_block_opponent_win,
    find_breakthrough_lane_move,
    find_forced_win_move,
    find_immediate_win,
    find_mandatory_capture,
    get_free_captures,
    is_goal_race,
    prioritize_tactical_moves,
    should_skip_opening_book,
)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return float(raw)


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _seconds_left(deadline: float) -> float:
    return deadline - perf_counter()


def _fast_fallback_move(board: Board, player: Player) -> Move:
    legal = board.get_legal_moves(player)
    if not legal:
        raise ValueError("No legal moves for fallback.")
    cap = find_mandatory_capture(board, player)
    if cap is not None:
        return cap
    safe = filter_safe_root_moves(board, player, legal, protect_wing_structure=False)
    pool = safe if safe else legal
    ordered = prioritize_tactical_moves(pool, board=board, player=player)
    ordered = order_moves(board, ordered, player, heuristic_name="breakthrough")
    return ordered[0]


def choose_tournament_move(
    board: Board,
    player: Player,
    *,
    time_limit_s: float,
    max_depth: int = 6,
    heuristic_name: str = "breakthrough",
    use_opening_book: bool = True,
    use_endgame_solver: bool = True,
    use_mcts: bool | None = None,
    mcts_time_fraction: float | None = None,
    use_tactical_layers: bool | None = None,
) -> tuple[Move | None, int, float]:
    start = perf_counter()
    deadline = start + time_limit_s
    visited = 0
    tactical_layers = (
        _env_flag("BREAKTHROUGH_TACTICS", True)
        if use_tactical_layers is None
        else use_tactical_layers
    )

    def out(move: Move | None, nodes: int = 1) -> tuple[Move | None, int, float]:
        return move, nodes, perf_counter() - start

    if _seconds_left(deadline) <= 0.03:
        return out(_fast_fallback_move(board, player))

    win_move = find_immediate_win(board, player)
    if win_move is not None:
        return out(win_move)

    if tactical_layers and _seconds_left(deadline) > 0.05:
        block_move = find_block_opponent_win(board, player)
        if block_move is not None:
            return out(block_move)

    capture_move = find_mandatory_capture(board, player)
    if capture_move is not None and (
        get_free_captures(board, player) or _seconds_left(deadline) > 0.04
    ):
        return out(capture_move)

    if use_opening_book and _seconds_left(deadline) > 0.05:
        if not tactical_layers or not should_skip_opening_book(board, player):
            book_move = lookup_opening_move(board, player)
            if book_move is not None:
                return out(book_move)

    race = is_goal_race(board, player)

    if tactical_layers and _seconds_left(deadline) > 0.12:
        if race and total_pieces(board) <= 16:
            forced_win = find_forced_win_move(
                board,
                player,
                max_depth=5,
                deadline=start + min(0.12, time_limit_s * 0.25),
            )
            if forced_win is not None:
                return out(forced_win)

        if should_skip_opening_book(board, player):
            breakthrough = find_breakthrough_lane_move(board, player)
            if breakthrough is not None and not get_free_captures(board, player):
                return out(breakthrough)

    if (
        use_endgame_solver
        and total_pieces(board) <= 12
        and _seconds_left(deadline) > 0.15
    ):
        end_budget = min(0.12, _seconds_left(deadline) - 0.04)
        if end_budget > 0.03:
            end_move, nodes = solve_endgame(board, player, end_budget)
            if end_move is not None:
                return out(end_move, nodes)

    legal = board.get_legal_moves(player)
    if not legal:
        return out(None)

    if _seconds_left(deadline) <= 0.05:
        return out(_fast_fallback_move(board, player))

    best_move = _fast_fallback_move(board, player)

    use_mcts_flag = _env_flag("BREAKTHROUGH_MCTS", False) if use_mcts is None else use_mcts
    mcts_frac = (
        _env_float("BREAKTHROUGH_MCTS_FRACTION", 0.32)
        if mcts_time_fraction is None
        else mcts_time_fraction
    )

    remaining = _seconds_left(deadline)
    mcts_move: Move | None = None
    mcts_sims = 0

    if use_mcts_flag and remaining > 0.2:
        mcts_budget = min(remaining * 0.25, _seconds_left(deadline) - 0.05)
        if mcts_budget > 0.05:
            mcts_move, mcts_sims = mcts_choose_move(board, player, mcts_budget)
            visited += mcts_sims
        remaining = _seconds_left(deadline)

    search_depth = min(max_depth, 5)
    if race:
        search_depth = min(max_depth, 6)

    if remaining > 0.08:
        search = choose_best_move_timed(
            board=board,
            player=player,
            heuristic_name=heuristic_name,
            time_limit_s=max(0.05, remaining - 0.03),
            max_depth=search_depth,
            min_depth=2,
            min_remaining_to_start_s=0.08,
            use_quiescence=False,
            use_tactical_filter=tactical_layers,
            use_transposition=True,
        )
        visited += search.visited_nodes
        if search.best_move is not None:
            best_move = search.best_move

    if mcts_move is not None and mcts_sims >= 8:
        best_move = mcts_move

    if best_move not in legal:
        best_move = legal[0]

    return out(best_move, visited)
