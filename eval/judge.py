import os
from dotenv import load_dotenv

load_dotenv()

JUDGE_RUBRIC = """Score this customer support reply on a 1-5 scale for each criterion:

1. Groundedness: Does the reply avoid inventing facts not present in the customer
   message or reference reply? (1=hallucinates specifics, 5=fully grounded)
2. Relevance: Does it actually address the customer's issue? (1=off-topic, 5=directly relevant)
3. Tone: Does it sound like a helpful, professional support agent? (1=robotic/rude, 5=natural and warm)
4. Helpfulness: Would this reply genuinely help resolve or progress the issue? (1=useless, 5=very helpful)

Customer message: {text}
Reference reply (what a good agent said historically): {reference}
Generated reply to evaluate: {generated}

Respond in this exact format, nothing else:
Groundedness: <score>
Relevance: <score>
Tone: <score>
Helpfulness: <score>
Overall: <average of the four scores, one decimal place>
Justification: <one sentence>"""

def judge_single_reply(text, reference, generated):
    prompt = JUDGE_RUBRIC.format(text=text, reference=reference, generated=generated)
    from src.pipeline import call_llm_with_retry
    raw = call_llm_with_retry(prompt)

    scores = {}
    for line in raw.split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            scores[key.strip()] = val.strip()
    return scores

def score_reply_grounding(results_df):
    import time
    all_scores = []
    for i, row in results_df.iterrows():
        scores = judge_single_reply(row['text'], row['gold_reply_reference'], row['pred_reply'])
        try:
            overall = float(scores.get("Overall", 0))
        except ValueError:
            overall = 0
        all_scores.append({**scores, "id": row['id'], "overall_numeric": overall})
        if i % 20 == 0:
            print(f"Judged {i}/{len(results_df)}")
        time.sleep(0.1)

    scores_df = pd.DataFrame(all_scores)
    scores_df.to_csv("outputs/runs/judge_scores.csv", index=False)

    return {
        "average_score": scores_df['overall_numeric'].mean(),
        "scores_df": scores_df
    }

import pandas as pd  # needed for score_reply_grounding above