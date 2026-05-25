# Zadanie 2 — Robot odkurzający (PDDL)

Robot odwiedza wszystkie pokoje i je odkurza. Model **STRIPS** z typowaniem (materiały [IDA LiU — Planning](https://www.ida.liu.se/~heltand/planning/)).

## Pliki

| Plik | Opis |
|------|------|
| `domain.pddl` | Domena `vacuum` — akcje `move`, `clean` |
| `problem.pddl` | Instancja `vacuum-three-rooms` |
| `problem.pddl.soln` | Plan z planera |

## Model logiczny

### Obiekty

- Robot: `robot`
- Pokoje: `pokoj1`, `pokoj2`, `pokoj3`

### Predykaty

| Predykat | Znaczenie |
|----------|-----------|
| `(at ?r - robot ?p - room)` | Robot w pokoju |
| `(dirty ?p - room)` | Pokój brudny |
| `(clean ?p - room)` | Pokój czysty |

### Akcje

**`move`** — robot przechodzi z `?from` do `?to` (dowolna para pokoi).  
Pre: `(at ?r ?from)` → Efekt: robot w `?to`.

**`clean`** — sprzątanie bieżącego pokoju.  
Pre: robot w `?p`, `(dirty ?p)` → Efekt: `(clean ?p)`, usunięcie `(dirty ?p)`.

### Stan początkowy i cel

- **Init:** robot w `pokoj1`, wszystkie pokoje `(dirty …)`.
- **Goal:** `(and (clean pokoj1) (clean pokoj2) (clean pokoj3))`.

## Uruchomienie planera

```bash
cd task-3
.venv/bin/pyperplan Zadanie-2/domain.pddl Zadanie-2/problem.pddl
```

Alternatywnie: [solver.planning.domains](https://solver.planning.domains/) → **lama-first**.

## Wygenerowany plan (5 akcji)

| # | Akcja | Opis |
|---|--------|------|
| 1 | `clean robot pokoj1` | Odkurzenie pokoju startowego |
| 2 | `move robot pokoj1 pokoj3` | Skok do pokoj3 |
| 3 | `clean robot pokoj3` | Odkurzenie pokoj3 |
| 4 | `move robot pokoj3 pokoj2` | Przejazd do pokoj2 |
| 5 | `clean robot pokoj2` | Odkurzenie pokoj2 → cel |

**Wynik planera (Pyperplan, BFS):** długość **5**, 22 rozwinięte węzły, ~0,3 ms.

Inny poprawny plan (np. kolejność pokoj1 → pokoj2 → pokoj3) też ma zwykle **5** kroków.

## Analiza planu

### 1. Poprawność

- `clean` wymaga obecności robota w pokoju i `(dirty ?p)` — nie da się posprzątać zdalnie.
- Po każdym `clean` pokój ma `(clean ?p)` i nie ma `(dirty ?p)`.
- `move` zmienia wyłącznie pozycję robota; nie czyści pokoi automatycznie.
- Po kroku 5 wszystkie trzy `(clean pokoj*)` są prawdziwe — cel spełniony.

### 2. Optymalność długości

- Każdy brudny pokój wymaga **dokładnie jednego** `clean` → minimum **3** akcji `clean`.
- Robot startuje w `pokoj1`; musi **fizycznie być** w `pokoj2` i `pokoj3` → co najmniej **2** przejścia `move`.
- Dolna granica: **3 + 2 = 5** akcji — plan BFS jest **optymalny**.

### 3. Kolejność odwiedzin

Planer wybrał trasę **pokoj1 → pokoj3 → pokoj2** (bez predykatu `connected` każdy `move` jest dozwolony). To równoważne klasycznemu **pokoj1 → pokoj2 → pokoj3** — ta sama długość 5.

### 4. Stany pośrednie

| Po kroku | Robot | Brudne | Czyste |
|----------|-------|--------|--------|
| 0 | pokoj1 | 1,2,3 | — |
| 1 | pokoj1 | 2,3 | pokoj1 |
| 3 | pokoj3 | 2 | pokoj1, pokoj3 |
| 5 | pokoj2 | — | 1,2,3 ✓ |

### 5. STRIPS (wykład)

- **Stan** = zbiór faktów (`at`, `dirty`, `clean`).
- **Operator** = schemat z preconditions i add/delete lists.
- **Plan** = sekwencja operatorów od `:init` do `:goal`.

Rozszerzenie z `(connected ?from ?to)` ograniczyłoby ruch do grafu pokoi; przy pełnej łączności długość optymalnego planu pozostaje **5**.
