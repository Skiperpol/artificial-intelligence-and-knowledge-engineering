"""
Mapowanie etykiet między zbiorem PolEmo2.0-IN a odpowiedziami modeli.

Zbiór używa identyfikatorów __label__meta_*.
Modele encoder/decoder zwracają zwykle słowa po angielsku (positive, negative, neutral).
"""

# Etykieta klasy mieszanej — wykluczamy ją z zadania
AMBIGUOUS_LABEL = "__label__meta_amb"

# Mapowanie surowych etykiet ze zbioru na czytelne nazwy klas
DATASET_LABEL_TO_CLASS = {
    "__label__meta_plus_m": "plus",
    "__label__meta_minus_m": "minus",
    "__label__meta_zero": "neutral",
    AMBIGUOUS_LABEL: "ambiguous",
}

# Klasy używane w ewaluacji (bez ambiguous)
CLASS_NAMES = ["minus", "neutral", "plus"]

# Słowa kluczowe, które model może wygenerować → nasza klasa
_TEXT_TO_CLASS = {
    # negatywne
    "minus": "minus",
    "negative": "minus",
    "neg": "minus",
    "negatywny": "minus",
    "negatywna": "minus",
    "zły": "minus",
    "zla": "minus",
    "złe": "minus",
    # pozytywne
    "plus": "plus",
    "positive": "plus",
    "pos": "plus",
    "pozytywny": "plus",
    "pozytywna": "plus",
    "dobry": "plus",
    "dobra": "plus",
    "dobre": "plus",
    # neutralne
    "neutral": "neutral",
    "zero": "neutral",
    "neutralny": "neutral",
    "neutralna": "neutral",
    "opisowy": "neutral",
}


def map_dataset_label(raw_label: str) -> str:
    """Zamienia etykietę ze zbioru (np. __label__meta_plus_m) na nazwę klasy."""
    if raw_label not in DATASET_LABEL_TO_CLASS:
        raise ValueError(f"Nieznana etykieta ze zbioru: {raw_label}")
    return DATASET_LABEL_TO_CLASS[raw_label]


def map_text_to_class(text: str) -> str | None:
    """
    Próbuje dopasować dowolny tekst z modelu do jednej z klas.

    Zwraca None, gdy nie udało się rozpoznać klasy (np. halucynacja LLM).
    """
    if text is None:
        return None

    cleaned = text.strip().lower()

    # Dokładne dopasowanie całego tekstu
    if cleaned in _TEXT_TO_CLASS:
        return _TEXT_TO_CLASS[cleaned]

    # Szukamy słowa kluczowego w odpowiedzi (np. "Class: positive")
    for keyword, class_name in _TEXT_TO_CLASS.items():
        if keyword in cleaned:
            return class_name

    return None
