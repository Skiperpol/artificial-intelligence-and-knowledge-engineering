from __future__ import annotations

import random
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple

from ai.agent_logic import choose_move_for_agent
from ai.eval_context import reset_active_genome, set_active_genome
from ai.genome import BotGenome
from engine.board import Board
from players.players import FirstPlayer, Player, SecondPlayer, get_opponent

MAX_ROUNDS = 200


@dataclass(frozen=True)
class GameJob:
    white: BotGenome
    black: BotGenome
    seed: int


@dataclass(frozen=True)
class GameOutcome:
    white_id: int
    black_id: int
    winner_id: int | None
    rounds: int


def _play_as(
    board: Board,
    player: Player,
    genome: BotGenome,
) -> bool:
    token = set_active_genome(genome)
    try:
        move, _nodes, _elapsed = choose_move_for_agent(
            board=board,
            player=player,
            agent_type="minimax",
            depth=genome.depth,
            heuristic_name="breakthrough",
            use_alpha_beta=True,
            epsilon=0.0,
        )
    finally:
        reset_active_genome(token)

    if move is None:
        return False
    board.apply_move(move, player)
    return True


def play_game(white: BotGenome, black: BotGenome, seed: int) -> GameOutcome:
    rng = random.Random(seed)
    rng.randint(0, 10**6)

    board = Board(rows=8, cols=8)
    player_b = FirstPlayer(board.rows)
    player_w = SecondPlayer(board.rows)
    genomes = {player_b.symbol: black, player_w.symbol: white}
    players = {player_b.symbol: player_b, player_w.symbol: player_w}
    current = player_b
    rounds = 0
    winner: Player | None = None

    while rounds < MAX_ROUNDS:
        if board.has_player_won(player_b):
            winner = player_b
            break
        if board.has_player_won(player_w):
            winner = player_w
            break

        if not board.get_legal_moves(current):
            winner = get_opponent(current)
            break

        moved = _play_as(board, current, genomes[current.symbol])
        if not moved:
            winner = get_opponent(current)
            break

        rounds += 1
        current = get_opponent(current)

    winner_id: int | None
    if winner is None:
        winner_id = None
    elif winner.symbol == "B":
        winner_id = black.genome_id
    else:
        winner_id = white.genome_id

    return GameOutcome(
        white_id=white.genome_id,
        black_id=black.genome_id,
        winner_id=winner_id,
        rounds=rounds,
    )


def _run_game_job(job: GameJob) -> GameOutcome:
    return play_game(job.white, job.black, job.seed)


def build_evaluation_jobs(
    population: List[BotGenome],
    games_per_bot: int,
    rng: random.Random,
) -> List[GameJob]:
    jobs: List[GameJob] = []
    for bot in population:
        opponents = [other for other in population if other.genome_id != bot.genome_id]
        if not opponents:
            continue
        for _ in range(games_per_bot):
            opponent = rng.choice(opponents)
            if rng.random() < 0.5:
                white, black = bot, opponent
            else:
                white, black = opponent, bot
            jobs.append(
                GameJob(
                    white=white,
                    black=black,
                    seed=rng.randint(0, 2**31 - 1),
                )
            )
    return jobs


def evaluate_population(
    population: List[BotGenome],
    games_per_bot: int,
    rng: random.Random,
    workers: int,
    progress_callback,
) -> dict[int, float]:
    jobs = build_evaluation_jobs(population, games_per_bot, rng)
    wins: dict[int, float] = defaultdict(float)
    completed = 0
    total = len(jobs)

    if workers <= 1:
        for job in jobs:
            outcome = _run_game_job(job)
            completed += 1
            if outcome.winner_id is not None:
                wins[outcome.winner_id] += 1.0
            progress_callback(completed, total)
        return dict(wins)

    from multiprocessing import Pool

    with Pool(processes=workers) as pool:
        for outcome in pool.imap_unordered(_run_game_job, jobs, chunksize=4):
            completed += 1
            if outcome.winner_id is not None:
                wins[outcome.winner_id] += 1.0
            progress_callback(completed, total)

    return dict(wins)


def rank_population(population: List[BotGenome], wins: dict[int, float]) -> List[BotGenome]:
    return sorted(
        population,
        key=lambda bot: (wins.get(bot.genome_id, 0.0), -bot.genome_id),
        reverse=True,
    )


def print_progress(
    generation: int,
    total_generations: int,
    completed: int,
    total_jobs: int,
    best_wins: float | None = None,
) -> None:
    if best_wins is None:
        msg = f"gen {generation}/{total_generations}  games {completed}/{total_jobs}"
    else:
        msg = (
            f"gen {generation}/{total_generations}  "
            f"games {completed}/{total_jobs}  best_wins={best_wins:.0f}"
        )
    print(msg, file=sys.stderr, flush=True)
