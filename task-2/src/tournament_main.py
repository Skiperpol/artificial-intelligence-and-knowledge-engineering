from __future__ import annotations

import os
import sys

# Limit 1 s od startu kontenera — handshake przed ciężkimi importami.
print("1 1", flush=True)

from time import perf_counter

from ai.tournament_search import choose_tournament_move, _fast_fallback_move
from ai.eval_context import reset_active_genome, set_active_genome
from ai.genome import BotGenome, load_genome_file
from engine.board import Board
from players.players import Player, TournamentBlack, TournamentWhite, get_opponent
from tournament.protocol import (
    apply_tournament_move,
    emit_move,
    is_coordinate_move,
    is_full_board_line,
    read_line,
)

# Turniej: t_move=1.0 s — budżet wewnętrzny + twardy limit w play_turn.
MOVE_TIME_BUDGET_S = 0.48
MAX_SEARCH_DEPTH = 5
HARD_TURN_LIMIT_S = 0.92


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


def play_turn(board: Board, player: Player, rows: int, genome: BotGenome | None) -> None:
    legal_moves = board.get_legal_moves(player)
    if not legal_moves:
        raise SystemExit(0)

    search_depth = MAX_SEARCH_DEPTH
    if genome is not None:
        search_depth = max(MAX_SEARCH_DEPTH, min(5, genome.depth + 3))

    turn_start = perf_counter()
    token = set_active_genome(genome) if genome else None
    move = None
    try:
        if perf_counter() - turn_start < HARD_TURN_LIMIT_S - 0.05:
            move, _visited, _elapsed = choose_tournament_move(
                board,
                player,
                time_limit_s=MOVE_TIME_BUDGET_S,
                max_depth=search_depth,
                heuristic_name="breakthrough",
                use_mcts=False,
            )
    finally:
        if token is not None:
            reset_active_genome(token)

    if move is None or move not in legal_moves:
        move = _fast_fallback_move(board, player)
    if move not in legal_moves:
        move = legal_moves[0]

    try:
        emit_move(move, rows)
    except BrokenPipeError:
        raise SystemExit(0) from None
    board.apply_move(move, player)


def main() -> None:
    # Domyślnie: src/best_genome_selfplay.json. BREAKTHROUGH_GENOME nadpisuje ścieżkę.
    genome = load_genome_file(os.environ.get("BREAKTHROUGH_GENOME"))

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
        play_turn(board, me, rows, genome)
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
