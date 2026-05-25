#!/usr/bin/env python3
"""Ewolucja wag bota: populacja → mecze → top K → mutacja → kolejna generacja."""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

from ai.genome import breed_next_generation, make_population, save_genome
from evolution.engine import evaluate_population, print_progress, rank_population


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ewolucyjny tuning wag heurystyki breakthrough.",
    )
    parser.add_argument("--population", type=int, default=20, help="Rozmiar populacji.")
    parser.add_argument("--top", type=int, default=5, help="Liczba elit do rozmnażania.")
    parser.add_argument(
        "--games",
        type=int,
        default=5,
        help="Liczba gier na bota w każdej generacji.",
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=8,
        help="Liczba generacji ewolucji.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Procesy równoległe (1 = sekwencyjnie).",
    )
    parser.add_argument("--seed", type=int, default=42, help="Ziarno RNG.")
    parser.add_argument(
        "--output",
        type=str,
        default="best_genome.json",
        help="Plik JSON z najlepszym genomem.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.top > args.population:
        raise SystemExit("--top nie może być większe niż --population")
    if args.population < 2:
        raise SystemExit("--population musi być >= 2")

    rng = random.Random(args.seed)
    population = make_population(args.population, rng, start_id=0)
    best_ever = None
    best_ever_wins = -1.0
    next_id = args.population
    output_path = Path(args.output)

    for generation in range(1, args.generations + 1):
        jobs_total = args.population * args.games

        def progress(done: int, total: int) -> None:
            print_progress(generation, args.generations, done, total)

        wins = evaluate_population(
            population=population,
            games_per_bot=args.games,
            rng=rng,
            workers=args.workers,
            progress_callback=progress,
        )

        ranked = rank_population(population, wins)
        top_wins = wins.get(ranked[0].genome_id, 0.0)
        print_progress(generation, args.generations, jobs_total, jobs_total, top_wins)

        if top_wins > best_ever_wins:
            best_ever_wins = top_wins
            best_ever = ranked[0]

        if generation < args.generations:
            elites = ranked[: args.top]
            population = breed_next_generation(
                elites=elites,
                population_size=args.population,
                rng=rng,
                start_id=next_id,
            )
            next_id += args.population

    if best_ever is None:
        raise SystemExit("Brak wyników ewolucji.")

    save_genome(str(output_path.resolve()), best_ever)
    print(
        f"done  best_id={best_ever.genome_id}  wins={best_ever_wins:.0f}  "
        f"depth={best_ever.depth}  saved={output_path}",
        file=sys.stderr,
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        sys.exit(130)
