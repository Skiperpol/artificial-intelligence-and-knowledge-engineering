# Testy twardych reguł: bicie, wiszące piony, pułapki.

import time

from _setup import Runner
from _positions import capture_or_lose_board
from engine.board import Board, Move
from players.players import FirstPlayer, SecondPlayer
from ai.tactics import (
    find_best_capture,
    find_forced_win_move,
    get_free_captures,
    get_good_captures,
    is_capture_trap,
    is_free_capture,
    move_exposes_hanging_piece,
)
from ai.tournament_search import choose_tournament_move
from players.players import TournamentBlack


def run(runner: Runner | None = None) -> Runner:
    if runner is None:
        runner = Runner()
    runner.section("Tactics: captures and hanging pieces")

    board = capture_or_lose_board()
    player = FirstPlayer()
    cap = find_best_capture(board, player)
    runner.check(cap is not None and cap.is_capture, "must-capture position: find_best_capture")
    free = get_free_captures(board, player)
    runner.check(len(free) >= 1, "must-capture position has free capture")
    if free:
        runner.check(
            is_free_capture(board, player, free[0]),
            "free capture detected",
        )

    move, _, _ = choose_tournament_move(
        board, player, time_limit_s=0.5, use_opening_book=False
    )
    runner.check(
        move is not None and move.is_capture,
        f"tournament must capture, got {move}",
    )

    # B idzie na (4,3); W może zbić — nie wolno tam iść bez powodu.
    lines = [
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ B _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ W _ _ _",
        "_ _ _ _ _ _ _ _",
    ]
    hang_board = Board.from_lines(lines)
    hang_move = Move(4, 3, 5, 3, False)
    runner.check(
        move_exposes_hanging_piece(hang_board, FirstPlayer(), hang_move),
        "forward onto capturable square should be flagged as hanging",
    )

    # Proste bicie w końcówce nie jest pułapką.
    cap_board = capture_or_lose_board()
    good = get_good_captures(cap_board, FirstPlayer())
    runner.check(len(good) >= 1, "capture_or_lose has at least one good capture")
    if good:
        runner.check(
            not is_capture_trap(cap_board, FirstPlayer(), good[0]),
            "obvious capture should not be a trap",
        )

    # Wyścig do mety (turniej W): 3 ruchy do rzędu 7.
    race_lines = ["_ _ _ _ _ _ _ _"] * 4 + [
        "_ _ B _ _ _ _ _",
        "_ _ _ W _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
    ]
    race_board = Board.from_lines(race_lines)
    w = TournamentBlack(8)
    forced = find_forced_win_move(race_board, w, max_depth=7)
    runner.check(
        forced is not None and forced.to_row >= 5,
        f"tournament race should push forward, got {forced}",
    )
    race_move, _, _ = choose_tournament_move(
        race_board, w, time_limit_s=0.85, use_opening_book=True
    )
    runner.check(
        race_move is not None and race_move.to_row >= 5,
        f"tournament race move expected forward, got {race_move}",
    )

    return runner


if __name__ == "__main__":
    t0 = time.perf_counter()
    raise SystemExit(run().summary(time.perf_counter() - t0))
