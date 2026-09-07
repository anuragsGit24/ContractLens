import argparse
import json
import re
from pathlib import Path

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_curve

from backend.schemas.contracts import Clause
from backend.services.document_graph import build_document_graph, find_internal_contradictions
from backend.services.law_checker import check_against_law
from backend.services.model_singleton import embed
from backend.services.risk_scorer import score_all_clauses

RISK_LEVELS = ["HIGH", "MEDIUM", "LOW"]

def evaluate_retrieval(dataset, law_checks):
    hits = {1: 0, 3: 0, 5: 0}
    eligible = 0
    law_by_index = {check.clause_index: check for check in law_checks}

    for idx, item in enumerate(dataset, start=1):
        gt_sections = item["ground_truth"]["relevant_statute_sections"]
        law_check = law_by_index.get(idx)
        
        law_matches = []
        if law_check and hasattr(law_check, "law_matches"):
            law_matches = getattr(law_check, "law_matches", [])

        predictions = []
        for match in law_matches:
            # Ultra-robust extraction: handles both dicts and objects
            match_data = match if isinstance(match, dict) else (match.__dict__ if hasattr(match, "__dict__") else {})
            payload = match_data.get("payload") if isinstance(match_data, dict) else None

            def _extract_field(keys):
                for key in keys:
                    if isinstance(match_data, dict) and match_data.get(key):
                        return str(match_data.get(key))
                    if isinstance(payload, dict) and payload.get(key):
                        return str(payload.get(key))
                return ""

            act_title = _extract_field(["act_full_name", "act_title", "act"]).strip()
            section_number = _extract_field(["section_number", "section", "act_number"]).strip()

            act_lower = act_title.lower()
            if "contract" in act_lower or "ica" in act_lower:
                acronym = "ICA"
            elif "penal" in act_lower or "ipc" in act_lower:
                acronym = "IPC"
            elif "constitution" in act_lower:
                acronym = "CONSTITUTION"
            else:
                acronym = act_title

            predicted = f"{acronym} {section_number}".strip()
            if predicted:
                predictions.append(predicted)

        print(f"[Retrieval Debug] Clause: {item['clause_id']} | Ground Truth: {gt_sections} | Predicted: {predictions}")

        if not gt_sections:
            continue

        eligible += 1
        for k in [1, 3, 5]:
            top_predictions = [p.lower().strip() for p in predictions[:k]]
            normalized_gt = [s.lower().strip() for s in gt_sections]
            
            if any(section in top_predictions for section in normalized_gt):
                hits[k] += 1

    recalls = {k: (hits[k] / eligible if eligible else 0.0) for k in [1, 3, 5]}
    table = pd.DataFrame(
        {
            "Metric": ["Recall@1", "Recall@3", "Recall@5"],
            "Value (%)": [round(recalls[1] * 100, 2), round(recalls[3] * 100, 2), round(recalls[5] * 100, 2)],
        }
    )
    return table

def build_contradiction_pairs(dataset):
    pairs = set()
    for item in dataset:
        source = item["clause_id"]
        for target in item["ground_truth"].get("contradicts_with", []):
            pair = tuple(sorted([source, target]))
            pairs.add(pair)
    return pairs

def evaluate_contradictions(dataset, clauses, clause_id_by_index, output_dir):
    all_clause_ids = [item["clause_id"] for item in dataset]
    gt_pairs = build_contradiction_pairs(dataset)

    _, edges, _ = build_document_graph(clauses)
    contradictions = find_internal_contradictions(clauses=clauses, edges=edges)

    pred_pairs = set()
    score_by_pair = {}
    for item in contradictions:
        clause_a = clause_id_by_index.get(item.clause_a_index)
        clause_b = clause_id_by_index.get(item.clause_b_index)
        if not clause_a or not clause_b:
            continue
        pair = tuple(sorted([clause_a, clause_b]))
        pred_pairs.add(pair)
        score_by_pair[pair] = max(score_by_pair.get(pair, 0.0), float(item.contradiction_score))

    tp = len(gt_pairs & pred_pairs)
    fp = len(pred_pairs - gt_pairs)
    fn = len(gt_pairs - pred_pairs)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    table = pd.DataFrame(
        {
            "Metric": ["Precision", "Recall", "F1-Score"],
            "Value (%)": [round(precision * 100, 2), round(recall * 100, 2), round(f1 * 100, 2)],
        }
    )

    all_pairs = []
    for i in range(len(all_clause_ids)):
        for j in range(i + 1, len(all_clause_ids)):
            all_pairs.append((all_clause_ids[i], all_clause_ids[j]))

    y_true = []
    y_score = []
    for pair in all_pairs:
        label = 1 if pair in gt_pairs else 0
        score = score_by_pair.get(pair, 0.0) 
        y_true.append(label)
        y_score.append(score)

    try:
        precision_curve, recall_curve, _ = precision_recall_curve(y_true, y_score)
        plt.figure(figsize=(6, 4))
        plt.plot(recall_curve, precision_curve, color="#1f77b4", linewidth=2)
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        plt.title("Contradiction Detection Precision-Recall Curve")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_dir / "contradiction_pr_curve.png", dpi=300)
        plt.close()
    except Exception as e:
        print("Skipped PR curve generation due to lack of pairs.")

    return table

def evaluate_risk(dataset, clauses, vectors, output_dir):
    y_true = []
    y_pred = []

    risks = score_all_clauses(clauses, clause_vectors=vectors)
    risk_by_index = {risk.clause_index: risk for risk in risks}

    for idx, item in enumerate(dataset, start=1):
        y_true.append(item["ground_truth"]["risk_level"].upper())
        
        risk = risk_by_index.get(idx)
        raw_pred = str(getattr(risk, "risk_level", "LOW") if risk else "LOW").upper()
        
        final_pred = "LOW"
        if "HIGH" in raw_pred:
            final_pred = "HIGH"
        elif "MEDIUM" in raw_pred:
            final_pred = "MEDIUM"
            
        y_pred.append(final_pred)

    overall_acc = accuracy_score(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred, labels=RISK_LEVELS)

    rows = []
    for label in RISK_LEVELS:
        mask = [gt == label for gt in y_true]
        support = sum(mask)
        correct = sum(1 for gt, pred in zip(y_true, y_pred) if gt == label and pred == label)
        acc = correct / support if support else 0.0
        rows.append({"Class": label, "Accuracy (%)": round(acc * 100, 2), "Support": support})

    rows.append({"Class": "Overall", "Accuracy (%)": round(overall_acc * 100, 2), "Support": len(y_true)})
    table = pd.DataFrame(rows)

    sns.set_theme(style="white", font_scale=1.0)
    plt.figure(figsize=(6, 4.5))
    ax = sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", cbar=True,
        xticklabels=["High", "Medium", "Low"], yticklabels=["High", "Medium", "Low"]
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Risk Classification Confusion Matrix")
    plt.tight_layout()
    plt.savefig(output_dir / "risk_confusion_matrix.png", dpi=300)
    plt.close()

    return table

def resolve_input_path(cli_path):
    candidates = []
    if cli_path: candidates.append(Path(cli_path))
    candidates.extend([Path("data/evaluation_data/eval_dataset.json"), Path("data/evaluation_data/eval.json"), Path("eval_dataset.json"), Path("eval.json")])
    for path in candidates:
        if path.exists(): return path
    raise FileNotFoundError("No evaluation dataset found.")

def load_dataset(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def prepare_clauses(dataset):
    clauses = []
    clause_id_by_index = {}
    for idx, item in enumerate(dataset, start=1):
        clause_id = str(item.get("clause_id", idx))
        clause = Clause(index=idx, label=clause_id, text=item["text"])
        clauses.append(clause)
        clause_id_by_index[idx] = clause_id
    return clauses, clause_id_by_index

def print_table(title, df):
    separator = "=" * 72
    print("\n" + separator)
    print(title)
    print(separator)
    print(df.to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description="Run evaluation metrics for ContractLens.")
    parser.add_argument("--input", help="Path to eval_dataset.json", default="data/evaluation_data/eval_dataset.json")
    parser.add_argument("--output", help="Directory to store plots", default="outputs/evaluation")
    args = parser.parse_args()

    input_path = resolve_input_path(args.input)
    dataset = load_dataset(input_path)

    clauses, clause_id_by_index = prepare_clauses(dataset)
    vectors = embed([clause.text[:1200] for clause in clauses])
    
    law_checks = check_against_law(clauses=clauses, clause_vectors=vectors, top_k_raw=12, top_k_final=5)

    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    table1 = evaluate_retrieval(dataset, law_checks)
    print_table("Table 1: Statute Retrieval Performance", table1)

    table2 = evaluate_contradictions(dataset, clauses, clause_id_by_index, output_dir)
    print_table("Table 2: Contradiction Detection Performance", table2)

    table3 = evaluate_risk(dataset, clauses, vectors, output_dir)
    print_table("Table 3: Risk Classification Accuracy", table3)

if __name__ == "__main__":
    main()