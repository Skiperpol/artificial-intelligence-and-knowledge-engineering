"""Twarde reguły taktyczne: bicia, groźba matu, filtrowanie ruchów u korzenia."""

from __future__ import annotations

from math import inf
from typing import List, Set, Tuple

from engine.board import Board, Move
from players.players import Player, get_opponent

def copy_board(board: Board) -> Board:
    return Board([row[:] for row in board.grid])


def is_capture_or_goal_move(board: Board, move: Move, player: Player) -> bool:
    if move.is_capture:
        return True
    return move.to_row == player.goal_row


def opponent_can_win_next_turn(board: Board, player: Player) -> bool:
    """Czy przeciwnik ma ruch wygrywający od razu."""
    opponent = get_opponent(player)
    if board.has_player_won(opponent):
        return True
    for move in board.get_legal_moves(opponent):
        trial = copy_board(board)
        trial.apply_move(move, opponent)
        if trial.has_player_won(opponent):
            return True
    return False


def move_allows_opponent_win_in_one(board: Board, player: Player, move: Move) -> bool:
    trial = copy_board(board)
    trial.apply_move(move, player)
    return opponent_can_win_next_turn(trial, player)


def opponent_can_win_in_two_if_we_move(
    board: Board, player: Player, move: Move
) -> bool:
    """Czy po naszym ruchu przeciwnik ma wymuszającą wygraną w 2 pełnych pół-ruchach."""
    after_us = copy_board(board)
    after_us.apply_move(move, player)
    opponent = get_opponent(player)

    for opp_move in after_us.get_legal_moves(opponent):
        after_opp = copy_board(after_us)
        after_opp.apply_move(opp_move, opponent)
        if after_opp.has_player_won(opponent):
            return True

        if not after_opp.get_legal_moves(player):
            continue

        all_responses_fail = True
        for reply in after_opp.get_legal_moves(player):
            after_reply = copy_board(after_opp)
            after_reply.apply_move(reply, player)
            if not opponent_can_win_next_turn(after_reply, player):
                all_responses_fail = False
                break

        if all_responses_fail and after_opp.get_legal_moves(player):
            return True

    return False


def _is_protected(board: Board, row: int, col: int, player: Player) -> bool:
    support_row = row - player.direction
    if not (0 <= support_row < board.rows):
        return False
    for support_col in (col - 1, col + 1):
        if 0 <= support_col < board.cols and board.grid[support_row][support_col] == player.symbol:
            return True
    return False


def _opponent_capture_moves_on(
    board: Board, player: Player, row: int, col: int
) -> List[Move]:
    opponent = get_opponent(player)
    return [
        move
        for move in board.get_legal_moves(opponent)
        if move.is_capture and move.to_row == row and move.to_col == col
    ]


def is_free_capture(board: Board, player: Player, move: Move) -> bool:
    """Bicie, po którym przeciwnik nie może od razu zbić pionu na tym polu."""
    if not move.is_capture:
        return False
    trial = copy_board(board)
    trial.apply_move(move, player)
    if trial.has_player_won(player):
        return True
    return len(_opponent_capture_moves_on(trial, player, move.to_row, move.to_col)) == 0


def is_capture_trap(board: Board, player: Player, move: Move) -> bool:
    """Bicie, po którym przeciwnik wygrywa lub bierze pion bez sensownej rekompensaty."""
    if not move.is_capture:
        return False
    if is_free_capture(board, player, move):
        return False

    trial = copy_board(board)
    trial.apply_move(move, player)
    if trial.has_player_won(player) or move.to_row == player.goal_row:
        return False
    if opponent_can_win_next_turn(trial, player):
        return True

    recaptures = _opponent_capture_moves_on(trial, player, move.to_row, move.to_col)
    if not recaptures:
        return False

    pieces_before = board.count_pieces(player.symbol)
    for opp_move in recaptures:
        after = copy_board(trial)
        after.apply_move(opp_move, get_opponent(player))
        if after.has_player_won(get_opponent(player)):
            return True
        if after.count_pieces(player.symbol) >= pieces_before:
            continue
        if find_immediate_win(after, player) is not None:
            continue
        if any(m.is_capture for m in after.get_legal_moves(player)):
            continue
        return True

    return False


def _capture_on_square_hurts_us(
    board: Board, player: Player, row: int, col: int
) -> bool:
    """Czy przeciwnik może zbić na tym polu z realną stratą materiału."""
    opponent = get_opponent(player)
    caps = _opponent_capture_moves_on(board, player, row, col)
    if not caps:
        return False
    pieces_before = board.count_pieces(player.symbol)
    for opp_move in caps:
        after = copy_board(board)
        after.apply_move(opp_move, opponent)
        if after.has_player_won(opponent):
            return True
        if find_immediate_win(after, player) is not None:
            continue
        if get_good_captures(after, player):
            continue
        if after.count_pieces(player.symbol) < pieces_before:
            return True
    return False


def is_hanging_piece_at(board: Board, player: Player, row: int, col: int) -> bool:
    """Niechroniony pion, którego przeciwnik może zbić z korzyścią."""
    if board.grid[row][col] != player.symbol:
        return False
    if _is_protected(board, row, col, player):
        return False
    return _capture_on_square_hurts_us(board, player, row, col)


def list_hanging_squares(board: Board, player: Player) -> List[Tuple[int, int]]:
    hanging: List[Tuple[int, int]] = []
    for row in range(board.rows):
        for col in range(board.cols):
            if is_hanging_piece_at(board, player, row, col):
                hanging.append((row, col))
    return hanging


def threat_piece_squares(
    board: Board, player: Player, hanging: List[Tuple[int, int]]
) -> Set[Tuple[int, int]]:
    """Pola, na których stoi przeciwnik mogący zbić wiszący pion w następnej turze."""
    threats: Set[Tuple[int, int]] = set()
    for row, col in hanging:
        for opp_move in _opponent_capture_moves_on(board, player, row, col):
            threats.add((opp_move.from_row, opp_move.from_col))
    return threats


def quiet_move_adds_support(
    board: Board, player: Player, move: Move, row: int, col: int
) -> bool:
    """Inny pion zasłania wiszący — nie liczy się ucieczka samego zagrożonego."""
    if move.is_capture or (move.from_row == row and move.from_col == col):
        return False
    trial = copy_board(board)
    trial.apply_move(move, player)
    if trial.grid[row][col] != player.symbol:
        return False
    return _is_protected(trial, row, col, player)


def has_quiet_protection_for_hanging(
    board: Board, player: Player, hanging: List[Tuple[int, int]]
) -> bool:
    """Czy da się w tej turze dodać wsparcie innym pionem (bez ruszania ofiary)."""
    for move in board.get_legal_moves(player):
        if move.is_capture:
            continue
        if move_allows_opponent_win_in_one(board, player, move):
            continue
        if move_exposes_hanging_piece(board, player, move):
            continue
        if all(
            quiet_move_adds_support(board, player, move, row, col)
            for row, col in hanging
        ):
            return True
    return False


def find_preemptive_threat_capture(board: Board, player: Player) -> Move | None:
    """
    Zbij pion zagrożenia, gdy mamy niechronionego własnego pionka
    i w tej turze nie dodajemy ochrony cichym ruchem.
    """
    hanging = list_hanging_squares(board, player)
    if not hanging:
        return None

    threats = threat_piece_squares(board, player, hanging)
    if not threats:
        return None

    if has_quiet_protection_for_hanging(board, player, hanging):
        return None

    candidates = [
        move
        for move in get_good_captures(board, player)
        if (move.to_row, move.to_col) in threats
    ]
    if not candidates:
        return None

    def rank(move: Move) -> tuple:
        trial = copy_board(board)
        trial.apply_move(move, player)
        resolved = sum(
            1
            for row, col in hanging
            if trial.grid[row][col] != player.symbol
            or not is_hanging_piece_at(trial, player, row, col)
        )
        return (
            1 if trial.has_player_won(player) else 0,
            1 if is_free_capture(board, player, move) else 0,
            resolved,
            goal_progress_score(move, player),
        )

    return max(candidates, key=rank)


def move_exposes_hanging_piece(board: Board, player: Player, move: Move) -> bool:
    """Cichy ruch pozwala przeciwnikowi zbić (zwłaszcza bez odpowiedzi)."""
    if move.is_capture or move.to_row == player.goal_row:
        return False

    trial = copy_board(board)
    trial.apply_move(move, player)
    if trial.has_player_won(player):
        return False

    row, col = move.to_row, move.to_col
    opponent = get_opponent(player)
    pieces_before = board.count_pieces(player.symbol)

    for opp_move in trial.get_legal_moves(opponent):
        if not opp_move.is_capture:
            continue
        after = copy_board(trial)
        after.apply_move(opp_move, opponent)
        if after.has_player_won(opponent):
            return True
        if opp_move.to_row != row or opp_move.to_col != col:
            continue
        if find_immediate_win(after, player) is not None:
            continue
        if get_good_captures(after, player):
            continue
        if after.count_pieces(player.symbol) < pieces_before:
            return True
    return False


def get_free_captures(board: Board, player: Player) -> List[Move]:
    return [
        move
        for move in board.get_legal_moves(player)
        if is_free_capture(board, player, move)
    ]


def get_good_captures(board: Board, player: Player) -> List[Move]:
    return [
        move
        for move in board.get_legal_moves(player)
        if move.is_capture and not is_capture_trap(board, player, move)
    ]


def _rank_capture(board: Board, player: Player, move: Move) -> tuple:
    trial = copy_board(board)
    trial.apply_move(move, player)
    return (
        1 if trial.has_player_won(player) else 0,
        1 if is_free_capture(board, player, move) else 0,
        1 if move.to_row == player.goal_row else 0,
        goal_progress_score(move, player),
    )


def find_best_capture(board: Board, player: Player) -> Move | None:
    """Najlepsze bezpieczne bicie (darmowe bicia mają pierwszeństwo)."""
    free = get_free_captures(board, player)
    if free:
        return max(free, key=lambda m: _rank_capture(board, player, m))

    good = get_good_captures(board, player)
    if not good:
        return None
    return max(good, key=lambda m: _rank_capture(board, player, m))


def find_mandatory_capture(board: Board, player: Player) -> Move | None:
    """Bicie zagrożenia / darmowe / inne dobre bicie — w tej kolejności."""
    threat = find_preemptive_threat_capture(board, player)
    if threat is not None:
        return threat
    return find_best_capture(board, player)


def filter_safe_root_moves(
    board: Board,
    player: Player,
    moves: List[Move],
    *,
    block_win_in_two: bool = True,
    avoid_hanging: bool = True,
    protect_wing_structure: bool = True,
) -> List[Move]:
    from ai.strategy import (
        detect_style_phase,
        move_creates_double_home_gap,
        move_worsens_flank_defense,
        premature_wing_advance,
    )

    opening_like = protect_wing_structure and detect_style_phase(board, player) in (
        "opening",
        "maneuvering",
    )
    safe: List[Move] = []
    for move in moves:
        if move_allows_opponent_win_in_one(board, player, move):
            continue
        if block_win_in_two and opponent_can_win_in_two_if_we_move(board, player, move):
            continue
        if avoid_hanging and move_exposes_hanging_piece(board, player, move):
            continue
        if opening_like and (
            premature_wing_advance(board, player, move)
            or move_creates_double_home_gap(board, player, move)
        ):
            continue
        if move_worsens_flank_defense(board, player, move):
            continue
        safe.append(move)

    if safe:
        return safe
    captures = [m for m in moves if m.is_capture]
    if captures:
        return captures
    return list(moves)


def apply_tactical_constraints(
    board: Board,
    player: Player,
    moves: List[Move],
) -> List[Move]:
    """Mat w 1, potem bicia, potem bezpieczne ruchy ciche."""
    if not moves:
        return moves

    win = find_immediate_win(board, player)
    if win is not None:
        return [win]

    free = [m for m in moves if is_free_capture(board, player, m)]
    if free:
        return free

    good_caps = [m for m in moves if m.is_capture and not is_capture_trap(board, player, m)]
    if good_caps:
        return good_caps

    safe = filter_safe_root_moves(board, player, moves)
    if safe:
        return safe
    quiet = [m for m in moves if not m.is_capture]
    return quiet if quiet else list(moves)


def closest_goal_distance(board: Board, player: Player) -> int:
    rows = [
        row
        for row in range(board.rows)
        for col in range(board.cols)
        if board.grid[row][col] == player.symbol
    ]
    if not rows:
        return board.rows
    return min(abs(row - player.goal_row) for row in rows)


def is_goal_race(board: Board, player: Player) -> bool:
    return closest_goal_distance(board, player) <= 4


def should_skip_opening_book(board: Board, player: Player) -> bool:
    """Nie trzymaj się debiutu, gdy liczy się wyścig do mety lub przebój."""
    if is_goal_race(board, player):
        return True
    from ai.strategy import opponent_wins_race_if_ignored, weak_flank_breakthrough_ready

    if opponent_wins_race_if_ignored(board, player):
        return True
    return weak_flank_breakthrough_ready(board, player)


def goal_progress_score(move: Move, player: Player) -> int:
    before = abs(move.from_row - player.goal_row)
    after = abs(move.to_row - player.goal_row)
    return before - after


def find_immediate_win(board: Board, player: Player) -> Move | None:
    """Ruch kończący partię od razu — najpierw wejście na rząd mety."""
    fallback: Move | None = None
    for move in board.get_legal_moves(player):
        trial = copy_board(board)
        trial.apply_move(move, player)
        if not trial.has_player_won(player):
            continue
        if move.to_row == player.goal_row:
            return move
        if fallback is None:
            fallback = move
    return fallback


def _probe_negamax(
    board: Board,
    current: Player,
    root: Player,
    depth_left: int,
) -> float:
    """Płytkie drzewo: czy root wymusza wygraną w depth_left pół-ruchach."""
    from ai.minimax import MATE_SCORE, _evaluate_terminal

    terminal = _evaluate_terminal(board, root, current)
    if terminal is not None:
        return terminal
    if depth_left <= 0:
        return 0.0

    legal = board.get_legal_moves(current)
    if not legal:
        opponent = get_opponent(current)
        if not board.get_legal_moves(opponent):
            return MATE_SCORE if current.symbol != root.symbol else -MATE_SCORE
        return -MATE_SCORE if current.symbol == root.symbol else MATE_SCORE

    opponent = get_opponent(current)
    if current.symbol == root.symbol:
        value = -inf
        for move in legal:
            child = copy_board(board)
            child.apply_move(move, current)
            value = max(
                value, _probe_negamax(child, opponent, root, depth_left - 1)
            )
        return value

    value = inf
    for move in legal:
        child = copy_board(board)
        child.apply_move(move, current)
        value = min(value, _probe_negamax(child, opponent, root, depth_left - 1))
    return value


def find_forced_win_move(
    board: Board,
    player: Player,
    *,
    max_depth: int = 7,
    deadline: float | None = None,
) -> Move | None:
    """Ruch wymuszający wygraną w max_depth pół-ruchach (tylko wyścig do mety)."""
    from time import perf_counter

    from ai.minimax import MATE_SCORE

    if not is_goal_race(board, player):
        return None

    legal = board.get_legal_moves(player)
    if not legal:
        return None

    ordered = sorted(
        legal,
        key=lambda move: (
            move.to_row == player.goal_row,
            goal_progress_score(move, player),
            move.is_capture,
        ),
        reverse=True,
    )

    best_move: Move | None = None
    best_score = -inf
    opponent = get_opponent(player)

    ply_cap = min(max_depth, 4 + closest_goal_distance(board, player))

    for move in ordered:
        if deadline is not None and perf_counter() >= deadline:
            break
        trial = copy_board(board)
        trial.apply_move(move, player)
        if trial.has_player_won(player) and move.to_row == player.goal_row:
            return move
        score = _probe_negamax(trial, opponent, player, ply_cap - 1)
        if score >= MATE_SCORE - 1.0 and score > best_score:
            best_score = score
            best_move = move

    return best_move


def find_breakthrough_lane_move(board: Board, player: Player) -> Move | None:
    """Przebój słabym skrzydłem przeciwnika w stronę mety."""
    from ai.strategy import (
        move_targets_weak_flank,
        needs_flank_defense,
        opponent_wins_race_if_ignored,
        weak_flank_breakthrough_ready,
    )

    if needs_flank_defense(board, player):
        return None

    legal = filter_safe_root_moves(board, player, board.get_legal_moves(player))
    if not legal:
        return None

    candidates: List[Move] = []
    for move in legal:
        if move.to_row == player.goal_row:
            candidates.append(move)
            continue
        if goal_progress_score(move, player) <= 0:
            continue
        if weak_flank_breakthrough_ready(board, player) and move_targets_weak_flank(
            board, move, player
        ):
            candidates.append(move)
        elif opponent_wins_race_if_ignored(board, player):
            candidates.append(move)

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda move: (
            move.to_row == player.goal_row,
            goal_progress_score(move, player),
            1 if move_targets_weak_flank(board, move, player) else 0,
        ),
    )


def should_force_capture(board: Board, player: Player) -> bool:
    """Wymuś bicie, gdy jest choć jedno bezpieczne (zwłaszcza darmowe)."""
    if get_free_captures(board, player):
        return True
    if not get_good_captures(board, player):
        return False
    for move in board.get_legal_moves(player):
        if move.is_capture:
            continue
        if move.to_row == player.goal_row:
            return False
        trial = copy_board(board)
        trial.apply_move(move, player)
        if trial.has_player_won(player):
            return False
    return True


def find_block_opponent_win(board: Board, player: Player) -> Move | None:
    """Blokada matu przeciwnika w 1 — gdy taki ruch istnieje."""
    if not opponent_can_win_next_turn(board, player):
        return None
    legal = board.get_legal_moves(player)
    safe = filter_safe_root_moves(board, player, legal)
    if not safe:
        return None
    return max(
        safe,
        key=lambda move: (
            move.to_row == player.goal_row,
            goal_progress_score(move, player),
            move.is_capture,
        ),
    )


def prioritize_tactical_moves(
    moves: List[Move],
    *,
    board: Board | None = None,
    player: Player | None = None,
) -> List[Move]:
    if board is not None and player is not None:
        goal_moves = [move for move in moves if move.to_row == player.goal_row]
        captures = [
            move
            for move in moves
            if move.is_capture
            and move.to_row != player.goal_row
            and not is_capture_trap(board, player, move)
        ]
        advances = [
            move
            for move in moves
            if not move.is_capture and move.to_row != player.goal_row
        ]
        advances.sort(key=lambda move: goal_progress_score(move, player), reverse=True)
        return goal_moves + captures + advances

    captures = [move for move in moves if move.is_capture]
    non_captures = [move for move in moves if not move.is_capture]
    return captures + non_captures
