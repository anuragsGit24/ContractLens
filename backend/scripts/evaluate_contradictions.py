from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sentence_transformers import CrossEncoder
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from tqdm import tqdm

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
DEFAULT_INPUT = REPO_ROOT / "data" / "evaluation_data" / "task2_evaluation - data.csv.csv"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "evaluation_data" / "task2_evaluation_results.csv"
MODEL_NAME = "cross-encoder/nli-deberta-v3-base"
TRUE_VALUES = {"true", "1", "yes", "y", "t"}
FALSE_VALUES = {"false", "0", "no", "n", "f"}


def parse_bool(value: Any) -> bool:
    """Parse only explicit boolean-like values; never use eval() on CSV data."""
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if pd.isna(value):
        raise ValueError("empty boolean value")
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError(f"unsupported boolean value: {value!r}")


def softmax(scores: Any) -> np.ndarray:
    """Convert logits to probabilities with numerical stability."""
    logits = np.asarray(scores, dtype=np.float64).reshape(-1)
    if logits.size == 0 or not np.all(np.isfinite(logits)):
        raise ValueError("model returned empty or non-finite scores")
    shifted = logits - np.max(logits)
    probabilities = np.exp(shifted)
    return probabilities / probabilities.sum()


def evaluate(input_path: Path = DEFAULT_INPUT, output_path: Path = DEFAULT_OUTPUT) -> dict[str, float | int]:
    required_columns = {
        "pair_id", "contract_source", "clause_a_text", "clause_b_text", "your_label",
        "your_reasoning", "system_prediction", "system_confidence", "correct",
    }
    dataframe = pd.read_csv(input_path)
    missing = required_columns.difference(dataframe.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    dataframe["your_label"] = dataframe["your_label"].map(parse_bool)
    dataframe["system_prediction"] = False
    dataframe["system_confidence"] = 0.0
    dataframe["correct"] = False
    dataframe["evaluation_error"] = ""

    model = CrossEncoder(MODEL_NAME)
    for index, row in tqdm(dataframe.iterrows(), total=len(dataframe), desc="Evaluating contradiction pairs"):
        try:
            text_a = str(row["clause_a_text"]).strip()
            text_b = str(row["clause_b_text"]).strip()
            if not text_a or not text_b:
                raise ValueError("clause text is empty")

            scores = model.predict([[text_a, text_b]])[0]
            probabilities = softmax(scores)
            contradiction_probability = float(probabilities[0])
            prediction = contradiction_probability > 0.50

            dataframe.at[index, "system_prediction"] = prediction
            dataframe.at[index, "system_confidence"] = contradiction_probability
            dataframe.at[index, "correct"] = prediction == row["your_label"]
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            dataframe.at[index, "evaluation_error"] = message
            print(f"Row {index} ({row.get('pair_id', 'unknown')}) failed: {message}")

    valid = dataframe["evaluation_error"].eq("")
    if not valid.any():
        raise RuntimeError("No rows were evaluated successfully.")
    labels = dataframe.loc[valid, "your_label"].astype(bool).astype(int).to_numpy()
    predictions = dataframe.loc[valid, "system_prediction"].astype(bool).astype(int).to_numpy()
    confidence = dataframe.loc[valid, "system_confidence"].astype(float).to_numpy()

    metrics: dict[str, float | int] = {
        "rows_total": int(len(dataframe)),
        "rows_evaluated": int(valid.sum()),
        "rows_failed": int((~valid).sum()),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1_score": float(f1_score(labels, predictions, zero_division=0)),
        "accuracy": float(accuracy_score(labels, predictions)),
        "auc_roc": float(roc_auc_score(labels, confidence)) if len(np.unique(labels)) == 2 else float("nan"),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    print("\nCross-Encoder Contradiction Evaluation")
    print(f"Input:            {input_path}")
    print(f"Output:           {output_path}")
    print(f"Rows evaluated:   {metrics['rows_evaluated']}/{metrics['rows_total']}")
    print(f"Precision:        {metrics['precision']:.4f}")
    print(f"Recall:           {metrics['recall']:.4f}")
    print(f"F1-Score:         {metrics['f1_score']:.4f}")
    print(f"Accuracy:         {metrics['accuracy']:.4f}")
    print(f"AUC-ROC:          {metrics['auc_roc']:.4f}")
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark a cross-encoder on legal contradiction pairs.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    evaluate(arguments.input, arguments.output)
