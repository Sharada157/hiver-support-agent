import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score

from src.baselines import simple_predict, trivial_predict


os.makedirs("outputs/baselines", exist_ok=True)
golden_df = pd.read_csv("eval/golden_set.csv")
knowledge_base = pd.read_csv("data/processed/knowledge_base.csv")


def evaluate_baseline(predict_fn, name, use_kb=False):
    results = []
    for index, row in golden_df.iterrows():
        if use_kb:
            prediction = predict_fn(row["text"], row["thread_context"], knowledge_base)
        else:
            prediction = predict_fn(row["text"], row["thread_context"])
        results.append({
            "id": row["id"],
            "text": row["text"],
            "gold_intent": row["gold_intent"],
            "pred_intent": prediction["intent"],
            "gold_escalate": row["gold_escalate"],
            "pred_escalate": prediction["escalate"],
            "gold_reply_reference": row["gold_reply_reference"],
            "pred_reply": prediction["reply"],
        })
        if index % 40 == 0:
            print(f"[{name}] {index}/{len(golden_df)}")
    results_df = pd.DataFrame(results)
    results_df.to_csv(f"outputs/baselines/{name}_predictions.csv", index=False)
    return results_df


def compute_metrics(results_df, name):
    intent_accuracy = (results_df["gold_intent"] == results_df["pred_intent"]).mean()
    gold_escalate = results_df["gold_escalate"].astype(bool)
    pred_escalate = results_df["pred_escalate"].astype(bool)
    escalation_precision = precision_score(gold_escalate, pred_escalate, zero_division=0)
    escalation_recall = recall_score(gold_escalate, pred_escalate, zero_division=0)
    escalation_f1 = f1_score(gold_escalate, pred_escalate, zero_division=0)
    per_category = results_df.assign(
        correct_intent=results_df["gold_intent"] == results_df["pred_intent"]
    ).groupby("gold_intent")["correct_intent"].mean()
    print(f"\n=== {name} ===")
    print(f"Intent accuracy: {intent_accuracy:.2%}")
    print(
        f"Escalation precision: {escalation_precision:.2%}, "
        f"recall: {escalation_recall:.2%}, f1: {escalation_f1:.2%}"
    )
    print(per_category)
    return {
        "name": name,
        "intent_accuracy": intent_accuracy,
        "escalation_precision": escalation_precision,
        "escalation_recall": escalation_recall,
        "escalation_f1": escalation_f1,
        "per_category_accuracy": per_category.to_dict(),
    }


if __name__ == "__main__":
    print("Running trivial baseline...")
    trivial_results = evaluate_baseline(trivial_predict, "trivial_baseline")
    trivial_metrics = compute_metrics(trivial_results, "Trivial Baseline")

    print("\nRunning simple baseline (regex intent + TF-IDF reply)...")
    simple_results = evaluate_baseline(simple_predict, "simple_baseline", use_kb=True)
    simple_metrics = compute_metrics(simple_results, "Simple Baseline")

    pd.DataFrame([trivial_metrics, simple_metrics]).to_csv(
        "outputs/baselines/baseline_metrics_summary.csv", index=False
    )
    print("\nSaved outputs/baselines/baseline_metrics_summary.csv")
