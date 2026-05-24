from __future__ import annotations

import sys

# Limit 1 s od startu kontenera — handshake przed ciężkimi importami.
print("1 1", flush=True)

from time import perf_counter

from ai.agent_logic import choose_adaptive_heuristic, choose_move_for_agent
from engine.board import Board
from players.players import Player, TournamentBlack, TournamentWhite, get_opponent
from tournament.protocol import (
    apply_tournament_move,
    emit_move,
    is_coordinate_move,
    is_full_board_line,
    read_line,
)

# Turniej: 1 s na ruch; zostawiamy zapas na I/O i jitter (suma spóźnień max 3 s).
MOVE_TIME_BUDGET_S = 0.92
MIN_SEARCH_DEPTH = 2
MIN_TIME_TO_START_SEARCH_S = 0.22
MAX_SINGLE_SEARCH_S = 0.35


def max_search_depth(rows: int, cols: int) -> int:
    area = rows * cols
    if area <= 36:
        return 5
    if area <= 49:
        return 4
    return 3


def parse_game_info(line: str) -> tuple[int, int, int]:
    parts = line.split()
    if len(parts) != 3:
        raise ValueError(f"Expected board info 'cols rows player_id', got: {line!r}")
    cols, rows, player_id = (int(part) for part in parts)
    if player_id not in (0, 1):
        raise ValueError(f"Invalid player id: {player_id}")
    return cols, rows, player_id


def make_player(player_id: int, rows: int) -> Player:
    if player_id == 0:
        return TournamentWhite(rows)
    return TournamentBlack(rows)


def ingest_opponent_turn(
    line: str,
    board: Board,
    cols: int,
    rows: int,
    opponent: Player,
) -> Board:
    if is_full_board_line(line, cols, rows):
        return Board.from_tournament_flat(line, cols, rows)
    if is_coordinate_move(line):
        apply_tournament_move(board, line, rows, opponent.symbol)
        return board
    raise ValueError(f"Unrecognized tournament input: {line!r}")


def choose_heuristic(board: Board, player: Player) -> str:
    return choose_adaptive_heuristic(board, player, "breakthrough")


def play_turn(board: Board, player: Player, rows: int) -> None:
    legal_moves = board.get_legal_moves(player)
    if not legal_moves:
        return

    deadline = perf_counter() + MOVE_TIME_BUDGET_S
    chosen = legal_moves[0]
    depth = MIN_SEARCH_DEPTH
    depth_limit = max_search_depth(rows, board.cols)
    while depth <= depth_limit:
        remaining = deadline - perf_counter()
        if remaining < MIN_TIME_TO_START_SEARCH_S:
            break
        heuristic_name = choose_heuristic(board, player)
        search_start = perf_counter()
        move, _visited, elapsed = choose_move_for_agent(
            board=board,
            player=player,
            agent_type="minimax",
            depth=depth,
            heuristic_name=heuristic_name,
            use_alpha_beta=True,
            epsilon=0.0,
        )
        elapsed = perf_counter() - search_start
        if move is not None:
            chosen = move
        if elapsed > MAX_SINGLE_SEARCH_S:
            break
        if deadline - perf_counter() < MIN_TIME_TO_START_SEARCH_S:
            break
        depth += 1

    if chosen not in legal_moves:
        chosen = legal_moves[0]

    try:
        emit_move(chosen, rows)
    except BrokenPipeError:
        raise SystemExit(0) from None
    board.apply_move(chosen, player)


def main() -> None:
    cols, rows, player_id = parse_game_info(read_line())
    me = make_player(player_id, rows)
    opponent = get_opponent(me)
    board = Board.tournament_default(rows, cols)

    incoming = read_line()
    if player_id == 0:
        if is_full_board_line(incoming, cols, rows):
            board = Board.from_tournament_flat(incoming, cols, rows)
    else:
        board = ingest_opponent_turn(incoming, board, cols, rows, opponent)

    while True:
        play_turn(board, me, rows)
        try:
            incoming = read_line()
        except EOFError:
            break
        board = ingest_opponent_turn(incoming, board, cols, rows, opponent)


if __name__ == "__main__":
    try:
        main()
    except (EOFError, BrokenPipeError):
        sys.exit(0)
