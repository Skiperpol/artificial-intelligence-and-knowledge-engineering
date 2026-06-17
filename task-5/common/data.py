"""Ładowanie i filtrowanie zbioru PolEmo2.0-IN."""

from datasets import load_dataset

from .labels import AMBIGUOUS_LABEL, map_dataset_label


def load_polemo_test():
    """
    Ładuje split testowy PolEmo2.0-IN i usuwa klasę ambiguous.

    Zwraca listę słowników:
        {"sentence": str, "target": str, "class": str}
    """
    dataset = load_dataset("allegro/klej-polemo2-in", split="test")

    examples = []
    for row in dataset:
        raw_label = row["target"]
        if raw_label == AMBIGUOUS_LABEL:
            continue

        examples.append(
            {
                "sentence": row["sentence"],
                "target": raw_label,
                "class": map_dataset_label(raw_label),
            }
        )

    return examples
