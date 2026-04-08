from typing import List
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
    my_count = len(_piece_positions(board, perspective.symbol))
    opp_count = len(_piece_positions(board, perspective.opponent_symbol()))
    return float(my_count - opp_count)


def advancement_heuristic(board: Board, perspective: Player) -> float:
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
    my_moves = len(board.get_legal_moves(perspective))
    opp_moves = len(board.get_legal_moves(get_opponent(perspective)))
    return float(my_moves - opp_moves)
