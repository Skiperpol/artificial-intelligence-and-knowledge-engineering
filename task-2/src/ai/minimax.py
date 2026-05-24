from dataclasses import dataclass
from math import inf
from time import perf_counter
from typing import Callable, Dict, List, Optional, Tuple

from engine.board import Board, Move
from players.players import Player, get_opponent
from ai.heuristics import HEURISTICS
from ai.strategy import order_moves
from ai.zobrist import hash_board

Heuristic = Callable[[Board, Player], float]

EXACT = 0
LOWER_BOUND = 1
UPPER_BOUND = 2


@dataclass
class _TTEntry:
    depth: int
    value: float
    flag: int


class TranspositionTable:
    def __init__(self, max_entries: int = 200_000) -> None:
        self._store: Dict[int, _TTEntry] = {}
        self._max_entries = max_entries

    def clear(self) -> None:
        self._store.clear()

    def lookup(self, key: int, depth: int, alpha: float, beta: float) -> Optional[float]:
        entry = self._store.get(key)
        if entry is None or entry.depth < depth:
            return None
        if entry.flag == EXACT:
            return entry.value
        if entry.flag == LOWER_BOUND and entry.value >= beta:
            return entry.value
        if entry.flag == UPPER_BOUND and entry.value <= alpha:
            return entry.value
        return None

    def store(self, key: int, depth: int, value: float, flag: int) -> None:
        if len(self._store) >= self._max_entries:
            self._store.clear()
        existing = self._store.get(key)
        if existing is not None and existing.depth > depth:
            return
        self._store[key] = _TTEntry(depth=depth, value=value, flag=flag)


@dataclass
class SearchResult:
    best_move: Optional[Move]
    score: float
    visited_nodes: int
    elapsed_seconds: float


def copy_board(board: Board) -> Board:
    new_grid = []
    for row in board.grid:
        new_grid.append(row[:])
    return Board(new_grid)


def _evaluate_terminal(board: Board, root_player: Player, current_player: Player) -> Optional[float]:
    opponent = get_opponent(current_player)
    if board.has_player_won(root_player):
        return 10_000.0
    if board.has_player_won(get_opponent(root_player)):
        return -10_000.0
    if not board.get_legal_moves(current_player):
        if current_player.symbol == root_player.symbol:
            return -10_000.0
        return 10_000.0
    if not board.get_legal_moves(opponent):
        if current_player.symbol == root_player.symbol:
            return 10_000.0
        return -10_000.0
    return None


def _minimax(
    board: Board,
    depth: int,
    current_player: Player,
    root_player: Player,
    heuristic: Heuristic,
    heuristic_name: str,
    alpha: float,
    beta: float,
    use_alpha_beta: bool,
    use_transposition: bool,
    counters: Dict[str, int],
    tt: TranspositionTable,
) -> float:
    counters["visited_nodes"] += 1

    terminal_score = _evaluate_terminal(board, root_player, current_player)
    if terminal_score is not None:
        return terminal_score

    tt_key: Optional[int] = None
    if use_transposition:
        tt_key = hash_board(board, current_player)
        cached = tt.lookup(tt_key, depth, alpha, beta)
        if cached is not None:
            counters["tt_hits"] += 1
            return cached

    if depth == 0:
        return heuristic(board, root_player)

    legal_moves = order_moves(
        board,
        board.get_legal_moves(current_player),
        current_player,
        heuristic_name=heuristic_name,
    )
    is_maximizing = current_player.symbol == root_player.symbol
    next_player = get_opponent(current_player)

    if is_maximizing:
        best_value = -inf
        flag = UPPER_BOUND
    else:
        best_value = inf
        flag = LOWER_BOUND

    for move in legal_moves:
        new_board = copy_board(board)
        new_board.apply_move(move, current_player)

        evaluation = _minimax(
            new_board,
            depth - 1,
            next_player,
            root_player,
            heuristic,
            heuristic_name,
            alpha,
            beta,
            use_alpha_beta,
            use_transposition,
            counters,
            tt,
        )

        if is_maximizing:
            if evaluation > best_value:
                best_value = evaluation
            alpha = max(alpha, best_value)
            if evaluation >= beta:
                flag = LOWER_BOUND
        else:
            if evaluation < best_value:
                best_value = evaluation
            beta = min(beta, best_value)
            if evaluation <= alpha:
                flag = UPPER_BOUND

        if use_alpha_beta and beta <= alpha:
            break

    if alpha < best_value < beta:
        flag = EXACT

    if use_transposition and tt_key is not None:
        tt.store(tt_key, depth, best_value, flag)

    return best_value


def choose_best_move(
    board: Board,
    player: Player,
    depth: int,
    heuristic_name: str,
    use_alpha_beta: bool = True,
    use_transposition: bool = True,
) -> SearchResult:
    heuristic = HEURISTICS.get(heuristic_name)
    if heuristic is None:
        raise ValueError(f"Unknown heuristic: {heuristic_name}")

    start = perf_counter()
    counters: Dict[str, int] = {"visited_nodes": 0, "tt_hits": 0}
    tt = TranspositionTable()
    legal_moves = order_moves(
        board,
        board.get_legal_moves(player),
        player,
        heuristic_name=heuristic_name,
    )
    if not legal_moves:
        return SearchResult(None, -10_000.0, 1, perf_counter() - start)

    best_score = -inf
    best_move: Optional[Move] = None
    opponent = get_opponent(player)

    for move in legal_moves:
        new_board = copy_board(board)
        new_board.apply_move(move, player)
        score = _minimax(
            new_board,
            depth - 1,
            opponent,
            player,
            heuristic,
            heuristic_name,
            alpha=-inf,
            beta=inf,
            use_alpha_beta=use_alpha_beta,
            use_transposition=use_transposition,
            counters=counters,
            tt=tt,
        )
        if score > best_score:
            best_score = score
            best_move = move

    return SearchResult(best_move, best_score, counters["visited_nodes"], perf_counter() - start)
