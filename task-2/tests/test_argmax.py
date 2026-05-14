import time

from _setup import Runner
from _positions import both_players, random_board
from _naive_minimax import naive_minimax

from ai.heuristics import HEURISTICS
from ai.minimax import choose_best_move, copy_board
from players.players import get_opponent


SEEDS = list(range(3))
DEPTHS = [1, 2]
HEURISTICS_UNDER_TEST = ("advancement", "material", "mobility")


def run(runner: Runner | None = None) -> Runner:
    if runner is None:
        runner = Runner()
    runner.section("Reported best move is an argmax over legal children")

    for seed in SEEDS:
        board = random_board(seed)
        for depth in DEPTHS:
            for heuristic_name in HEURISTICS_UNDER_TEST:
                heuristic_fn = HEURISTICS[heuristic_name]
                for player in both_players():
                    result = choose_best_move(
                        board, player, depth, heuristic_name, use_alpha_beta=True
                    )
                    if result.best_move is None:
                        continue

                    chosen_child = copy_board(board)
                    chosen_child.apply_move(result.best_move, player)
                    chosen_value = naive_minimax(
                        chosen_child, depth - 1,
                        get_opponent(player), player, heuristic_fn,
                    )
                    runner.check(
                        chosen_value == result.score,
                        f"chosen child value mismatch seed={seed} d={depth} "
                        f"h={heuristic_name} p={player.symbol}: "
                        f"chosen={chosen_value} reported={result.score}",
                    )

                    sibling_max = chosen_value
                    for move in board.get_legal_moves(player):
                        child = copy_board(board)
                        child.apply_move(move, player)
                        value = naive_minimax(
                            child, depth - 1,
                            get_opponent(player), player, heuristic_fn,
                        )
                        sibling_max = max(sibling_max, value)
                    runner.check(
                        sibling_max == result.score,
                        f"sibling max mismatch seed={seed} d={depth} "
                        f"h={heuristic_name} p={player.symbol}: "
                        f"sibling_max={sibling_max} reported={result.score}",
                    )

    return runner


if __name__ == "__main__":
    t0 = time.perf_counter()
    raise SystemExit(run().summary(time.perf_counter() - t0))
