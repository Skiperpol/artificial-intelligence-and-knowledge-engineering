from typing import Callable, Dict, List
from engine.board import BOARD_SIZE, Board
from players.players import Player, get_opponent

def _piece_positions(board: Board, symbol: str) -> List[tuple[int, int]]:
    positions: List[tuple[int, int]] = []
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board.grid[row][col] == symbol:
                positions.append((row, col))
    return positions

def material_heuristic(board: Board, perspective: Player) -> float:
    # [Punkt 2] Strategia 1: przewaga liczby pionów.
    my_count = len(_piece_positions(board, perspective.symbol))
    opp_count = len(_piece_positions(board, perspective.opponent_symbol()))
    return float(my_count - opp_count)


def advancement_heuristic(board: Board, perspective: Player) -> float:
    # [Punkt 2] Strategia 2: jak daleko piony są przesunięte w stronę mety.
    my_total_advancement = 0
    opp_total_advancement = 0

    for row, col in _piece_positions(board, perspective.symbol):
        if perspective.symbol == "B":
            dist_from_start = row
        else:
            dist_from_start = BOARD_SIZE - 1 - row
        
        my_total_advancement += dist_from_start

    opponent_symbol = perspective.opponent_symbol()
    for row, col in _piece_positions(board, opponent_symbol):
        if perspective.symbol == "B":
            opp_dist_from_start = BOARD_SIZE - 1 - row
        else:
            opp_dist_from_start = row
            
        opp_total_advancement += opp_dist_from_start

    return float(my_total_advancement - opp_total_advancement)

def mobility_heuristic(board: Board, perspective: Player) -> float:
    # [Punkt 2] Strategia 3: przewaga liczby legalnych ruchów.
    my_moves = len(board.get_legal_moves(perspective))
    opp_moves = len(board.get_legal_moves(get_opponent(perspective)))
    return float(my_moves - opp_moves)


def goal_pressure_heuristic(board: Board, perspective: Player) -> float:
    # [Punkt 2] Strategia 4: porównanie dystansu najszybszego pionu do celu.
    my_positions = _piece_positions(board, perspective.symbol)
    opp_positions = _piece_positions(board, perspective.opponent_symbol())

    my_closest = BOARD_SIZE
    for row, _ in my_positions:
        if perspective.symbol == "B":
            distance = BOARD_SIZE - 1 - row
        else:
            distance = row
        my_closest = min(my_closest, distance)

    opp_closest = BOARD_SIZE
    for row, _ in opp_positions:
        if perspective.symbol == "B":
            distance = row
        else:
            distance = BOARD_SIZE - 1 - row
        opp_closest = min(opp_closest, distance)

    return float(opp_closest - my_closest)


def center_control_heuristic(board: Board, perspective: Player) -> float:
    # [Punkt 2] Strategia 5: bonus za kontrolę centralnych pól planszy.
    center_low = (BOARD_SIZE // 2) - 1
    center_high = BOARD_SIZE // 2

    my_score = 0
    opp_score = 0

    for row, col in _piece_positions(board, perspective.symbol):
        if center_low <= row <= center_high and center_low <= col <= center_high:
            my_score += 2
        elif center_low <= col <= center_high:
            my_score += 1

    for row, col in _piece_positions(board, perspective.opponent_symbol()):
        if center_low <= row <= center_high and center_low <= col <= center_high:
            opp_score += 2
        elif center_low <= col <= center_high:
            opp_score += 1

    return float(my_score - opp_score)


def threatened_pieces_heuristic(board: Board, perspective: Player) -> float:
    # [Punkt 2] Strategia 6: bilans pionów zagrożonych biciem.
    my_symbol = perspective.symbol
    my_direction = perspective.direction
    opp_symbol = perspective.opponent_symbol()
    opp_direction = -my_direction

    my_threatened = 0
    opp_threatened = 0

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            if board.grid[row][col] == my_symbol:
                attacker_row = row - opp_direction
                for attacker_col in (col - 1, col + 1):
                    if 0 <= attacker_row < BOARD_SIZE and 0 <= attacker_col < BOARD_SIZE:
                        if board.grid[attacker_row][attacker_col] == opp_symbol:
                            my_threatened += 1
                            break
            elif board.grid[row][col] == opp_symbol:
                attacker_row = row - my_direction
                for attacker_col in (col - 1, col + 1):
                    if 0 <= attacker_row < BOARD_SIZE and 0 <= attacker_col < BOARD_SIZE:
                        if board.grid[attacker_row][attacker_col] == my_symbol:
                            opp_threatened += 1
                            break

    return float(opp_threatened - my_threatened)

Heuristic = Callable[[Board, Player], float]
HEURISTICS: Dict[str, Heuristic] = {
    "material": material_heuristic,
    "advancement": advancement_heuristic,
    "mobility": mobility_heuristic,
    "goal_pressure": goal_pressure_heuristic,
    "center_control": center_control_heuristic,
    "threatened_pieces": threatened_pieces_heuristic,
}