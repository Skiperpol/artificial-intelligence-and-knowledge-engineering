from dataclasses import dataclass
from math import inf
from time import perf_counter
from typing import Callable, Dict, List, Optional

from engine.board import Board, Move
from players.players import Player, get_opponent
from ai.heuristics import HEURISTICS
from ai.strategy import order_moves
from ai.tactics import (
    apply_tactical_constraints,
    filter_safe_root_moves,
    find_best_capture,
    find_immediate_win,
    is_capture_or_goal_move,
    prioritize_tactical_moves,
)
from ai.zobrist import hash_board

Heuristic = Callable[[Board, Player], float]

EXACT = 0
LOWER_BOUND = 1
UPPER_BOUND = 2

QUIESCENCE_MAX_DEPTH = 8
MATE_SCORE = 10_000.0


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
    depth_reached: int = 0


def copy_board(board: Board) -> Board:
    new_grid = []
    for row in board.grid:
        new_grid.append(row[:])
    return Board(new_grid)


def _past_deadline(deadline: float | None, counters: Dict[str, int]) -> bool:
    if deadline is None:
        return False
    if counters["visited_nodes"] & 127 != 0:
        return False
    return perf_counter() >= deadline


def _evaluate_terminal(board: Board, root_player: Player, current_player: Player) -> Optional[float]:
    opponent = get_opponent(current_player)
    if board.has_player_won(root_player):
        return MATE_SCORE
    if board.has_player_won(get_opponent(root_player)):
        return -MATE_SCORE
    if not board.get_legal_moves(current_player):
        if current_player.symbol == root_player.symbol:
            return -MATE_SCORE
        return MATE_SCORE
    if not board.get_legal_moves(opponent):
        if current_player.symbol == root_player.symbol:
            return MATE_SCORE
        return -MATE_SCORE
    return None


def _quiescence(
    board: Board,
    q_depth: int,
    current_player: Player,
    root_player: Player,
    heuristic: Heuristic,
    heuristic_name: str,
    alpha: float,
    beta: float,
    counters: Dict[str, int],
    deadline: float | None = None,
) -> float:
    counters["visited_nodes"] += 1
    if _past_deadline(deadline, counters):
        return heuristic(board, root_player)

    terminal_score = _evaluate_terminal(board, root_player, current_player)
    if terminal_score is not None:
        return terminal_score

    if q_depth <= 0:
        return heuristic(board, root_player)

    legal_moves = board.get_legal_moves(current_player)
    tactical = [
        move
        for move in legal_moves
        if is_capture_or_goal_move(board, move, current_player)
    ]
    if not tactical:
        return heuristic(board, root_player)

    ordered = order_moves(
        board,
        prioritize_tactical_moves(tactical, board=board, player=current_player),
        current_player,
        heuristic_name=heuristic_name,
    )
    is_maximizing = current_player.symbol == root_player.symbol
    next_player = get_opponent(current_player)

    if is_maximizing:
        best_value = -inf
    else:
        best_value = inf

    for move in ordered:
        new_board = copy_board(board)
        new_board.apply_move(move, current_player)
        value = _quiescence(
            new_board,
            q_depth - 1,
            next_player,
            root_player,
            heuristic,
            heuristic_name,
            alpha,
            beta,
            counters,
            deadline,
        )
        if is_maximizing:
            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
        else:
            best_value = min(best_value, value)
            beta = min(beta, best_value)
        if beta <= alpha:
            break
        if _past_deadline(deadline, counters):
            break

    return best_value


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
    use_quiescence: bool,
    counters: Dict[str, int],
    tt: TranspositionTable,
    deadline: float | None = None,
) -> float:
    counters["visited_nodes"] += 1
    if _past_deadline(deadline, counters):
        return heuristic(board, root_player)

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
        if use_quiescence:
            return _quiescence(
                board,
                QUIESCENCE_MAX_DEPTH,
                current_player,
                root_player,
                heuristic,
                heuristic_name,
                alpha,
                beta,
                counters,
                deadline,
            )
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
            use_quiescence,
            counters,
            tt,
            deadline,
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
        if _past_deadline(deadline, counters):
            break

    if alpha < best_value < beta:
        flag = EXACT

    if use_transposition and tt_key is not None:
        tt.store(tt_key, depth, best_value, flag)

    return best_value


def _search_at_depth(
    board: Board,
    player: Player,
    depth: int,
    heuristic: Heuristic,
    heuristic_name: str,
    use_alpha_beta: bool,
    use_transposition: bool,
    use_quiescence: bool,
    use_tactical_filter: bool,
    tt: TranspositionTable,
    counters: Dict[str, int],
    deadline: float | None = None,
) -> SearchResult:
    start = perf_counter()
    legal_moves = board.get_legal_moves(player)
    if not legal_moves:
        return SearchResult(None, -MATE_SCORE, 1, 0.0, depth)

    instant_win = find_immediate_win(board, player)
    if instant_win is not None:
        return SearchResult(instant_win, MATE_SCORE, 1, 0.0, depth)

    if use_tactical_filter:
        legal_moves = apply_tactical_constraints(board, player, legal_moves)
    else:
        legal_moves = filter_safe_root_moves(board, player, legal_moves)
    legal_moves = order_moves(board, legal_moves, player, heuristic_name=heuristic_name)
    legal_moves = prioritize_tactical_moves(
        legal_moves, board=board, player=player
    )

    best_score = -inf
    best_move: Optional[Move] = None
    opponent = get_opponent(player)

    for move in legal_moves:
        if deadline is not None and perf_counter() >= deadline:
            break
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
            use_quiescence=use_quiescence,
            counters=counters,
            tt=tt,
            deadline=deadline,
        )
        if score > best_score:
            best_score = score
            best_move = move

    if best_move is None and legal_moves:
        best_move = legal_moves[0]
        best_score = heuristic(board, player)

    elapsed = perf_counter() - start
    return SearchResult(
        best_move,
        best_score,
        counters["visited_nodes"],
        elapsed,
        depth,
    )


def choose_best_move(
    board: Board,
    player: Player,
    depth: int,
    heuristic_name: str,
    use_alpha_beta: bool = True,
    use_transposition: bool = True,
    use_quiescence: bool = False,
    use_tactical_filter: bool = False,
) -> SearchResult:
    heuristic = HEURISTICS.get(heuristic_name)
    if heuristic is None:
        raise ValueError(f"Unknown heuristic: {heuristic_name}")

    counters: Dict[str, int] = {"visited_nodes": 0, "tt_hits": 0}
    tt = TranspositionTable()
    return _search_at_depth(
        board,
        player,
        depth,
        heuristic,
        heuristic_name,
        use_alpha_beta,
        use_transposition,
        use_quiescence,
        use_tactical_filter,
        tt,
        counters,
    )


def choose_best_move_timed(
    board: Board,
    player: Player,
    heuristic_name: str,
    time_limit_s: float,
    max_depth: int = 6,
    min_depth: int = 2,
    min_remaining_to_start_s: float = 0.2,
    use_alpha_beta: bool = True,
    use_transposition: bool = True,
    use_quiescence: bool = True,
    use_tactical_filter: bool = True,
) -> SearchResult:
    heuristic = HEURISTICS.get(heuristic_name)
    if heuristic is None:
        raise ValueError(f"Unknown heuristic: {heuristic_name}")

    start = perf_counter()
    deadline = start + time_limit_s
    counters: Dict[str, int] = {"visited_nodes": 0, "tt_hits": 0}
    tt = TranspositionTable()

    best_result = SearchResult(None, -MATE_SCORE, 0, 0.0, 0)
    legal_fallback = board.get_legal_moves(player)
    if legal_fallback:
        best_result = SearchResult(
            legal_fallback[0], 0.0, 0, 0.0, 0
        )

    for depth in range(min_depth, max_depth + 1):
        if perf_counter() >= deadline - min_remaining_to_start_s:
            break

        result = _search_at_depth(
            board,
            player,
            depth,
            heuristic,
            heuristic_name,
            use_alpha_beta,
            use_transposition,
            use_quiescence,
            use_tactical_filter,
            tt,
            counters,
            deadline=deadline,
        )
        if result.best_move is not None:
            best_result = SearchResult(
                result.best_move,
                result.score,
                counters["visited_nodes"],
                perf_counter() - start,
                result.depth_reached,
            )

    if best_result.best_move is None:
        legal = apply_tactical_constraints(board, player, board.get_legal_moves(player))
        if legal:
            best_result = SearchResult(
                legal[0],
                0.0,
                counters["visited_nodes"],
                perf_counter() - start,
                0,
            )

    return best_result
