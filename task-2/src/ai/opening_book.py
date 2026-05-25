"""Książka debiutowa: skrzydła 0/7 puste, figury na 1 i przedostatniej, wejście w centrum."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from engine.board import Board, Move
from players.players import Player, TournamentBlack, TournamentWhite, get_opponent
from ai.zobrist import hash_board

BookKey = Tuple[int, str]
_OPENING_BOOK: Dict[BookKey, Move] = {}


def _add(book: Dict[BookKey, Move], board: Board, player: Player, move: Move) -> None:
    key = (hash_board(board, player), player.symbol)
    book[key] = move


def _play(board: Board, player: Player, move: Move) -> None:
    board.apply_move(move, player)


def _build_standard_8x8_book() -> Dict[BookKey, Move]:
    book: Dict[BookKey, Move] = {}
    board = Board.tournament_default(8, 8)
    white = TournamentWhite(8)
    black = TournamentBlack(8)

    def turn(player: Player, move: Move) -> None:
        _add(book, board, player, move)
        _play(board, player, move)

    # B: najpierw lewe skrzydło (1 dziura na skraju), centrum, dopiero prawe skrzydło.
    b_line: List[Move] = [
        Move(6, 0, 5, 1, False),
        Move(5, 1, 4, 2, False),
        Move(6, 2, 5, 3, False),
        Move(7, 1, 6, 2, False),
        Move(5, 3, 4, 4, False),
        Move(6, 7, 5, 6, False),
        Move(7, 6, 6, 5, False),
        Move(5, 4, 4, 5, False),
    ]

    # W: to samo — jedno skrzydło, potem środek, drugie skrzydło później.
    w_line: List[Move] = [
        Move(1, 0, 2, 1, False),
        Move(2, 1, 3, 2, False),
        Move(1, 2, 2, 3, False),
        Move(0, 1, 1, 2, False),
        Move(2, 3, 3, 4, False),
        Move(1, 7, 2, 6, False),
        Move(0, 6, 1, 5, False),
        Move(2, 4, 3, 5, False),
    ]

    current = white
    b_index = 0
    w_index = 0
    for ply in range(16):
        if current.symbol == "B" and b_index < len(b_line):
            move = b_line[b_index]
            if move in [m for m in board.get_legal_moves(current)]:
                turn(current, move)
                b_index += 1
            else:
                break
        elif current.symbol == "W" and w_index < len(w_line):
            move = w_line[w_index]
            if move in board.get_legal_moves(current):
                turn(current, move)
                w_index += 1
            else:
                break
        else:
            break
        current = get_opponent(current)

    return book


def _ensure_book(board: Board) -> None:
    global _OPENING_BOOK
    if board.rows == 8 and board.cols == 8 and not _OPENING_BOOK:
        _OPENING_BOOK = _build_standard_8x8_book()


def lookup_opening_move(board: Board, player: Player) -> Optional[Move]:
    _ensure_book(board)
    key = (hash_board(board, player), player.symbol)
    move = _OPENING_BOOK.get(key)
    if move is None:
        return None
    legal = board.get_legal_moves(player)
    if move in legal:
        return move
    return None
