#!/usr/bin/env python3
"""Round-robin + Elo dla bota turniejowego vs baseline'y."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from ai.eval_context import reset_active_genome, set_active_genome
from ai.genome import BotGenome
from ai.tournament_search import choose_tournament_move
from ai.agent_logic import choose_move_for_agent
from engine.board import Board, Move
from players.players import Player, TournamentBlack, TournamentWhite, get_opponent

MoveFn = Callable[[Board, Player], Move | None]
MAX_ROUNDS = 200


@dataclass
class BenchBot:
    name: str
    move_fn: MoveFn


def _random_move(board: Board, player: Player) -> Move | None:
    moves = board.get_legal_moves(player)
    if not moves:
        return None
    return random.choice(moves)


def _minimax_move(
    depth: int,
    tournament: bool,
    time_limit_s: float,
    *,
    use_mcts: bool = True,
    use_opening_book: bool = True,
) -> MoveFn:
    def pick(board: Board, player: Player) -> Move | None:
        if tournament:
            move, _n, _t = choose_tournament_move(
                board,
                player,
                time_limit_s=time_limit_s,
                max_depth=depth,
                use_mcts=use_mcts,
                use_opening_book=use_opening_book,
            )
            return move
        move, _n, _t = choose_move_for_agent(
            board,
            player,
            agent_type="minimax",
            depth=depth,
            heuristic_name="breakthrough",
            use_alpha_beta=True,
            epsilon=0.0,
            tournament_mode=False,
        )
        return move

    return pick


def _genome_move(genome: BotGenome, tournament: bool, time_limit_s: float) -> MoveFn:
    def pick(board: Board, player: Player) -> Move | None:
        token = set_active_genome(genome)
        try:
            if tournament:
                move, _n, _t = choose_tournament_move(
                    board,
                    player,
                    time_limit_s=time_limit_s,
                    max_depth=genome.depth,
                )
                return move
            move, _n, _t = choose_move_for_agent(
                board,
                player,
                agent_type="minimax",
                depth=genome.depth,
                heuristic_name="breakthrough",
                use_alpha_beta=True,
                epsilon=0.0,
                tournament_mode=False,
            )
            return move
        finally:
            reset_active_genome(token)

    return pick


def _play_match(
    bot_a: BenchBot,
    bot_b: BenchBot,
    seed: int,
    *,
    bot_a_plays_white: bool,
) -> float:
    """Wynik z perspektywy bot_a. B (TournamentWhite) zaczyna."""
    rng = random.Random(seed)
    rng.randint(0, 10**6)

    board = Board.tournament_default(8, 8)
    white = TournamentWhite(board.rows)
    black = TournamentBlack(board.rows)
    if bot_a_plays_white:
        fns = {white.symbol: bot_a.move_fn, black.symbol: bot_b.move_fn}
        bot_for_white = bot_a
    else:
        fns = {white.symbol: bot_b.move_fn, black.symbol: bot_a.move_fn}
        bot_for_white = bot_b

    current: Player = white
    rounds = 0

    while rounds < MAX_ROUNDS:
        if board.has_player_won(white):
            return 1.0 if bot_for_white is bot_a else 0.0
        if board.has_player_won(black):
            return 0.0 if bot_for_white is bot_a else 1.0
        if not board.get_legal_moves(current):
            winner = get_opponent(current)
            white_won = winner.symbol == white.symbol
            return 1.0 if (white_won and bot_for_white is bot_a) or (
                not white_won and bot_for_white is bot_b
            ) else 0.0

        move = fns[current.symbol](board, current)
        if move is None:
            winner = get_opponent(current)
            white_won = winner.symbol == white.symbol
            return 1.0 if (white_won and bot_for_white is bot_a) or (
                not white_won and bot_for_white is bot_b
            ) else 0.0

        board.apply_move(move, current)
        rounds += 1
        current = get_opponent(current)

    return 0.5


def update_elo(ra: float, rb: float, score_a: float, k: float = 32.0) -> tuple[float, float]:
    expected_a = 1.0 / (1.0 + 10 ** ((rb - ra) / 400.0))
    expected_b = 1.0 - expected_a
    new_a = ra + k * (score_a - expected_a)
    new_b = rb + k * ((1.0 - score_a) - expected_b)
    return new_a, new_b


def build_roster(
    genome_path: str | None, quick: bool, time_limit_s: float
) -> List[BenchBot]:
    tour_depth = 4 if quick else 6
    tour_time = min(time_limit_s, 0.4 if quick else time_limit_s)
    tour_kw = dict(
        time_limit_s=tour_time,
        use_mcts=not quick,
        use_opening_book=True,
    )
    bots: List[BenchBot] = [
        BenchBot("random", _random_move),
        BenchBot("minimax-d2", _minimax_move(2, tournament=False, time_limit_s=tour_time)),
    ]
    if not quick:
        bots.extend(
            [
                BenchBot("minimax-d3", _minimax_move(3, tournament=False, time_limit_s=time_limit_s)),
                BenchBot(
                    "tournament-default",
                    _minimax_move(3, tournament=True, **tour_kw),
                ),
            ]
        )
    bots.insert(
        0,
        BenchBot(
            "my-bot-tournament",
            _minimax_move(tour_depth, tournament=True, **tour_kw),
        ),
    )
    if genome_path:
        path = Path(genome_path)
        if path.is_file():
            genome = BotGenome.from_dict(
                json.loads(path.read_text(encoding="utf-8"))
            )
            bots.insert(
                0,
                BenchBot(
                    f"my-genome-{genome.genome_id}",
                    _genome_move(genome, tournament=True, time_limit_s=tour_time),
                ),
            )
    return bots


def run_benchmark(
    bots: List[BenchBot],
    games_per_pair: int,
    seed: int,
    swap_colors: bool,
) -> dict[str, float]:
    rng = random.Random(seed)
    ratings = {bot.name: 1500.0 for bot in bots}
    total = len(bots) * (len(bots) - 1) // 2 * games_per_pair * (2 if swap_colors else 1)
    done = 0

    for i in range(len(bots)):
        for j in range(i + 1, len(bots)):
            a, b = bots[i], bots[j]
            for game_index in range(games_per_pair):
                game_seed = rng.randint(0, 2**31 - 1)
                a_white = (game_index % 2 == 0) if swap_colors else True
                score_a = _play_match(a, b, game_seed, bot_a_plays_white=a_white)
                ratings[a.name], ratings[b.name] = update_elo(
                    ratings[a.name], ratings[b.name], score_a
                )
                done += 1
                if done % 5 == 0 or done == total:
                    print(f"games {done}/{total}", file=sys.stderr, flush=True)

                if swap_colors:
                    game_seed = rng.randint(0, 2**31 - 1)
                    score_a = _play_match(
                        a, b, game_seed, bot_a_plays_white=not a_white
                    )
                    ratings[a.name], ratings[b.name] = update_elo(
                        ratings[a.name], ratings[b.name], score_a
                    )
                    done += 1
                    if done % 5 == 0 or done == total:
                        print(f"games {done}/{total}", file=sys.stderr, flush=True)

    return ratings


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Elo bota Breakthrough")
    parser.add_argument("--games-per-pair", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--genome", type=str, default=None)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Tylko random + minimax-d2 (szybciej).",
    )
    parser.add_argument(
        "--no-swap",
        action="store_true",
        help="Nie graj drugiej partii z zamienionymi kolorami.",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=0.92,
        help="Budżet czasu na ruch bota turniejowego (s).",
    )
    args = parser.parse_args()

    bots = build_roster(args.genome, args.quick, args.time_limit)
    print("Bots:", ", ".join(b.name for b in bots), file=sys.stderr)

    ratings = run_benchmark(
        bots,
        games_per_pair=args.games_per_pair,
        seed=args.seed,
        swap_colors=not args.no_swap,
    )

    print("\nElo (szacunek, start 1500):")
    for name, elo in sorted(ratings.items(), key=lambda item: item[1], reverse=True):
        print(f"  {name:24s}  {elo:7.1f}")

    my_names = [n for n in ratings if n.startswith("my-")]
    if my_names:
        best = max(my_names, key=lambda n: ratings[n])
        print(f"\nTwój bot ({best}): {ratings[best]:.1f} Elo", file=sys.stderr)


if __name__ == "__main__":
    main()
