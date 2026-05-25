#!/usr/bin/env python3
"""Lokalny serwer: plansza HTML + silnik turniejowy (choose_tournament_move)."""

from __future__ import annotations

import json
import sys
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai.eval_context import reset_active_genome, set_active_genome
from ai.genome import load_genome_file
from ai.tournament_search import choose_tournament_move
from engine.board import Board, Move
from players.players import FirstPlayer, Player, SecondPlayer, get_opponent

STATIC = ROOT / "static"
HOST = "127.0.0.1"
PORT = 8765
MOVE_TIME_BUDGET_S = 0.48
MAX_SEARCH_DEPTH = 5

_game: dict[str, Any] | None = None


def _player_for_side(symbol: str, rows: int) -> Player:
    if symbol == "B":
        return FirstPlayer(board_rows=rows)
    return SecondPlayer(board_rows=rows)


def _move_dict(move: Move) -> dict[str, Any]:
    return {
        "from_row": move.from_row,
        "from_col": move.from_col,
        "to_row": move.to_row,
        "to_col": move.to_col,
        "is_capture": move.is_capture,
    }


def _board_payload(board: Board) -> list[list[str]]:
    out: list[list[str]] = []
    for row in board.grid:
        out.append([cell if cell != "o" else "_" for cell in row])
    return out


def _last_move_marker(board: Board) -> dict[str, int] | None:
    for row in range(board.rows):
        for col in range(board.cols):
            if board.grid[row][col] == "o":
                return {"from_row": row, "from_col": col}
    return None


def _winner(board: Board, human: Player, bot: Player) -> str | None:
    if board.has_player_won(human):
        return "human"
    if board.has_player_won(bot):
        return "bot"
    return None


def _state_json() -> dict[str, Any]:
    if _game is None:
        return {"active": False}
    board: Board = _game["board"]
    human: Player = _game["human"]
    bot: Player = _game["bot"]
    current: Player = _game["current"]
    winner = _winner(board, human, bot)
    legal = board.get_legal_moves(current) if winner is None else []
    return {
        "active": True,
        "grid": _board_payload(board),
        "rows": board.rows,
        "cols": board.cols,
        "human_symbol": human.symbol,
        "bot_symbol": bot.symbol,
        "turn": "human" if current.symbol == human.symbol else "bot",
        "legal_moves": [_move_dict(m) for m in legal],
        "last_from": _last_move_marker(board),
        "winner": winner,
        "message": _game.get("message", ""),
    }


def _new_game(human_side: str) -> dict[str, Any]:
    global _game
    board = Board(rows=8, cols=8)
    if human_side not in {"B", "W"}:
        human_side = "B"
    human = _player_for_side(human_side, board.rows)
    bot = get_opponent(human)
    bot = Player(name="Bot", symbol=bot.symbol, direction=bot.direction, board_rows=board.rows)
    _game = {
        "board": board,
        "human": human,
        "bot": bot,
        "current": human,
        "genome": load_genome_file(),
        "message": "Nowa gra. Przeciągnij swój pion na dozwolone pole.",
    }
    return _state_json()


def _find_move(board: Board, player: Player, fr: int, fc: int, tr: int, tc: int) -> Move | None:
    for move in board.get_legal_moves(player):
        if (
            move.from_row == fr
            and move.from_col == fc
            and move.to_row == tr
            and move.to_col == tc
        ):
            return move
    return None


def _bot_move(board: Board, bot: Player, genome: Any) -> Move | None:
    token = set_active_genome(genome) if genome is not None else None
    try:
        move, _, _ = choose_tournament_move(
            board,
            bot,
            time_limit_s=MOVE_TIME_BUDGET_S,
            max_depth=MAX_SEARCH_DEPTH,
            heuristic_name="breakthrough",
        )
    finally:
        if token is not None:
            reset_active_genome(token)
    return move


def _apply_human_and_bot(fr: int, fc: int, tr: int, tc: int) -> dict[str, Any]:
    if _game is None:
        raise ValueError("Brak aktywnej gry — wywołaj /api/new.")
    board: Board = _game["board"]
    human: Player = _game["human"]
    bot: Player = _game["bot"]
    current: Player = _game["current"]

    if _winner(board, human, bot) is not None:
        raise ValueError("Gra już się skończyła.")
    if current.symbol != human.symbol:
        raise ValueError("Teraz nie jest Twoja kolej.")

    move = _find_move(board, human, fr, fc, tr, tc)
    if move is None:
        raise ValueError("Niedozwolony ruch.")

    board.apply_move(move, human)
    _game["current"] = bot
    _game["message"] = f"Ty: ({fr},{fc})→({tr},{tc})"

    if _winner(board, human, bot) is not None:
        return _state_json()

    bot_move = _bot_move(board, bot, _game["genome"])
    if bot_move is None:
        _game["message"] = "Bot nie ma ruchu — wygrywasz!"
        return _state_json()

    board.apply_move(bot_move, bot)
    _game["current"] = human
    cap = " (bicie)" if bot_move.is_capture else ""
    _game["message"] = (
        f"Bot: ({bot_move.from_row},{bot_move.from_col})→"
        f"({bot_move.to_row},{bot_move.to_col}){cap}"
    )
    return _state_json()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/state":
            self._send_json(_state_json())
            return
        if path in {"/", "/index.html"}:
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            data = self._read_json()
            if path == "/api/new":
                side = str(data.get("human_side", "B")).upper()
                self._send_json(_new_game(side))
                return
            if path == "/api/move":
                payload = _apply_human_and_bot(
                    int(data["from_row"]),
                    int(data["from_col"]),
                    int(data["to_row"]),
                    int(data["to_col"]),
                )
                self._send_json(payload)
                return
            self._send_json({"error": "unknown endpoint"}, HTTPStatus.NOT_FOUND)
        except (KeyError, TypeError, ValueError) as exc:
            self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
        except json.JSONDecodeError:
            self._send_json({"error": "invalid JSON"}, HTTPStatus.BAD_REQUEST)


def main() -> None:
    if not STATIC.is_dir():
        raise SystemExit(f"Brak katalogu static: {STATIC}")
    genome = load_genome_file()
    genome_note = (
        f"genom: {genome.genome_id}" if genome else "genom: domyślna heurystyka"
    )
    print(f"Breakthrough play-board — http://{HOST}:{PORT}/")
    print(f"Silnik turniejowy ({MOVE_TIME_BUDGET_S}s/ruch, depth≤{MAX_SEARCH_DEPTH}), {genome_note}")
    print("Ctrl+C aby zatrzymać.")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKoniec.")
        server.server_close()


if __name__ == "__main__":
    main()
