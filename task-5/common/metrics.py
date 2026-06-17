"""Obliczanie i wyświetlanie metryk klasyfikacji."""

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

from .labels import CLASS_NAMES


def evaluate_predictions(y_true: list[str], y_pred: list[str]) -> dict:
    """
    Liczy standardowe metryki dla klasyfikacji 3-klasowej.

    Zwraca słownik z accuracy, f1_macro, f1_weighted, raportem tekstowym
    i macierzą pomyłek.
    """
    accuracy = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, labels=CLASS_NAMES, average="macro", zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, labels=CLASS_NAMES, average="weighted", zero_division=0)

    report = classification_report(
        y_true,
        y_pred,
        labels=CLASS_NAMES,
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, y_pred, labels=CLASS_NAMES)

    return {
        "accuracy": accuracy,
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted,
        "classification_report": report,
        "confusion_matrix": matrix,
        "confusion_matrix_labels": CLASS_NAMES,
    }


def print_evaluation(results: dict, title: str = "Wyniki ewaluacji") -> None:
    """Wypisuje metryki w czytelnej formie."""
    print(f"\n{'=' * 50}")
    print(title)
    print(f"{'=' * 50}")
    print(f"Accuracy:    {results['accuracy']:.4f}")
    print(f"F1 (macro):  {results['f1_macro']:.4f}")
    print(f"F1 (weighted): {results['f1_weighted']:.4f}")
    print("\nRaport per klasa:")
    print(results["classification_report"])
    print("Macierz pomyłek (wiersze = prawda, kolumny = predykcja):")
    print(f"Klasy: {results['confusion_matrix_labels']}")
    print(results["confusion_matrix"])
