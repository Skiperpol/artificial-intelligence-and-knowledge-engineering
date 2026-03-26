<center>
  
# Raport (Lista 1)
Autor: Dawid Błaszczyk 280518  

</center>

## 1. Cel ćwiczenia

Celem zadania jest implementacja i przetestowanie algorytmów do rozwiązywania problemów optymalizacji/wyznaczania ścieżek na danych transportowych GTFS, w szczególności:

- wyszukiwania najkrótszej ścieżki między przystankami z użyciem `Dijkstra` oraz `A*`,
- wariantu `A*` z wagowaniem heurystyki,
- oraz algorytmu `Tabu Search` do problemu przejścia przez zestaw przystanków i powrotu.

## 2. Problem i dane

### 2.1 Dane GTFS i ich interpretacja

W projekcie wykorzystywany jest standard GTFS (pliki m.in. `stops.txt`, `trips.txt`, `stop_times.txt`, `routes.txt`, `calendar.txt`, `calendar_dates.txt`).

W implementacji zakładamy, że:

- wierzchołki grafu odpowiadają przystankom/peronom (`stop_id` z `stops.txt`),
- krawędzie „travel” odzwierciedlają przejazd w ramach konkretnego kursu (kolejne pozycje w sekwencji `stop_times` dla danego `trip_id`),
- krawędzie „transfer” odzwierciedlają przesiadkę na tej samej stacji (połączenia między peronami o tym samym `parent_station`).

### 2.2 Budowa grafu skierowanego zależnego od czasu

Implementacja realizuje graf w postaci mapy `stop_id -> lista krawędzi`. Krawędź ma m.in.:

- `type`: `"travel"` albo `"transfer"`,
- `to`: docelowy `stop_id`,
- dla travel: czasy `dep_time` i `arr_time`, identyfikator kursu `trip_id`, identyfikator usługi `service_id` i nazwę linii `route_name`.

W module `task-1/graph/graph.py`:

- tworzenie krawędzi travel odbywa się przez połączenie kolejnych wierszy w posortowanych `stop_times` dla tego samego `trip_id`,
- przesiadki tworzone są przez dodanie krawędzi `"transfer"` z `duration = 0` między wszystkimi peronami/punktami należącymi do tej samej stacji nadrzędnej (`parent_station`).

W module `task-1/graph/prepare.py` wykonywane jest filtrowanie aktywnych kursów:

- wejście: data w formacie `YYYYMMDD` (domyślnie `20260303`),
- algorytm włącza krawędzie dla dnia bieżącego oraz (dla zapewnienia poprawności przy trasach przechodzących przez północ) dla dnia następnego, przesuwając czasy o `SEC_IN_DAY=86400`.

To filtrowanie wykorzystuje:

- `utils/calendar_utils.py`: połączenie `calendar.txt` oraz `calendar_dates.txt`.

## 3. Metryka kosztu i kryteria optymalizacji (t/p)

W kodzie wszystkie algorytmy (Dijkstra/A*/Weighted A*) uruchamiane są na tym samym grafie, a różnią się tylko sposobem przeszukiwania.

Kluczowe jest to, jak liczony jest koszt w `task-1/algorithms/utils.py`:

### 3.1 Kryterium `t` (minimalizacja czasu przejazdu)

- Dla krawędzi travel koszt rośnie o `(arr_time - real_time)` (czyli „od aktualnego czasu do przyjazdu”: zawiera także czas oczekiwania do odjazdu).
- Dla krawędzi transfer koszt jest zwiększany o `duration` (w implementacji `duration=0`).
- Dodatkowo doliczana jest kara za zmianę `trip_id` względem poprzednio użytego kursu: `penalty_value = 600` (10 minut w sekundach).

Finalnie, w `task-1/main.py` raportowana wartość kryterium to `total_cost - start_secs`, czyli (w przybliżeniu) „czas od startu do końca”, uwzględniający też kary.

### 3.2 Kryterium `p` (minimalizacja liczby przesiadek)

W implementacji `p` jest modelowane pośrednio:

- nadal liczymy składnik czasowy (jak w `t`), ale
- przy zmianie `trip_id` wprowadzamy bardzo dużą karę `penalty_value = 1000000`.

Intuicyjnie: ponieważ kara dominuje nad czasem, najlepsza trasa ma minimalizować liczbę zmian kursu (które odpowiadają przesiadkom w modelu „krawędź travel = konkretny kurs”).

### 3.3 Stan w algorytmach: (wierzchołek, trip_id)

Algorytmy przechowują stany jako `(stop_id, last_trip_id)`:

- dla krawędzi `"transfer"` `last_trip_id` nie zmienia się,
- dla krawędzi `"travel"` `last_trip_id` ustawiany jest na `edge['trip_id']`.

Dzięki temu kara za zmianę kursu działa poprawnie i nie „gubi się” podczas modelowania przesiadek.

## 4. Algorytmy i modyfikacje

### 4.1 Dijkstra (zadanie 1a)

**Tło teoretyczne:** Dijkstra wyznacza najkrótszą ścieżkę w grafie skierowanym z nieujemnymi wagami, zakładając jedno źródło i iteracyjnie relaksując odległości.

**Modyfikacje w implementacji (`task-1/algorithms/dijkstra.py`):**

- zamiast klasycznego przetwarzania wierzchołków, relaksacja dotyczy stanów `(stop_id, last_trip_id)`,
- krawędzie są „czasowe”: krawędź travel może być użyta tylko, jeśli `edge['dep_time'] >= real_time`,
- koszt przejścia jest liczony funkcją `calculate_edge_params(...)` (czas oczekiwania + ewentualna kara za zmianę kursu).

### 4.2 A* (zadanie 1b i 1c)

**Tło teoretyczne:** A* rozszerza Dijkstrę o heurystykę `h(n)` i wybiera kolejny stan o najmniejszym `f(n) = g(n) + h(n)`.

**Modyfikacje w implementacji (`task-1/algorithms/astar.py`):**

- identyczna jak w Dijkstra logika stanów `(stop_id, last_trip_id)`,
- heurystyka liczona jest w `task-1/algorithms/heuristics.py`: dla `mode='t'` wykorzystujemy odległość Haversine między współrzędnymi przystanków i przeliczamy ją na czas przy założonej prędkości 120 km/h jako `h = (distance_km / 120) * 3600`, a dla `mode='p'` heurystyka zwraca `0`, aby nie wprowadzać heurystyki niezgodnej z metryką „liczba przesiadek (modelowana karą)”.
- analogicznie do Dijkstry, krawędź travel jest pomijana jeśli jej `dep_time` jest wcześniejsze niż aktualny `real_time`.

### 4.3 Weighted A* (zadanie 1d / modyfikacja)

**Tło teoretyczne:** Weighted A* polega na zastosowaniu w A* wagi `epsilon >= 1` do heurystyki: `f = g + epsilon * h`. Zwykle daje to szybsze znalezienie rozwiązania kosztem potencjalnej utraty jakości optymalności.

**Modyfikacja w implementacji (`task-1/algorithms/weighted_astar.py`):**

- `epsilon = 10.0`,
- w chwili wstawiania do kolejki priorytetowej używana jest funkcja `f_cost = new_g + (epsilon * h_val)`,
- logika stanu, odrzucania krawędzi wcześniejszych oraz koszt przejścia jest taka sama jak w A*.

### 4.4 Tabu Search dla problemu TSP-przypominającego (zadanie 2)

**Tło teoretyczne:** Tabu Search jest metaheurystyką, która iteracyjnie bada sąsiedztwo bieżącego rozwiązania, ale unika cykli dzięki pamięci tablicy tabu. Może również używać „aspiracji”, aby mimo tabu dopuścić rozwiązania wystarczająco dobre.

W zadaniu interpretujemy rozwiązanie jako permutację listy przystanków do odwiedzenia, a koszt rozwiązania to:

- dla `criterion='t'`: czas start -> ... -> powrót do A,
- dla `criterion='p'`: koszt wewnętrzny algorytmu (z dominującą karą za zmianę `trip_id`).

**Implementacja (`task-1/algorithms/tabu_search.py`):**

1. Rozwiązanie początkowe: losowa permutacja (`random.shuffle`).
2. Sąsiedztwo: generowane przez zamianę miejsc dwóch przystanków (swap w permutacji).
3. Tabu: tabu jest implementowane jako kolejka FIFO (`collections.deque`) o maksymalnym rozmiarze `tabu_size = len(stop_ids) * 2`, a do tabu dodawane jest bieżące „wybrane” rozwiązanie.
4. Aspiracja:
   jeśli kandydat jest w tabu, ale ma koszt lepszy niż dotychczas najlepszy (`n_cost < best_cost`), może zostać dopuszczony.
5. Strategia próbkowania sąsiedztwa:
   gdy liczba sąsiadów jest duża, losowo wybieramy maksymalnie 10 kandydatów (`random.sample`), aby ograniczyć czas obliczeń.
6. Kryterium stopu:
   liczba iteracji `k` jest stała: `for k in range(50)`.

**Zauważalna konsekwencja:** ocena każdego kandydata wymaga wielokrotnego wywołania algorytmu najkrótszej ścieżki dla kolejnych par `(u, v)` w sekwencji permutacji, dlatego ograniczanie rozmiaru sąsiedztwa i tablicy tabu jest kluczowe dla czasu działania.


## 5. Przykłady użycia

### 5.1 Zadanie 1: ścieżka między przystankami A -> B

Uruchom z katalogu `task-1`:

```bash
cd task-1
./venv/bin/python main.py "<Przystanek_A>" "<Przystanek_B>" <t/p> <HH:MM:SS> [YYYYMMDD] [astar/dijkstra/weighted_astar]
```

Przykłady (GTFS Dolnośląskie, data domyślna `20260303`):

1. `Dijkstra`, kryterium czasu `t`:
```bash
./venv/bin/python main.py "Wrocław Główny" "Legnica" t 06:30:00 20260303 dijkstra
```

2. `A*`, kryterium czasu `t`:
```bash
./venv/bin/python main.py "Wrocław Główny" "Legnica" t 06:30:00 20260303 astar
```

3. `A*`, kryterium przesiadek `p` (heurystyka = 0, modelowane karą za zmianę `trip_id`):
```bash
./venv/bin/python main.py "Wrocław Główny" "Legnica" p 06:30:00 20260303 astar
```

### 5.2 Prawdziwe przypadki (wyniki z uruchomień)

Wykonane na danych GTFS Dolnośląskie, data `20260303`, start `06:30:00`.

Przypadek 1: `Dijkstra`, `t`, `Wrocław Główny -> Legnica`
```bash
./venv/bin/python main.py "Wrocław Główny" "Legnica" t 06:30:00 20260303 dijkstra
```
Wynik: odwiedzone stany `37689`, czas `0.6226s`, wartość kryterium `3540`.

Przypadek 2: `A*`, `t`, `Wrocław Główny -> Legnica`
```bash
./venv/bin/python main.py "Wrocław Główny" "Legnica" t 06:30:00 20260303 astar
```
Wynik: odwiedzone stany `129`, czas `0.0096s`, wartość kryterium `3540`.

Przypadek 3: `Weighted A*`, `t`, `Wrocław Główny -> Legnica`
```bash
./venv/bin/python main.py "Wrocław Główny" "Legnica" t 06:30:00 20260303 weighted_astar
```
Wynik: odwiedzone stany `13`, czas `0.0018s`, wartość kryterium `6420` (gorsze od wariantu nie-zwagowego).

Przypadek 4: `A*`, `p`, `Wrocław Główny -> Legnica`
```bash
./venv/bin/python main.py "Wrocław Główny" "Legnica" p 06:30:00 20260303 astar
```
Wynik: odwiedzone stany `297`, czas `0.0112s`, wartość kryterium `3540`.

Przypadek 5: `Tabu Search` (TSP po liście), `t`, `Legnica -> Jelenia Góra;Głogów`
```bash
./venv/bin/python main.py "Legnica" "Jelenia Góra;Głogów" t 06:30:00 20260303 astar
```
Wynik: czas `1.1538s`, łączny koszt `(t)` `33600`.

### 5.3 Zadanie 2: TSP po liście przystanków (powrót do A)

W tym trybie podajesz `B` jako listę przystanków rozdzieloną średnikami `;`:

```bash
./venv/bin/python main.py "<Przystanek_A>" "<B1;B2;...;Bn>" <t/p> <HH:MM:SS> [YYYYMMDD] [astar/dijkstra/weighted_astar]
```

Przykład (lista 3 przystanków, kryterium czasu `t`):

```bash
./venv/bin/python main.py "Wrocław Główny" "Legnica;Jelenia Góra;Głogów" t 06:30:00 20260303 astar
```

## 6. Dodatkowe materiały wykorzystane do realizacji

- Specyfikacja GTFS Schedule Reference (GTFS: `agency`, `routes`, `stops`, `trips`, `stop_times`, `calendar`, `calendar_dates`).
- Podstawy i pseudokod A* oraz Dijkstry (w tym interpretacja funkcji `f = g + h` i kolejki priorytetowej).
- Opis i ogólne zasady Tabu Search (tablica tabu jako FIFO oraz aspiracja).
- Wykorzystany wzór na odległość geograficzną: odległość Haversine (w `algorithms/heuristics.py`).

## 7. Użyte biblioteki

- `pandas` – wczytywanie plików GTFS i filtrowanie aktywnych usług.
- `heapq` – kolejka priorytetowa w Dijkstrze/A*.
- `itertools` – licznik do jednoznacznego porządkowania elementów w kolejce.
- `math` – matematyka heurystyki Haversine.
- `datetime` – przetwarzanie dat do filtrowania `calendar/calendar_dates`.
- `random` – losowa inicjalizacja i próbkowanie sąsiedztwa w Tabu Search.
- `collections.deque` – implementacja FIFO tablicy tabu.
- `pathlib` – praca ze ścieżkami systemu plików.

## 8. Podsumowanie i problemy napotkane podczas implementacji

Najtrudniejsze rzeczy przy tym zadaniu to głównie kwestia modelu „czasowego” i liczenia odpowiedniego kosztu:

1. Koszt `p` (czyli „ma być mało przesiadek”) zrobiłem jako dużą karę za zmianę `trip_id`. Nie liczę przesiadek „na sztywno”, tylko pozwalam tej karze wymuszać wybieranie tras z mniejszą liczbą zmian kursu.

2. W grafie czasowym musiałem pilnować, żeby dało się w ogóle skorzystać z krawędzi `travel`: `dep_time` musi być >= aktualny czas (`real_time`). Dodatkowo doszło przesunięcie godzin o `SEC_IN_DAY`, bo czasem trasa przechodzi przez północ.

3. Żeby kara za zmianę kursu działała poprawnie, algorytmy muszą pamiętać `last_trip_id`. Dlatego stan jest typu `(stop_id, last_trip_id)`, a nie tylko `stop_id`.

