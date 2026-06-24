# Raport laboratoryjny (Lista 5)

**Przedmiot:** Sztuczna Inteligencja i Inżynieria Wiedzy — Lista nr 5  
**Zakres:** Klasyfikacja wydźwięku tekstu (PolEmo2.0-IN) — modele encoder-only (HerBERT) i decoder-only (Qwen LLM), ewaluacja metrykami.  
**Autor:** Dawid Błaszczyk

---

## Spis treści

1. [Cel ćwiczenia](#1-cel-ćwiczenia)
2. [Wstęp teoretyczny](#2-wstęp-teoretyczny)
3. [Implementacja i środowisko](#3-implementacja-i-środowisko)
4. [Zadanie 1 — Eksploracja danych (10 pkt)](#4-zadanie-1--eksploracja-danych-10-pkt)
5. [Zadanie 2 — Klasyfikacja encoder-only (20 pkt)](#5-zadanie-2--klasyfikacja-encoder-only-20-pkt)
6. [Zadanie 3 — Eksploracja encoder (20 pkt)](#6-zadanie-3--eksploracja-encoder-20-pkt)
7. [Zadanie 4 — Klasyfikacja decoder-only LLM (20 pkt)](#7-zadanie-4--klasyfikacja-decoder-only-llm-20-pkt)
8. [Zadanie 5 — Eksploracja parametrów LLM (30 pkt)](#8-zadanie-5--eksploracja-parametrów-llm-30-pkt)
9. [Porównanie encoder vs decoder](#9-porównanie-encoder-vs-decoder)
10. [Podsumowanie i wnioski](#10-podsumowanie-i-wnioski)
11. [Biblioteki i materiały źródłowe](#11-biblioteki-i-materiały-źródłowe)

---

## 1. Cel ćwiczenia

Celem listy jest praktyczne zapoznanie z klasyfikacją wydźwięku tekstu przy użyciu nowoczesnych modeli językowych:

- eksploracja zbioru **PolEmo2.0-IN** (benchmark KLEJ),
- klasyfikacja modelem **encoder-only** (`Voicelab/herbert-base-cased-sentiment`),
- eksploracja parametrów encoder (model bazowy, `max_length`),
- klasyfikacja **zero-shot** modelem **decoder-only** (`Qwen/Qwen2.5-1.5B-Instruct`),
- eksploracja parametrów LLM (temperatura, prompt, parsowanie JSON),
- ocena wyników metrykami **Accuracy**, **F1** oraz analiza jakości **per klasa**.

---

## 2. Wstęp teoretyczny

### 2.1. Klasyfikacja tekstu

Klasyfikacja tekstu polega na automatycznym przypisaniu etykiety c \in C do nieustrukturyzowanego tekstu t za pomocą klasyfikatora f(t) \rightarrow c. W analizie wydźwięku zbiór kategorii obejmuje zwykle wartości: pozytywny, negatywny, neutralny (oraz opcjonalnie mieszany).

### 2.2. Modele encoder-only (HerBERT)

Modele typu **Encoder-only** (np. BERT, HerBERT) przekształcają tekst na wektor reprezentujący całe zdanie (token `[CLS]`), co umożliwia klasyfikację przez dodanie głowy klasyfikującej. Są mniejsze i szybsze niż modele generatywne, idealne do masowej klasyfikacji.

### 2.3. Modele decoder-only (LLM)

**Wielkie Modele Językowe** (LLM) oparte na architekturze Transformer (Decoder-only) przewidują kolejny token na podstawie kontekstu. W klasyfikacji wykorzystuje się **zero-shot learning**, poprzez odpowiedni **prompt** wymuszamy na modelu wygenerowanie nazwy kategorii zamiast swobodnej odpowiedzi.

### 2.4. Metryki ewaluacji

Do oceny klasyfikacji wieloklasowej zastosowano:


| Metryka                   | Opis                                                     |
| ------------------------- | -------------------------------------------------------- |
| **Accuracy**              | Odsetek poprawnych klasyfikacji                          |
| **F1 (macro)**            | Średnia harmoniczna precyzji i czułości, równa waga klas |
| **F1 (weighted)**         | F1 ważone licznością klas                                |
| **Classification report** | Precyzja, czułość, F1 per klasa                          |
| **Confusion matrix**      | Macierz pomyłek — które klasy są mylone                  |


---

## 3. Implementacja

### 3.1. Mapowanie etykiet

Kluczowym elementem implementacji jest mapowanie między etykietami zbioru a odpowiedziami modeli:


| Etykieta zbioru         | Klasa robocza  | Etykieta modelu (EN) |
| ----------------------- | -------------- | -------------------- |
| `__label__meta_minus_m` | minus          | negative             |
| `__label__meta_zero`    | neutral        | neutral              |
| `__label__meta_plus_m`  | plus           | positive             |
| `__label__meta_amb`     | *(wykluczona)* | —                    |


---

## 4. Zadanie 1 — Eksploracja danych (10 pkt)

### 4.1. Źródło i wczytanie

Dane pobrałem z Hugging Face:

```python
from datasets import load_dataset
dataset = load_dataset("allegro/klej-polemo2-in", split="test")
```

### 4.2. Filtrowanie klasy ambiguous

Zgodnie z wymaganiami listy użyłem **tylko splitu testowego** i **wykluczyłem klasę ambiguous**:

Filtrowanie danych


| Element                      | Wartość |
| ---------------------------- | ------- |
| Próbek w split test (surowo) | **722** |
| Usunięto (ambiguous)         | **108** |
| Pozostało do klasyfikacji    | **614** |


### 4.3. Rozkład klas


| Klasa       | Liczność | Udział (%) |
| ----------- | -------- | ---------- |
| **minus**   | 300      | 48,9       |
| **neutral** | 117      | 19,1       |
| **plus**    | 197      | 32,1       |


Rozkład klas

Klasa **minus** dominuje (49%), klasa **neutral** jest najmniej liczna (19%). Zbiór jest **trochę niezbalansowany**.

### 4.4. Długość tekstów


| Statystyka | Znaki | Słowa |
| ---------- | ----- | ----- |
| Średnia    | 759,4 | 132,6 |
| Mediana    | 694,0 | 120,0 |
| Min        | 29    | 6     |
| Max        | 2469  | 440   |
| Odch. std. | 403,0 | 71,7  |


Recenzje są **dość długie** (średnio ~760 znaków, ~133 słowa) co jest istotne przy doborze parametru `max_length` w modelach.

### 4.5. Przykładowe recenzje

**minus** — negatywna opinia o lekarzu (pomimo pozytywnego tonu końcówki, etykieta minus wynika z kontekstu całej wypowiedzi):

> *„Leczyła m się u niej parę lat i nic mi nie pomogła, a jak zmieniłam lekarza po krótkim czasie zobaczyłam już poprawę..."*

**neutral** — tekst informacyjny o cukrzycy, bez wyraźnego ładunku emocjonalnego:

> *„Cukrzyca, to choroba, którą już pod końcem XX wieku uważano za epidemię..."*

**plus** — jednoznacznie pozytywna recenzja lekarza:

> *„Konkretna, wszystkie badania robi na miejscu od razu przy wizycie. Zawsze wychodzi się z gabinetu z postawioną diagnozą..."*

### 4.6. Wnioski z eksploracji

1. Klasa minus stanowi prawie połowę zbioru 49%, a neutral zaledwie 19%. Przy takim rozjeździe samo Accuracy może mocno przekłamywać rzeczywistą jakość klasyfikacji, dlatego kluczowe będzie analizowanie metryki F1-macro.
2. Przykłady pokazują, że teksty oznaczone jako neutral to najczęściej suche artykuły informacyjne lub popularnonaukowe, a nie typowe opinie. Dla modeli odróżnienie braku emocji od pozytywnego nacechowania będzie prawdopodobnie najtrudniejszym zadaniem.
3. Recenzje w zbiorze są dość długie. Oznacza to, że zbyt niskie ustawienie parametru max_length (np. na 128) może ucinać końcówki wypowiedzi, w których autorzy zazwyczaj umieszczają ostateczne podsumowanie i puentę całej opinii.
4. W tekstach często pojawiają się sformułowania, które wyrwane z kontekstu brzmią pozytywnie (np. "zobaczyłam poprawę"), ale sens całego zdania jednoznacznie wskazuje na krytykę. To pokazuje, że proste metody bazujące na pojedynczych słowach kluczowych tutaj nie zadziałają i potrzebne są modele dobrze radzące sobie z kontekstem.

---

## 5. Zadanie 2 — Klasyfikacja encoder-only (20 pkt)

### 5.1. Model i konfiguracja


| Parametr   | Wartość                                        |
| ---------- | ---------------------------------------------- |
| Model      | `Voicelab/herbert-base-cased-sentiment`        |
| Pipeline   | `transformers.pipeline("text-classification")` |
| Urządzenie | GPU (T4)                                       |


Model HerBERT fine-tuned na analizę sentymentu w języku polskim, zwraca etykiety `negative`, `neutral`, `positive`, mapowane na klasy zbioru.

### 5.2. Wyniki ewaluacji

Wyniki HerBERT baseline


| Metryka           | Wartość    |
| ----------------- | ---------- |
| **Accuracy**      | **0,7590** |
| **F1 (macro)**    | **0,6263** |
| **F1 (weighted)** | **0,7294** |


Wskaźnik ogólnej dokładności (Accuracy) na poziomie 75,90% oraz ważona miara F1 (weighted) wynosząca 72,94% sugerują, że model HerBERT baseline radzi sobie poprawnie z ogólną klasyfikacją zbioru. Jednakże, drastyczny spadek wartości metryki F1 (macro) do poziomu 62,63% jasno wskazuje na poważny problem z nierównomierną skutecznością klasyfikacji dla poszczególnych kategorii.

**Raport dla każdej klasy:**


| Klasa   | Precyzja | Czułość | F1       | Support |
| ------- | -------- | ------- | -------- | ------- |
| minus   | 0,97     | 0,85    | **0,91** | 300     |
| neutral | 0,34     | 0,14    | **0,20** | 117     |
| plus    | 0,64     | 0,98    | **0,78** | 197     |


Szczegółowa analiza metryk dla poszczególnych klas ujawnia, że model wykazuje bardzo wysoką skuteczność w rozpoznawaniu emocji skrajnych. Natomiast głównym problemem modelu baseline jest klasa 'neutral', dla której miara F1 wynosi zaledwie 0,20. Bardzo niska czułość (0,14) oznacza, że model poprawnie identyfikuje jedynie 14% wszystkich rzeczywistych komentarzy neutralnych.

**Macierz pomyłek** (wiersze = prawda, kolumny = predykcja):

```
              minus  neutral  plus
minus    [    256       31      13  ]
neutral  [      6       16      95  ]
plus     [      3        0     194  ]
```

Głębszy wgląd w naturę błędów daje analiza macierzy pomyłek. Wynika z niej, że:

- **Klasa neutralna jest masowo mylona z pozytywną:** Aż 95 ze 117 rzeczywistych próbek neutralnych zostało sklasyfikowanych przez model jako 'plus'. Oznacza to, że granica semantyczna między neutralnymi a pozytywnymi recenzjami jest dla modelu HerBERT bardzo rozmyta.
- **Bezpieczna klasyfikacja negatywna:** Model rzadko myli klasę negatywną z pozytywną (tylko 13 przypadków) i odwrotnie (tylko 3 przypadki). Oznacza to, że model bardzo dobrze odróżnia skrajne emocje od siebie.
- **Asymetria błędów:** Model ma silną tendencję (tzw. bias) do przewidywania klasy pozytywnej w sytuacjach niepewnych. Widać to po kolumnie 'plus' w macierzy, model przypisał tę etykietę aż 302 razy (13 + 95 + 194), mimo że w rzeczywistości klasa ta liczyła tylko 197 próbek."

### 5.3. Analiza błędów

Typowe pomyłki modelu:


| Prawda  | Predykcja | Przyczyna                                                                             |
| ------- | --------- | ------------------------------------------------------------------------------------- |
| minus   | plus      | Tekst z pozytywnym zakończeniem („jest wszystko dobrze”), ale negatywna ocena lekarza |
| minus   | neutral   | Długa recenzja z elementami pozytywnymi i negatywnymi                                 |
| neutral | plus      | Tekst informacyjno-naukowy mylony z opinią pozytywną                                  |
| neutral | plus      | Artykuł o technologii medycznej — brak emocji, ale słownictwo „pozytywne”             |


### 5.4. Wnioski

1. Sam wynik dokładności (Accuracy = 76%) wygląda dobrze, ale to zasługa tego, że model świetnie radzi sobie z wyłapywaniem minusów i plusów. Niestety, kompletnie niedaje rady z klasami neutralnymi.
2. Model ma dużą tendencję do wrzucania wszystkiego, co neutralne, do worka z plusami. Wystarczy, że tekst jest pisany suchym, medycznym lub technicznym językiem, a model uznaje to za coś pozytywnego, mimo że nie ma tam żadnych emocji.
3. Jeśli pacjent napisze długą, negatywną recenzję, ale na końcu rzuci luźne „ogólnie jest wszystko dobrze”, model gubi kontekst. Zamiast oceniać całość, łapie się na te pojedyncze, miłe słowa i błędnie daje plusa lub neutrala.
4. Model rzadko robi błędy "krytyczne", czyli prawie nigdy nie myli ewidentnego plusa z ewidentnym minusem (i odwrotnie). Rozróżnia skrajności, ma po prostu problem z odcieniami szarości.
5. Encoder działa szybko i bez dodatkowej konfiguracji, gdyż wynik „out of the box” bez promptów.

---

## 6. Zadanie 3 — Eksploracja encoder (20 pkt)

Przeprowadziłem trzy rodzaje eksperymentów: porównanie modeli, wpływ `max_length` oraz wpływ `temperature`.

### 6.1. Eksperyment A — porównanie modeli

Porównywane modele


| Model                                   | Opis               | Accuracy   | F1 macro   | F1 weighted |
| --------------------------------------- | ------------------ | ---------- | ---------- | ----------- |
| `Voicelab/herbert-base-cased-sentiment` | HerBERT — recenzje | **0,7590** | **0,6263** | **0,7294**  |
| `bardsai/finance-sentiment-pl-base`     | HerBERT — finanse  | 0,4121     | 0,4292     | 0,4405      |


**Wnioski:**

- **Znacząca różnica skuteczności:** Model dostrojony do recenzji osiągnął znacznie lepsze wyniki (Accuracy 0,76) niż model dedykowany dla tekstów finansowych (Accuracy 0,41).
- **Problem dopasowania dziedzinowego:** Model finansowy nie generalizuje dobrze na dane z recenzji produktów czy usług. Widać to szczególnie w klasyfikacji tekstów negatywnych, które model bardzo często błędnie przypisywał do klasy neutralnej (210 pomyłek na 300 przypadków).
- **Podsumowanie:** Dobór modelu musi odpowiadać charakterystyce zbioru danych. Modele NLP są silnie zależne od kontekstu, w którym były trenowane, dlatego model finansowy nie jest odpowiedni do analizy sentymentu w recenzjach konsumenckich.

### 6.2. Eksperyment B — wpływ max_length

Model: `Voicelab/herbert-base-cased-sentiment`


| max_length | Accuracy   | F1 macro   | F1 weighted |
| ---------- | ---------- | ---------- | ----------- |
| 32         | 0,6173     | 0,5839     | 0,6275      |
| 64         | 0,6889     | 0,6182     | 0,6880      |
| 128        | 0,7459     | **0,6405** | 0,7277      |
| 256        | **0,7622** | 0,6279     | **0,7315**  |
| 512        | 0,7590     | 0,6263     | 0,7294      |


**Wnioski:**

- **Spadek jakości przy zbyt krótkim tekście:** Ustawienie `max_length` na 32 lub 64 tokeny widocznie pogarsza wyniki (Accuracy spada poniżej 70%). Zbyt mocne ucięcie tekstu sprawia, że model traci kluczowe informacje, które w recenzjach często znajdują się na samym końcu wypowiedzi (np. ostateczne podsumowanie).
- **Punkt optymalny:** Najwyższą dokładność (Accuracy 0,7622) uzyskano dla wartości 256. Z kolei dla wartości 128 model osiągnął najlepszy balans między wszystkimi klasami (F1 macro: 0,6405), co wynika z lepszego rozpoznawania klasy neutralnej.
- **Stabilność powyżej średniej:** W przedziale od 128 do 512 tokenów różnice w wynikach są minimalne (poniżej 2 punktów procentowych). Oznacza to, że model radzi sobie stabilnie, o ile nie ograniczamy mu sztucznie kontekstu poniżej średniej długości recenzji w zbiorze.

### 6.3. Eksperyment C — wpływ temperatury

Model: `Voicelab/herbert-base-cased-sentiment`


| temperature | Accuracy | F1 macro | F1 weighted |
| ----------- | -------- | -------- | ----------- |
| 0           | 0,7590   | 0,6263   | 0,7294      |
| 0,5         | 0,7590   | 0,6263   | 0,7294      |
| 1,0         | 0,7590   | 0,6263   | 0,7294      |
| 2,0         | 0,7590   | 0,6263   | 0,7294      |


**Wnioski:**

- **Brak wpływu na ostateczną predykcję:** Zmiana wartości temperatury w całym badanym zakresie nie wpłynęła na zmianę ani jednej metryki. Wszystkie uzyskane wyniki są identyczne z wariantem bazowym.
- **Podsumowanie:** Parametr temperatury nie ma znaczenia praktycznego w tradycyjnej klasyfikacji deterministycznej za pomocą enkoderów.

### 6.4. Tabela porównawcza

Tabela porównawcza — wszystkie eksperymenty


| eksperyment | wariant                      | accuracy   | f1_macro   | f1_weighted |
| ----------- | ---------------------------- | ---------- | ---------- | ----------- |
| model       | herbert-base-cased-sentiment | **0,7590** | **0,6263** | **0,7294**  |
| model       | finance-sentiment-pl-base    | 0,4121     | 0,4292     | 0,4405      |
| max_length  | 32                           | 0,6173     | 0,5839     | 0,6275      |
| max_length  | 64                           | 0,6889     | 0,6182     | 0,6880      |
| max_length  | 128                          | 0,7459     | **0,6405** | 0,7277      |
| max_length  | 256                          | **0,7622** | 0,6279     | **0,7315**  |
| max_length  | 512                          | 0,7590     | 0,6263     | 0,7294      |
| temperature | 0 / 0,5 / 1,0 / 2,0          | 0,7590     | 0,6263     | 0,7294      |


**Główna obserwacja:** Najwyższą ogólną dokładność (Accuracy 76,2%) uzyskano przy ograniczeniu kontekstu do `max_length=256`. Z kolei najwyższy wskaźnik zbalansowania klas (F1 macro 64,1%) model osiągnął przy długości `128`.

### 6.5. Wnioski

- **Kluczowa rola domeny danych (*domain shift*):** Model dostrojony na danych zbliżonych do docelowych (recenzje konsumenckie) poradził sobie radykalnie lepiej (Accuracy 75,9%) niż model wyspecjalizowany w tekstach finansowych (Accuracy 41,2%). Potwierdza to, że wiedza językowa z wąskiej dziedziny nie podlega prostej generalizacji na ogólną analizę emocji.
- **Wpływ okna kontekstowego (**`max_length`**):** Długość tekstu ma krytyczne znaczenie, jeśli okno zostanie ustawione poniżej średniej długości wypowiedzi (wartości 32 i 64). Skracanie recenzji odcina kluczowe słowa kluczowe i podsumowania. Optymalnym kompromisem wydajnościowym i jakościowym jest wartość 256 tokenów. Powyżej tej granicy następuje stabilizacja wyników, co oznacza, że dłuższy kontekst nie wnosi już nowych informacji.
- **Niezależność od temperatury:** Eksperyment potwierdził teoretyczne założenia, że w przypadku klasyfikacji z twardym mapowaniem (operacja `argmax` na logitach) modyfikacja temperatury nie wpływa w żaden sposób na ostatecznie wybieraną klasę. Metryki dla każdego wariantu $T$ pozostały identyczne.
- **Charakterystyka klas:** Niezależnie od testowanej konfiguracji, klasa *neutral* niezmiennie stanowiła największe wyzwanie klasyfikacyjne (notując najniższe wartości miary Recall), co wynika ze specyfiki i niejednoznaczności języka używanego w neutralnych recenzjach.

---

## 7. Zadanie 4 — Klasyfikacja decoder-only LLM (20 pkt)

### 7.1. Model i konfiguracja


| Parametr  | Wartość                         |
| --------- | ------------------------------- |
| Model     | `Qwen/Qwen2.5-1.5B-Instruct`    |
| Framework | LangChain + HuggingFacePipeline |


Liczba próbek

**Ładowanie modelu**

Konfiguracja pipeline

**Prompt bazowy** — ścisła instrukcja + spacja po `Class:`  wymuszająca jednowyrazową odpowiedź:

Prompt i łańcuch LangChain

```
Classify the text sentiment into one of three classes: positive, negative, neutral.
Reply with only one word — the class name. Do not explain your choice.

Text: {text}
Class: 
```

**Parsowanie odpowiedzi** — przed mapowaniem brana jest tylko pierwsza linia odpowiedzi:

Funkcja classify_with_llm

### 7.2. Wyniki ewaluacji

Wyniki Qwen LLM


| Metryka           | Wartość    |
| ----------------- | ---------- |
| **Accuracy**      | **0,8697** |
| **F1 (macro)**    | **0,8106** |
| **F1 (weighted)** | **0,8602** |


**Raport dla każdej klasy:**


| Klasa   | Precyzja | Czułość | F1       | Support |
| ------- | -------- | ------- | -------- | ------- |
| minus   | 0,95     | 0,97    | **0,96** | 300     |
| neutral | 0,83     | 0,50    | **0,62** | 117     |
| plus    | 0,78     | 0,94    | **0,85** | 197     |


**Macierz pomyłek:**

```
              minus  neutral  plus
minus    [    291        4       5  ]
neutral  [     12       58      47  ]
plus     [      4        8     185  ]
```

### 7.3. Analiza surowych odpowiedzi LLM

Podgląd surowych odpowiedzi

Mapowanie na klasy zbioru:


| Prawda  | Odpowiedź LLM | Zmapowano | Poprawne? |
| ------- | ------------- | --------- | --------- |
| minus   | **positive**  | plus      | ✗         |
| minus   | **negative**  | minus     | ✓         |
| minus   | **Negative**  | minus     | ✓         |
| neutral | **neutral**   | neutral   | ✓         |
| plus    | **positive**  | plus      | ✓         |


Model radzi sobie z wielką/małą literą (`Negative` → minus). Główny błąd to **mylenie minus z plus** w długich, dwuznacznych recenzjach (pierwszy przykład — pozytywne zakończenie przy negatywnej ocenie lekarza).

### 7.4. Wnioski

1. Po naprawie parsowania LLM osiąga **accuracy 87,0%** na pełnym teście — **lepszy wynik niż HerBERT** (75,9%) przy tej samej liczbie próbek.
2. Klasa **minus** jest rozpoznawana bardzo dobrze (F1 = 0,96); **plus** również (F1 = 0,85).
3. **Neutral** pozostaje trudny (recall 0,50) — 47 z 117 przypadków mylonych z **plus** (teksty informacyjne bez wyraźnych emocji).

---

## 8. Zadanie 5 — Eksploracja parametrów LLM (30 pkt)

### 8.1. Metodologia

Zbadano trzy aspekty wpływające na wyniki klasyfikacji LLM:


| Aspekt          | Warianty                                                    |
| --------------- | ----------------------------------------------------------- |
| **Temperatura** | 0,0 / 0,1 / 0,7                                             |
| **Prompt**      | prosty (EN) / szczegółowy (PL z definicjami klas)           |
| **Parsowanie**  | regex (`map_text_to_class`) / `JsonOutputParser` (Pydantic) |


Eksperymenty uruchomiono na **podzbiorze zbioru testowego (70 próbek)** — ze względu na czas inferencji LLM:

Liczba próbek

Implementacja w module eksperymentów:

- `get_llm(temperature)` — ładowanie modelu z cache (jednorazowe),
- `parse_text_answer()` — parsowanie odpowiedzi tekstowej (wyciąganie etykiety po `Class:` / `Klasa:`),
- `parse_json_answer()` — parsowanie JSON z fallback regex,
- `run_llm_experiment()` — uruchomienie pełnego eksperymentu z metrykami.

### 8.2. Definicje promptów

Definicje promptów


| Prompt            | Język | Opis                                                       |
| ----------------- | ----- | ---------------------------------------------------------- |
| `PROMPT_SIMPLE`   | EN    | Krótka instrukcja: 3 klasy, odpowiedź jednym słowem        |
| `PROMPT_DETAILED` | PL    | Definicje klas po polsku (pozytywna / negatywna / opisowa) |
| `PROMPT_JSON`     | PL    | Żądanie odpowiedzi w formacie JSON + `JsonOutputParser`    |


### 8.3. Eksperyment A — wpływ temperatury

Model: `Qwen/Qwen2.5-1.5B-Instruct`, prompt prosty (`PROMPT_SIMPLE`).

Eksperyment temperatury


| Temperatura | Accuracy | F1 macro | F1 weighted |
| ----------- | -------- | -------- | ----------- |
| 0,0         | 0,7743   | 0,6507   | 0,7189      |
| 0,1         | 0,7743   | 0,6507   | 0,7189      |
| 0,7         | 0,7829   | 0,6671   | 0,7318      |


**Wniosek:** Przy `do_sample=False` (temperatura 0,0 i 0,1) wyniki są **identyczne**. Wyższa temperatura (0,7) daje **niewielką poprawę**, kosztem większej losowości odpowiedzi.

### 8.4. Eksperyment B — wpływ promptu

Temperatura stała: 0,1.

Eksperyment promptu


| Prompt           | Accuracy | F1 macro | F1 weighted |
| ---------------- | -------- | -------- | ----------- |
| prosty (EN)      | 0,7714   | 0,6436   | 0,7133      |
| szczegółowy (PL) | 0,8314   | 0,7960   | 0,8268      |


**Wniosek:** Szczegółowy prompt po polsku z definicjami klas **znacząco poprawia** wyniki w porównaniu z prostym promptem angielskim, model lepiej radzi sobie z polskimi recenzjami przy jasnych instrukcjach.

### 8.5. Eksperyment C — parsowanie JSON

Eksperyment JSON


| Parsowanie       | Accuracy | F1 macro | F1 weighted |
| ---------------- | -------- | -------- | ----------- |
| JsonOutputParser | 0,4857   | 0,4878   | 0,4956      |


**Wniosek:** Parsowanie JSON osiąga wyniki na poziomie **losowego zgadywania** (~49% accuracy), model generuje niepełny lub niepoprawny JSON, a `JsonOutputParser` nie poprawia jakości klasyfikacji w tej konfiguracji.

### 8.6. Tabela porównawcza wszystkich eksperymentów

Tabela porównawcza zadanie 5


| Eksperyment        | Temperatura | Accuracy | F1 macro | F1 weighted | Prompt      |
| ------------------ | ----------- | -------- | -------- | ----------- | ----------- |
| prompt=szczegółowy | 0,1         | 0,8314   | 0,7960   | 0,8268      | szczegółowy |
| temp=0.7           | 0,7         | 0,7829   | 0,6671   | 0,7318      | —           |
| temp=0.1           | 0,1         | 0,7743   | 0,6507   | 0,7189      | —           |
| temp=0.0           | 0,0         | 0,7743   | 0,6507   | 0,7189      | —           |
| prompt=prosty      | 0,1         | 0,7714   | 0,6436   | 0,7133      | prosty      |
| parsowanie=JSON    | 0,1         | 0,4857   | 0,4878   | 0,4956      | JSON        |


Najlepszy wariant: **prompt szczegółowy (PL)** przy temperaturze 0,1 — accuracy **83,1%**, F1 macro **79,6%**.

### 8.7. Interpretacja wyników

1. **Prompt ma największy wpływ** — szczegółowy prompt po polsku (+6 pp accuracy vs prosty EN) wykorzystuje wiedzę modelu o polskim języku i jasno definiuje klasy.
2. **Temperatura ma marginalny wpływ** — 0,0 i 0,1 dają identyczne wyniki (greedy decoding); 0,7 nieznacznie poprawia F1 macro, ale zwiększa wariancję.
3. **JSON nie działa** — `JsonOutputParser` przy małym modelu (1,5B) generuje niekompletne struktury JSON; wyniki (~49%) są zbliżone do błędnego parsowania sprzed poprawki.
4. Baseline z zad. 4 (prosty prompt EN, pełny test 614 próbek) osiąga **87,0% accuracy** — więcej niż HerBERT (75,9%). Eksploracja w zad. 5 na podzbiorze 70 próbek pokazuje dodatkowo wpływ promptu PL i temperatury.

### 8.8. Wnioski z zadania 5

1. **Prompt** — decydujący czynnik po naprawie parsowania; definicje klas po polsku dają najlepsze wyniki.
2. **Temperatura** — niska (0,0–0,1) zapewnia stabilność; 0,7 daje niewielką poprawę kosztem powtarzalności.
3. **JsonOutputParser** — niepoprawny wybór dla tego modelu i zadania; proste parsowanie tekstowe działa znacznie lepiej.

---

## 9. Porównanie encoder vs decoder


| Kryterium         | Encoder (HerBERT)     | Decoder (Qwen LLM, zad. 4) |
| ----------------- | --------------------- | -------------------------- |
| **Accuracy**      | 0,7590                | **0,8697**                 |
| **F1 macro**      | 0,6263                | **0,8106**                 |
| **F1 weighted**   | 0,7294                | **0,8602**                 |
| **F1 minus**      | 0,91                  | **0,96**                   |
| **F1 neutral**    | 0,20                  | **0,62**                   |
| **F1 plus**       | 0,78                  | **0,85**                   |
| **Zbiór testowy** | 614 próbek            | 614 próbek                 |
| **Szybkość**      | Szybki (batch 16)     | Wolny (~1 tekst/sek.)      |
| **Konfiguracja**  | Pipeline, zero config | Prompt + parsowanie        |
| **GPU RAM**       | ~0,5 GB               | ~3 GB (1,5B params)        |


Na **tym samym pełnym zbiorze testowym** Qwen po poprawce parsowania **przewyższa HerBERT** we wszystkich metrykach globalnych. Encoder pozostaje szybszy i prostszy w wdrożeniu; LLM wymaga starannej konfiguracji promptu i warstwy parsowania.

W zadaniu 5 (podzbiór 70 próbek) najlepszy wariant LLM z promptem szczegółowym PL osiąga accuracy 83,1% — wynik nieco niższy niż baseline z zad. 4 na pełnym teście, co wynika z mniejszej próbki i różnych wariantów promptu.

### Kluczowe obserwacje

1. **LLM wygrywa na jakości** — przy poprawnym parsowaniu accuracy 87,0% vs 75,9% encodera na pełnym teście.
2. **Neutral — LLM radzi sobie lepiej** — F1 0,62 (LLM) vs 0,20 (encoder); encoder myli neutral z plus (95/117), LLM częściej trafia (58/117), ale też myli z plus (47/117).
3. **Encoder wygrywa na szybkości i prostocie** — brak promptów, batch inference, mniejsze zużycie RAM.
4. **Parsowanie decyduje o wynikach LLM** — bez `return_full_text=False` i izolacji etykiety wyniki spadają do ~49%.
5. **Domena treningu** (encoder, zad. 3) — model finansowy osiąga accuracy 0,41 vs 0,76 modelu recenzyjnego.

---

## 10. Podsumowanie i wnioski

### 10.1. Odpowiedzi na pytania badawcze

1. **Czy encoder-only radzi sobie z klasyfikacją wydźwięku polskich recenzji?**
  Tak — HerBERT osiąga accuracy **75,9%** bez dodatkowego treningu. Klasy skrajne (minus, plus) rozpoznawane są dobrze (F1 > 0,78).
2. **Czy LLM zero-shot jest konkurencyjny?**
  **Tak** — po poprawce parsowania Qwen osiąga accuracy **87,0%** i F1 macro **81,1%** na pełnym teście (614 próbek), przewyższając HerBERT (75,9% / 62,6%). Wymaga to jednak precyzyjnego promptu, `return_full_text=False` i czyszczenia odpowiedzi; bez tego wyniki spadają do ~49%.
3. **Która klasa jest najtrudniejsza?**
  **Neutral** — encoder: F1 = 0,20 (czułość 0,14); LLM: F1 = 0,62 (czułość 0,50). LLM radzi sobie z neutral znacznie lepiej, ale nadal myli go z plus w połowie przypadków.
4. **Jak parametry wpływają na wyniki?**
  - **Encoder — domena modelu** — decydujący czynnik (recenzje vs finanse: 0,76 vs 0,41).
  - **Encoder — max_length** — marginalny wpływ (optimum: 256 tokenów).
  - **LLM — parsowanie odpowiedzi** — warunek konieczny poprawnych wyników (`return_full_text=False`, pierwsza linia odpowiedzi).
  - **LLM — prompt** (zad. 5) — szczegółowy PL poprawia wyniki na podzbiorze; prosty EN w zad. 4 wystarcza do 87% na pełnym teście.
  - **LLM — temperatura / JSON** (zad. 5) — marginalny wpływ temperatury; JSON niepoprawny (~49%).

### 10.2. Wnioski praktyczne

- Do **produkcji przy ograniczonym czasie inferencji**: encoder-only (HerBERT) — szybki, prosty, 76% accuracy bez konfiguracji.
- Do **maksymalnej jakości zero-shot**: decoder LLM (Qwen) — **87% accuracy** na pełnym teście, ale wolniejszy i wymaga warstwy parsowania.
- **Parsowanie odpowiedzi LLM** (`return_full_text=False`, izolacja etykiety) — bez tego wyniki są fałszywie złe (~49%).
- Klasa **neutral** wymaga uwagi w obu architekturach; LLM (F1 0,62) znacznie przewyższa encoder (F1 0,20), ale nadal myli neutral z plus.

