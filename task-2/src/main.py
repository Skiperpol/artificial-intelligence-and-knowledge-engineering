from __future__ import annotations

import argparse
from pathlib import Path
import select
import sys

from ai.minimax import HEURISTICS, choose_best_move, get_opponent
from engine.board import BOARD_SIZE, Board
from engine.game_logger import GameLogger
from players.players import FirstPlayer, Player, SecondPlayer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Breakthrough Minimax")
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Maximum search depth for Minimax (default: 3)",
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


def read_board_from_stdin() -> Board:
    if sys.stdin.isatty():
        return Board()
    ready, _, _ = select.select([sys.stdin], [], [], 0.0)
    if not ready:
        return Board()
    lines = [line.strip() for line in sys.stdin.read().splitlines() if line.strip()]
    if not lines:
        return Board()
    if len(lines) != BOARD_SIZE:
        raise ValueError("Expected exactly 8 non-empty lines for input board.")
    return Board.from_lines(lines)


def print_board(board: Board) -> None:
    for line in board.to_lines():
        print(line)


def choose_heuristic_for_player(player: Player, p1_heuristic: str, p2_heuristic: str) -> str:
    return p1_heuristic if player.symbol == "B" else p2_heuristic


def main() -> None:
    args = parse_args()
    board = read_board_from_stdin()
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

        heuristic_name = choose_heuristic_for_player(
            current_player,
            args.heuristic_p1,
            args.heuristic_p2,
        )
        search = choose_best_move(
            board=board,
            player=current_player,
            depth=args.depth,
            heuristic_name=heuristic_name,
            use_alpha_beta=not args.no_alpha_beta,
        )
        total_visited_nodes += search.visited_nodes
        total_time += search.elapsed_seconds

        if search.best_move is None:
            winner = get_opponent(current_player)
            break

        board.apply_move(search.best_move, current_player)
        rounds += 1
        logger.log_turn(
            round_no=rounds,
            player=current_player,
            move=search.best_move,
            heuristic_name=heuristic_name,
            visited_nodes=search.visited_nodes,
            elapsed_seconds=search.elapsed_seconds,
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
