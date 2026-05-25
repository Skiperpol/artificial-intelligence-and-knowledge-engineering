# Testy twardych reguł: bicie, wiszące piony, pułapki.

import time

from _setup import Runner
from _positions import capture_or_lose_board
from engine.board import Board, Move
from players.players import FirstPlayer, SecondPlayer
from ai.strategy import (
    find_defend_flank_move,
    move_creates_same_color_wall,
    needs_flank_defense,
    row_same_parity_cluster,
)
from ai.tactics import (
    capture_non_worsening_in_2ply,
    capture_exchange_balance,
    find_best_capture,
    find_forced_win_move,
    find_preemptive_threat_capture,
    find_profitable_capture_move,
    find_stop_free_gift_capture,
    move_creates_free_gift_for_opponent,
    get_free_captures,
    get_good_captures,
    is_capture_trap,
    is_free_capture,
    is_hanging_piece_at,
    is_profitable_capture,
    list_hanging_squares,
    list_threatened_squares,
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

    # W zagrożeniu: zbić pion przeciwnika zamiast iść do przodu.
    threat_lines = [
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ B _ _ _ _ _",
        "_ _ _ W _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
    ]
    threat_board = Board.from_lines(threat_lines)
    b = FirstPlayer()
    runner.check(
        is_hanging_piece_at(threat_board, b, 3, 2),
        "B at (3,2) should be hanging under W threat",
    )
    pre = find_preemptive_threat_capture(threat_board, b)
    runner.check(
        pre is not None
        and pre.is_capture
        and pre.from_row == 3
        and pre.from_col == 2
        and pre.to_row == 4
        and pre.to_col == 3,
        f"preemptive capture of threat, got {pre}",
    )
    tm, _, _ = choose_tournament_move(
        threat_board, b, time_limit_s=0.5, use_opening_book=False
    )
    runner.check(
        tm is not None and tm.is_capture and tm.to_row == 4 and tm.to_col == 3,
        f"tournament should capture threat W, got {tm}",
    )

    # Przeciwnik może zbić za darmo — bot musi zbić W.
    gift_lines = [
        "B B B B B B B B",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ B _ _ _ _",
        "_ _ _ _ W _ _ _",
        "_ _ _ _ _ _ _ _",
        "W W W W W W W W",
    ]
    gift_board = Board.from_lines(gift_lines)
    b_gift = FirstPlayer()
    gift_cap = find_stop_free_gift_capture(gift_board, b_gift)
    runner.check(
        gift_cap is not None and gift_cap.is_capture,
        f"should capture before free gift, got {gift_cap}",
    )

    # Wymiana niechronionym: B bije W (1:1), inaczej traci pion.
    trade_lines = [
        "B B B B B B B B",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ B _ _ _ _",
        "_ _ _ _ W _ _ _",
        "_ _ _ _ _ _ _ _",
        "W W W W W W W W",
    ]
    trade_board = Board.from_lines(trade_lines)
    b_trade = FirstPlayer()
    cap = find_profitable_capture_move(trade_board, b_trade)
    runner.check(
        cap is not None and cap.is_capture and cap.to_row == 5 and cap.to_col == 4,
        f"unprotected trade capture, got {cap}",
    )
    runner.check(
        capture_exchange_balance(trade_board, b_trade, cap) >= 0,
        "exchange should be even or better",
    )
    runner.check(
        capture_non_worsening_in_2ply(trade_board, b_trade, cap),
        "forced capture should pass 2-ply material gate",
    )
    lose_after_cap_lines = [
        "_ _ _ _ _ _ _ _",
        "_ W _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ B _ _ _ _",
        "_ _ _ _ W _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
    ]
    lose_after_cap_board = Board.from_lines(lose_after_cap_lines)
    lose_cap = Move(4, 3, 5, 4, True)
    runner.check(
        not capture_non_worsening_in_2ply(lose_after_cap_board, FirstPlayer(), lose_cap),
        "capture should fail 2-ply gate when opponent wins next",
    )
    # „Ochrona” z tyłu, ale W i tak może zbić — bot bierze W zamiast stać.
    protected_lines = [
        "B B B B B B B B",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ B _ _ _ _",
        "_ _ _ B W _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "W W W W W W W W",
    ]
    prot_board = Board.from_lines(protected_lines)
    b_prot = FirstPlayer()
    runner.check(
        len(list_threatened_squares(prot_board, b_prot)) >= 1,
        "supported pawn still under capture threat",
    )
    runner.check(
        len(list_hanging_squares(prot_board, b_prot)) == 0
        or len(list_threatened_squares(prot_board, b_prot)) >= 1,
        "threatened vs hanging distinction",
    )
    pre_prot = find_preemptive_threat_capture(prot_board, b_prot)
    runner.check(
        pre_prot is not None and pre_prot.is_capture and pre_prot.to_row == 4 and pre_prot.to_col == 4,
        f"should capture approaching W despite back support, got {pre_prot}",
    )

    # Przeciwnik jedzie lewym skrzydłem — bot blokuje kolumnę 0/1 zamiast centrum.
    flank_lines = [
        "_ W _ _ _ _ _ _",
        "W _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "_ _ _ _ _ _ _ _",
        "B B B B B B B B",
        "_ _ _ _ _ _ _ _",
    ]
    flank_board = Board.from_lines(flank_lines)
    b_flank = FirstPlayer()
    runner.check(
        needs_flank_defense(flank_board, b_flank),
        "opponent wing run should trigger flank defense",
    )
    defend = find_defend_flank_move(flank_board, b_flank)
    runner.check(
        defend is not None and defend.to_col in {0, 1},
        f"flank defense should use col 0/1, got {defend}",
    )
    fm, _, _ = choose_tournament_move(
        flank_board, b_flank, time_limit_s=0.5, use_opening_book=False
    )
    runner.check(
        fm is not None and fm.to_col in {0, 1, 2},
        f"tournament should block flank, got {fm}",
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
