"""Kontekst genomu bota (ewolucja wag) — izolowany per wątek / proces."""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from ai.genome import BotGenome

_GENOME: ContextVar[BotGenome | None] = ContextVar("bot_genome", default=None)


def set_active_genome(genome: BotGenome | None):
    return _GENOME.set(genome)


def reset_active_genome(token) -> None:
    _GENOME.reset(token)


def get_active_genome() -> BotGenome | None:
    return _GENOME.get()


def scaled_base_weights() -> Dict[str, float]:
    from ai.heuristics import EVAL_WEIGHTS

    genome = _GENOME.get()
    if genome is None:
        return dict(EVAL_WEIGHTS)
    return {key: EVAL_WEIGHTS[key] * genome.scales.get(key, 1.0) for key in EVAL_WEIGHTS}
