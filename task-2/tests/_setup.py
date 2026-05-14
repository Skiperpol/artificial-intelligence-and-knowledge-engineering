import sys
from pathlib import Path

# Importowanie kodu z innego folderu
_SRC = Path(__file__).resolve().parent.parent / "src"
_src_str = str(_SRC)
if _src_str not in sys.path:
    sys.path.insert(0, _src_str)


class Runner:
    def __init__(self) -> None:
        self._passed = 0
        self._failed = 0
        self._failures: list[str] = []

    def section(self, title: str) -> None:
        print()
        print(title)
        print("-" * min(len(title), 72))

    def check(self, ok: bool, message: str) -> None:
        if ok:
            self._passed += 1
        else:
            self._failed += 1
            self._failures.append(message)
            print(f"FAIL: {message}")

    def summary(self, elapsed: float) -> int:
        total = self._passed + self._failed
        print()
        print(
            f"Ran {total} checks in {elapsed:.3f}s: "
            f"{self._passed} passed, {self._failed} failed"
        )
        if self._failures:
            print("\nFailed checks:")
            for msg in self._failures:
                print(f"  - {msg}")
        return 1 if self._failed else 0
