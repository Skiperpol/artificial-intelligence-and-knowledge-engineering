"""Styl gry: centrum i rozwój → manewrowanie → przełamanie."""

from typing import List

from engine.board import Board, Move
from players.players import Player

def _piece_positions(board: Board, symbol: str) -> List[tuple[int, int]]:
    positions: List[tuple[int, int]] = []
    for row in range(board.rows):
        for col in range(board.cols):
            if board.grid[row][col] == symbol:
                positions.append((row, col))
    return positions


def _center_columns(board: Board) -> range:
    if board.cols <= 4:
        return range(board.cols)
    low = max(0, (board.cols // 2) - 2)
    high = min(board.cols - 1, (board.cols // 2) + 1)
    return range(low, high + 1)


def _center_balance(board: Board, perspective: Player) -> float:
    center_cols = set(_center_columns(board))
    my_score = 0
    opp_score = 0
    for _row, col in _piece_positions(board, perspective.symbol):
        if col in center_cols:
            my_score += 2
        elif abs(col - (board.cols // 2)) <= 2:
            my_score += 1
    for _row, col in _piece_positions(board, perspective.opponent_symbol()):
        if col in center_cols:
            opp_score += 2
        elif abs(col - (board.cols // 2)) <= 2:
            opp_score += 1
    return float(my_score - opp_score)


def _advancement_balance(board: Board, perspective: Player) -> float:
    from players.players import get_opponent

    opponent = get_opponent(perspective)
    my_positions = _piece_positions(board, perspective.symbol)
    opp_positions = _piece_positions(board, opponent.symbol)
    if not my_positions:
        return -float(board.rows)
    if not opp_positions:
        return float(board.rows)
    my_sum = sum(abs(row - perspective.goal_row) for row, _ in my_positions)
    opp_sum = sum(abs(row - opponent.goal_row) for row, _ in opp_positions)
    return float(opp_sum - my_sum)

StylePhase = str  # "opening" | "maneuvering" | "attack" | "endgame"


def _setup_depth(board: Board) -> int:
    return min(2, board.rows // 2)


def home_rank_rows(board: Board, player: Player) -> List[int]:
    """Rzędy startowe (tylna linia obozu)."""
    depth = _setup_depth(board)
    if player.direction > 0:
        return list(range(board.rows - depth, board.rows))
    return list(range(depth))


def count_internal_pawn_gaps_on_row(board: Board, row: int, symbol: str) -> int:
    """Liczba dziur między pionami w rzędzie (0 = zwarta linia)."""
    cols = sorted(
        c for c in range(board.cols) if board.grid[row][c] == symbol
    )
    if len(cols) < 2:
        return 0
    gaps = 0
    for index in range(len(cols) - 1):
        if cols[index + 1] - cols[index] > 1:
            gaps += 1
    return gaps


def max_home_rank_gaps(board: Board, player: Player) -> int:
    return max(
        (
            count_internal_pawn_gaps_on_row(board, row, player.symbol)
            for row in home_rank_rows(board, player)
        ),
        default=0,
    )


def move_creates_double_home_gap(board: Board, player: Player, move: Move) -> bool:
    trial = Board([row[:] for row in board.grid])
    trial.apply_move(move, player)
    return max_home_rank_gaps(trial, player) >= 2


def premature_wing_advance(board: Board, player: Player, move: Move) -> bool:
    """Za szybkie skrzydło: dziura na tylnej linii lub druga luka między pionami."""
    if move.is_capture or move.to_row == player.goal_row:
        return False
    guard = flank_guard_columns(board)
    edge = edge_columns(board)
    if move.from_col not in guard:
        return False
    if _forward_steps(move, player) <= 0:
        return False
    if move_creates_double_home_gap(board, player, move):
        return True
    side_edge = min(edge) if move.from_col <= min(guard) else max(edge)
    for row in home_rank_rows(board, player):
        if board.grid[row][side_edge] in {"_", "o"}:
            return True
    return False


def _has_left_home_rank(board: Board, row: int, player: Player) -> bool:
    setup = _setup_depth(board)
    if player.direction > 0:
        return row >= setup
    return row <= board.rows - 1 - setup


def army_mobilization_ratio(board: Board, player: Player) -> float:
    positions = _piece_positions(board, player.symbol)
    if not positions:
        return 0.0
    mobilized = sum(1 for row, _ in positions if _has_left_home_rank(board, row, player))
    return mobilized / len(positions)


def has_capture_moves(board: Board, player: Player) -> bool:
    return any(move.is_capture for move in board.get_legal_moves(player))


def count_capture_moves(board: Board, player: Player) -> int:
    return sum(1 for move in board.get_legal_moves(player) if move.is_capture)


def detect_style_phase(board: Board, perspective: Player) -> StylePhase:
    total = board.count_pieces("B") + board.count_pieces("W")
    max_cells = board.rows * board.cols

    if total <= max(8, int(0.22 * max_cells)):
        return "endgame"

    mobilization = army_mobilization_ratio(board, perspective)
    center_adv = _center_balance(board, perspective)
    advance_score = _advancement_balance(board, perspective)
    my_captures = count_capture_moves(board, perspective)

    if my_captures > 0:
        return "attack"
    if mobilization >= 0.5 and (center_adv >= 1 or advance_score >= 1):
        return "attack"
    if mobilization >= 0.6:
        return "attack"

    if mobilization < 0.42:
        return "opening"

    return "maneuvering"


def edge_columns(board: Board) -> set[int]:
    """Skrajne kolumny 0 i ostatnia — mają być puste (autostrada tylko dla rywali)."""
    return {0, board.cols - 1}


def flank_guard_columns(board: Board) -> set[int]:
    """Kolumny 1 i przedostatnia — mają mieć figury (blokada przejścia)."""
    if board.cols < 4:
        return set()
    return {1, board.cols - 2}


def _closest_goal_distance(board: Board, player: Player) -> int:
    rows = [
        row
        for row, _col in _piece_positions(board, player.symbol)
    ]
    if not rows:
        return board.rows
    return min(abs(row - player.goal_row) for row in rows)


def opponent_wins_race_if_ignored(board: Board, perspective: Player) -> bool:
    """Czy przeciwnik jest wyraźnie bliżej mety — wtedy nie gram all-in na skrzydło."""
    from players.players import get_opponent

    opponent = get_opponent(perspective)
    my_distance = _closest_goal_distance(board, perspective)
    opp_distance = _closest_goal_distance(board, opponent)
    return opp_distance + 1 < my_distance


def flank_lane_strength(board: Board, perspective: Player, side: str) -> float:
    """Im niżej, tym słabsza obrona przeciwnika na tym skrzydle (łatwiejszy przebój)."""
    from players.players import get_opponent

    opponent = get_opponent(perspective)
    if side == "left":
        lane_cols = [0, 1] if board.cols >= 2 else [0]
        edge_col = 0
    else:
        lane_cols = [board.cols - 2, board.cols - 1] if board.cols >= 2 else [board.cols - 1]
        edge_col = board.cols - 1

    defense = 0.0
    for col in lane_cols:
        for row in range(board.rows):
            cell = board.grid[row][col]
            if cell == opponent.symbol:
                defense += 2.0 + (board.rows - abs(row - opponent.goal_row)) * 0.25
            elif cell == perspective.symbol:
                defense -= (board.rows - abs(row - perspective.goal_row)) * 0.15

    empty_on_edge = sum(
        1
        for row in range(board.rows)
        if board.grid[row][edge_col] in {"_", "o"}
    )
    defense -= empty_on_edge * 1.2
    return defense


def weaker_opponent_flank(board: Board, perspective: Player) -> str:
    left_strength = flank_lane_strength(board, perspective, "left")
    right_strength = flank_lane_strength(board, perspective, "right")
    if left_strength <= right_strength:
        return "left"
    return "right"


def weak_flank_breakthrough_ready(board: Board, perspective: Player) -> bool:
    """Czy na słabszym skrzydle przeciwnika da się sensownie przebić do mety."""
    left = flank_lane_strength(board, perspective, "left")
    right = flank_lane_strength(board, perspective, "right")
    weak = weaker_opponent_flank(board, perspective)
    weak_val = left if weak == "left" else right
    strong_val = right if weak == "left" else left
    if weak_val + 1.5 > strong_val:
        return False
    edge = edge_columns(board)
    for row, col in _piece_positions(board, perspective.symbol):
        if col in edge:
            continue
        if weak == "left" and col <= 1:
            if abs(row - perspective.goal_row) <= 4:
                return True
        elif weak == "right" and col >= board.cols - 2:
            if abs(row - perspective.goal_row) <= 4:
                return True
    return False


def move_targets_weak_flank(board: Board, move: Move, player: Player) -> bool:
    weak = weaker_opponent_flank(board, player)
    if weak == "left":
        return move.to_col <= 1
    return move.to_col >= board.cols - 2


def _edge_columns(board: Board) -> set[int]:
    return edge_columns(board)


def _center_col_score(board: Board, col: int) -> int:
    center = set(_center_columns(board))
    if col in center:
        return 3
    mid = board.cols // 2
    if abs(col - mid) <= 2:
        return 1
    return 0


def _forward_steps(move: Move, player: Player) -> int:
    return (move.to_row - move.from_row) * player.direction


def _col_distance_to_center(board: Board, col: int) -> int:
    mid = (board.cols - 1) / 2.0
    return int(abs(col - mid))


def is_center_diagonal_opening_move(board: Board, move: Move, player: Player) -> bool:
    """Ruch typu (2,2)->(3,3): po skosie do przodu na pole bliżej centrum."""
    if move.is_capture:
        return False
    forward = _forward_steps(move, player)
    if forward != 1:
        return False
    if abs(move.to_col - move.from_col) != 1:
        return False
    center = set(_center_columns(board))
    if move.to_col not in center:
        return False
    from_dist = _col_distance_to_center(board, move.from_col)
    to_dist = _col_distance_to_center(board, move.to_col)
    return to_dist < from_dist


def move_priority(board: Board, move: Move, player: Player, phase: StylePhase) -> int:
    priority = 0
    edge_cols = edge_columns(board)
    guard_cols = flank_guard_columns(board)
    center = set(_center_columns(board))
    safe_flank_push = not opponent_wins_race_if_ignored(board, player)

    to_center = _center_col_score(board, move.to_col)
    from_center = _center_col_score(board, move.from_col)
    forward = _forward_steps(move, player)
    inward = _col_distance_to_center(board, move.from_col) - _col_distance_to_center(
        board, move.to_col
    )

    if phase == "opening":
        # Puste tylko kolumny 0 i ostatnia; jedno skrzydło naraz, max 1 luka w linii tylnej.
        if move.from_col in edge_cols and move.to_col in guard_cols:
            priority += 75
        if move.from_col in edge_cols:
            priority += 50
            if move.to_col not in edge_cols:
                priority += 35
        if move.from_col in guard_cols and move.to_col in center:
            priority += 45
        if is_center_diagonal_opening_move(board, move, player):
            priority += 65
        if move.from_col in edge_cols and move.to_col in edge_cols:
            priority -= 120
        if forward > 0 and move.from_col in edge_cols:
            priority -= 90
        if premature_wing_advance(board, player, move):
            priority -= 150
        if move_creates_double_home_gap(board, player, move):
            priority -= 200
        if move.from_col in guard_cols and forward > 0:
            other_guard = max(guard_cols) if move.from_col == min(guard_cols) else min(guard_cols)
            if any(
                board.grid[row][other_guard] == player.symbol
                for row in home_rank_rows(board, player)
            ):
                priority -= 40

        priority += to_center * 10
        if move.is_capture:
            priority += 90

    elif phase == "maneuvering":
        if move.is_capture:
            priority += 50
        if safe_flank_push and move_targets_weak_flank(board, move, player) and forward > 0:
            priority += 45
        elif forward > 0:
            priority += to_center * 4

    elif phase == "attack":
        if move.is_capture:
            priority += 80
        priority += max(forward, 0) * 16
        if move_targets_weak_flank(board, move, player):
            priority += 85 if safe_flank_push else 45
        elif forward > 0:
            priority += to_center * 3

    else:
        priority += max(forward, 0) * 22
        if move.is_capture:
            priority += 35
        if move_targets_weak_flank(board, move, player):
            priority += 70
        priority += to_center * 5

    return priority


def order_moves(
    board: Board,
    moves: List[Move],
    player: Player,
    *,
    heuristic_name: str,
) -> List[Move]:
    if heuristic_name != "breakthrough" or not moves:
        return moves

    phase = detect_style_phase(board, player)
    if has_capture_moves(board, player) and phase != "endgame":
        phase = "attack"
    return sorted(moves, key=lambda m: move_priority(board, m, player, phase), reverse=True)
