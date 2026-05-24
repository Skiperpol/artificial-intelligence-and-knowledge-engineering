from __future__ import annotations

import sys
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


MOVE_TIME_BUDGET_S = 0.85
MIN_SEARCH_DEPTH = 2


def max_search_depth(rows: int, cols: int) -> int:
    area = rows * cols
    if area <= 36:
        return 6
    if area <= 49:
        return 5
    return 4


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
    return choose_adaptive_heuristic(board, player, "advancement")


def play_turn(board: Board, player: Player, rows: int) -> None:
    legal_moves = board.get_legal_moves(player)
    if not legal_moves:
        return

    deadline = perf_counter() + MOVE_TIME_BUDGET_S
    chosen = legal_moves[0]
    emit_move(chosen, rows)

    depth = MIN_SEARCH_DEPTH
    depth_limit = max_search_depth(rows, board.cols)
    while depth <= depth_limit and perf_counter() < deadline:
        if deadline - perf_counter() < 0.12:
            break
        heuristic_name = choose_heuristic(board, player)
        move, _visited, elapsed = choose_move_for_agent(
            board=board,
            player=player,
            agent_type="minimax",
            depth=depth,
            heuristic_name=heuristic_name,
            use_alpha_beta=True,
            epsilon=0.0,
        )
        if move is not None:
            chosen = move
            emit_move(chosen, rows)
        if elapsed > 0.18:
            break
        depth += 1

    board.apply_move(chosen, player)


def main() -> None:
    print("1 1", flush=True)

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
    except EOFError:
        sys.exit(0)
