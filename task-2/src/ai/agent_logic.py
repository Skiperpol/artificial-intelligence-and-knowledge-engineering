from __future__ import annotations

import random

from ai.heuristics import material_heuristic
from ai.minimax import choose_best_move
from engine.board import BOARD_SIZE, Board, Move
from players.players import Player


def choose_heuristic_for_player(player: Player, p1_heuristic: str, p2_heuristic: str) -> str:
    return p1_heuristic if player.symbol == "B" else p2_heuristic


def choose_depth_for_player(player: Player, default_depth: int, p1_depth: int | None, p2_depth: int | None) -> int:
    selected_depth = p1_depth if player.symbol == "B" else p2_depth
    return selected_depth if selected_depth is not None else default_depth


def choose_agent_type_for_player(player: Player, p1_agent_type: str, p2_agent_type: str) -> str:
    return p1_agent_type if player.symbol == "B" else p2_agent_type


def choose_epsilon_for_player(player: Player, p1_epsilon: float, p2_epsilon: float) -> float:
    return p1_epsilon if player.symbol == "B" else p2_epsilon


def _distance_to_goal(board: Board, player: Player) -> int:
    pieces_rows = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board.grid[row][col] == player.symbol:
                pieces_rows.append(row)
    if not pieces_rows:
        return BOARD_SIZE
    if player.symbol == "B":
        return min((BOARD_SIZE - 1) - row for row in pieces_rows)
    return min(pieces_rows)


def choose_adaptive_heuristic(board: Board, player: Player, fallback_heuristic: str) -> str:
    if _distance_to_goal(board, player) <= 2:
        return "advancement"
    if material_heuristic(board, player) < 0:
        return "material"
    return "mobility" if fallback_heuristic == "advancement" else fallback_heuristic


def choose_move_for_agent(
    board: Board,
    player: Player,
    *,
    agent_type: str,
    depth: int,
    heuristic_name: str,
    use_alpha_beta: bool,
    epsilon: float,
) -> tuple[Move | None, int, float]:
    legal_moves = board.get_legal_moves(player)
    if not legal_moves:
        return None, 1, 0.0

    if agent_type == "random":
        return random.choice(legal_moves), 1, 0.0

    if agent_type == "epsilon-greedy" and random.random() < epsilon:
        return random.choice(legal_moves), 1, 0.0

    search = choose_best_move(
        board=board,
        player=player,
        depth=depth,
        heuristic_name=heuristic_name,
        use_alpha_beta=use_alpha_beta,
    )
    return search.best_move, search.visited_nodes, search.elapsed_seconds
