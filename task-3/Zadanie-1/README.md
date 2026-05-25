# Zadanie 1 — System transportu paczek (PDDL)

Wielomodalna logistyka: paczki, lokacje (lotnisko, port, stacja), pojazdy (ciężarówka, samolot, statek, pociąg). Plan minimalizuje `(total-cost)`.

## Pliki

| Plik | Opis |
|------|------|
| `domain.pddl` | Wersja **klasyczna** pod Fast Downward / LAMA (`:action`, `:action-costs`) |
| `domain-temporal.pddl` | Wersja **temporalna** (`:durative-actions`, `:numeric-fluents`) |
| `problem.pddl` | Wspólna instancja problemu `transport-chicago-ny` |

## Rozszerzenia PDDL (wymagania zadania)

| Rozszerzenie | `domain.pddl` | `domain-temporal.pddl` |
|--------------|:-------------:|:----------------------:|
| `:strips` | ✓ | ✓ |
| `:typing` | ✓ | ✓ |
| `:negative-preconditions` | ✓ | ✓ |
| `:conditional-effects` | — (zastąpione `unload-at-port`) | ✓ |
| `:action-costs` | ✓ | — |
| `:numeric-fluents` | — | ✓ |
| `:durative-actions` | — | ✓ |

Model **multi-agent** (wiele pojazdów współpracujących: `truck1`, `truck2`, `plane1`, `ship1`, `train1`) — bez osobnego rozszerzenia `:multi-agent`.

## Uruchomienie planera

### Wersja klasyczna (planning.domains / Fast Downward)

1. Wejdź na [solver.planning.domains](https://solver.planning.domains/)
2. Wybierz pakiet **lama-first**
3. Wgraj `domain.pddl` + `problem.pddl`

### Wersja temporalna (OPTIC / TFD)

1. Na planning.domains wybierz planer temporalny (np. **optic-clp**), **albo**
2. Lokalnie: `optic domain-temporal.pddl problem.pddl`

> Fast Downward **nie** obsługuje `:durative-action` — do testów czasowych używaj `domain-temporal.pddl`.

---

# Model logiczny

## Hierarchia typów

- **location** — obiekt bazowy dla miejsc przestrzennych.
- **warehouse, airport, port, station** — podtypy lokacji.
- **vehicle** — obiekt bazowy dla środków transportu.
- **truck, plane, ship, train** — podtypy pojazdów.
- **package** — niezależny obiekt transportowany.

W implementacji PDDL typ ruchomy to `physobj` (nadtyp dla `package` i `vehicle`).

## Predykaty

- `(at ?obj - physobj ?l - location)` — paczka lub pojazd w lokacji.
- `(in ?p - package ?v - vehicle)` — paczka w pojeździe.
- `(port-location ?l - location)` — lokacja portowa (dopłata przy rozładunku).
- `(road-connection ?l1 - location ?l2 - location)` — droga lądowa.
- `(flight-connection ?l1 - airport ?l2 - airport)` — korytarz lotniczy.
- `(water-connection ?l1 - port ?l2 - port)` — szlak morski/rzeczny.
- `(rail-connection ?l1 - station ?l2 - station)` — tor kolejowy.

## Funkcje numeryczne

- `(total-cost)` — skumulowany koszt (metryka).
- **Droga:** `(road-cost)`, `(road-time)`
- **Lot:** `(flight-cost)`, `(flight-time)`
- **Morze:** `(cruise-cost)`, `(cruise-time)`
- **Kolej:** `(travel-cost)`, `(travel-time)`

## Opłata portowa (rozładunek)

- **`domain-temporal.pddl`:** efekt warunkowy `(when (port-location ?l) (increase (total-cost) 3))`
- **`domain.pddl`:** osobna akcja `unload-at-port` (koszt **8** = 5+3), bo Fast Downward nie obsługuje `:conditional-effects`

## Specyfikacja akcji (temporalna)

Szczegóły akcji duratywnych — w pliku `domain-temporal.pddl` (zgodnie z sekcjami poniżej).

### 1. `:load-package` — czas 2, koszt +5

### 2. `:unload-package` — czas 2, koszt +5 (+3 w porcie)

### 3. `:drive-truck` — czas `(road-time)`, koszt `(road-cost)`

### 4. `:fly-plane` — czas `(flight-time)`, koszt `(flight-cost)`

### 5. `:sail-ship` — czas `(cruise-time)`, koszt `(cruise-cost)`

### 6. `:move-train` — czas `(travel-time)`, koszt `(travel-cost)`

---

# Instancja problemu

**Cel:** `(at p1 ny-port)`, `(at p2 ny-airport)` — start: obie paczki w `warszawa-hub`.

**Topologia:**

- Drogi: hub ↔ Gdańsk, hub ↔ stacja, port ↔ stacja, NY lotnisko ↔ NY port.
- Lot: warszawa-hub ↔ ny-airport.
- Morze: gdansk-port ↔ ny-port.
- Kolej: warszawa-station ↔ gdansk-station.

**Pojazdy:** `truck1` (hub), `truck2` (NY), `plane1` (hub), `ship1` (Gdańsk), `train1` (stacja Warszawa).

---

# Analiza planu (wersja klasyczna)

Planer **LAMA-first** (koszt) wybiera trasę minimalizującą `total-cost`. Poniższy plan optymalny wynika z porównania modów (obliczenie ręczne + struktura grafu).

## Plan optymalny (9 kroków, koszt **191**)

| # | Akcja | Koszt kroku | Σ koszt |
|---|--------|-------------|---------|
| 1 | `load-package(p2, plane1, warszawa-hub)` | 5 | 5 |
| 2 | `fly-plane(plane1, warszawa-hub, ny-airport)` | 100 | 105 |
| 3 | `unload-package(p2, plane1, ny-airport)` | 5 | 110 |
| 4 | `load-package(p1, truck1, warszawa-hub)` | 5 | 115 |
| 5 | `drive-truck(truck1, warszawa-hub, gdansk-port)` | 15 | 130 |
| 6 | `unload-at-port(p1, truck1, gdansk-port)` | 8 | 138 |
| 7 | `load-package(p1, ship1, gdansk-port)` | 5 | 143 |
| 8 | `sail-ship(ship1, gdansk-port, ny-port)` | 40 | 183 |
| 9 | `unload-at-port(p1, ship1, ny-port)` | 8 | **191** |

- **Długość planu:** 9 akcji  
- **Koszt planu:** 191  
- **Czas (szacunek temporalny, sekwencyjnie):** 2+4+2 + 2+10+2+2+25+2 = **51** jednostek czasu  

## Trasy alternatywne (dla p1)

| Wariant | Opis | Szac. koszt |
|---------|------|-------------|
| **A (optymalny)** | truck → statek (morze) | **191** |
| B | samolot → truck2 NY lotnisko→port | ~238 |
| C | kolej + przesiadki drogowe | >200 (więcej załadunków) |

**p2** — jedyna sensowna ścieżka to lot bezpośredni (100 + załadunki).

## Wpływ topologii

| Usunięte połączenie | Skutek |
|---------------------|--------|
| `water-connection` (Gdańsk–NY) | Brak `sail-ship` → p1 musi lecieć + truck w NY → **koszt ↑** |
| `flight-connection` (Warszawa–NY) | Brak lotu → p2 tylko lądem/morzem → **długość i koszt ↑** |
| `road-connection` (hub–Gdańsk) | truck nie dojedzie do portu → **plan niemożliwy** bez innej ścieżki |
| `rail-connection` | `move-train` niedostępny; plan optymalny **bez zmian** (kolej nie wchodzi w plan A) |

## Wnioski

1. Topologia **multimodalna** pozwala specjalizować pojazdy (samolot na dystans, statek na cargo port–port).
2. **Koszt** sterowany fluently (`road-cost`, `flight-cost`, …) — planer wybiera tańszy wariant morski zamiast lotu dla p1.
3. **Czas** w wersji temporalnej zależy od `:duration` — morze (25) vs lot (4) pokazuje kompromis czas/koszt.
4. Wiele agentów (pojazdów) — równoległe użycie `plane1` i `truck1`/`ship1` skraca realizację wykonania rzeczywistego.

---

# Mapowanie wymagań zadania

| Wymaganie projektu | Realizacja |
|--------------------|------------|
| Model logiczny | README + oba pliki domeny |
| Pliki PDDL | `domain.pddl`, `domain-temporal.pddl`, `problem.pddl` |
| Test planera | planning.domains, pakiet lama-first |
| Analiza długości/kosztu/czasu/topologii | sekcja powyżej |
| Topologia droga/lot/woda | predykaty + problem |
| Kolej (rozszerzona topologia) | `rail-connection`, `train1`, stacje |
