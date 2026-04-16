from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys

from ai.agent_logic import (
    choose_adaptive_heuristic,
    choose_agent_type_for_player,
    choose_depth_for_player,
    choose_epsilon_for_player,
    choose_heuristic_for_player,
    choose_move_for_agent,
)
from ai.minimax import HEURISTICS, get_opponent
from engine.board import Board
from engine.game_logger import GameLogger
from players.players import FirstPlayer, Player, SecondPlayer

# python main.py --agent-p1 minimax --agent-p2 minimax --heuristic-p1 advancement --heuristic-p2 advancement --depth 3
# python main.py --agent-p1 minimax --agent-p2 epsilon-greedy --depth-p1 4 --depth-p2 2 --adaptive-strategy --epsilon-p2 0.2

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Breakthrough Minimax")
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Default maximum search depth for Minimax agents (default: 3).",
    )
    parser.add_argument(
        "--depth-p1",
        type=int,
        default=None,
        help="Maximum search depth for player 1 agent.",
    )
    parser.add_argument(
        "--depth-p2",
        type=int,
        default=None,
        help="Maximum search depth for player 2 agent.",
    )
    parser.add_argument(
        "--heuristic-p1",
        choices=list(HEURISTICS.keys()),
        default="advancement",
        help="Heuristic for player 1 (B).",
    )
    parser.add_argument(
        "--heuristic-p2",
        choices=list(HEURISTICS.keys()),
        default="advancement",
        help="Heuristic for player 2 (W).",
    )
    parser.add_argument(
        "--no-alpha-beta",
        action="store_true",
        help="Disable alpha-beta pruning.",
    )
    parser.add_argument(
        "--agent-p1",
        choices=["minimax", "random", "epsilon-greedy"],
        default="minimax",
        help="Agent type for player 1 (B).",
    )
    parser.add_argument(
        "--agent-p2",
        choices=["minimax", "random", "epsilon-greedy"],
        default="minimax",
        help="Agent type for player 2 (W).",
    )
    parser.add_argument(
        "--epsilon-p1",
        type=float,
        default=0.15,
        help="Random move probability for player 1 epsilon-greedy agent.",
    )
    parser.add_argument(
        "--epsilon-p2",
        type=float,
        default=0.15,
        help="Random move probability for player 2 epsilon-greedy agent.",
    )
    parser.add_argument(
        "--adaptive-strategy",
        action="store_true",
        help="Enable dynamic heuristic switching based on board state.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed for pseudo-random choices (default: 42).",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=200,
        help="Safety cap for turns (default: 200).",
    )
    parser.add_argument(
        "--log-file",
        default="task-2/game_log.txt",
        help="Path to output log file with move-by-move game history.",
    )
    return parser.parse_args()


def print_board(board: Board) -> None:
    for line in board.to_lines():
        print(line)


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    board = Board()
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = logs_dir / Path(args.log_file).name
    logger = GameLogger(str(log_path))
    logger.log_initial_board(board)

    player_1 = FirstPlayer()
    player_2 = SecondPlayer()
    current_player: Player = player_1
    rounds = 0
    total_visited_nodes = 0
    total_time = 0.0
    winner: Player | None = None

    while True:
        if rounds >= args.max_rounds:
            break

        if board.has_player_won(player_1):
            winner = player_1
            break
        if board.has_player_won(player_2):
            winner = player_2
            break

        if not board.get_legal_moves(current_player):
            winner = get_opponent(current_player)
            break

        base_heuristic_name = choose_heuristic_for_player(
            current_player,
            args.heuristic_p1,
            args.heuristic_p2,
        )
        if args.adaptive_strategy:
            heuristic_name = choose_adaptive_heuristic(board, current_player, base_heuristic_name)
        else:
            heuristic_name = base_heuristic_name
        depth = choose_depth_for_player(current_player, args.depth, args.depth_p1, args.depth_p2)
        agent_type = choose_agent_type_for_player(current_player, args.agent_p1, args.agent_p2)
        epsilon = choose_epsilon_for_player(current_player, args.epsilon_p1, args.epsilon_p2)

        move, visited_nodes, elapsed_seconds = choose_move_for_agent(
            board=board,
            player=current_player,
            agent_type=agent_type,
            depth=depth,
            heuristic_name=heuristic_name,
            use_alpha_beta=not args.no_alpha_beta,
            epsilon=epsilon,
        )
        total_visited_nodes += visited_nodes
        total_time += elapsed_seconds

        if move is None:
            winner = get_opponent(current_player)
            break

        board.apply_move(move, current_player)
        rounds += 1
        logger.log_turn(
            round_no=rounds,
            player=current_player,
            move=move,
            heuristic_name=heuristic_name,
            visited_nodes=visited_nodes,
            elapsed_seconds=elapsed_seconds,
            board_after_move=board,
        )
        current_player = player_2 if current_player.symbol == "B" else player_1

    logger.log_end(rounds=rounds, winner_name=winner.name if winner else None)
    print_board(board)
    print(f"Rundy: {rounds}, zwyciezca: {winner.name if winner else 'brak'}")
    print(
        f"odwiedzone_wezly={total_visited_nodes} czas_s={total_time:.6f}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
