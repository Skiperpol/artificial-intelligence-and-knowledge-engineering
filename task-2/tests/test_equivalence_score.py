import time

from _setup import Runner
from _positions import both_players, random_board

from ai.heuristics import HEURISTICS
from ai.minimax import choose_best_move


SEEDS = list(range(8))
DEPTHS = [1, 2, 3]
HEURISTIC_NAMES = list(HEURISTICS.keys())


def run(runner: Runner | None = None) -> Runner:
    if runner is None:
        runner = Runner()
    runner.section("Minimax and alpha-beta return the same root score")

    for seed in SEEDS:
        board = random_board(seed)
        for depth in DEPTHS:
            for heuristic in HEURISTIC_NAMES:
                for player in both_players():
                    plain = choose_best_move(
                        board, player, depth, heuristic, use_alpha_beta=False
                    )
                    pruned = choose_best_move(
                        board, player, depth, heuristic, use_alpha_beta=True
                    )
                    runner.check(
                        plain.score == pruned.score,
                        f"score mismatch seed={seed} d={depth} h={heuristic} "
                        f"p={player.symbol}: minimax={plain.score} "
                        f"alpha_beta={pruned.score}",
                    )

    return runner


if __name__ == "__main__":
    t0 = time.perf_counter()
    raise SystemExit(run().summary(time.perf_counter() - t0))
