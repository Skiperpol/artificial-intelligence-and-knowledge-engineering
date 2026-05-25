from __future__ import annotations

import json
import random
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from ai.heuristics import EVAL_WEIGHTS

WEIGHT_KEYS: List[str] = list(EVAL_WEIGHTS.keys())
DEFAULT_GENOME_FILENAME = "best_genome_selfplay.json"


@dataclass
class BotGenome:
    genome_id: int
    scales: Dict[str, float] = field(default_factory=dict)
    depth: int = 3

    def __post_init__(self) -> None:
        for key in WEIGHT_KEYS:
            self.scales.setdefault(key, 1.0)
        self.depth = max(2, min(4, int(self.depth)))

    @classmethod
    def random(cls, genome_id: int, rng: random.Random) -> BotGenome:
        scales = {key: rng.uniform(0.35, 2.8) for key in WEIGHT_KEYS}
        depth = rng.choice([2, 2, 2, 3, 3, 4])
        return cls(genome_id=genome_id, scales=scales, depth=depth)

    def mutate(self, rng: random.Random, mutation_rate: float = 0.28) -> BotGenome:
        child = deepcopy(self)
        for key in WEIGHT_KEYS:
            if rng.random() < mutation_rate:
                child.scales[key] *= rng.uniform(0.72, 1.38)
                child.scales[key] = max(0.15, min(5.0, child.scales[key]))
        if rng.random() < 0.18:
            child.depth = rng.choice([2, 3, 4])
        return child

    def to_dict(self) -> dict:
        return {
            "genome_id": self.genome_id,
            "depth": self.depth,
            "scales": dict(self.scales),
        }

    @classmethod
    def from_dict(cls, data: dict) -> BotGenome:
        return cls(
            genome_id=int(data["genome_id"]),
            scales={k: float(v) for k, v in data["scales"].items()},
            depth=int(data.get("depth", 3)),
        )


def make_population(
    size: int,
    rng: random.Random,
    start_id: int = 0,
    *,
    fixed_depth: int | None = None,
) -> List[BotGenome]:
    population: List[BotGenome] = []
    for index in range(size):
        genome = BotGenome.random(start_id + index, rng)
        if fixed_depth is not None:
            genome.depth = fixed_depth
        population.append(genome)
    return population


def breed_next_generation(
    elites: List[BotGenome],
    population_size: int,
    rng: random.Random,
    start_id: int,
    *,
    fixed_depth: int | None = None,
) -> List[BotGenome]:
    if not elites:
        return make_population(population_size, rng, start_id)

    children: List[BotGenome] = []
    slots_per_parent = population_size // len(elites)
    remainder = population_size - slots_per_parent * len(elites)
    next_id = start_id

    for index, parent in enumerate(elites):
        count = slots_per_parent + (1 if index < remainder else 0)
        for _ in range(count):
            child = parent.mutate(rng)
            child.genome_id = next_id
            if fixed_depth is not None:
                child.depth = fixed_depth
            next_id += 1
            children.append(child)

    while len(children) < population_size:
        parent = rng.choice(elites)
        child = parent.mutate(rng)
        child.genome_id = next_id
        if fixed_depth is not None:
            child.depth = fixed_depth
        next_id += 1
        children.append(child)

    return children[:population_size]


def default_genome_path() -> Path:
    """Plik z self-play obok katalogu src/ (obok tournament_main.py w Dockerze)."""
    return Path(__file__).resolve().parent.parent / DEFAULT_GENOME_FILENAME


def load_genome_file(path: str | Path | None = None) -> BotGenome | None:
    """Wczytaj genom z JSON. path=None → domyślny best_genome_selfplay.json."""
    candidate = Path(path) if path is not None else default_genome_path()
    if not candidate.is_file():
        return None
    return BotGenome.from_dict(
        json.loads(candidate.read_text(encoding="utf-8"))
    )


def save_genome(path: str, genome: BotGenome) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(genome.to_dict(), handle, indent=2)
