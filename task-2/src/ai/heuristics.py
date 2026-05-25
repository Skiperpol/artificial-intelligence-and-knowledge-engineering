from typing import Callable, Dict, List, Literal

from engine.board import Board
from players.players import Player, get_opponent
from ai.strategy import (
    army_mobilization_ratio,
    count_capture_moves,
    detect_style_phase,
    edge_columns,
    flank_guard_columns,
    flank_lane_strength,
    has_capture_moves,
    opponent_wins_race_if_ignored,
    weaker_opponent_flank,
)

GamePhase = Literal["opening", "maneuvering", "attack", "endgame"]

# Wagi złożonej funkcji oceny (priorytet maleje w dół listy dokumentacji).
EVAL_WEIGHTS: Dict[str, float] = {
    "advancement": 100.0,
    "mobility": 12.0,
    "goal_pressure": 45.0,
    "safety": 28.0,
    "center_control": 8.0,
    "center_advancement": 20.0,
    "attack_threats": 18.0,
    "bottlenecks": 22.0,
    "material": 25.0,
    "chain_support": 14.0,
    "fork_risk": 32.0,
    "blocked_trap": 40.0,
    "isolated_lead": 15.0,
    "suicidal_exposure": 25.0,
    "harmonious_development": 18.0,
    "wing_vacancy": 35.0,
    "center_diagonal_setup": 28.0,
    "army_mobilization": 16.0,
    "active_pieces": 14.0,
    "capture_options": 30.0,
    "flank_guard": 22.0,
    "weak_flank_attack": 26.0,
    "defend_our_flanks": 24.0,
}


def _piece_positions(board: Board, symbol: str) -> List[tuple[int, int]]:
    positions: List[tuple[int, int]] = []
    for row in range(board.rows):
        for col in range(board.cols):
            if board.grid[row][col] == symbol:
                positions.append((row, col))
    return positions


def _distance_to_goal_row(row: int, goal_row: int, board_rows: int) -> int:
    return abs(row - goal_row)


def _game_phase(board: Board, perspective: Player) -> GamePhase:
    return detect_style_phase(board, perspective)  # type: ignore[return-value]


def _phase_weights(phase: GamePhase) -> Dict[str, float]:
    from ai.eval_context import scaled_base_weights

    weights = scaled_base_weights()
    if phase == "opening":
        # Debiut: czyste skrzydła, obsesja na centrum, równy rozwój, bez gróźb (ruchy 1–13).
        weights["center_control"] *= 4.5
        weights["harmonious_development"] *= 3.0
        weights["wing_vacancy"] *= 4.5
        weights["center_diagonal_setup"] *= 3.5
        weights["army_mobilization"] *= 1.4
        weights["advancement"] *= 0.5
        weights["goal_pressure"] *= 0.4
        weights["attack_threats"] *= 0.2
        weights["material"] *= 0.3
        weights["center_advancement"] *= 1.2
        weights["flank_guard"] *= 2.5
    elif phase == "maneuvering":
        # Gra środkowa: napięcie, łańcuchy; centrum już mniej ważne niż groźby.
        weights["mobility"] *= 2.0
        weights["center_advancement"] *= 1.2
        weights["active_pieces"] *= 1.6
        weights["chain_support"] *= 2.2
        weights["attack_threats"] *= 2.0
        weights["harmonious_development"] *= 1.0
        weights["isolated_lead"] *= 1.2
        weights["advancement"] *= 0.9
        weights["material"] *= 0.8
        weights["center_control"] *= 1.0
        weights["wing_vacancy"] *= 0.5
        weights["center_diagonal_setup"] *= 0.4
        weights["flank_guard"] *= 1.5
        weights["defend_our_flanks"] *= 2.0
        weights["weak_flank_attack"] *= 1.2
    elif phase == "attack":
        # Atak: bicia, przełamanie, zatory — nie dalsze „budowanie” centrum.
        weights["advancement"] *= 1.8
        weights["attack_threats"] *= 3.5
        weights["bottlenecks"] *= 2.5
        weights["goal_pressure"] *= 1.6
        weights["material"] *= 1.4
        weights["mobility"] *= 1.0
        weights["center_control"] *= 0.4
        weights["center_advancement"] *= 0.5
        weights["wing_vacancy"] *= 0.15
        weights["center_diagonal_setup"] *= 0.1
        weights["harmonious_development"] *= 0.5
        weights["weak_flank_attack"] *= 2.8
        weights["defend_our_flanks"] *= 1.4
        weights["goal_pressure"] *= 2.0
    else:
        weights["advancement"] *= 1.35
        weights["goal_pressure"] *= 1.8
        weights["mobility"] *= 0.9
        weights["material"] *= 0.75
    return weights


def material_heuristic(board: Board, perspective: Player) -> float:
    my_count = len(_piece_positions(board, perspective.symbol))
    opp_count = len(_piece_positions(board, perspective.opponent_symbol()))
    return float(my_count - opp_count)


def _advancement_for_row(row: int, goal_row: int) -> int:
    return _distance_to_goal_row(row, goal_row, 0)


def advancement_heuristic(board: Board, perspective: Player) -> float:
    my_total_advancement = 0
    opp_total_advancement = 0
    opponent = get_opponent(perspective)

    for row, _col in _piece_positions(board, perspective.symbol):
        my_total_advancement += _advancement_for_row(row, perspective.goal_row)

    for row, _col in _piece_positions(board, opponent.symbol):
        opp_total_advancement += _advancement_for_row(row, opponent.goal_row)

    return float(my_total_advancement - opp_total_advancement)


def mobility_heuristic(board: Board, perspective: Player) -> float:
    my_moves = len(board.get_legal_moves(perspective))
    opp_moves = len(board.get_legal_moves(get_opponent(perspective)))
    return float(my_moves - opp_moves)


def goal_pressure_heuristic(board: Board, perspective: Player) -> float:
    my_positions = _piece_positions(board, perspective.symbol)
    opp_positions = _piece_positions(board, perspective.opponent_symbol())

    if not my_positions:
        return -float(board.rows)
    if not opp_positions:
        return float(board.rows)

    my_closest = min(
        _distance_to_goal_row(row, perspective.goal_row, board.rows) for row, _ in my_positions
    )
    opp_closest = min(
        _distance_to_goal_row(row, get_opponent(perspective).goal_row, board.rows)
        for row, _ in opp_positions
    )
    return float(opp_closest - my_closest)


def _center_columns(board: Board) -> range:
    if board.cols <= 4:
        return range(board.cols)
    low = max(0, (board.cols // 2) - 2)
    high = min(board.cols - 1, (board.cols // 2) + 1)
    return range(low, high + 1)


def center_control_heuristic(board: Board, perspective: Player) -> float:
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


def _is_protected(board: Board, row: int, col: int, player: Player) -> bool:
    guard_row = row - player.direction
    if not (0 <= guard_row < board.rows):
        return False
    for guard_col in (col - 1, col + 1):
        if 0 <= guard_col < board.cols and board.grid[guard_row][guard_col] == player.symbol:
            return True
    return False


def safety_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_safe = 0
    opp_safe = 0

    for row, col in _piece_positions(board, perspective.symbol):
        if _is_protected(board, row, col, perspective):
            my_safe += 1

    for row, col in _piece_positions(board, opponent.symbol):
        if _is_protected(board, row, col, opponent):
            opp_safe += 1

    return float(my_safe - opp_safe)


def _can_attack_from(board: Board, row: int, col: int, attacker: Player) -> bool:
    target_row = row + attacker.direction
    if not (0 <= target_row < board.rows):
        return False
    for target_col in (col - 1, col + 1):
        if 0 <= target_col < board.cols:
            if board.grid[target_row][target_col] == attacker.opponent_symbol():
                return True
    return False


def attack_threats_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_threats = 0
    opp_threats = 0

    for row, col in _piece_positions(board, perspective.symbol):
        if _can_attack_from(board, row, col, perspective):
            my_threats += 1

    for row, col in _piece_positions(board, opponent.symbol):
        if _can_attack_from(board, row, col, opponent):
            opp_threats += 1

    return float(my_threats - opp_threats)


def threatened_pieces_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_threatened = 0
    opp_threatened = 0

    for row, col in _piece_positions(board, perspective.symbol):
        if _can_attack_from(board, row, col, opponent):
            my_threatened += 1

    for row, col in _piece_positions(board, opponent.symbol):
        if _can_attack_from(board, row, col, perspective):
            opp_threatened += 1

    return float(opp_threatened - my_threatened)


def _is_occupied(cell: str) -> bool:
    return cell in ("B", "W")


def _forward_blocked(board: Board, row: int, col: int, player: Player) -> bool:
    next_row = row + player.direction
    if not (0 <= next_row < board.rows):
        return True
    if _is_occupied(board.grid[next_row][col]):
        return True
    for delta_col in (-1, 1):
        next_col = col + delta_col
        if 0 <= next_col < board.cols and not _is_occupied(board.grid[next_row][next_col]):
            return False
    return True


def bottleneck_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_blocks = 0
    opp_blocks = 0

    for row, col in _piece_positions(board, perspective.symbol):
        opp_row = row - opponent.direction
        if 0 <= opp_row < board.rows and board.grid[opp_row][col] == opponent.symbol:
            if _forward_blocked(board, opp_row, col, opponent):
                my_blocks += 1

    for row, col in _piece_positions(board, opponent.symbol):
        my_row = row - perspective.direction
        if 0 <= my_row < board.rows and board.grid[my_row][col] == perspective.symbol:
            if _forward_blocked(board, my_row, col, perspective):
                opp_blocks += 1

    return float(my_blocks - opp_blocks)


def chain_support_heuristic(board: Board, perspective: Player) -> float:
    my_chains = 0
    opp_chains = 0
    opponent = get_opponent(perspective)

    for row, col in _piece_positions(board, perspective.symbol):
        support_row = row - perspective.direction
        if not (0 <= support_row < board.rows):
            continue
        for support_col in (col - 1, col + 1):
            if 0 <= support_col < board.cols:
                if board.grid[support_row][support_col] == perspective.symbol:
                    my_chains += 1
                    break

    for row, col in _piece_positions(board, opponent.symbol):
        support_row = row - opponent.direction
        if not (0 <= support_row < board.rows):
            continue
        for support_col in (col - 1, col + 1):
            if 0 <= support_col < board.cols:
                if board.grid[support_row][support_col] == opponent.symbol:
                    opp_chains += 1
                    break

    return float(my_chains - opp_chains)


def _opponent_attack_targets(board: Board, attacker_row: int, attacker_col: int, attacker: Player) -> List[tuple[int, int]]:
    targets: List[tuple[int, int]] = []
    target_row = attacker_row + attacker.direction
    if not (0 <= target_row < board.rows):
        return targets
    for target_col in (attacker_col - 1, attacker_col + 1):
        if 0 <= target_col < board.cols:
            if board.grid[target_row][target_col] == attacker.opponent_symbol():
                targets.append((target_row, target_col))
    return targets


def fork_risk_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_forked = 0
    opp_forked = 0

    for row, col in _piece_positions(board, opponent.symbol):
        targets = _opponent_attack_targets(board, row, col, opponent)
        if len(targets) >= 2:
            my_forked += len(targets) - 1

    for row, col in _piece_positions(board, perspective.symbol):
        targets = _opponent_attack_targets(board, row, col, perspective)
        if len(targets) >= 2:
            opp_forked += len(targets) - 1

    return float(opp_forked - my_forked)


def blocked_trap_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_trapped = 0
    opp_trapped = 0

    for row, col in _piece_positions(board, perspective.symbol):
        if _forward_blocked(board, row, col, perspective):
            my_trapped += 1

    for row, col in _piece_positions(board, opponent.symbol):
        if _forward_blocked(board, row, col, opponent):
            opp_trapped += 1

    return float(opp_trapped - my_trapped)


def isolated_lead_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_penalty = 0.0
    opp_penalty = 0.0

    for symbol, player, penalty in (
        (perspective.symbol, perspective, "my"),
        (opponent.symbol, opponent, "opp"),
    ):
        rows = [row for row, _ in _piece_positions(board, symbol)]
        if not rows:
            continue
        army_front = max(rows) if player.direction > 0 else min(rows)
        for row, col in _piece_positions(board, symbol):
            lead_distance = abs(row - army_front)
            if lead_distance >= 2 and not _is_protected(board, row, col, player):
                if penalty == "my":
                    my_penalty += lead_distance
                else:
                    opp_penalty += lead_distance

    return float(opp_penalty - my_penalty)


def suicidal_exposure_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_exposed = 0
    opp_exposed = 0

    for row, col in _piece_positions(board, perspective.symbol):
        if _can_attack_from(board, row, col, opponent) and not _is_protected(board, row, col, perspective):
            if not _has_recapture_support(board, row, col, perspective, opponent):
                my_exposed += 1

    for row, col in _piece_positions(board, opponent.symbol):
        if _can_attack_from(board, row, col, perspective) and not _is_protected(board, row, col, opponent):
            if not _has_recapture_support(board, row, col, opponent, perspective):
                opp_exposed += 1

    return float(opp_exposed - my_exposed)


def harmonious_development_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_rows = [row for row, _ in _piece_positions(board, perspective.symbol)]
    opp_rows = [row for row, _ in _piece_positions(board, opponent.symbol)]
    if len(my_rows) < 2:
        my_spread = 0
    else:
        my_spread = max(my_rows) - min(my_rows)
    if len(opp_rows) < 2:
        opp_spread = 0
    else:
        opp_spread = max(opp_rows) - min(opp_rows)
    return float(opp_spread - my_spread)


def wing_vacancy_heuristic(board: Board, perspective: Player) -> float:
    """Puste tylko skrajne kolumny; kara za 2+ dziury między pionami na linii tylnej."""
    if board.cols <= 3:
        return 0.0
    from ai.strategy import count_internal_pawn_gaps_on_row, home_rank_rows

    edge = edge_columns(board)
    opponent = get_opponent(perspective)

    def edge_penalty(symbol: str) -> float:
        penalty = 0.0
        for _row, col in _piece_positions(board, symbol):
            if col in edge:
                penalty += 5.0
        for wing_col in edge:
            if all(board.grid[row][wing_col] != symbol for row in range(board.rows)):
                penalty -= 2.0
        for row in home_rank_rows(board, perspective):
            gaps = count_internal_pawn_gaps_on_row(board, row, symbol)
            if gaps >= 2:
                penalty -= 6.0 * gaps
            elif gaps == 1:
                penalty -= 1.5
        return penalty

    return float(edge_penalty(opponent.symbol) - edge_penalty(perspective.symbol))


def flank_guard_heuristic(board: Board, perspective: Player) -> float:
    """Figury na kolumnach 1 i przedostatniej — blokada łatwego przejścia."""
    guard = flank_guard_columns(board)
    if not guard:
        return 0.0
    opponent = get_opponent(perspective)
    my_score = 0.0
    opp_score = 0.0

    for col in guard:
        my_on_col = sum(
            1 for row, c in _piece_positions(board, perspective.symbol) if c == col
        )
        opp_on_col = sum(
            1 for row, c in _piece_positions(board, opponent.symbol) if c == col
        )
        my_score += my_on_col * 2.5
        opp_score += opp_on_col * 2.5
        if my_on_col == 0:
            my_score -= 3.0
        if opp_on_col == 0:
            opp_score -= 3.0

    return float(my_score - opp_score)


def defend_our_flanks_heuristic(board: Board, perspective: Player) -> float:
    """Kara za odsłonięte nasze skrzydło; premia gdy blokujemy autostradę przeciwnika."""
    edge = edge_columns(board)
    guard = flank_guard_columns(board)
    opponent = get_opponent(perspective)
    my_score = 0.0
    opp_score = 0.0

    for side, cols in (("left", [0, 1]), ("right", [board.cols - 2, board.cols - 1])):
        if board.cols < 4:
            continue
        edge_col = cols[0] if side == "left" else cols[-1]
        open_edge = sum(
            1 for row in range(board.rows) if board.grid[row][edge_col] in {"_", "o"}
        )
        my_guard = sum(1 for _r, c in _piece_positions(board, perspective.symbol) if c in guard)
        opp_threat = sum(1 for _r, c in _piece_positions(board, opponent.symbol) if c in cols)

        if open_edge >= board.rows // 2:
            my_score -= open_edge * 1.5
        my_score += my_guard * 0.5
        opp_score += opp_threat * 0.4

    return float(my_score - opp_score)


def weak_flank_attack_heuristic(board: Board, perspective: Player) -> float:
    """Nacisk na słabsze skrzydło przeciwnika, o ile nie przegrywamy wyścigu do mety."""
    if opponent_wins_race_if_ignored(board, perspective):
        return goal_pressure_heuristic(board, perspective) * 1.5

    weak_side = weaker_opponent_flank(board, perspective)
    opponent = get_opponent(perspective)
    my_score = 0.0
    opp_score = 0.0

    if weak_side == "left":
        target_cols = {0, 1} if board.cols >= 2 else {0}
    else:
        target_cols = {board.cols - 2, board.cols - 1}

    for row, col in _piece_positions(board, perspective.symbol):
        if col in target_cols:
            my_score += board.rows - abs(row - perspective.goal_row)

    for row, col in _piece_positions(board, opponent.symbol):
        if col in target_cols:
            opp_score += board.rows - abs(row - opponent.goal_row)

    left_open = flank_lane_strength(board, perspective, "left")
    right_open = flank_lane_strength(board, perspective, "right")
    if weak_side == "left":
        my_score += max(0.0, right_open - left_open) * 2.0
    else:
        my_score += max(0.0, left_open - right_open) * 2.0

    return float(my_score - opp_score)


def center_diagonal_setup_heuristic(board: Board, perspective: Player) -> float:
    """Piony w centrum ustawione po skosie (jak 2,2 -> 3,3 w notacji 1-indeksowej)."""
    center_cols = set(_center_columns(board))
    opponent = get_opponent(perspective)
    my_score = 0.0
    opp_score = 0.0

    for row, col in _piece_positions(board, perspective.symbol):
        if col not in center_cols:
            continue
        my_score += 2.0
        if _is_protected(board, row, col, perspective):
            my_score += 1.5
        guard_row = row - perspective.direction
        for guard_col in (col - 1, col + 1):
            if 0 <= guard_row < board.rows and 0 <= guard_col < board.cols:
                if board.grid[guard_row][guard_col] == perspective.symbol:
                    if abs(guard_col - col) == 1:
                        my_score += 2.5

    for row, col in _piece_positions(board, opponent.symbol):
        if col not in center_cols:
            continue
        opp_score += 2.0
        if _is_protected(board, row, col, opponent):
            opp_score += 1.5

    return float(my_score - opp_score)


def wing_discouragement_heuristic(board: Board, perspective: Player) -> float:
    return wing_vacancy_heuristic(board, perspective)


def center_advancement_heuristic(board: Board, perspective: Player) -> float:
    center_cols = set(_center_columns(board))
    opponent = get_opponent(perspective)
    my_score = 0
    opp_score = 0
    for row, col in _piece_positions(board, perspective.symbol):
        if col in center_cols:
            my_score += board.rows - abs(row - perspective.goal_row)
    for row, col in _piece_positions(board, opponent.symbol):
        if col in center_cols:
            opp_score += board.rows - abs(row - opponent.goal_row)
    return float(my_score - opp_score)


def army_mobilization_heuristic(board: Board, perspective: Player) -> float:
    my_ratio = army_mobilization_ratio(board, perspective)
    opponent = get_opponent(perspective)
    opp_ratio = army_mobilization_ratio(board, opponent)
    return float(my_ratio - opp_ratio) * board.rows


def capture_options_heuristic(board: Board, perspective: Player) -> float:
    opponent = get_opponent(perspective)
    my_captures = count_capture_moves(board, perspective)
    opp_captures = count_capture_moves(board, opponent)
    return float(my_captures - opp_captures)


def active_pieces_heuristic(board: Board, perspective: Player) -> float:
    my_moves = board.get_legal_moves(perspective)
    opp_moves = board.get_legal_moves(get_opponent(perspective))
    my_active = len({(m.from_row, m.from_col) for m in my_moves})
    opp_active = len({(m.from_row, m.from_col) for m in opp_moves})
    return float(my_active - opp_active)


def _has_recapture_support(
    board: Board,
    row: int,
    col: int,
    victim: Player,
    attacker: Player,
) -> bool:
    for attacker_row, attacker_col in _piece_positions(board, attacker.symbol):
        targets = _opponent_attack_targets(board, attacker_row, attacker_col, attacker)
        if (row, col) not in targets:
            continue
        recapture_row = attacker_row - victim.direction
        for recapture_col in (attacker_col - 1, attacker_col + 1):
            if 0 <= recapture_row < board.rows and 0 <= recapture_col < board.cols:
                if board.grid[recapture_row][recapture_col] == victim.symbol:
                    if (recapture_row, recapture_col) != (row, col):
                        return True
    return False


def breakthrough_heuristic(board: Board, perspective: Player) -> float:
    phase = _game_phase(board, perspective)
    weights = _phase_weights(phase)

    if has_capture_moves(board, perspective):
        weights["capture_options"] *= 4.0
        weights["attack_threats"] *= 2.5
        weights["material"] *= 2.5
        weights["suicidal_exposure"] *= 0.35
        weights["wing_vacancy"] *= 0.15
        weights["center_diagonal_setup"] *= 0.1
        weights["center_control"] *= 0.25
        weights["harmonious_development"] *= 0.4

    if opponent_wins_race_if_ignored(board, perspective):
        weights["weak_flank_attack"] *= 0.25
        weights["goal_pressure"] *= 2.5
        weights["advancement"] *= 1.4

    components = {
        "advancement": advancement_heuristic(board, perspective),
        "mobility": mobility_heuristic(board, perspective),
        "goal_pressure": goal_pressure_heuristic(board, perspective),
        "safety": safety_heuristic(board, perspective),
        "center_control": center_control_heuristic(board, perspective),
        "center_advancement": center_advancement_heuristic(board, perspective),
        "attack_threats": attack_threats_heuristic(board, perspective),
        "bottlenecks": bottleneck_heuristic(board, perspective),
        "material": material_heuristic(board, perspective),
        "chain_support": chain_support_heuristic(board, perspective),
        "fork_risk": fork_risk_heuristic(board, perspective),
        "blocked_trap": blocked_trap_heuristic(board, perspective),
        "isolated_lead": isolated_lead_heuristic(board, perspective),
        "suicidal_exposure": suicidal_exposure_heuristic(board, perspective),
        "harmonious_development": harmonious_development_heuristic(board, perspective),
        "wing_vacancy": wing_vacancy_heuristic(board, perspective),
        "center_diagonal_setup": center_diagonal_setup_heuristic(board, perspective),
        "army_mobilization": army_mobilization_heuristic(board, perspective),
        "active_pieces": active_pieces_heuristic(board, perspective),
        "capture_options": capture_options_heuristic(board, perspective),
        "flank_guard": flank_guard_heuristic(board, perspective),
        "weak_flank_attack": weak_flank_attack_heuristic(board, perspective),
        "defend_our_flanks": defend_our_flanks_heuristic(board, perspective),
    }

    score = 0.0
    for name, value in components.items():
        score += weights.get(name, 0.0) * value

    return score


# Szybka wersja do self-play — te same genomy (scales), mniej składników na liściu.
TRAINING_COMPONENTS: tuple[str, ...] = (
    "advancement",
    "goal_pressure",
    "material",
    "mobility",
    "safety",
    "attack_threats",
    "capture_options",
    "center_control",
)


def breakthrough_training_heuristic(board: Board, perspective: Player) -> float:
    from ai.eval_context import scaled_base_weights

    weights = scaled_base_weights()
    score = 0.0
    for name in TRAINING_COMPONENTS:
        fn = HEURISTIC_COMPONENTS[name]
        score += weights.get(name, EVAL_WEIGHTS[name]) * fn(board, perspective)
    return score


Heuristic = Callable[[Board, Player], float]
HEURISTIC_COMPONENTS: Dict[str, Heuristic] = {
    "material": material_heuristic,
    "advancement": advancement_heuristic,
    "mobility": mobility_heuristic,
    "goal_pressure": goal_pressure_heuristic,
    "center_control": center_control_heuristic,
    "threatened_pieces": threatened_pieces_heuristic,
    "safety": safety_heuristic,
    "attack_threats": attack_threats_heuristic,
    "bottlenecks": bottleneck_heuristic,
    "chain_support": chain_support_heuristic,
    "fork_risk": fork_risk_heuristic,
    "blocked_trap": blocked_trap_heuristic,
    "isolated_lead": isolated_lead_heuristic,
    "suicidal_exposure": suicidal_exposure_heuristic,
    "harmonious_development": harmonious_development_heuristic,
    "wing_vacancy": wing_vacancy_heuristic,
    "wing_discouragement": wing_discouragement_heuristic,
    "center_diagonal_setup": center_diagonal_setup_heuristic,
    "center_advancement": center_advancement_heuristic,
    "army_mobilization": army_mobilization_heuristic,
    "active_pieces": active_pieces_heuristic,
    "capture_options": capture_options_heuristic,
    "flank_guard": flank_guard_heuristic,
    "weak_flank_attack": weak_flank_attack_heuristic,
    "defend_our_flanks": defend_our_flanks_heuristic,
}

HEURISTICS: Dict[str, Heuristic] = {
    **HEURISTIC_COMPONENTS,
    "breakthrough": breakthrough_heuristic,
    "breakthrough-train": breakthrough_training_heuristic,
}
