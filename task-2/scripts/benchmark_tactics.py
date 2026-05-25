#!/usr/bin/env python3
"""Porównanie bota: pełne warstwy taktyczne vs sam minimax turniejowy."""

from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

from _positions import (  # noqa: E402
    capture_or_lose_board,
    mate_in_one_board_for_black,
    mate_in_one_board_for_white,
)
from ai.minimax import choose_best_move_timed  # noqa: E402
from ai.tournament_search import choose_tournament_move  # noqa: E402
from engine.board import Board, Move  # noqa: E402
from players.players import (  # noqa: E402
    FirstPlayer,
    SecondPlayer,
    TournamentBlack,
    TournamentWhite,
    get_opponent,
)

TIME_S = 0.52
DEPTH = 6


def tournament_full(board: Board, player) -> Move | None:
    move, _, _ = choose_tournament_move(
        board,
        player,
        time_limit_s=TIME_S,
        max_depth=DEPTH,
        use_opening_book=True,
        use_endgame_solver=True,
    )
    return move


def tournament_search_only(board: Board, player) -> Move | None:
    """Tylko mat/blokada + minimax (bez książki, wymuszonego bicia, przeboju)."""
    from ai.tactics import find_block_opponent_win, find_immediate_win

    win = find_immediate_win(board, player)
    if win:
        return win
    block = find_block_opponent_win(board, player)
    if block:
        return block
    result = choose_best_move_timed(
        board,
        player,
        heuristic_name="breakthrough",
        time_limit_s=TIME_S,
        max_depth=DEPTH,
        use_tactical_filter=False,
        use_quiescence=False,
    )
    return result.best_move


# Filtr taktyczny tylko w minimaxie (bez wymuszonego bicia u korzenia w turnieju)
def tournament_tactical_search(board: Board, player) -> Move | None:
    from ai.tactics import find_block_opponent_win, find_immediate_win

    win = find_immediate_win(board, player)
    if win:
        return win
    block = find_block_opponent_win(board, player)
    if block:
        return block
    result = choose_best_move_timed(
        board,
        player,
        heuristic_name="breakthrough",
        time_limit_s=TIME_S,
        max_depth=DEPTH,
        use_tactical_filter=True,
        use_quiescence=True,
    )
    return result.best_move


def play_game(move_fn_a, move_fn_b, seed: int, white_is_a: bool) -> float:
    """+1 wygrana A, 0 remis, -1 przegrana A."""
    rng = random.Random(seed)
    rng.randint(0, 10**6)
    board = Board.tournament_default(8, 8)
    white = TournamentWhite(8)
    black = TournamentBlack(8)
    if white_is_a:
        fns = {white.symbol: move_fn_a, black.symbol: move_fn_b}
    else:
        fns = {white.symbol: move_fn_b, black.symbol: move_fn_a}
    current = white
    for _ in range(200):
        if board.has_player_won(white):
            return 1.0 if white_is_a else -1.0
        if board.has_player_won(black):
            return -1.0 if white_is_a else 1.0
        moves = board.get_legal_moves(current)
        if not moves:
            winner = get_opponent(current)
            if winner.symbol == white.symbol:
                return 1.0 if white_is_a else -1.0
            return -1.0 if white_is_a else 1.0
        move = fns[current.symbol](board, current)
        if move is None or move not in moves:
            move = moves[0]
        board.apply_move(move, current)
        current = get_opponent(current)
    return 0.0


def puzzle_checks() -> list[str]:
    issues: list[str] = []
    cases = [
        ("mate B", mate_in_one_board_for_black(), FirstPlayer(), 7),
        ("mate W", mate_in_one_board_for_white(), SecondPlayer(), 0),
        ("must capture", capture_or_lose_board(), FirstPlayer(), None),
    ]
    configs = [
        ("full", tournament_full),
        ("search_only", tournament_search_only),
        ("tactical_search", tournament_tactical_search),
    ]
    for pname, board, player, goal_row in cases:
        for cname, fn in configs:
            m = fn(board, player)
            if m is None:
                issues.append(f"{pname}/{cname}: brak ruchu")
                continue
            if goal_row is not None and m.to_row != goal_row:
                issues.append(f"{pname}/{cname}: oczekiwano to_row={goal_row}, jest {m.to_row}")
            if pname == "must capture" and not m.is_capture:
                issues.append(f"{pname}/{cname}: nie wykonano bicia")
    return issues


def round_robin(games: int) -> dict[str, float]:
    configs = {
        "full": tournament_full,
        "search_only": tournament_search_only,
        "tactical_search": tournament_tactical_search,
    }
    names = list(configs.keys())
    scores = {n: 0.0 for n in names}
    seed = 0
    for a in names:
        for b in names:
            if a == b:
                continue
            for g in range(games):
                seed += 1
                r1 = play_game(configs[a], configs[b], seed, white_is_a=True)
                seed += 1
                r2 = play_game(configs[b], configs[a], seed, white_is_a=True)
                scores[a] += r1 - r2
    return scores


def main() -> None:
    print("=== Zagadki taktyczne ===")
    issues = puzzle_checks()
    if issues:
        for line in issues:
            print("  FAIL:", line)
    else:
        print("  Wszystkie zagadki OK dla 3 wariantów.")

    print("\n=== Round-robin (8 gier na parę, perspektywa białego) ===")
    scores = round_robin(8)
    for name, sc in sorted(scores.items(), key=lambda x: -x[1]):
        print(f"  {name}: {sc:+.0f}")

    print("\n=== Wnioski ===")
    if scores.get("full", 0) < scores.get("search_only", 0):
        print("  UWAGA: Pełne warstwy GORSZE od czystego minimax w meczach.")
    elif scores.get("full", 0) < scores.get("tactical_search", 0):
        print("  UWAGA: Wymuszone bicie/książka gorsze; filtr w minimaxie OK.")
    else:
        print("  Pełny bot nie przegrywa z lżejszymi wariantami w tym próbkowaniu.")


if __name__ == "__main__":
    main()
