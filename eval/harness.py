import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import time
import os
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

from src.pipeline import run_agent
from src.baselines import trivial_predict, simple_predict, offline_predict
from eval.judge import score_reply_grounding

golden_df = pd.read_csv("eval/golden_set.csv")
knowledge_base = pd.read_csv("data/processed/knowledge_base.csv")

def evaluate_system(predict_fn, name, use_kb=False):
    results = []
    for i, row in golden_df.iterrows():
        if use_kb:
            pred = predict_fn(row['text'], row['thread_context'], knowledge_base)
        else:
            pred = predict_fn(row['text'], row['thread_context'])

        results.append({
            "id": row['id'],
            "text": row['text'],
            "gold_intent": row['gold_intent'],
            "pred_intent": pred['intent'],
            "gold_escalate": row['gold_escalate'],
            "pred_escalate": pred['escalate'],
            "gold_reply_reference": row['gold_reply_reference'],
            "pred_reply": pred['reply'],
        })
        if i % 20 == 0:
            print(f"[{name}] {i}/{len(golden_df)}")
        time.sleep(float(os.getenv("EVAL_SLEEP_SECONDS", "13")))

    results_df = pd.DataFrame(results)
    results_df.to_csv(f"outputs/runs/{name}_predictions.csv", index=False)
    return results_df

def compute_metrics(results_df, name):
    intent_accuracy = (results_df['gold_intent'] == results_df['pred_intent']).mean()

    gold_esc = results_df['gold_escalate'].astype(bool)
    pred_esc = results_df['pred_escalate'].astype(bool)
    esc_precision = precision_score(gold_esc, pred_esc, zero_division=0)
    esc_recall = recall_score(gold_esc, pred_esc, zero_division=0)
    esc_f1 = f1_score(gold_esc, pred_esc, zero_division=0)

    per_category = results_df.groupby('gold_intent').apply(
        lambda g: (g['gold_intent'] == g['pred_intent']).mean()
    )

    print(f"\n=== {name} ===")
    print(f"Intent accuracy: {intent_accuracy:.2%}")
    print(f"Escalation precision: {esc_precision:.2%}, recall: {esc_recall:.2%}, f1: {esc_f1:.2%}")
    print("\nPer-category accuracy:")
    print(per_category)

    return {
        "name": name,
        "intent_accuracy": intent_accuracy,
        "escalation_precision": esc_precision,
        "escalation_recall": esc_recall,
        "escalation_f1": esc_f1,
        "per_category_accuracy": per_category.to_dict()
    }

def get_failures(results_df, n=5):
    misclassified = results_df[results_df['gold_intent'] != results_df['pred_intent']]
    return misclassified.head(n)


if __name__ == "__main__":
    os.makedirs("outputs/runs", exist_ok=True)

    run_baselines = os.getenv("RUN_BASELINES", "1").lower() in {"1", "true", "yes"}
    if run_baselines:
        print("Running trivial baseline...")
        trivial_results = evaluate_system(trivial_predict, "trivial_baseline")
        trivial_metrics = compute_metrics(trivial_results, "Trivial Baseline")

        print("\nRunning simple baseline...")
        simple_results = evaluate_system(simple_predict, "simple_baseline", use_kb=True)
        simple_metrics = compute_metrics(simple_results, "Simple Baseline")
    else:
        trivial_metrics = None
        simple_metrics = None

    print("\nRunning full agent (API calls; failures are not silently replaced)...")
    agent_results = evaluate_system(lambda text, ctx: run_agent(text, ctx), "full_agent")
    agent_metrics = compute_metrics(agent_results, "Full Agent")

    print("\nScoring reply grounding via LLM judge (full agent only)...")
    grounding_scores = score_reply_grounding(agent_results)
    print(f"Average reply grounding score: {grounding_scores['average_score']:.2f}/5")

    print("\n=== Failure Examples (Full Agent) ===")
    failures = get_failures(agent_results, n=5)
    for _, row in failures.iterrows():
        print(f"\nText: {row['text']}")
        print(f"Gold: {row['gold_intent']} | Predicted: {row['pred_intent']}")

    summary = pd.DataFrame([metric for metric in [trivial_metrics, simple_metrics, agent_metrics] if metric is not None])
    summary.to_csv("outputs/runs/metrics_summary.csv", index=False)
    print("\nSaved metrics_summary.csv")