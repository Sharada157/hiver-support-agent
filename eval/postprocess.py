import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

os.makedirs("outputs/runs", exist_ok=True)

# ============================================================
# 1. Diagnostic: confirm the fallback bug is actually gone (no API cost)
# ============================================================
simple = pd.read_csv("outputs/runs/simple_baseline_predictions.csv")
agent = pd.read_csv("outputs/runs/full_agent_predictions.csv")

matching = (simple['pred_intent'].values == agent['pred_intent'].values)
print(f"[Diagnostic] Identical predictions vs simple baseline: {matching.sum()}/{len(matching)}")
if matching.sum() > 180:
    print("WARNING: still suspiciously high overlap - fallback bug may persist")

# ============================================================
# 2. Rebuild full 3-way metrics table (no API cost, reads saved CSVs)
# ============================================================
def compute_metrics(results_df, name):
    intent_accuracy = (results_df['gold_intent'] == results_df['pred_intent']).mean()
    gold_esc = results_df['gold_escalate'].astype(bool)
    pred_esc = results_df['pred_escalate'].astype(bool)
    esc_precision = precision_score(gold_esc, pred_esc, zero_division=0)
    esc_recall = recall_score(gold_esc, pred_esc, zero_division=0)
    esc_f1 = f1_score(gold_esc, pred_esc, zero_division=0)
    per_category = results_df.assign(
        correct=results_df['gold_intent'] == results_df['pred_intent']
    ).groupby('gold_intent')['correct'].mean()
    return {
        "name": name, "intent_accuracy": intent_accuracy,
        "escalation_precision": esc_precision, "escalation_recall": esc_recall,
        "escalation_f1": esc_f1, "per_category_accuracy": per_category.to_dict()
    }

trivial = pd.read_csv("outputs/runs/trivial_baseline_predictions.csv")
summary = pd.DataFrame([
    compute_metrics(trivial, "Trivial Baseline"),
    compute_metrics(simple, "Simple Baseline"),
    compute_metrics(agent, "Full Agent"),
])
summary.to_csv("outputs/runs/metrics_summary.csv", index=False)
print("\n[Metrics] Saved outputs/runs/metrics_summary.csv")
print(summary[['name', 'intent_accuracy', 'escalation_f1']])

# ============================================================
# 3. Save "Other" category failure examples (no API cost)
# ============================================================
other_failures = agent[(agent['gold_intent'] == 'Other') & (agent['pred_intent'] != 'Other')]
other_failures[['id', 'text', 'gold_intent', 'pred_intent']].to_csv(
    "outputs/runs/other_category_failures.csv", index=False
)
print(f"\n[Failures] 'Other' misclassifications saved: {len(other_failures)} rows -> outputs/runs/other_category_failures.csv")

# ============================================================
# 4. LLM-judge scoring on a COST-LIMITED subsample only (this costs API calls)
# ============================================================
JUDGE_SAMPLE_SIZE = 60  # deliberately smaller than 200 to conserve API budget

if os.path.exists("outputs/runs/judge_scores.csv"):
    print("\n[Judge] judge_scores.csv already exists - skipping to avoid re-spending tokens")
else:
    from eval.judge import judge_single_reply
    import time

    judge_sample = agent.sample(n=min(JUDGE_SAMPLE_SIZE, len(agent)), random_state=9)
    all_scores = []
    for i, (_, row) in enumerate(judge_sample.iterrows()):
        scores = judge_single_reply(row['text'], row['gold_reply_reference'], row['pred_reply'])
        try:
            overall = float(scores.get("Overall", 0))
        except ValueError:
            overall = 0
        all_scores.append({**scores, "id": row['id'], "overall_numeric": overall})
        print(f"[Judge] {i+1}/{len(judge_sample)}")
        time.sleep(13)  # stay under free-tier rate limit

    scores_df = pd.DataFrame(all_scores)
    scores_df.to_csv("outputs/runs/judge_scores.csv", index=False)
    print(f"\n[Judge] Average reply grounding score: {scores_df['overall_numeric'].mean():.2f}/5")
    print(f"[Judge] Scored on a {len(judge_sample)}-example subsample (not all 200) to conserve API quota - document this in your report")

# ============================================================
# 5. Prepare human-agreement subset from the SAME judged examples (no extra API cost)
# ============================================================
judge_scores = pd.read_csv("outputs/runs/judge_scores.csv")
human_check_size = min(25, len(judge_scores))
human_check = judge_scores.sample(n=human_check_size, random_state=7)

human_check_full = human_check.merge(
    agent[['id', 'text', 'gold_reply_reference', 'pred_reply']], on='id'
)
human_check_full.to_csv("eval/judge_agreement_sample.csv", index=False)
print(f"\n[Agreement] Saved {human_check_size}-example subset to eval/judge_agreement_sample.csv")
print("Open this file, add your own 1-5 scores per row by hand, then run the correlation check separately.")