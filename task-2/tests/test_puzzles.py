import time

from _setup import Runner
from _positions import (
    capture_or_lose_board,
    mate_in_one_board_for_black,
    mate_in_one_board_for_white,
)
from _naive_minimax import WIN_SCORE

from ai.heuristics import HEURISTICS
from ai.minimax import choose_best_move
from players.players import FirstPlayer, SecondPlayer


HEURISTIC_NAMES = list(HEURISTICS.keys())


def run(runner: Runner | None = None) -> Runner:
    if runner is None:
        runner = Runner()
    runner.section("Tactical puzzles: mate-in-1 and capture-or-lose")

    cases = [
        ("mate-in-1 B", mate_in_one_board_for_black(), FirstPlayer(), 7, None),
        ("mate-in-1 W", mate_in_one_board_for_white(), SecondPlayer(), 0, None),
        ("must-capture", capture_or_lose_board(), FirstPlayer(), None, True),
    ]

    for label, board, player, expected_to_row, expected_capture in cases:
        for heuristic in HEURISTIC_NAMES:
            for use_alpha_beta in (False, True):
                result = choose_best_move(
                    board, player, depth=2,
                    heuristic_name=heuristic, use_alpha_beta=use_alpha_beta,
                )
                tag = f"{label} h={heuristic} ab={use_alpha_beta}"

                runner.check(result.best_move is not None, f"{tag}: best_move was None")
                if result.best_move is None:
                    continue

                runner.check(
                    result.score == WIN_SCORE,
                    f"{tag}: expected score {WIN_SCORE}, got {result.score}",
                )
                if expected_to_row is not None:
                    runner.check(
                        result.best_move.to_row == expected_to_row,
                        f"{tag}: expected to_row {expected_to_row}, "
                        f"got {result.best_move.to_row}",
                    )
                if expected_capture is not None:
                    runner.check(
                        result.best_move.is_capture is expected_capture,
                        f"{tag}: expected is_capture {expected_capture}, "
                        f"got {result.best_move.is_capture}",
                    )

    return runner


if __name__ == "__main__":
    t0 = time.perf_counter()
    raise SystemExit(run().summary(time.perf_counter() - t0))
