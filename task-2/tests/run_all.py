import time

from _setup import Runner

import test_argmax
import test_brute_force
import test_equivalence_nodes
import test_equivalence_score
import test_puzzles


MODULES = (
    test_equivalence_score,
    test_equivalence_nodes,
    test_puzzles,
    test_brute_force,
    test_argmax,
)


def main() -> int:
    t0 = time.perf_counter()
    runner = Runner()
    for module in MODULES:
        module.run(runner)
    return runner.summary(time.perf_counter() - t0)


if __name__ == "__main__":
    raise SystemExit(main())
