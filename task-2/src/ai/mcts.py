"""MCTS (UCT) z rolloutem heurystycznym breakthrough."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from time import perf_counter
from typing import Dict, List, Optional

from engine.board import Board, Move
from players.players import Player, get_opponent
from ai.heuristics import breakthrough_heuristic
from ai.minimax import copy_board
from ai.strategy import order_moves
from ai.tactics import is_capture_or_goal_move, prioritize_tactical_moves


@dataclass
class _Node:
    visits: int = 0
    value: float = 0.0
    prior_move: Move | None = None
    player_to_move: str = "B"
    children: Dict[Move, "_Node"] = field(default_factory=dict)
    untried: List[Move] = field(default_factory=list)


def _terminal_winner(board: Board, root: Player) -> Optional[float]:
    if board.has_player_won(root):
        return 1.0
    if board.has_player_won(get_opponent(root)):
        return -1.0
    return None


def _rollout(
    board: Board,
    side: Player,
    root: Player,
    rng: random.Random,
    max_plies: int = 40,
) -> float:
    current = side
    trial = copy_board(board)
    for _ in range(max_plies):
        outcome = _terminal_winner(trial, root)
        if outcome is not None:
            return outcome

        moves = trial.get_legal_moves(current)
        if not moves:
            if current.symbol == root.symbol:
                return -1.0
            return 1.0

        tactical = [m for m in moves if is_capture_or_goal_move(trial, m, current)]
        if tactical:
            moves = tactical
        elif rng.random() < 0.25:
            moves = order_moves(trial, moves, current, heuristic_name="breakthrough")

        move = rng.choice(moves)
        trial.apply_move(move, current)
        current = get_opponent(current)

    return breakthrough_heuristic(trial, root) / 5000.0


def _uct_select(node: _Node, exploration: float) -> Move:
    best_move: Optional[Move] = None
    best_score = -float("inf")
    log_parent = math.log(max(node.visits, 1))

    for move, child in node.children.items():
        if child.visits == 0:
            uct = float("inf")
        else:
            exploit = child.value / child.visits
            explore = exploration * math.sqrt(log_parent / child.visits)
            uct = exploit + explore
        if uct > best_score:
            best_score = uct
            best_move = move

    assert best_move is not None
    return best_move


def mcts_choose_move(
    board: Board,
    player: Player,
    time_limit_s: float,
    exploration: float = 1.35,
) -> tuple[Optional[Move], int]:
    legal = board.get_legal_moves(player)
    if not legal:
        return None, 0

    root = _Node(player_to_move=player.symbol, untried=list(legal))
    rng = random.Random(hash_board_simple(board))
    deadline = perf_counter() + time_limit_s
    simulations = 0

    while perf_counter() < deadline:
        node_board = copy_board(board)
        node = root
        path: List[_Node] = [node]
        current_player = player

        while not node.untried and node.children:
            move = _uct_select(node, exploration)
            node_board.apply_move(move, current_player)
            node = node.children[move]
            path.append(node)
            current_player = get_opponent(current_player)

        if node.untried:
            move = node.untried.pop(rng.randrange(len(node.untried)))
            node_board.apply_move(move, current_player)
            child = _Node(
                prior_move=move,
                player_to_move=get_opponent(current_player).symbol,
                untried=list(node_board.get_legal_moves(get_opponent(current_player))),
            )
            node.children[move] = child
            node = child
            path.append(node)
            current_player = get_opponent(current_player)

        result = _rollout(node_board, current_player, player, rng)

        for path_node in reversed(path):
            path_node.visits += 1
            path_node.value += result
            result = -result

        simulations += 1

    best_move: Optional[Move] = None
    best_visits = -1
    for move, child in root.children.items():
        if child.visits > best_visits:
            best_visits = child.visits
            best_move = move

    if best_move is None:
        return prioritize_tactical_moves(legal, board=board, player=player)[0], simulations

    return best_move, simulations


def hash_board_simple(board: Board) -> int:
    value = 0
    for row in range(board.rows):
        for col in range(board.cols):
            value = value * 3 + hash(board.grid[row][col])
    return value
