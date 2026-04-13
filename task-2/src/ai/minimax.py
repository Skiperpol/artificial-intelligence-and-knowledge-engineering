from __future__ import annotations

from dataclasses import dataclass
from math import inf
from time import perf_counter
from typing import Callable, Dict, List, Optional

from engine.board import Board, Move
from players.players import Player, get_opponent
from ai.heuristics import (
    advancement_heuristic,
    center_control_heuristic,
    goal_pressure_heuristic,
    material_heuristic,
    mobility_heuristic,
    threatened_pieces_heuristic,
)

Heuristic = Callable[[Board, Player], float]


@dataclass
class SearchResult:
    best_move: Optional[Move]
    score: float
    visited_nodes: int
    elapsed_seconds: float


def copy_board(board: Board) -> Board:
    return Board([row[:] for row in board.grid])

HEURISTICS: Dict[str, Heuristic] = {
    # [Punkt 2] Rejestr heurystyk dostępnych z CLI.
    "material": material_heuristic,
    "advancement": advancement_heuristic,
    "mobility": mobility_heuristic,
    "goal_pressure": goal_pressure_heuristic,
    "center_control": center_control_heuristic,
    "threatened_pieces": threatened_pieces_heuristic,
}


def _evaluate_terminal(board: Board, root_player: Player, current_player: Player) -> Optional[float]:
    opponent = get_opponent(current_player)
    if board.has_player_won(root_player):
        return 10_000.0
    if board.has_player_won(get_opponent(root_player)):
        return -10_000.0
    if not board.get_legal_moves(current_player):
        return -10_000.0 if current_player.symbol == root_player.symbol else 10_000.0
    if not board.get_legal_moves(opponent):
        return 10_000.0 if current_player.symbol == root_player.symbol else -10_000.0
    return None

def _minimax(
    board: Board,
    depth: int,
    current_player: Player,
    root_player: Player,
    heuristic: Heuristic,
    alpha: float,
    beta: float,
    use_alpha_beta: bool,
    counters: Dict[str, int],
) -> float:
    # [Punkt 3] Właściwy minimax (max dla gracza korzenia, min dla przeciwnika).
    counters["visited_nodes"] += 1
    
    terminal_score = _evaluate_terminal(board, root_player, current_player)
    if terminal_score is not None:
        return terminal_score
    if depth == 0:
        return heuristic(board, root_player)

    legal_moves = board.get_legal_moves(current_player)
    is_maximizing = (current_player.symbol == root_player.symbol)
    next_player = get_opponent(current_player)
    
    best_value = -inf if is_maximizing else inf
    
    for move in legal_moves:
        new_board = copy_board(board)
        new_board.apply_move(move, current_player)
        
        evaluation = _minimax(
            new_board, depth - 1, next_player, root_player, 
            heuristic, alpha, beta, use_alpha_beta, counters
        )

        if is_maximizing:
            best_value = max(best_value, evaluation)
            alpha = max(alpha, best_value)
        else:
            best_value = min(best_value, evaluation)
            beta = min(beta, best_value)

        if use_alpha_beta and beta <= alpha:
            # [Punkt 4] Alfa-beta: odcinamy gałąź, która nie wpłynie na decyzję.
            break
            
    return best_value


def choose_best_move(
    board: Board,
    player: Player,
    depth: int,
    heuristic_name: str,
    use_alpha_beta: bool = True,
) -> SearchResult:
    # [Punkt 3/4] Przegląd ruchów korzenia i wybór najlepszego wg minimax/alfa-beta.
    heuristic = HEURISTICS.get(heuristic_name)
    if heuristic is None:
        raise ValueError(f"Unknown heuristic: {heuristic_name}")

    start = perf_counter()
    counters = {"visited_nodes": 0}
    legal_moves = board.get_legal_moves(player)
    if not legal_moves:
        return SearchResult(None, -10_000.0, 1, perf_counter() - start)

    best_score = -inf
    best_move: Optional[Move] = None
    opponent = get_opponent(player)

    for move in legal_moves:
        new_board = copy_board(board)
        new_board.apply_move(move, player)
        score = _minimax(
            new_board,
            depth - 1,
            opponent,
            player,
            heuristic,
            alpha=-inf,
            beta=inf,
            use_alpha_beta=use_alpha_beta,
            counters=counters,
        )
        if score > best_score:
            best_score = score
            best_move = move

    return SearchResult(best_move, best_score, counters["visited_nodes"], perf_counter() - start)

