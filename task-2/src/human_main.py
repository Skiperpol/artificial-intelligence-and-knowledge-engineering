import argparse
import json
import sys
from pathlib import Path

from ai.agent_logic import (
    choose_adaptive_heuristic,
    choose_move_for_agent,
)
from ai.eval_context import reset_active_genome, set_active_genome
from ai.genome import BotGenome
from ai.minimax import HEURISTICS
from engine.board import Board, Move
from players.players import Player

TOURNAMENT_TIME_BUDGET_S = 0.92
TOURNAMENT_MAX_DEPTH = 6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Breakthrough — human vs bot")
    parser.add_argument(
        "--rows",
        type=int,
        default=8,
        metavar="R",
        help="Number of board rows (default: 8). Must be >= 2.",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=8,
        metavar="C",
        help="Number of board columns (default: 8). Must be >= 1.",
    )
    parser.add_argument(
        "--human-side",
        choices=["B", "W"],
        default="B",
        help="Your piece color: B (starts, moves down) or W (starts, moves up).",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Bot search depth (default: 3).",
    )
    parser.add_argument(
        "--heuristic",
        choices=list(HEURISTICS.keys()),
        default="breakthrough",
        help="Bot heuristic (default: breakthrough).",
    )
    parser.add_argument(
        "--tournament-mode",
        action="store_true",
        help=(
            "Turniejowy silnik: iterative deepening na czas, quiescence, "
            "filtr taktyczny (jak tournament_main.py)."
        ),
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=TOURNAMENT_TIME_BUDGET_S,
        help=f"Limit czasu bota w trybie turniejowym (default: {TOURNAMENT_TIME_BUDGET_S}).",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=TOURNAMENT_MAX_DEPTH,
        help=f"Maks. głębokość w trybie turniejowym (default: {TOURNAMENT_MAX_DEPTH}).",
    )
    parser.add_argument(
        "--genome",
        type=str,
        default=None,
        help="Opcjonalny plik JSON z wagami (np. z evolve_main.py).",
    )
    parser.add_argument(
        "--no-alpha-beta",
        action="store_true",
        help="Disable alpha-beta pruning for the bot.",
    )
    parser.add_argument(
        "--adaptive-strategy",
        action="store_true",
        help="Let the bot switch heuristics based on board state.",
    )
    return parser.parse_args()


def load_genome(path: str | None) -> BotGenome | None:
    if not path:
        return None
    genome_path = Path(path)
    if not genome_path.is_file():
        raise SystemExit(f"Genome file not found: {genome_path}")
    return BotGenome.from_dict(json.loads(genome_path.read_text(encoding="utf-8")))


def make_players(rows: int, human_side: str) -> tuple[Player, Player]:
    if human_side == "B":
        human = Player(name="You", symbol="B", direction=1, board_rows=rows)
        bot = Player(name="Bot", symbol="W", direction=-1, board_rows=rows)
    else:
        human = Player(name="You", symbol="W", direction=-1, board_rows=rows)
        bot = Player(name="Bot", symbol="B", direction=1, board_rows=rows)
    return human, bot


def print_board(board: Board) -> None:
    col_header = "   " + " ".join(str(col) for col in range(board.cols))
    print(col_header)
    for row in range(board.rows):
        print(f"{row:2d} " + " ".join(board.grid[row]))


def format_move(move: Move) -> str:
    capture = " capture" if move.is_capture else ""
    return (
        f"({move.from_row},{move.from_col}) -> "
        f"({move.to_row},{move.to_col}){capture}"
    )


def print_legal_moves(moves: list[Move]) -> None:
    print("Legal moves:")
    for index, move in enumerate(moves, start=1):
        print(f"  {index}: {format_move(move)}")


def parse_human_move(raw: str, legal_moves: list[Move]) -> Move | None:
    stripped = raw.strip()
    if not stripped:
        return None

    parts = stripped.split()
    if len(parts) == 1 and parts[0].isdigit():
        choice = int(parts[0])
        if 1 <= choice <= len(legal_moves):
            return legal_moves[choice - 1]
        print(f"Invalid move number: choose 1..{len(legal_moves)}.")
        return None

    if len(parts) != 4:
        print("Enter move number or: from_row from_col to_row to_col")
        return None

    try:
        from_row, from_col, to_row, to_col = (int(part) for part in parts)
    except ValueError:
        print("Coordinates must be integers.")
        return None

    for move in legal_moves:
        if (
            move.from_row == from_row
            and move.from_col == from_col
            and move.to_row == to_row
            and move.to_col == to_col
        ):
            return move

    print(f"No legal move: ({from_row},{from_col}) -> ({to_row},{to_col}).")
    return None


def read_human_move(legal_moves: list[Move]) -> Move:
    print_legal_moves(legal_moves)
    while True:
        try:
            raw = input("Your move (number, coords, or q to quit): ")
        except EOFError:
            print()
            raise SystemExit(0)

        if raw.strip().lower() in {"q", "quit", "exit"}:
            raise SystemExit(0)

        move = parse_human_move(raw, legal_moves)
        if move is not None:
            return move


def play_turn(
    board: Board,
    player: Player,
    *,
    depth: int,
    heuristic: str,
    use_alpha_beta: bool,
    adaptive: bool,
    tournament_mode: bool,
    time_limit_s: float,
    max_depth: int,
    genome: BotGenome | None,
) -> None:
    heuristic_name = (
        choose_adaptive_heuristic(board, player, heuristic)
        if adaptive and not tournament_mode
        else heuristic
    )
    if tournament_mode:
        mode_label = (
            f"tournament timed={time_limit_s:.2f}s max_depth={max_depth} "
            f"quiescence+filter"
        )
    else:
        mode_label = f"depth={depth}"
    print(f"{player.name} thinking ({mode_label}, heuristic={heuristic_name})...")

    token = set_active_genome(genome) if genome else None
    try:
        move, visited_nodes, elapsed = choose_move_for_agent(
            board=board,
            player=player,
            agent_type="minimax",
            depth=depth,
            heuristic_name=heuristic_name,
            use_alpha_beta=use_alpha_beta,
            epsilon=0.0,
            time_limit_s=time_limit_s if tournament_mode else None,
            max_depth=max_depth if tournament_mode else None,
            tournament_mode=tournament_mode,
        )
    finally:
        if token is not None:
            reset_active_genome(token)
    if move is None:
        return
    board.apply_move(move, player)
    print(f"{player.name}: {format_move(move)}")
    print(
        f"  visited_nodes={visited_nodes} time_s={elapsed:.3f}",
        file=sys.stderr,
    )


def main() -> None:
    args = parse_args()
    if args.rows < 2:
        raise SystemExit("argument --rows: must be >= 2")
    if args.cols < 1:
        raise SystemExit("argument --cols: must be >= 1")

    board = Board(rows=args.rows, cols=args.cols)
    human, bot = make_players(board.rows, args.human_side)
    genome = load_genome(args.genome)
    current: Player = human
    rounds = 0

    print("Breakthrough — human vs bot")
    print(f"You play as {human.symbol} ({human.name}), bot plays as {bot.symbol}.")
    if args.tournament_mode:
        print(
            "Bot: tournament mode "
            f"(time_limit={args.time_limit}s, max_depth={args.max_depth})."
        )
    else:
        print(f"Bot: classic mode (fixed depth={args.depth}).")
    if genome is not None:
        print(f"Bot genome: id={genome.genome_id}, depth={genome.depth}")
    print("Rows and columns are numbered from 0. Enter a move number or four coordinates.")
    print()

    while True:
        print_board(board)
        print()

        if board.has_player_won(human):
            print("You win!")
            break
        if board.has_player_won(bot):
            print("Bot wins!")
            break

        legal = board.get_legal_moves(current)
        if not legal:
            winner = bot if current is human else human
            print(f"No legal moves — {winner.name} wins!")
            break

        if current is human:
            move = read_human_move(legal)
            board.apply_move(move, human)
        else:
            play_turn(
                board,
                bot,
                depth=args.depth,
                heuristic=args.heuristic,
                use_alpha_beta=not args.no_alpha_beta,
                adaptive=args.adaptive_strategy,
                tournament_mode=args.tournament_mode,
                time_limit_s=args.time_limit,
                max_depth=args.max_depth,
                genome=genome,
            )

        rounds += 1
        current = bot if current is human else human
        print()

    print(f"Rounds played: {rounds}")


if __name__ == "__main__":
    main()
