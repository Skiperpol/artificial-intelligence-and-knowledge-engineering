# [TEST]: Test sprawdza, czy algorytm alfa-beta faktycznie odwiedza mniej węzłów niż 
#         Minimax i czy realnie odcina zbędne gałęzie.

import time

from _setup import Runner
from _positions import both_players, random_board

from ai.heuristics import HEURISTICS
from ai.minimax import choose_best_move


SEEDS = list(range(8))
DEPTHS = [1, 2, 3]
HEURISTIC_NAMES = list(HEURISTICS.keys())


def _check_weak_bound(runner: Runner) -> None:
    runner.section("Alpha-beta visits no more nodes than plain Minimax")
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
                        pruned.visited_nodes <= plain.visited_nodes,
                        f"alpha-beta visited more nodes seed={seed} d={depth} "
                        f"h={heuristic} p={player.symbol}: "
                        f"mm={plain.visited_nodes} ab={pruned.visited_nodes}",
                    )


def _check_strict_prune_at_depth_3(runner: Runner) -> None:
    runner.section("Alpha-beta strictly prunes at depth 3 on a representative position")
    board = random_board(seed=123)
    for heuristic in HEURISTIC_NAMES:
        strict_prune_seen = False
        for player in both_players():
            plain = choose_best_move(
                board, player, 3, heuristic, use_alpha_beta=False
            )
            pruned = choose_best_move(
                board, player, 3, heuristic, use_alpha_beta=True
            )
            if pruned.visited_nodes < plain.visited_nodes:
                strict_prune_seen = True
        runner.check(
            strict_prune_seen,
            f"h={heuristic}: alpha-beta did NOT strictly reduce node count "
            f"for any player",
        )


def run(runner: Runner | None = None) -> Runner:
    if runner is None:
        runner = Runner()
    _check_weak_bound(runner)
    _check_strict_prune_at_depth_3(runner)
    return runner


if __name__ == "__main__":
    t0 = time.perf_counter()
    raise SystemExit(run().summary(time.perf_counter() - t0))
