from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Player:
    name: str
    symbol: str
    direction: int
    goal_row: int

    def opponent_symbol(self) -> str:
        return "W" if self.symbol == "B" else "B"

class FirstPlayer(Player):
    def __init__(self) -> None:
        super().__init__(name="Player 1", symbol="B", direction=1, goal_row=7)


class SecondPlayer(Player):
    def __init__(self) -> None:
        super().__init__(name="Player 2", symbol="W", direction=-1, goal_row=0)
