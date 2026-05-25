import random

from ai.heuristics import _game_phase, material_heuristic
from ai.minimax import choose_best_move, choose_best_move_timed
from ai.tournament_search import choose_tournament_move
from engine.board import Board, Move
from players.players import Player


def choose_heuristic_for_player(player: Player, p1_heuristic: str, p2_heuristic: str) -> str:
    if player.symbol == "B":
        return p1_heuristic

    return p2_heuristic


def choose_depth_for_player(player: Player, default_depth: int, p1_depth: int | None, p2_depth: int | None) -> int:
    if player.symbol == "B":
        selected_depth = p1_depth
    else:
        selected_depth = p2_depth

    if selected_depth is not None:
        return selected_depth

    return default_depth


def choose_agent_type_for_player(player: Player, p1_agent_type: str, p2_agent_type: str) -> str:
    if player.symbol == "B":
        return p1_agent_type

    return p2_agent_type


def choose_epsilon_for_player(player: Player, p1_epsilon: float, p2_epsilon: float) -> float:
    if player.symbol == "B":
        return p1_epsilon

    return p2_epsilon


def _distance_to_goal(board: Board, player: Player) -> int:
    pieces_rows = []
    for row in range(board.rows):
        for col in range(board.cols):
            if board.grid[row][col] == player.symbol:
                pieces_rows.append(row)
    if not pieces_rows:
        return board.rows
    return min(abs(row - player.goal_row) for row in pieces_rows)


def choose_adaptive_heuristic(board: Board, player: Player, fallback_heuristic: str) -> str:
    # Złożona funkcja oceny obejmuje fazy debiutu, środka i końcówki.
    if fallback_heuristic == "breakthrough":
        return "breakthrough"

    phase = _game_phase(board, player)
    if phase == "endgame" or _distance_to_goal(board, player) <= 2:
        return "advancement"
    if material_heuristic(board, player) < -1:
        return "material"
    if phase == "opening":
        return "center_control"
    if phase == "maneuvering":
        return "mobility"
    if phase == "attack":
        return "attack_threats"

    return fallback_heuristic


def choose_move_for_agent(
    board: Board,
    player: Player,
    agent_type: str,
    depth: int,
    heuristic_name: str,
    use_alpha_beta: bool,
    epsilon: float,
    time_limit_s: float | None = None,
    max_depth: int | None = None,
    tournament_mode: bool = False,
) -> tuple[Move | None, int, float]:
    legal_moves = board.get_legal_moves(player)
    if not legal_moves:
        return None, 1, 0.0

    if agent_type == "random":
        return random.choice(legal_moves), 1, 0.0

    if agent_type == "epsilon-greedy" and random.random() < epsilon:
        return random.choice(legal_moves), 1, 0.0

    if tournament_mode and time_limit_s is not None:
        move, visited, elapsed = choose_tournament_move(
            board,
            player,
            time_limit_s=time_limit_s,
            max_depth=max_depth if max_depth is not None else depth,
            heuristic_name=heuristic_name,
        )
        return move, visited, elapsed

    use_quiescence = tournament_mode
    use_tactical_filter = tournament_mode

    if time_limit_s is not None:
        search = choose_best_move_timed(
            board=board,
            player=player,
            heuristic_name=heuristic_name,
            time_limit_s=time_limit_s,
            max_depth=max_depth if max_depth is not None else depth,
            min_depth=min(2, depth),
            use_alpha_beta=use_alpha_beta,
            use_quiescence=use_quiescence,
            use_tactical_filter=use_tactical_filter,
        )
    else:
        search = choose_best_move(
            board=board,
            player=player,
            depth=depth,
            heuristic_name=heuristic_name,
            use_alpha_beta=use_alpha_beta,
            use_quiescence=use_quiescence,
            use_tactical_filter=use_tactical_filter,
        )
    return search.best_move, search.visited_nodes, search.elapsed_seconds
