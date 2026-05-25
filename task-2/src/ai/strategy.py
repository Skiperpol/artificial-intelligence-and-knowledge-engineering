"""Styl gry: centrum i rozwój → manewrowanie → przełamanie."""

from typing import List

from engine.board import Board, Move
from players.players import Player, get_opponent

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


def square_parity(row: int, col: int) -> int:
    return (row + col) % 2


def row_occupied_single_parity(
    board: Board, player: Player, row: int, *, min_pawns: int = 2
) -> bool:
    """W rzędzie są piony wyłącznie na jasnych lub wyłącznie na ciemnych polach."""
    if not (0 <= row < board.rows):
        return False
    parities: set[int] = set()
    count = 0
    for col in range(board.cols):
        if board.grid[row][col] != player.symbol:
            continue
        count += 1
        parities.add(square_parity(row, col))
    return count >= min_pawns and len(parities) == 1


def row_same_parity_cluster(
    board: Board, player: Player, row: int, *, min_count: int = 3
) -> bool:
    """Za dużo pionów w jednym rzędzie tylko na jasnych lub tylko na ciemnych polach."""
    if not (0 <= row < board.rows):
        return False
    light = 0
    dark = 0
    for col in range(board.cols):
        if board.grid[row][col] != player.symbol:
            continue
        if square_parity(row, col) == 0:
            light += 1
        else:
            dark += 1
    return (dark >= min_count and light == 0) or (light >= min_count and dark == 0)


def _lane_rows_between(from_row: int, to_row: int, direction: int) -> List[int]:
    if direction > 0:
        if to_row <= from_row:
            return []
        return list(range(from_row + 1, to_row + 1))
    if to_row >= from_row:
        return []
    return list(range(from_row - 1, to_row - 1, -1))


def lane_blocked_by_us(
    board: Board, player: Player, col: int, from_row: int, to_row: int
) -> bool:
    """Czy po drodze do mety stoi nasz pion w pasie (col±1)."""
    opponent = get_opponent(player)
    for row in _lane_rows_between(from_row, to_row, opponent.direction):
        for ncol in (col - 1, col, col + 1):
            if 0 <= ncol < board.cols and board.grid[row][ncol] == player.symbol:
                return True
    return False


def opponent_has_clear_lane_to_goal(board: Board, player: Player) -> bool:
    """Przeciwnik ma wolną drogę do mety w swoim pasie (bez naszych pionów przed nim)."""
    opponent = get_opponent(player)
    for row, col in _piece_positions(board, opponent.symbol):
        if not lane_blocked_by_us(board, player, col, row, opponent.goal_row):
            return True
    return False


def _ordered_opponent_moves(board: Board, opponent: Player, limit: int = 16) -> List[Move]:
    moves = board.get_legal_moves(opponent)
    moves.sort(
        key=lambda move: (
            move.is_capture,
            1 if move.to_row == opponent.goal_row else 0,
            abs(move.to_row - opponent.goal_row) * -1,
        ),
        reverse=True,
    )
    return moves[:limit]


def our_single_parity_ratio(board: Board, player: Player) -> float:
    """Ułamek pionów na dominującym kolorze pola (1.0 = wszystkie na jednym)."""
    light = 0
    dark = 0
    for row, col in _piece_positions(board, player.symbol):
        if square_parity(row, col) == 0:
            light += 1
        else:
            dark += 1
    total = light + dark
    if total == 0:
        return 0.0
    return max(light, dark) / total


def staircase_single_parity_formation(board: Board, player: Player) -> bool:
    """Kilka rzędów pod rząd — piony tylko na jednym kolorze (autostrada po skosie)."""
    streak = 0
    for row in range(board.rows):
        if row_occupied_single_parity(board, player, row, min_pawns=2):
            streak += 1
            if streak >= 2:
                return True
        else:
            streak = 0
    return False


def opponent_can_reach_goal_without_capture(
    board: Board, player: Player, *, max_ply: int = 10
) -> bool:
    """Czy przeciwnik może dojść do mety samymi ruchami cichymi (po skosach bez bić)."""
    opponent = get_opponent(player)
    if board.has_player_won(opponent):
        return True

    stack: List[tuple[Board, int]] = [(board, 0)]
    seen: set[int] = set()
    checked = 0
    limit = 120

    while stack and checked < limit:
        state, depth = stack.pop()
        state_key = hash(tuple(tuple(row) for row in state.grid))
        if state_key in seen:
            continue
        seen.add(state_key)
        checked += 1

        if state.has_player_won(opponent):
            return True
        if depth >= max_ply:
            continue

        for move in _ordered_opponent_moves(state, opponent, limit=14):
            if move.is_capture:
                continue
            child = Board([row[:] for row in state.grid])
            child.apply_move(move, opponent)
            stack.append((child, depth + 1))

    return False


def quick_diagonal_highway_risk(board: Board, player: Player) -> bool:
    return (
        opponent_has_clear_lane_to_goal(board, player)
        or (
            our_single_parity_ratio(board, player) >= 0.68
            and staircase_single_parity_formation(board, player)
        )
    )


def opponent_diagonal_highway_threat(
    board: Board, player: Player, *, lookahead: int = 4
) -> bool:
    """
    Układ na jednym kolorze pól + przeciwnik może przejść do mety bez bicia.
    """
    if opponent_has_clear_lane_to_goal(board, player):
        return True
    if not quick_diagonal_highway_risk(board, player):
        return False
    return opponent_can_reach_goal_without_capture(board, player, max_ply=lookahead + 1)


def opponent_clear_lane_threat_in_n_moves(
    board: Board, player: Player, opponent_moves: int = 3
) -> bool:
    """
    Czy przeciwnik w <=N swoich ruchach może mieć wolny bieg do mety
    (przed pionem brak naszych blokad w pasie).
    """
    if opponent_has_clear_lane_to_goal(board, player):
        return True
    if opponent_moves <= 0:
        return False

    opponent = get_opponent(player)
    stack: List[tuple[Board, int]] = [(board, 0)]
    seen: set[tuple] = set()
    states_checked = 0
    max_states = 220

    while stack and states_checked < max_states:
        state, depth = stack.pop()
        key = (tuple(tuple(row) for row in state.grid), depth)
        if key in seen:
            continue
        seen.add(key)
        states_checked += 1

        if opponent_has_clear_lane_to_goal(state, player):
            return True
        if state.has_player_won(opponent):
            return True
        if depth >= opponent_moves:
            continue

        for move in _ordered_opponent_moves(state, opponent):
            child = Board([row[:] for row in state.grid])
            child.apply_move(move, opponent)
            stack.append((child, depth + 1))

    return False


def lattice_open_lane_score(board: Board, player: Player) -> float:
    """
    Kara za „autostradę”: piony tylko na jednym kolorze pól,
    przeciwnik może iść po skosach / drugim kolorze bez bicia.
    """
    opponent = get_opponent(player)
    penalty = 0.0
    ratio = our_single_parity_ratio(board, player)
    if ratio >= 0.65:
        penalty += (ratio - 0.5) * 10.0
    if staircase_single_parity_formation(board, player):
        penalty += 5.0
    if opponent_can_reach_goal_without_capture(board, player, max_ply=10):
        penalty += 12.0
    for row in range(board.rows):
        if not row_same_parity_cluster(board, player, row, min_count=3):
            if not row_occupied_single_parity(board, player, row, min_pawns=2):
                continue
        penalty += 4.0
        for col in range(board.cols):
            if board.grid[row][col] != player.symbol:
                continue
            parity = square_parity(row, col)
            for next_row in (row + opponent.direction,):
                if not (0 <= next_row < board.rows):
                    continue
                for next_col in range(board.cols):
                    if square_parity(next_row, next_col) == parity:
                        continue
                    if board.grid[next_row][next_col] in {"_", "o"}:
                        penalty += 0.35
    return -penalty


def move_creates_same_color_wall(board: Board, player: Player, move: Move) -> bool:
    """Cichy ruch pogarsza siatkę (jeden kolor pól) lub otwiera bieg bez bicia."""
    if move.is_capture or move.to_row == player.goal_row:
        return False
    trial = Board([row[:] for row in board.grid])
    trial.apply_move(move, player)
    for row in (move.to_row, move.from_row):
        if row_same_parity_cluster(trial, player, row, min_count=3):
            return True
        if row_occupied_single_parity(trial, player, row, min_pawns=2):
            if our_single_parity_ratio(trial, player) >= 0.7:
                return True
    behind = move.to_row - player.direction
    if 0 <= behind < trial.rows and row_same_parity_cluster(
        trial, player, behind, min_count=3
    ):
        return True
    if not opponent_can_reach_goal_without_capture(board, player, max_ply=8):
        if opponent_can_reach_goal_without_capture(trial, player, max_ply=8):
            return True
    return False


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


def flank_column_set(board: Board, side: str) -> set[int]:
    if board.cols < 2:
        return {0} if side == "left" else {board.cols - 1}
    if side == "left":
        return {0, 1}
    return {board.cols - 2, board.cols - 1}


def opponent_flank_race_pressure(board: Board, perspective: Player) -> float:
    """Im wyżej, tym bardziej przeciwnik jedzie autostradą bokiem do mety."""
    from players.players import get_opponent

    opponent = get_opponent(perspective)
    pressure = 0.0
    for side in ("left", "right"):
        cols = flank_column_set(board, side)
        edge_col = min(cols) if side == "left" else max(cols)
        open_edge = sum(
            1
            for row in range(board.rows)
            if board.grid[row][edge_col] in {"_", "o"}
        )
        if open_edge >= board.rows // 2:
            pressure += open_edge * 0.55

        for row, col in _piece_positions(board, opponent.symbol):
            if col not in cols:
                continue
            dist = abs(row - opponent.goal_row)
            progress = max(0, board.rows - dist)
            pressure += progress * 1.15
            if col == edge_col:
                pressure += 2.5
            cleared = 0
            scan = row + opponent.direction
            while 0 <= scan < board.rows:
                cell = board.grid[scan][edge_col]
                if cell in {"_", "o"}:
                    cleared += 1
                    scan += opponent.direction
                elif cell == opponent.symbol:
                    scan += opponent.direction
                else:
                    break
            pressure += cleared * 2.0
    return pressure


def opponent_piece_on_flank_near_goal(board: Board, perspective: Player) -> bool:
    from players.players import get_opponent

    opponent = get_opponent(perspective)
    for side in ("left", "right"):
        cols = flank_column_set(board, side)
        for row, col in _piece_positions(board, opponent.symbol):
            if col in cols and abs(row - opponent.goal_row) <= 4:
                return True
    return False


def needs_flank_defense(board: Board, perspective: Player) -> bool:
    """Przeciwnik realnie grozi wejściem bokiem — trzeba blokować, nie iść w centrum."""
    if not opponent_piece_on_flank_near_goal(board, perspective):
        return False
    return opponent_flank_race_pressure(board, perspective) >= 6.0


def primary_threat_flank_side(board: Board, perspective: Player) -> str:
    """Które skrzydło przeciwnik najmocniej naciska."""
    from players.players import get_opponent

    opponent = get_opponent(perspective)
    left_score = 0.0
    right_score = 0.0
    for row, col in _piece_positions(board, opponent.symbol):
        progress = board.rows - abs(row - opponent.goal_row)
        if col <= 1:
            left_score += progress + (2.0 if col == 0 else 0.0)
        elif col >= board.cols - 2:
            right_score += progress + (2.0 if col == board.cols - 1 else 0.0)
    return "left" if left_score >= right_score else "right"


def threatened_flank_columns(board: Board, perspective: Player) -> set[int]:
    return flank_column_set(board, primary_threat_flank_side(board, perspective))


def flank_pressure_after_move(board: Board, player: Player, move: Move) -> float:
    trial = Board([row[:] for row in board.grid])
    trial.apply_move(move, player)
    return opponent_flank_race_pressure(trial, player)


def move_improves_flank_defense(board: Board, player: Player, move: Move) -> bool:
    before = opponent_flank_race_pressure(board, player)
    after = flank_pressure_after_move(board, player, move)
    return after + 0.4 < before


def move_worsens_flank_defense(board: Board, player: Player, move: Move) -> bool:
    if not needs_flank_defense(board, player):
        return False
    if move.is_capture or move.to_row == player.goal_row:
        return False
    before = opponent_flank_race_pressure(board, player)
    after = flank_pressure_after_move(board, player, move)
    return after > before + 0.6


def find_defend_flank_move(board: Board, player: Player) -> Move | None:
    """Blokada / odcięcie przejścia bokiem, gdy przeciwnik jedzie skrzydłem do mety."""
    if not needs_flank_defense(board, player):
        return None

    from ai.tactics import (
        copy_board,
        goal_progress_score,
        move_allows_opponent_win_in_one,
        move_exposes_hanging_piece,
    )

    before = opponent_flank_race_pressure(board, player)
    flank_cols = threatened_flank_columns(board, player)
    legal = []
    fallback_legal = []
    all_legal = list(board.get_legal_moves(player))
    for move in all_legal:
        if move_allows_opponent_win_in_one(board, player, move):
            continue
        fallback_legal.append(move)
        if not move.is_capture and move_exposes_hanging_piece(board, player, move):
            continue
        legal.append(move)
    if not fallback_legal:
        fallback_legal = all_legal
    if not legal:
        legal = fallback_legal
    if not legal:
        return None

    def rank(move: Move) -> tuple:
        trial = copy_board(board)
        trial.apply_move(move, player)
        reduction = before - opponent_flank_race_pressure(trial, player)
        on_lane = move.to_col in flank_cols
        return (
            1 if trial.has_player_won(player) else 0,
            1 if move.is_capture and move.to_col in flank_cols else 0,
            reduction,
            1 if on_lane else 0,
            1 if on_lane and move_improves_flank_defense(board, player, move) else 0,
            goal_progress_score(move, player) if move.is_capture else 0,
        )

    on_threat_lane = [move for move in legal if move.to_col in flank_cols]
    if not on_threat_lane:
        return None

    improving = [
        move
        for move in on_threat_lane
        if move_improves_flank_defense(board, player, move)
        or move.is_capture
    ]
    if improving:
        return max(improving, key=rank)

    return max(on_threat_lane, key=rank)


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

    if move_creates_same_color_wall(board, player, move):
        priority -= 160

    if needs_flank_defense(board, player):
        if move_improves_flank_defense(board, player, move):
            priority += 140
        if move.to_col in edge_cols or move.to_col in guard_cols:
            priority += 70
        if move.is_capture and (move.to_col in edge_cols or move.to_col in guard_cols):
            priority += 100
        if forward > 0 and move.to_col not in edge_cols and move.to_col not in guard_cols:
            if move.to_col in center:
                priority -= 100

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
            priority -= 140
        if forward > 0 and move.from_col in edge_cols:
            priority -= 110
        if forward > 0 and move.to_col in edge_cols:
            priority -= 130
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
