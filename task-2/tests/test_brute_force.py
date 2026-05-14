# [TEST]: Test weryfikuje, czy optymalizacje silnika (jak alfa-beta) nie psują wyniku, 
#         porównując go z pewną, choć wolniejszą metodą naiwnego minimaxa.

import time

from _setup import Runner
from _positions import both_players, random_board
from _naive_minimax import naive_minimax

from ai.heuristics import HEURISTICS
from ai.minimax import choose_best_move, copy_board
from players.players import get_opponent


SEEDS = list(range(3))
DEPTHS = [1, 2]
HEURISTIC_NAMES = list(HEURISTICS.keys())


def run(runner: Runner | None = None) -> Runner:
    if runner is None:
        runner = Runner()
    runner.section("Production score equals independent brute-force Minimax")

    for seed in SEEDS:
        board = random_board(seed)
        for depth in DEPTHS:
            for heuristic_name in HEURISTIC_NAMES:
                heuristic_fn = HEURISTICS[heuristic_name]
                for player in both_players():
                    legal = board.get_legal_moves(player)
                    if not legal:
                        continue

                    reference_scores = []
                    for move in legal:
                        child = copy_board(board)
                        child.apply_move(move, player)
                        reference_scores.append(
                            naive_minimax(
                                child, depth - 1,
                                get_opponent(player), player, heuristic_fn,
                            )
                        )
                    expected = max(reference_scores)

                    for use_alpha_beta in (False, True):
                        result = choose_best_move(
                            board, player, depth, heuristic_name,
                            use_alpha_beta=use_alpha_beta,
                        )
                        runner.check(
                            result.score == expected,
                            f"production != brute-force seed={seed} d={depth} "
                            f"h={heuristic_name} p={player.symbol} "
                            f"ab={use_alpha_beta}: prod={result.score} ref={expected}",
                        )

    return runner


if __name__ == "__main__":
    t0 = time.perf_counter()
    raise SystemExit(run().summary(time.perf_counter() - t0))
