# Lista 5 — Klasyfikacja wydźwięku (PolEmo2.0-IN)

Porównanie podejść **encoder-only** (HerBERT) i **decoder-only** (Qwen LLM) na zbiorze `allegro/klej-polemo2-in`.

## Struktura projektu

```
task-5/
├── common/                          # wspólny kod (etykiety, dane, metryki)
├── zadanie-1-eksploracja/           # eksploracja zbioru (10 pkt)
│   └── eksploracja.ipynb
├── zadanie-2-encoder-bazowy/        # HerBERT baseline (20 pkt)
│   └── klasyfikacja_herbert.ipynb
├── zadanie-3-encoder-eksploracja/   # porównanie modeli encoder (20 pkt)
│   └── eksploracja_encoder.ipynb
├── zadanie-4-decoder-llm/           # Qwen LLM baseline (20 pkt)
│   └── klasyfikacja_qwen.ipynb
├── zadanie-5-decoder-eksploracja/   # eksploracja prompt/temp/JSON (30 pkt)
│   └── eksploracja_llm.ipynb
└── requirements.txt
```

## Uruchomienie

### Google Colab (zalecane)

1. Wgraj folder `task-5` na Google Drive lub sklonuj repozytorium.
2. Otwórz notebook w Colab.
3. **Runtime → Change runtime type → T4 GPU**.
4. Uruchamiaj komórki kolejno od góry.

### Lokalnie

```bash
cd task-5
pip install -r requirements.txt
jupyter lab
```

Otwórz notebooki w podfolderach `zadanie-*`.

## Kolejność wykonywania

1. **Zadanie 1** — zawsze pierwsze (sprawdzenie danych).
2. **Zadanie 2** — baseline encoder (wymaga GPU, ale działa też na CPU).
3. **Zadanie 3** — eksploracja encoder (dłużej — kilka modeli).
4. **Zadanie 4** — baseline LLM (wolne; ustaw `SAMPLE_SIZE` na mniejszą liczbę do testu).
5. **Zadanie 5** — eksploracja LLM (najdłuższe; domyślnie `SAMPLE_SIZE=80`).

## Ważne uwagi

- Używamy **tylko splitu `test`**, bez klasy **ambiguous**.
- Mapowanie etykiet jest w `common/labels.py` — kluczowe dla poprawnych wyników.
- W zadaniach 4–5 ustaw `SAMPLE_SIZE = None`, aby uruchomić pełną ewaluację przed oddaniem.

## Biblioteki

| Biblioteka | Zastosowanie |
|------------|--------------|
| `datasets` | Ładowanie PolEmo2.0-IN z Hugging Face |
| `transformers` | Modele encoder i decoder |
| `langchain-core`, `langchain-huggingface` | Prompty i łańcuchy LLM |
| `pydantic`, `JsonOutputParser` | Strukturyzowane parsowanie odpowiedzi LLM |
| `scikit-learn` | Accuracy, F1, classification report |
| `matplotlib`, `seaborn` | Wykresy w zadaniu 1 |

## Źródła

- Zbiór: [allegro/klej-polemo2-in](https://huggingface.co/datasets/allegro/klej-polemo2-in)
- Model encoder: [Voicelab/herbert-base-cased-sentiment](https://huggingface.co/Voicelab/herbert-base-cased-sentiment)
- Model LLM: [Qwen/Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct)
- Lista zadań: `Lista_5_PL.pdf`
