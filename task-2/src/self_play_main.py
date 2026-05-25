#!/usr/bin/env python3
"""Self-play: szybki tuning wag genomu (minimax, domyślnie głębokość 2)."""

from __future__ import annotations

import argparse
import random
import sys
from multiprocessing import Pool

from ai.eval_context import reset_active_genome, set_active_genome
from ai.genome import BotGenome, breed_next_generation, make_population, save_genome
from ai.minimax import choose_best_move
from ai.tactics import apply_tactical_constraints, find_immediate_win
from engine.board import Board
from players.players import FirstPlayer, Player, SecondPlayer, get_opponent

MAX_ROUNDS_DEFAULT = 80


def _play_self_play_game(
    white: BotGenome,
    black: BotGenome,
    seed: int,
    depth: int,
    max_rounds: int,
    heuristic_name: str,
) -> int | None:
    rng = random.Random(seed)
    rng.randint(0, 10**6)

    board = Board(rows=8, cols=8)
    player_b = FirstPlayer(board.rows)
    player_w = SecondPlayer(board.rows)
    genomes = {player_b.symbol: black, player_w.symbol: white}
    current: Player = player_b
    rounds = 0

    while rounds < max_rounds:
        if board.has_player_won(player_b):
            return black.genome_id
        if board.has_player_won(player_w):
            return white.genome_id

        if not board.get_legal_moves(current):
            winner = get_opponent(current)
            return genomes[winner.symbol].genome_id

        genome = genomes[current.symbol]
        token = set_active_genome(genome)
        try:
            legal = board.get_legal_moves(current)
            constrained = apply_tactical_constraints(board, current, legal)
            move = find_immediate_win(board, current)
            if move is None and len(constrained) == 1:
                move = constrained[0]
            elif move is None:
                search = choose_best_move(
                    board=board,
                    player=current,
                    depth=depth,
                    heuristic_name=heuristic_name,
                    use_alpha_beta=True,
                    use_transposition=False,
                    use_quiescence=any(m.is_capture for m in legal),
                    use_tactical_filter=True,
                )
                move = search.best_move
        finally:
            reset_active_genome(token)

        if move is None:
            return genomes[get_opponent(current).symbol].genome_id

        board.apply_move(move, current)
        rounds += 1
        current = get_opponent(current)

    return None


def _job(args: tuple) -> int | None:
    white, black, seed, depth, max_rounds, heuristic_name = args
    return _play_self_play_game(white, black, seed, depth, max_rounds, heuristic_name)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Szybki self-play wag heurystyki (minimax, bez turniejowego overheadu).",
    )
    parser.add_argument("--population", type=int, default=10)
    parser.add_argument("--top", type=int, default=3)
    parser.add_argument("--games-per-bot", type=int, default=2)
    parser.add_argument("--generations", type=int, default=3)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Skrót: pop=8, gen=2, games/bot=2, max-rounds=60.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--depth", type=int, default=2, help="Głębokość minimax (domyślnie 2).")
    parser.add_argument(
        "--heuristic",
        type=str,
        default="breakthrough-train",
        choices=["breakthrough-train", "breakthrough"],
        help="Funkcja oceny (train = szybciej).",
    )
    parser.add_argument(
        "--max-rounds",
        type=int,
        default=MAX_ROUNDS_DEFAULT,
        help="Limit pół-ruchów w jednej grze.",
    )
    parser.add_argument("--output", type=str, default="best_genome_selfplay.json")
    args = parser.parse_args()

    if args.quick:
        args.population = 8
        args.generations = 2
        args.games_per_bot = 2
        args.max_rounds = min(args.max_rounds, 60)

    if args.depth < 2 or args.depth > 4:
        raise SystemExit("--depth musi być w zakresie 2–4.")
    if args.top > args.population:
        raise SystemExit("--top nie może być większe niż --population")

    rng = random.Random(args.seed)
    population = make_population(
        args.population, rng, 0, fixed_depth=args.depth
    )
    best_ever: BotGenome | None = None
    best_wins = -1.0
    next_id = args.population

    print(
        f"start  pop={args.population}  gen={args.generations}  "
        f"games/bot={args.games_per_bot}  depth={args.depth}  "
        f"h={args.heuristic}  workers={args.workers}",
        file=sys.stderr,
        flush=True,
    )

    for generation in range(1, args.generations + 1):
        jobs = []
        for bot in population:
            opponents = [o for o in population if o.genome_id != bot.genome_id]
            for _ in range(args.games_per_bot):
                opp = rng.choice(opponents)
                seed = rng.randint(0, 2**31 - 1)
                if rng.random() < 0.5:
                    jobs.append(
                        (bot, opp, seed, args.depth, args.max_rounds, args.heuristic)
                    )
                else:
                    jobs.append(
                        (opp, bot, seed, args.depth, args.max_rounds, args.heuristic)
                    )

        wins: dict[int, float] = {}
        completed = 0
        total = len(jobs)

        if args.workers <= 1:
            for job in jobs:
                winner = _job(job)
                completed += 1
                if winner is not None:
                    wins[winner] = wins.get(winner, 0.0) + 1.0
                if completed % 10 == 0 or completed == total:
                    print(
                        f"gen {generation}/{args.generations}  games {completed}/{total}",
                        file=sys.stderr,
                        flush=True,
                    )
        else:
            with Pool(processes=args.workers) as pool:
                for winner in pool.imap_unordered(_job, jobs, chunksize=4):
                    completed += 1
                    if winner is not None:
                        wins[winner] = wins.get(winner, 0.0) + 1.0
                    if completed % 10 == 0 or completed == total:
                        print(
                            f"gen {generation}/{args.generations}  games {completed}/{total}",
                            file=sys.stderr,
                            flush=True,
                        )

        ranked = sorted(
            population,
            key=lambda g: (wins.get(g.genome_id, 0.0), -g.genome_id),
            reverse=True,
        )
        top_wins = wins.get(ranked[0].genome_id, 0.0)
        print(
            f"gen {generation} done  best_wins={top_wins:.0f}",
            file=sys.stderr,
            flush=True,
        )

        if top_wins > best_wins:
            best_wins = top_wins
            best_ever = ranked[0]

        if generation < args.generations:
            elites = ranked[: args.top]
            population = breed_next_generation(
                elites,
                args.population,
                rng,
                next_id,
                fixed_depth=args.depth,
            )
            next_id += args.population

    if best_ever is None:
        raise SystemExit("Brak wyniku self-play.")

    best_ever.depth = args.depth
    save_genome(args.output, best_ever)
    print(
        f"done  id={best_ever.genome_id}  wins={best_wins:.0f}  depth={best_ever.depth}  "
        f"saved={args.output}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        sys.exit(130)
