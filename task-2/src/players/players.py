from dataclasses import dataclass


@dataclass(frozen=True)
class Player:
    name: str
    symbol: str
    direction: int
    board_rows: int

    @property
    def goal_row(self) -> int:
        if self.symbol == "B":
            return self.board_rows - 1
        return 0

    def opponent_symbol(self) -> str:
        return "W" if self.symbol == "B" else "B"


class FirstPlayer(Player):
    def __init__(self, board_rows: int = 8) -> None:
        super().__init__(
            name="Player 1", symbol="B", direction=1, board_rows=board_rows
        )


class SecondPlayer(Player):
    def __init__(self, board_rows: int = 8) -> None:
        super().__init__(
            name="Player 2", symbol="W", direction=-1, board_rows=board_rows
        )


class TournamentWhite(Player):
    """Tournament player id 0 — B at the bottom, advances toward row 0."""

    def __init__(self, board_rows: int = 8) -> None:
        super().__init__(
            name="White (B)", symbol="B", direction=-1, board_rows=board_rows
        )

    @property
    def goal_row(self) -> int:
        return 0


class TournamentBlack(Player):
    """Tournament player id 1 — W at the top, advances toward the last row."""

    def __init__(self, board_rows: int = 8) -> None:
        super().__init__(
            name="Black (W)", symbol="W", direction=1, board_rows=board_rows
        )

    @property
    def goal_row(self) -> int:
        return self.board_rows - 1


def get_opponent(player: Player) -> Player:
    if isinstance(player, TournamentWhite):
        return TournamentBlack(player.board_rows)
    if isinstance(player, TournamentBlack):
        return TournamentWhite(player.board_rows)
    if player.symbol == "B":
        return Player(
            name="Player 2",
            symbol="W",
            direction=-1,
            board_rows=player.board_rows,
        )
    return Player(
        name="Player 1", symbol="B", direction=1, board_rows=player.board_rows
    )
