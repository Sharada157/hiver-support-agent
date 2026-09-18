import json
import os
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd

from src.pipeline import run_agent


os.makedirs("outputs/runs", exist_ok=True)


def run_on_dataset(golden_df, output_name, sleep_seconds=13):
    all_logs = []
    for position, (_, row) in enumerate(golden_df.iterrows(), start=1):
        print(f"[{output_name}] {position}/{len(golden_df)}: {row['text'][:60]}...")
        num_turns = row.get("num_turns_in_thread", 1)
        if pd.isna(num_turns):
            num_turns = 1
        result = run_agent(
            row["text"],
            row["thread_context"],
            int(num_turns),
        )
        result.update({
            "id": row["id"],
            "gold_intent": row["gold_intent"],
            "gold_escalate": row["gold_escalate"],
        })
        all_logs.append(result)
        if sleep_seconds and position < len(golden_df):
            time.sleep(sleep_seconds)

    with open(f"outputs/runs/{output_name}_full_log.json", "w") as file:
        json.dump(all_logs, file, indent=2)

    flat_rows = []
    for log in all_logs:
        flat_rows.append({
            "id": log["id"],
            "text": log["input_text"],
            "gold_intent": log["gold_intent"],
            "pred_intent": log["intent"],
            "confidence": log["confidence"],
            "intent_used_fallback": log["intent_used_fallback"],
            "gold_escalate": log["gold_escalate"],
            "pred_escalate": log["escalate"],
            "escalate_reason": log["escalate_reason"],
            "pred_reply": log["reply"],
            "hallucination_flagged": log["hallucination_flagged"],
            "hallucination_details": json.dumps(log["hallucination_details"]),
            "num_turns": log["num_turns"],
            "latency_seconds": log["latency_seconds"],
        })
    output_path = f"outputs/runs/{output_name}_predictions_with_confidence.csv"
    pd.DataFrame(flat_rows).to_csv(output_path, index=False)
    print(f"\nSaved {len(flat_rows)} results to outputs/runs/{output_name}_*")


if __name__ == "__main__":
    golden_df = pd.read_csv("eval/golden_set.csv")
    sleep_seconds = float(os.getenv("PIPELINE_SLEEP_SECONDS", "13"))
    if os.getenv("FULL_RUN") == "1":
        print("=== RUNNING FULL GOLDEN SET (200 examples) ===")
        run_on_dataset(golden_df, "full_agent", sleep_seconds=sleep_seconds)
    else:
        test_batch = golden_df.sample(n=8, random_state=42)
        print("=== RUNNING SMALL TEST BATCH (8 examples) ===")
        run_on_dataset(test_batch, "test_batch", sleep_seconds=sleep_seconds)