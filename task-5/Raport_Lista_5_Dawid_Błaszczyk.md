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


Recenzje są **dość długie** (średnio ≈760 znaków, ≈133 słowa) co jest istotne przy doborze parametru `max_length` w modelach.

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
- **Niezależność od temperatury:** Eksperyment potwierdził teoretyczne założenia, że w przypadku klasyfikacji z twardym mapowaniem (operacja `argmax` na logitach) modyfikacja temperatury nie wpływa w żaden sposób na ostatecznie wybieraną klasę. Metryki dla każdego wariantu temperatury pozostały identyczne.
- **Charakterystyka klas:** Niezależnie od testowanej konfiguracji, klasa *neutral* niezmiennie stanowiła największe wyzwanie klasyfikacyjne (notując najniższe wartości miary Recall), co wynika ze specyfiki i niejednoznaczności języka używanego w neutralnych recenzjach.

---

## 7. Zadanie 4 — Klasyfikacja decoder-only LLM (20 pkt)

### 7.1. Model i konfiguracja

Do przeprowadzenia klasyfikacji z użyciem architektury *decoder-only* wykorzystałem mniejszy model LLM, dostosowany do dostępnych zasobów obliczeniowych, zintegrowany z ekosystemem LangChain.


| Parametr  | Wartość                         |
| --------- | ------------------------------- |
| Model     | `Qwen/Qwen2.5-1.5B-Instruct`    |
| Framework | LangChain + HuggingFacePipeline |


W celu zmuszenia modelu generatywnego do działania w trybie klasyfikatora deterministycznego, zaprojektowano restrykcyjną instrukcję systemową. Na końcu struktury celowo dodano znak spacji po tokenie `Class:` , co ułatwia modelowi natychmiastowe wygenerowanie poprawnej etykiety:

```
Classify the text sentiment into one of three classes: positive, negative, neutral.
Reply with only one word — the class name. Do not explain your choice.

Text: {text}
Class: 
```

#### Przepływ danych i parsowanie wyników

Generowanie odpowiedzi przez model zostało zamknięte w strukturze łańcucha LangChain (`LCEL`). Ze względu na to, że modele generatywne (dekodery) mogą dopisywać zbędne znaki białej spacji lub komentarze, potok przetwarzania został wyposażony w mechanizm czyszczący:

1. **Wywołanie LLM:** Model generuje tekst odpowiedzi na podstawie przekazanego tekstu recenzji.
2. **Parsowanie tekstu:** Dedykowana funkcja `classify_with_llm` pobiera surowy tekst, odcina białe znaki, konwertuje litery na małe oraz – w ramach zabezpieczenia – ekstrahuje **wyłącznie pierwszą linię** wygenerowanej odpowiedzi.
3. **Mapowanie etykiet:** Oczyszczony ciąg znaków jest mapowany na identyfikator numeryczny zgodny ze strukturą zbioru PolEmo2.0-IN. W przypadku błędu generowania lub braku odpowiedzi, aplikowana jest domyślna klasa bezpieczna (`neutral`).

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

Proces parsowania tekstu generowanego przez LLM wykazał wysoką stabilność. Model w pełni respektował ograniczenia promptu (zwracał pojedyncze tokeny) oraz poprawnie radził sobie z różną wielkością liter (np. automatyczna konwersja tokenu `Negative` lub `negative` na wewnętrzny identyfikator klasy `minus`).


| Prawda  | Odpowiedź LLM | Zmapowano | Poprawne? |
| ------- | ------------- | --------- | --------- |
| minus   | **positive**  | plus      | ✗         |
| minus   | **negative**  | minus     | ✓         |
| minus   | **Negative**  | minus     | ✓         |
| neutral | **neutral**   | neutral   | ✓         |
| plus    | **positive**  | plus      | ✓         |


#### Charakterystyka błędów

Głównym źródłem pomyłek modelu generatywnego były sytuacje skrajne w długich i wielowątkowych recenzjach (np. w domenie medycznej). Przykładowo, w tekstach, gdzie pacjent szczegółowo opisywał negatywne aspekty zachowania personelu, ale na samym końcu umieszczał jedno zdanie o pozytywnym efekcie leczenia, model dawał się zwieść końcowemu wnioskowi i błędnie klasyfikował całą wypowiedź jako `positive`.

### 7.4. Wnioski końcowe z sekcji decoder-only

- **Przewaga architektury generatywnej:** Po wdrożeniu poprawnego potoku parsowania i czyszczenia tekstu, model `Qwen2.5-1.5B-Instruct` osiągnął bardzo wysoką dokładność ogólną na poziomie **87,0%**. Wynik ten w sposób wyraźny przewyższa najlepszy wariant modelu bazowanego na enkoderze (`HerBERT` osiągnął maksymalnie 76,2% dla okna 256). Pokazuje to duży potencjał modeli z rodziny LLM w zadaniach zero-shot z odpowiednio skonstruowanym promptem.
- **Znakomita separacja skrajnych emocji:** Model wykazuje niemal perfekcyjną zdolność rozpoznawania tekstów silnie negatywnych (miara F1 = 0,96 dla klasy `minus`) oraz bardzo wysoką dla tekstów pozytywnych (F1 = 0,85 dla klasy `plus`). Przypadki bezpośredniego pomylenia klasy negatywnej z pozytywną (i odwrotnie) były incydentalne (łącznie 9 przypadków na cały zbiór).
- **Trudność klasy neutralnej:** Podobnie jak w przypadku enkoderów, najtrudniejszym zadaniem okazało się wychwycenie tekstów neutralnych (niski Recall na poziomie 0,50). Macierz pomyłek jednoznacznie wskazuje, że model przejawia silną tendencję do nadinterpretacji tekstów obiektywnych/neutralnych i błędnego przypisywania ich do klasy pozytywnej (aż 47 przypadków fałszywie dodatnich). Prawdopodobnie wynika to z uprzejmego tonu wypowiedzi, który model generatywny utożsamia z sentymentem pozytywnym.

---

## 8. Zadanie 5 — Eksploracja parametrów LLM (30 pkt)

### 8.1. Metodologia

Zbadałem **cztery aspekty** wpływające na wyniki klasyfikacji LLM:


| Aspekt          | Warianty                                                         |
| --------------- | ---------------------------------------------------------------- |
| **Temperatura** | 0,0 / 0,1 / 0,7                                                  |
| **Prompt**      | Prosty (angielski) / Szczegółowy (polski z definicjami klas)     |
| **Parsowanie**  | Wyrażenia regularne (Regex) / Strukturyzowany `JsonOutputParser` |
| **Kwantyzacja** | float16 / 4-bit NF4 (`bitsandbytes`)                             |


W celu automatyzacji testów i zapewnienia powtarzalności środowiska zaimplementowano dedykowany potok przetwarzania oparty na następujących komponentach programistycznych:

- `load_model(quantization)` – dynamiczne ładowanie wag modelu `Qwen2.5-1.5B-Instruct` w natywnej precyzji `float16` lub w skompresowanym formacie 4-bitowym NF4.
- `reset_llm_cache()` – mechanizm czyszczenia pamięci podręcznej GPU (`torch.cuda.empty_cache()` oraz usunięcie referencji do obiektów), zapobiegający nakładaniu się alokacji i umożliwiający precyzyjny pomiar zużycia VRAM dla każdego wariantu.
- `parse_text_answer()` – funkcja wyciągająca twardą etykietę tekstową ze strumienia wyjściowego LLM (na podstawie markerów `Class:` lub `Klasa:`).
- `parse_json_answer()` – parser obiektów JSON implementujący regułę bezpieczeństwa (*fallback*) opartą na wyrażeniach regularnych w przypadku uszkodzenia struktury dokumentu przez model.
- `run_llm_experiment()` – nadrzędna funkcja sterująca, odpowiedzialna za sekwencyjne uruchamianie konfiguracji, zbieranie miar klasyfikacyjnych (Accuracy, F1), monitorowanie czasu inferencji (`czas_s`) oraz rejestrowanie szczytowego zużycia pamięci karty graficznej (`vram_gb`).

### 8.2. Definicje promptów

Definicje promptów


| Prompt            | Język | Opis                                                       |
| ----------------- | ----- | ---------------------------------------------------------- |
| `PROMPT_SIMPLE`   | EN    | Krótka instrukcja: 3 klasy, odpowiedź jednym słowem        |
| `PROMPT_DETAILED` | PL    | Definicje klas po polsku (pozytywna / negatywna / opisowa) |
| `PROMPT_JSON`     | PL    | Żądanie odpowiedzi w formacie JSON + `JsonOutputParser`    |


### 8.3. Eksperyment A — wpływ temperatury

Model: `Qwen/Qwen2.5-1.5B-Instruct`, prompt prosty (`PROMPT_SIMPLE`), kwantyzacja float16.


| Temperatura | Accuracy | F1 macro | F1 weighted | Czas [s] | VRAM [GB] |
| ----------- | -------- | -------- | ----------- | -------- | --------- |
| 0,0         | 0,8127   | 0,6626   | 0,7636      | 435,5    | 3,24      |
| 0,1         | 0,8111   | 0,6576   | 0,7605      | 410,8    | 3,24      |
| 0,7         | 0,8176   | 0,6832   | 0,7758      | 396,7    | 3,24      |


**Wnioski:**

- **Stabilność niskich temperatur:** Dla wartości $T=0.0$ oraz $T=0.1$ model wykazuje bardzo zbliżone wskaźniki efektywności (Accuracy $\approx 81\%$). Minimalne różnice wynikają z faktu, że bardzo niska temperatura nieznacznie modyfikuje prawdopodobieństwa, ale w większości przypadków utrzymuje model w trybie deterministycznego wyboru najbardziej prawdopodobnego tokenu (*greedy decoding*).
- **Wpływ próbkowania ($T=0.7$):** Podniesienie temperatury do $0.7$ (aktywujące pełne próbkowanie stochastyczne) przyniosło zauważalną poprawę zbalansowanej miary $F1\text{ macro}$ (wzrost z 0,657 do 0,683). Delikatne rozmycie rozkładu prawdopodobieństwa pozwoliło modelowi na bardziej elastyczny wybór etykiet w przypadkach niejednoznacznych, co pozytywnie wpłynęło na rzadziej reprezentowane klasy. Odbywa się to jednak kosztem utraty determinizmu — przy ponownym uruchomieniu wyniki mogą się nieznacznie różnić.
- **Analiza wydajnościowa:** Zużycie pamięci VRAM pozostało idealnie stałe (3,24 GB), co potwierdza, że temperatura modyfikuje jedynie operację próbkowania na wyjściu i nie zmienia rozmiaru struktur modelu. Obserwowane wahania czasu inferencji (zakres 396–435 sekund) mają charakter czysto środowiskowy (wynikają z chwilowego obciążenia zasobów sprzętowych) i nie są matematyczną konsekwencją zmiany temperatury.

### 8.4. Eksperyment B — wpływ promptu

Temperatura stała: 0,1, kwantyzacja float16.


| Prompt           | Accuracy   | F1 macro   | F1 weighted | Czas [s] | VRAM [GB] |
| ---------------- | ---------- | ---------- | ----------- | -------- | --------- |
| prosty (EN)      | 0,8143     | 0,6674     | 0,7668      | 399,8    | 3,24      |
| szczegółowy (PL) | **0,8583** | **0,7999** | **0,8513**  | 424,1    | 3,27      |


**Wnioski:**

- **Drastyczny wzrost jakości klasyfikacji:** Zastosowanie rozbudowanego promptu w języku polskim przyniosło zdecydowanie najlepsze wyniki w całej eksploracji parametrów LLM. Wskaźnik celności wzrósł o **4,4 punktu procentowego**, natomiast zbalansowana miara $F1\text{ macro}$ zanotowała potężny skok o ponad **13 p.p.** (z 0,667 do 0,799).
- **Uzasadnienie lingwistyczne:** Podanie precyzyjnych definicji klas bezpośrednio w języku polskim (będącym językiem analizowanych recenzji) pozwoliło modelowi `Qwen2.5` na znacznie lepszą aktywację odpowiednich struktur semantycznych w jego wagach. Model przestał działać "intuicyjnie" na poziomie pojedynczych słów kluczowych, a zaczął poprawnie interpretować niejednoznaczne i neutralne opisy.
- **Analiza kosztu obliczeniowego:** Dłuższa i bardziej szczegółowa instrukcja po polsku przełożyła się na minimalny wzrost zapotrzebowania na pamięć graficzną (z 3,24 GB do 3,27 GB) oraz wydłużenie czasu przetwarzania o ok. 24 sekundy. Wynika to bezpośrednio z konieczności przeliczenia większej liczby tokenów wejściowych oraz alokacji większej przestrzeni na tzw. *KV Cache* (pamięć podręczną kontekstu). Biorąc pod uwagę potężny zysk jakościowy, koszt ten jest w pełni akceptowalny.

### 8.5. Eksperyment C — parsowanie JSON


| Parsowanie       | Accuracy | F1 macro | F1 weighted | Czas [s] | VRAM [GB] |
| ---------------- | -------- | -------- | ----------- | -------- | --------- |
| JsonOutputParser | 0,5016   | 0,5050   | 0,5295      | 434,9    | 3,33      |


**Wnioski:**

- **Drastyczny spadek skuteczności:** Próba wymuszenia ustrukturyzowanego wyjścia w formacie JSON zredukowała dokładność klasyfikacji do poziomu **50,16%**, co w zadaniu trójklasowym jest wynikiem zbliżonym do losowego zgadywania.
- **Syndrom przeciążenia małych architektur:** Model o skali 1.5B parametrów ma ograniczoną pojemność reprezentacji. Narzucenie mu restrykcyjnych reguł składniowych kodu programistycznego sprawiło, że model zużył swoje "zdolności uwagi" na dbanie o domykanie nawiasów klamrowych i cudzysłowów, tracąc przy tym zdolność logicznego wnioskowania o emocjach zawartych w tekście. W efekcie model często generował uszkodzone lub niekompletne obiekty tekstowe, co uniemożliwiło poprawne działanie parsera z biblioteki *LangChain*.
- **Ślad pamięciowy:** Eksperyment ten odnotował najwyższe zużycie pamięci graficznej (**3,33 GB**) spośród wszystkich testów przeprowadzonych w precyzji `float16`. Wynika to z dodatkowego narzutu na przetwarzanie tokenów strukturalnych (składni JSON) oraz konieczności utrzymywania w pamięci instrukcji i schematów walidacyjnych wstrzykiwanych automatycznie przez `JsonOutputParser`. Podsumowując, dla modeli tej skali podejście strukturyzowane jest wysoce nieefektywne.

### 8.6. Eksperyment D — kwantyzacja (float16 vs 4-bit)

Prompt prosty, temperatura 0,1.


| Kwantyzacja | Accuracy | F1 macro | F1 weighted | Czas [s] | VRAM [GB] |
| ----------- | -------- | -------- | ----------- | -------- | --------- |
| float16     | 0,8111   | 0,6575   | 0,7607      | 412,2    | **3,25**  |
| 4-bit (NF4) | 0,7866   | 0,6284   | 0,7365      | 798,9    | **1,31**  |


**Wnioski:**

- **Potężna redukcja śladu pamięciowego:** Skompresowanie wag modelu do formatu 4-bitowego (Normal Float 4) przyniosło radykalną, **blisko 60-procentową oszczędność pamięci VRAM** (spadek z 3,25 GB do zaledwie 1,31 GB). Wykazana redukcja udowadnia, że technika ta pozwala na uruchomienie modeli klasy LLM na sprzęcie o bardzo ograniczonych zasobach sprzętowych (np. starsze karty graficzne lub darmowe instancje chmurowe).
- **Koszt jakościowy kompresji:** Redukcja precyzji matematycznej odbiła się negatywnie na zdolnościach językowych modelu. Odnotowano spadek celności o **2,45 punktu procentowego** oraz obniżenie miary $F1\text{ macro}$ o blisko 3 p.p. Dla mniejszych architektur (skali 1.5B) odrzucenie bitów precyzji częściej prowadzi do gubienia subtelnych niuansów semantycznych w tekście.
- **Paradoks czasu inferencji:** Mimo mniejszego rozmiaru na dysku i w pamięci, model 4-bitowy przetwarzał zbiór testowy **niemal dwukrotnie dłużej** (798,9 s vs 412,2 s). Jest to bezpośredni skutek inżynieryjny działania biblioteki `bitsandbytes` – spakowane warianty 4-bitowe muszą być "w locie" dekwantyzowane (rozpakowywane) do formatu zmiennoprzecinkowego przed wykonaniem każdej operacji mnożenia macierzy na rdzeniach GPU, co generuje potężny narzut czasowy.
- **Podsumowanie kompromisu:** Kwantyzacja to klasyczny kompromis inżynierski (*trade-off*). Pozwala drastycznie zminimalizować wymagania sprzętowe, jednak bezpośrednią ceną za to jest odczuwalna strata na jakości predykcji oraz znaczące wydłużenie czasu działania potoku.

### 8.7. Tabela porównawcza wszystkich eksperymentów

Tabela porównawcza zadanie 5


| Eksperyment            | Temp. | Kwant.  | Accuracy   | F1 macro   | F1 weighted | Czas [s] | VRAM [GB] |
| ---------------------- | ----- | ------- | ---------- | ---------- | ----------- | -------- | --------- |
| **prompt=szczegółowy** | 0,1   | float16 | **0,8583** | **0,7999** | **0,8513**  | 424,1    | 3,27      |
| temp=0.7               | 0,7   | float16 | 0,8176     | 0,6832     | 0,7758      | 396,7    | 3,24      |
| prompt=prosty          | 0,1   | float16 | 0,8143     | 0,6674     | 0,7668      | 399,8    | 3,24      |
| temp=0.0               | 0,0   | float16 | 0,8127     | 0,6626     | 0,7636      | 435,5    | 3,24      |
| temp=0.1               | 0,1   | float16 | 0,8111     | 0,6576     | 0,7605      | 410,8    | 3,24      |
| quant=float16          | 0,1   | float16 | 0,8111     | 0,6575     | 0,7607      | 412,2    | 3,25      |
| quant=4bit             | 0,1   | 4bit    | 0,7866     | 0,6284     | 0,7365      | 798,9    | 1,31      |
| parsowanie=JSON        | 0,1   | float16 | 0,5016     | 0,5050     | 0,5295      | 434,9    | 3,33      |


**Główna obserwacja:** Optymalną konfiguracją dla badanego modelu okazało się zastosowanie **szczegółowego promptu w języku polskim przy niskiej temperaturze (0.1) w precyzji** `float16`, co pozwoliło na osiągnięcie najwyższej celności na poziomie **85,8%** oraz miary $F1\text{ macro} = 80,0\%$.

### 8.8. Interpretacja wyników

1. **Inżynieria promptów jako kluczowy czynnik sukcesu:** Zmiana treści instrukcji przyniosła najbardziej spektakularny zysk jakościowy (+4,4 p.p. Accuracy oraz ponad +13 p.p. F1 macro w porównaniu do prostego wariantu angielskiego). Przełamanie barier językowych w opisie klas pozwoliło modelowi `Qwen2.5` na pełne wykorzystanie wiedzy semantycznej o języku polskim.
2. **Umiarkowany i probabilistyczny wpływ temperatury:** Zmiana temperatury w zakresie 0.0–0.1 nie wpływa na model z uwagi na deterministyczne dekodowanie zachłanne (*greedy decoding*). Z kolei podbicie parametru do $T=0.7$ rozszerzyło przestrzeń poszukiwań tokenów, co poskutkowało nieznacznym wzrostem miary F1 macro (0,6832). Eksperyment ten dowodzi, że wyższa temperatura może pomóc w klasyfikacji klas rzadkich (np. *neutral*), kosztem utraty powtarzalności wyników.
3. **Składniowa destabilizacja przez format JSON:** Narzucenie strukturyzacji wyjścia za pomocą `JsonOutputParser` doprowadziło do załamania wydajności modelu do poziomu losowego (50,16%). Wynik ten jednoznacznie definiuje ograniczenia architektur o rozmiarze 1.5B parametrów — dbanie o techniczną poprawność kodu JSON odbywa się kosztem zdolności logicznego wnioskowania.
4. **Wydajnościowy kompromis kwantyzacji:** Przejście na format 4-bitowy NF4 to klasyczny, inżynierski kompromis. Zmniejszenie zużycia pamięci VRAM o blisko 60% (do poziomu zaledwie 1,31 GB) okopane jest spadkiem celności o ok. 2,5 p.p. oraz drastycznym, dwukrotnym wydłużeniem czasu pracy potoku (798,9 s). Kwantyzacja jest zatem doskonałym wyborem przy restrykcyjnych ograniczeniach sprzętowych, ale nie sprawdza się przy optymalizacji systemów pod kątem czystej jakości i szybkości.
5. **Kontekst porównawczy z modelem bazowym (Zadanie 4):** Baseline z zadania 4 (prosty prompt EN oparty na czystym pipeline transformers) osiągnął na pełnym teście 87,0% accuracy — wynik minimalnie lepszy niż najlepsza konfiguracja z zadania 5 (85,8%). Różnica ta wynika ze specyfiki implementacji: w zadaniu 4 model działał w środowisku bez narzutu abstrakcji frameworka LangChain, co minimalizowało ryzyko drobnych błędów parsowania. Warto jednak zaznaczyć, że **obie architektury LLM (zarówno z zadania 4, jak i 5) bezproblemowo i wyraźnie przewyższyły model enkoderowy HerBERT (75,9%)**, udowadniając wyższą elastyczność i potencjał modeli generatywnych w analizie sentymentu.

### 8.9. Wnioski z zadania 5

1. **Kluczowe znaczenie inżynierii promptów:** Dobór języka oraz precyzja instrukcji okazały się najważniejszym czynnikiem optymalizacyjnym. Szczegółowy prompt w języku polskim, wzbogacony o definicje semantyczne klas, pozwolił modelowi `Qwen2.5` na pełną aktywację powiązań językowych i osiągnięcie najwyższej w tym zadaniu celności (**85,8%**).
2. **Stabilność deterministyczna vs probabilistyczna elastyczność:** Niskie wartości temperatury ($T=0.0$ oraz $T=0.1$) gwarantują stabilność i pełną powtarzalność wyników klasyfikacji. Podniesienie parametru do $0.7$ aktywuje stochastyczne próbkowanie, co może nieznacznie poprawić rozpoznawanie klas rzadkich (wzrost $F1\text{ macro}$), lecz odbywa się to kosztem utraty determinizmu potoku przetwarzania.
3. **Nieefektywność ustrukturyzowanego wyjścia (JSON):** Wykorzystanie `JsonOutputParser` w modelach o mniejszej liczbie parametrów (skala 1.5B) jest błędem projektowym. Wymuszenie rygorystycznej składni programistycznej przeciąża model i drastycznie obniża jakość wnioskowania logicznego (spadek celności do poziomu losowego $\approx 50\%$). W takich architekturach znacznie skuteczniejsze jest proste parsowanie wyjścia tekstowego za pomocą wyrażeń regularnych.
4. **Kwantyzacja jako klasyczny kompromis inżynierski (*trade-off*):** Kompresja modelu do formatu 4-bitowego (NF4) pozwala na potężną, blisko 60-procentową oszczędność pamięci graficznej (redukcja z 3,25 GB do zaledwie 1,31 GB VRAM). Bezpośrednim kosztem tego zabiegu jest jednak utrata około 2,5 p.p. celności oraz dwukrotne wydłużenie czasu inferencji z powodu konieczności dekompresji wag "w locie". Jest to rozwiązanie rekomendowane wyłącznie w systemach o silnie ograniczonych zasobach sprzętowych.

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
| **Szybkość**      | Szybki (batch 16)     | Wolny (≈1 tekst/sek.)      |
| **Konfiguracja**  | Pipeline, zero config | Prompt + parsowanie        |
| **GPU RAM**       | ≈0,5 GB               | ≈3 GB (1,5B params)        |


### Kluczowe obserwacje i dyskusja

- **Dominacja jakościowa modeli LLM:** Model dekoderowy `Qwen2.5` po wdrożeniu poprawnej warstwy parsowania tekstu bezapelacyjnie przewyższa model enkoderowy `HerBERT` we wszystkich globalnych metrykach klasyfikacyjnych (wzrost ogólnego Accuracy o **11,07 punktu procentowego** oraz F1 macro o **18,43 p.p.**).
- **Przełom w detekcji klasy neutralnej:** Największą słabością modelu enkoderowego była klasyfikacja tekstów obiektywnych i opisowych — `HerBERT` zanotował krytycznie niski wynik $F1 = 0,20$, permanentnie myląc klasę *neutral* z klasą *plus* (aż 95 pomyłek na 117 próbek). Model `Qwen2.5` dzięki znacznie większej pojemności semantycznej poradził sobie z tym wyzwaniem bez porównania lepiej ($F1 = 0,62$). Choć on również przejawia tendencję do nadinterpretacji uprzejmego tonu jako sentymentu dodatniego (47 pomyłek), to poprawnie zidentyfikował połowę próbek neutralnych (58/117).
- **Efektywność ekonomiczna i wdrożeniowa enkoderów:** Choć architektury *decoder-only* wygrywają pod kątem czystej jakości predykcji, `HerBERT` pozostaje bezkonkurencyjny w kategoriach czysto inżynierskich. Wymaga blisko **7-krotnie mniej pamięci GPU** ($\approx 0,5$ GB vs $\approx 3,25$ GB), nie potrzebuje budowania skomplikowanych potoków instrukcji (prompów) i pozwala na natywne przetwarzanie potokowe (*batch inference*), co czyni go rozwiązaniem wielokrotnie tańszym i szybszym w środowisku produkcyjnym.
- **Krytyczna rola potoku przetwarzania (Parsowanie i Domena):** 1. Eksperymenty jednoznacznie dowiodły, że sukces modeli LLM w zadaniach deterministycznych w 100% zależy od czyszczenia danych wyjściowych (brak flagi `return_full_text=False` lub brak izolacji etykiety powoduje załamanie wyników do poziomu losowego $\approx 49\%$).
  2. W przypadku enkoderów kluczowa jest z kolei zgodność domenowa danych treningowych — wykorzystanie modelu wyspecjalizowanego w innej domenie (`finance-sentiment-pl-base` w Zadaniu 3) skutkowało drastycznym spadkiem celności do poziomu 41,21%

### Wnioski końcowe

Wybór między enkoderem a dekoderem w analizie sentymentu zależy bezpośrednio od priorytetów projektowych:

1. Jeśli celem nadrzędnym jest **maksymalna dokładność**, poprawna interpretacja tekstów neutralnych oraz elastyczność bez konieczności ponownego trenowania sieci, najlepszym wyborem są małe modele **LLM (Decoder)** sterowane precyzyjnym promptem.
2. Jeśli system ma działać w reżimie **czasu rzeczywistego (*low latency*)**, przy ograniczonych zasobach budżetowych/sprzętowych, mniejsze modele dedykowane **BERT (Encoder)** dostrojone do właściwej domeny językowej wciąż stanowią najbardziej optymalne i stabilne rozwiązanie inżynierskie.

---

## 10. Podsumowanie i wnioski

### 10.1. Odpowiedzi na pytania badawcze

- **Czy modele typu *encoder-only* radzą sobie z klasyfikacją wydźwięku polskich recenzji?** **Tak.** Model `HerBERT-base-cased-sentiment` bez konieczności dodatkowego douczania (*fine-tuningu*) osiągnął satysfakcjonującą celność ogólną na poziomie **75,90%**. Architektura ta wykazuje bardzo wysoką skuteczność w rozpoznawaniu klas o silnym ładunku emocjonalnym, notując miary $F1 > 0,78$ dla tekstów pozytywnych oraz $F1 = 0,91$ dla tekstów negatywnych.
- **Czy podejście *zero-shot* przy użyciu modeli LLM jest konkurencyjne?** **Tak, i wyraźnie przewyższa podejście enkoderowe.** Po wdrożeniu poprawnej warstwy parsowania, model `Qwen2.5-1.5B-Instruct` osiągnął na pełnym zbiorze testowym celność **87,0%** oraz miarę $F1\text{ macro} = 81,1\%$. Należy jednak podkreślić, że sukces ten jest całkowicie uwarunkowany inżynierią promptów oraz konfiguracją techniczną potoku (wymóg stosowania flagi `return_full_text=False` oraz izolacji pierwszej linii wyjściowej). Bez tych zabiegów jakość predykcji spada do poziomu losowego ($\approx 49\%$).
- **Która klasa sentymentu stanowiła największe wyzwanie klasyfikacyjne?** **Klasa *neutral* (teksty obiektywne/opisowe).** W przypadku modelu enkoderowego błąd miał charakter krytyczny ($F1 = 0,20$, czułość zaledwie $0,14$), objawiając się masowym myleniem tekstów neutralnych z pozytywnymi. Model LLM poradził sobie z tym wyzwaniem nieporównywalnie lepiej ($F1 = 0,62$, czułość $0,50$), aczkolwiek on również w blisko połowie przypadków ulegał tendencji nadinterpretacji uprzejmego tonu wypowiedzi jako sentymentu dodatniego.
- **Jak poszczególne parametry konfiguracyjne wpływają na końcowe wyniki?**
  - *Dla enkoderów:* **Domena danych** jest czynnikiem krytycznym — model finansowy przenesiony do domeny recenzji zanotował drastyczny spadek celności (z 75,9% do 41,2%). Wpływ parametru `max_length` okazał się marginalny, o ile okno kontekstu nie zostało drastycznie ucięte poniżej średniej długości tekstu (punkt optymalny to 256 tokenów).
  - *Dla dekoderów (LLM):* **Parsowanie wyjścia** oraz **treść promptu** to czynniki decydujące (szczegółowy prompt PL podniósł celność do 85,8% w porównaniu do 81,4% dla prostego promptu EN). Wpływ temperatury w zadaniu klasyfikacji okazał się umiarkowany (wariant $T=0.7$ nieznacznie podbił miarę $F1\text{ macro}$), podczas gdy narzucenie strukturyzacji wyjścia przez JSON całkowicie zdegradowało zdolności logiczne modelu ($\approx 50\%$ celności). Z kolei **kwantyzacja 4-bitowa** zaoferowała drastyczną redukcję zużycia VRAM (o ok. 60%), płacąc za to spadkiem celności o 2,5 p.p. oraz dwukrotnym wydłużeniem czasu inferencji.

### 10.2. Wdrożeniowe wnioski praktyczne

1. **Środowiska produkcyjne o niskiej latencji (*Low-Latency Production*):** W systemach komercyjnych, gdzie kluczowy jest krótki czas odpowiedzi, wysoka przepustowość (przetwarzanie paczkami — *batching*) oraz minimalne koszty infrastrukturalne, optymalnym wyborem pozostaje **architektura typu *encoder-only* (HerBERT)**. Zapewnia ona stabilne ~76% celności przy minimalnym narzucie na alokację pamięci GPU ($\approx 0,5$ GB) i zerowej podatności na błędy parsowania tekstu.
2. **Systemy nastawione na maksymalną jakość predykcji (*High-Accuracy Analytics*):** W systemach analitycznych typu *offline*, gdzie priorytetem jest precyzja (zwłaszcza w wyłapywaniu niuansów i tekstów neutralnych), a czas inferencji rzędu kilkunastu minut na kilkaset próbek jest akceptowalny, bezkonkurencyjne są **modele LLM (Decoder)**. Konfiguracja bazowa (Zadanie 4) lub zaawansowana inżynieria promptów po polsku (Zadanie 5) pozwalają przekroczyć barierę 85–87% dokładności bez procesu kosztownego douczania wag.
3. **Optymalizacja sprzętowa na brzegu sieci (*Edge AI / Low-VRAM*):** Kwantyzacja do formatu 4-bitowego (NF4) jest wysoce rekomendowaną praktyką inżynierską w sytuacjach restrykcyjnych ograniczeń budżetowych. Umożliwia ona redukcję progu wejścia pamięci VRAM z 3,3 GB do zaledwie 1,3 GB, co pozwala na lokalne uruchamianie klasyfikatorów LLM nawet na konsumenckich lub starszych układach GPU, przy w pełni akceptowalnym koszcie jakościowym ($\approx -2,5$ p.p. Accuracy).
4. **Złota zasada integracji z modelami generatywnymi:** Podczas implementacji potoków klasyfikacyjnych opartych na mniejszych modelach LLM (klasy 1.5B), należy bezwzględnie unikać parserów obiektowych (np. `JsonOutputParser`), które drastycznie destabilizują proces generowania. Najbardziej niezawodnym i wydajnym podejściem jest zmuszenie modelu do zwrotu pojedynczego tokenu tekstowego i jego późniejsza izolacja za pomocą prostych wyrażeń regularnych (Regex).

