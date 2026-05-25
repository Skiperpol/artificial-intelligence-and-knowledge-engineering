# Zadanie 3 — Robot z dwoma ramionami (PDDL)

Robot z ramionami `arm1`, `arm2` przenosi cztery piłki z `room1` do `room2`. Model w notacji **STRIPS** z typowaniem (materiały [IDA LiU — Planning](https://www.ida.liu.se/~heltand/planning/)).

## Pliki

| Plik | Opis |
|------|------|
| `domain.pddl` | Domena `ball-moving-robot` — akcje `move`, `pick-up`, `put-down` |
| `problem.pddl` | Instancja `move-balls` |
| `problem.pddl.soln` | Plan wygenerowany przez planer |

## Model logiczny

### Obiekty

- Pokoje: `room1`, `room2`
- Piłki: `ball1` … `ball4`
- Ramiona: `arm1`, `arm2`
- Robot: `robot`

### Predykaty

| Predykat | Znaczenie |
|----------|-----------|
| `(at ?r - robot ?rm - room)` | Robot w pokoju |
| `(inroom ?b - ball ?rm - room)` | Piłka leży w pokoju |
| `(holding ?a - arm ?b - ball)` | Ramię trzyma piłkę |
| `(arm-empty ?a - arm)` | Ramię jest wolne |

### Akcje (schematy operatorów STRIPS)

**`move`** — robot przechodzi z `?from` do `?to`.  
Pre: `(at ?r ?from)` → Efekt: robot w `?to`, nie w `?from`.

**`pick-up`** — podniesienie piłki ramieniem.  
Pre: robot w pokoju, piłka `inroom`, ramię puste.  
Efekt: `(holding ?a ?b)`, usunięcie `inroom` i `arm-empty`.

**`put-down`** — odłożenie piłki.  
Pre: robot w pokoju, `(holding ?a ?b)`.  
Efekt: `(inroom ?b ?rm)`, `(arm-empty ?a)`, usunięcie `holding`.

### Stan początkowy i cel

- **Init:** robot i wszystkie piłki w `room1`, oba ramiona puste.
- **Goal:** `(inroom ball1 room2)` … `(inroom ball4 room2)`.

## Uruchomienie planera

### Lokalnie (Pyperplan, BFS)

```bash
cd task-3
.venv/bin/pyperplan Zadanie-3/domain.pddl Zadanie-3/problem.pddl
```

### planning.domains (Fast Downward / LAMA)

1. Wejdź na [solver.planning.domains](https://solver.planning.domains/)
2. Wybierz pakiet **lama-first**
3. Wgraj `domain.pddl` oraz `problem.pddl`

## Wygenerowany plan (11 akcji)

| # | Akcja |
|---|--------|
| 1 | `pick-up robot arm2 ball3 room1` |
| 2 | `pick-up robot arm1 ball1 room1` |
| 3 | `move robot room1 room2` |
| 4 | `put-down robot arm2 ball3 room2` |
| 5 | `put-down robot arm1 ball1 room2` |
| 6 | `move robot room2 room1` |
| 7 | `pick-up robot arm2 ball2 room1` |
| 8 | `pick-up robot arm1 ball4 room1` |
| 9 | `move robot room1 room2` |
| 10 | `put-down robot arm2 ball2 room2` |
| 11 | `put-down robot arm1 ball4 room2` |

**Wynik planera (Pyperplan, BFS):** długość planu **11**, 253 rozwinięte węzły, ~3 ms, 34 zinstancjonowane operatory.

## Analiza planu

### 1. Poprawność względem domeny

Każdy krok spełnia preconditions:

- Kroki 1–2: robot w `room1`, piłki na miejscu, ramiona puste → po kroku 2: `holding(arm2,ball3)`, `holding(arm1,ball1)`, brak tych piłek w `room1`.
- Krok 3: `move` — robot zmienia pokój; piłki pozostają w ramionach (nie wymagają `inroom` podczas transportu).
- Kroki 4–5: `put-down` w `room2` — `ball3`, `ball1` w pokoju docelowym.
- Krok 6: powrót do `room1` po `ball2`, `ball4`.
- Kroki 7–11: drugi wsad — analogicznie; po kroku 11 spełniony pełny `:goal`.

### 2. Wykorzystanie dwóch ramion

Robot może jednocześnie trzymać **co najwyżej 2** piłki. Przy 4 piłkach potrzeba **co najmniej 2** przejazdów `room1 → room2`. Plan realizuje dokładnie dwa wsady po 2 piłki — strategia równoległego użycia ramion.

### 3. Optymalność długości

Jeden pełny wsad (dostawa): 2× `pick-up` + 1× `move` + 2× `put-down` = **5** akcji.  
Między wsadami: 1× `move` powrotny.  
Razem: **5 + 1 + 5 = 11** — to dolna granica; plan BFS jest **optymalny** pod względem liczby akcji.

Wariant z jedną piłką na kurs wymagałby ok. **19** kroków (4× podnieś–jedź–odłóż + 3 powroty).

### 4. Stany pośrednie (skrót)

| Po kroku | Robot | Piłki w room1 | Piłki w room2 | Ramiona |
|----------|-------|---------------|---------------|---------|
| 0 | room1 | ball1–4 | — | oba puste |
| 2 | room1 | ball2, ball4 | — | trzyma ball3, ball1 |
| 5 | room2 | ball2, ball4 | ball3, ball1 | oba puste |
| 8 | room1 | — | ball3, ball1 | trzyma ball2, ball4 |
| 11 | room2 | — | ball1–4 | oba puste ✓ |

### 5. Powiązanie z wykładem (STRIPS / IDA LiU)

- **Stan** = zbiór faktów (założenia zamknięte w świecie).
- **Operator** = nazwa + parametry + preconditions + add/delete lists (tu: `and`, `not`).
- **Plan** = sekwencja operatorów od stanu początkowego do stanu spełniającego cel.
- **Grounding** — ze schematów powstają konkretne instancje (np. `pick-up robot arm1 ball1 room1`).

Inne poprawne plany mogą zamieniać kolejność piłek lub przypisanie ramion w obrębie wsadu; długość pozostaje **11**.
