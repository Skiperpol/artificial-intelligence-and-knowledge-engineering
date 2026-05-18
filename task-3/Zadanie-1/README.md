# Hierarchia Typów

- **location** — obiekt bazowy dla miejsc przestrzennych.
- **warehouse, airport, port, station** — podtypy lokacji.
- **vehicle** — obiekt bazowy dla środków transportu.
- **truck, plane, ship, train** — podtypy pojazdów.
- **package** — niezależny obiekt transportowany.

# Predykaty

- `(at ?obj - object ?l - location)` — określa, że paczka lub pojazd znajduje się w danej lokacji.
- `(in ?p - package ?v - vehicle)` — określa, że paczka została załadowana do konkretnego pojazdu.
- `(road-connection ?l1 - location ?l2 - location)` — istnieje droga lądowa.
- `(flight-connection ?l1 - airport ?l2 - airport)` — istnieje korytarz powietrzny.
- `(water-connection ?l1 - port ?l2 - port)` — istnieje szlak morski/rzeczny.
- `(rail-connection ?l1 - station ?l2 - station)` — istnieje połączenie szynowe.

# Funkcje Numeryczne

- `(total-cost)` — skumulowany koszt wszystkich wykonanych operacji (szukamy minimum).
- **Road dimension:** `(road-cost ?l1 ?l2)`, `(road-time ?l1 ?l2)`
- **Aviation dimension:** `(flight-cost ?l1 ?l2)`, `(flight-time ?l1 ?l2)`
- **Water dimension:** `(cruise-cost ?l1 ?l2)`, `(cruise-time ?l1 ?l2)`
- **Railway dimension:** `(travel-cost ?l1 ?l2)`, `(travel-time ?l1 ?l2)`

# Specyfikacja Akcji

## 1. Akcja `: load-package`

Operacja załadunku paczki do dowolnego pojazdu. Odbywa się w stałym czasie i generuje stały koszt operacyjny.

**Parametry:** `?p` - package, `?v` - vehicle, `?l` - location

**Czas trwania (Duration):** Stały, np. `(= ?duration 2)`

**Warunki (Conditions):**

- **at start:** paczka musi znajdować się w lokacji `?l` → `(at ?p ?l)`
- **over all:** pojazd musi bezwzględnie stać w tej samej lokacji przez cały czas załadunku → `(at ?v ?l)`

**Efekty (Effects):**

- **at start:** paczka natychmiast znika z lokacji → `(not (at ?p ?l))` (zabezpieczenie przed przebywaniem w dwóch miejscach naraz)
- **at end:** paczka zostaje formalnie umieszczona w pojeździe → `(in ?p ?v)`
- **at end:** całkowity koszt rośnie o stałą opłatę załadunkową → `(increase (total-cost) 5)`

## 2. Akcja `:unload-package`

Operacja rozładunku paczki z pojazdu do lokacji, w której pojazd się znajduje.

**Parametry:** `?p` - package, `?v` - vehicle, `?l` - location

**Czas trwania (Duration):** Stały, np. `(= ?duration 2)`

**Warunki (Conditions):**

- **at start:** paczka musi znajdować się wewnątrz pojazdu → `(in ?p ?v)`
- **over all:** pojazd musi znajdować się w docelowej lokacji przez cały czas rozładunku → `(at ?v ?l)`

**Efekty (Effects):**

- **at start:** paczka przestaje być przypisana jako "wewnątrz pojazdu" → `(not (in ?p ?v))`
- **at end:** paczka pojawia się w przestrzeni lokacji → `(at ?p ?l)`
- **at end:** całkowity koszt rośnie o stałą opłatę wyładunkową → `(increase (total-cost) 5)`

## 3. Akcja `:drive-truck`

Przemieszczenie ciężarówki. Zgodnie z Twoim założeniem, ciężarówki mogą poruszać się między dowolnymi lokacjami (location), o ile istnieje między nimi bezpośrednie połączenie drogowe.

**Parametry:** `?t` - truck, `?from` - location, `?to` - location

**Czas trwania (Duration):** Dynamiczny → `(= ?duration (road-time ?from ?to))`

**Warunki (Conditions):**

- **at start:** ciężarówka znajduje się w lokacji startowej → `(at ?t ?from)`
- **over all:** między lokacjami musi istnieć połączenie drogowe → `(road-connection ?from ?to)`

**Efekty (Effects):**

- **at start:** ciężarówka opuszcza punkt startowy → `(not (at ?t ?from))`
- **at end:** ciężarówka dociera do punktu docelowego → `(at ?t ?to)`
- **at end:** koszt całkowity rośnie o koszt przejazdu tą trasą → `(increase (total-cost) (road-cost ?from ?to))`

## 4. Akcja `:fly-plane`

Przemieszczenie samolotu. Ruch jest restrykcyjnie ograniczony wyłącznie do obiektów typu airport.

**Parametry:** `?pl` - plane, `?from` - airport, `?to` - airport

**Czas trwania (Duration):** Dynamiczny → `(= ?duration (flight-time ?from ?to))`

**Warunki (Conditions):**

- **at start:** samolot znajduje się na lotnisku startowym → `(at ?pl ?from)`
- **over all:** musi istnieć połączenie lotnicze → `(flight-connection ?from ?to)`

**Efekty (Effects):**

- **at start:** samolot startuje i opuszcza lotnisko → `(not (at ?pl ?from))`
- **at end:** samolot ląduje na lotnisku docelowym → `(at ?pl ?to)`
- **at end:** koszt całkowity rośnie o koszt lotu → `(increase (total-cost) (flight-cost ?from ?to))`

## 5. Akcja `:sail-ship`

Przemieszczenie statku. Ruch jest ograniczony wyłącznie do obiektów typu port.

**Parametry:** `?s` - ship, `?from` - port, `?to` - port

**Czas trwania (Duration):** Dynamiczny → `(= ?duration (cruise-time ?from ?to))`

**Warunki (Conditions):**

- **at start:** statek cumuje w porcie startowym → `(at ?s ?from)`
- **over all:** musi istnieć połączenie wodne → `(water-connection ?from ?to)`

**Efekty (Effects):**

- **at start:** statek wypływa z portu → `(not (at ?s ?from))`
- **at end:** statek dopływa do portu przeznaczenia → `(at ?s ?to)`
- **at end:** koszt całkowity rośnie o koszt rejsu → `(increase (total-cost) (cruise-cost ?from ?to))`

## 6. Akcja `:move-train`

Przemieszczenie pociągu towarowego. Ruch jest ograniczony wyłącznie do obiektów typu station (stacje kolejowe).

**Parametry:** `?tr` - train, `?from` - station, `?to` - station

**Czas trwania (Duration):** Dynamiczny → `(= ?duration (travel-time ?from ?to))`

**Warunki (Conditions):**

- **at start:** pociąg znajduje się na stacji początkowej → `(at ?tr ?from)`
- **over all:** musi istnieć infrastruktura torowa między stacjami → `(rail-connection ?from ?to)`

**Efekty (Effects):**

- **at start:** pociąg odjeżdża ze stacji → `(not (at ?tr ?from))`
- **at end:** pociąg wjeżdża na stację docelową → `(at ?tr ?to)`
- **at end:** koszt całkowity rośnie o koszt przejazdu kolejowego → `(increase (total-cost) (travel-cost ?from ?to))`
