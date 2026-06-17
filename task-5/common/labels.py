AMBIGUOUS_LABEL = "__label__meta_amb"

DATASET_LABEL_TO_CLASS = {
    "__label__meta_plus_m": "plus",
    "__label__meta_minus_m": "minus",
    "__label__meta_zero": "neutral",
    AMBIGUOUS_LABEL: "ambiguous",
}

CLASS_NAMES = ["minus", "neutral", "plus"]

_TEXT_TO_CLASS = {
    "minus": "minus",
    "negative": "minus",
    "neg": "minus",
    "negatywny": "minus",
    "negatywna": "minus",
    "zły": "minus",
    "zla": "minus",
    "złe": "minus",
    #--------------------------------
    "plus": "plus",
    "positive": "plus",
    "pos": "plus",
    "pozytywny": "plus",
    "pozytywna": "plus",
    "dobry": "plus",
    "dobra": "plus",
    "dobre": "plus",
    #--------------------------------
    "neutral": "neutral",
    "zero": "neutral",
    "neutralny": "neutral",
    "neutralna": "neutral",
    "opisowy": "neutral",
}


def map_dataset_label(raw_label: str) -> str:
    if raw_label not in DATASET_LABEL_TO_CLASS:
        raise ValueError(f"Nieznana etykieta ze zbioru: {raw_label}")
    return DATASET_LABEL_TO_CLASS[raw_label]


def map_text_to_class(text: str) -> str | None:
    if text is None:
        return None

    cleaned = text.strip().lower()

    if cleaned in _TEXT_TO_CLASS:
        return _TEXT_TO_CLASS[cleaned]

    for keyword, class_name in _TEXT_TO_CLASS.items():
        if keyword in cleaned:
            return class_name

    return None
