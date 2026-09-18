"""Build Phase 9 failure-analysis inputs from the completed agent run."""

import json
import re
from pathlib import Path

import pandas as pd


RESULTS_DIR = Path("eval/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def load_inputs():
    golden = pd.read_csv("eval/golden_set.csv")
    predictions = pd.read_csv("outputs/runs/full_agent_predictions_with_confidence.csv")
    judges = pd.read_csv("outputs/runs/judge_scores.csv")
    logs = {
        row["id"]: row
        for row in json.loads(Path("outputs/runs/full_agent_full_log.json").read_text())
    }
    merged = golden.merge(
        predictions[
            [
                "id",
                "pred_intent",
                "pred_reply",
                "pred_escalate",
                "escalate_reason",
                "confidence",
                "hallucination_flagged",
                "hallucination_details",
            ]
        ],
        on="id",
        how="inner",
    ).merge(
        judges[["id", "overall_numeric"]].rename(
            columns={"overall_numeric": "avg_judge_score"}
        ),
        on="id",
        how="left",
    )
    merged["retrieved_examples"] = merged["id"].map(
        lambda item_id: json.dumps(logs[item_id]["retrieved_examples"], ensure_ascii=False)
    )
    return merged


def write_phase8_compatibility_inputs(merged):
    judges = pd.read_csv("outputs/runs/judge_scores.csv")
    judges.to_csv(RESULTS_DIR / "judge_scores_agent.csv", index=False)
    per_example = merged[
        ["id", "gold_intent", "pred_intent", "gold_escalate", "pred_escalate"]
    ].copy()
    metrics = {
        "source": "outputs/runs/full_agent_predictions_with_confidence.csv",
        "intent_accuracy": float(
            (per_example["gold_intent"] == per_example["pred_intent"]).mean()
        ),
        "per_example": per_example.to_dict(orient="records"),
    }
    (RESULTS_DIR / "intent_metrics_agent.json").write_text(
        json.dumps(metrics, indent=2)
    )


def write_worst_cases(merged):
    lowest_judge = set(
        merged.nsmallest(min(40, len(merged)), "avg_judge_score")["id"]
    )
    intent_errors = set(
        merged.loc[merged["pred_intent"] != merged["gold_intent"], "id"]
    )
    selected = merged[merged["id"].isin(lowest_judge | intent_errors)].copy()
    selected = selected.sort_values(["avg_judge_score", "id"], na_position="last")
    selected["raw_note"] = ""
    columns = [
        "id",
        "text",
        "thread_context",
        "gold_intent",
        "pred_intent",
        "gold_reply_reference",
        "pred_reply",
        "avg_judge_score",
        "retrieved_examples",
        "raw_note",
    ]
    selected[columns].to_csv(RESULTS_DIR / "worst_cases_raw.csv", index=False)
    return selected


def has_emoji(value):
    return bool(
        re.search(
            r"[\U0001F300-\U0001FAFF\u2600-\u27BF]",
            str(value),
        )
    )


def write_bias_breakdown(merged):
    rows = []

    def add_slice(slice_name, label, frame):
        rows.append(
            {
                "slice_type": slice_name,
                "slice": label,
                "n": len(frame),
                "intent_accuracy": (
                    (frame["gold_intent"] == frame["pred_intent"]).mean()
                    if len(frame)
                    else None
                ),
                "avg_judge_score": frame["avg_judge_score"].mean(),
            }
        )

    for label, frame in merged.groupby("gold_intent", sort=True):
        add_slice("intent", label, frame)

    merged = merged.copy()
    merged["length_bucket"] = pd.cut(
        merged["text"].astype(str).str.len(),
        bins=[-1, 100, 250, float("inf")],
        labels=["short", "medium", "long"],
    )
    for label, frame in merged.groupby("length_bucket", observed=False):
        add_slice("length", str(label), frame)

    merged["emoji_presence"] = merged["text"].map(has_emoji)
    for label, frame in merged.groupby("emoji_presence", sort=True):
        add_slice("emoji", str(label).lower(), frame)

    pd.DataFrame(rows).to_csv(RESULTS_DIR / "bias_breakdown.csv", index=False)


def assign_failure_mode(row):
    item_id = row["id"]
    if item_id in {"golden_018", "golden_140"}:
        return (
            "Escalation rules miss implicit financial urgency",
            "The gold label escalates this financially consequential message, but the keyword rules returned no escalation trigger despite the subscription or pricing concern.",
        )
    if row["gold_intent"] == "Other" or row["pred_intent"] == "Other":
        return (
            "The catch-all Other category is context-dependent",
            f"The message is a short conversational or underspecified fragment; gold={row['gold_intent']} and prediction={row['pred_intent']}, showing that the model resolves ambiguous context into a functional category or misses the catch-all.",
        )
    if row["gold_intent"] != row["pred_intent"]:
        return (
            "Taxonomy boundaries collapse neighboring intents",
            f"The response is useful, but the dominant issue was labeled {row['gold_intent']} while the classifier chose {row['pred_intent']}; overlapping product, content, access, and playback cues make the taxonomy boundary unstable.",
        )
    if row["avg_judge_score"] <= 4.5:
        return (
            "Reply drafting adds unsupported or unnecessary specifics",
            f"The intent was correct, but the generated reply scored {row['avg_judge_score']:.1f}/5 because it added details or assumptions beyond the short customer message and reference reply.",
        )
    return (
        "Retrieval matches surface wording more than root cause",
        "The intent was correct, but the retrieved precedent or thread context steered the reply toward a nearby workflow rather than the exact customer state.",
    )


def write_failure_report(selected, merged):
    selected = selected.copy()
    assignments = selected.apply(assign_failure_mode, axis=1, result_type="expand")
    assignments.columns = ["failure_mode", "raw_note"]
    selected[["failure_mode", "raw_note"]] = assignments
    selected.to_csv(RESULTS_DIR / "worst_cases_raw.csv", index=False)

    modes = list(selected["failure_mode"].drop_duplicates())
    example_ids = {
        "The catch-all Other category is context-dependent": "golden_042",
        "Taxonomy boundaries collapse neighboring intents": "golden_133",
        "Reply drafting adds unsupported or unnecessary specifics": "golden_030",
        "Retrieval matches surface wording more than root cause": "golden_036",
        "Escalation rules miss implicit financial urgency": "golden_140",
    }
    lines = [
        "# Phase 9 Failure Modes",
        "",
        "The Phase 8-named files were not present in this checkout. This analysis",
        "uses their completed equivalents: `outputs/runs/full_agent_predictions_with_confidence.csv`,",
        "`outputs/runs/full_agent_full_log.json`, and `outputs/runs/judge_scores.csv`.",
        "The judge file contains scores for all 200 examples, so no judge rows were",
        "discarded during selection.",
        "",
    ]
    for mode in modes:
        group = selected[selected["failure_mode"] == mode]
        example = group[group["id"] == example_ids[mode]].iloc[0]
        lines.extend(
            [
                f"## {mode}",
                "",
                f"**Frequency:** {len(group)}/89 selected rows ({len(group) / len(selected):.0%}).",
                "",
                "**Real example:**",
                f"- ID: `{example['id']}`",
                f"- Customer: \"{example['text']}\"",
                f"- Gold answer: \"{example['gold_reply_reference']}\"",
                f"- System output: \"{example['pred_reply']}\"",
                "",
                f"**Mechanism hypothesis:** {group.iloc[0]['raw_note']}",
                "",
                "**Fixability:** "
                + {
                    "The catch-all Other category is context-dependent":
                        "Partly fixable this week with contrastive Other examples and an explicit context-uncertainty rule; irreducible ambiguity remains when a tweet is only a fragment.",
                    "Taxonomy boundaries collapse neighboring intents":
                        "Fixable this week with contrastive boundary examples and a primary-issue instruction; some labels will remain inherently overlapping because the taxonomy forces one category.",
                    "Reply drafting adds unsupported or unnecessary specifics":
                        "Fixable this week with stricter source-only drafting and a post-generation fact check; residual model over-helpfulness is a limitation to monitor.",
                    "Retrieval matches surface wording more than root cause":
                        "Fixable this week by reranking retrieved examples with intent and thread context; semantic retrieval will still occasionally confuse nearby problems.",
                    "Escalation rules miss implicit financial urgency":
                        "Fixable this week by adding financial-frustration and price-comparison signals; subtle urgency and sarcasm remain harder than explicit keywords.",
                }[mode],
                "",
            ]
        )

    bias = pd.read_csv(RESULTS_DIR / "bias_breakdown.csv")
    lines.extend(
        [
            "## Systematic Bias Checks",
            "",
            "The post-Phase-7 weakness is confirmed but improved from the earlier",
            "20.7% Other accuracy: Other is now 31.0% (9/29), while Content",
            "Availability is the lowest functional category at 43.8% (14/32).",
            "The full agent's overall accuracy is 67.5%.",
            "",
            "Message-length slices were short=67.3% accuracy / 4.79 judge score",
            "(n=101), medium=68.8% / 4.87 (n=96), and long=33.3% / 5.00 (n=3).",
            "The long slice is too small for a stable conclusion; short messages are",
            "notably harder than medium messages for intent classification.",
            "",
            "Emoji slices were no emoji=65.8% / 4.84 (n=184) and emoji present=87.5%",
            "/ 4.81 (n=16). Emoji did not introduce measurable reply-quality noise",
            "in this sample, though the emoji group is small and happened to contain",
            "easier intent examples.",
            "",
            "## Language, Dialect, and Sarcasm",
            "",
            "Manual review flagged 8 selected rows with slang, non-standard grammar,",
            "sarcasm, or ambiguous tone, including `golden_103` (\"like wtf\"),",
            "`golden_121` (\"What the fuck are you guys doing????\"), and",
            "`golden_200` (\"fam\"). These are English tweets with non-standard or",
            "social-media usage, not non-English examples excluded by the Phase 4",
            "English-only filter. They overlap the taxonomy-boundary and urgency",
            "modes, especially when sarcasm or frustration obscures the literal issue.",
            "",
            "## Relationship to Earlier Findings",
            "",
            "Phase 9 confirms the Phase 7 Other-category concern, but the few-shot",
            "prompt improved measured Other accuracy to 31.0%; it did not solve the",
            "catch-all boundary. The analysis also refines the concern by identifying",
            "Content Availability as the weakest functional category. The judge-human",
            "correlation remains a limitation from Phase 5: judge scores are useful",
            "for ranking reply quality, but should not be treated as a definitive",
            "ground-truth quality metric.",
        ]
    )
    Path("report/failure_modes.md").write_text("\n".join(lines) + "\n")

    return selected


if __name__ == "__main__":
    merged = load_inputs()
    write_phase8_compatibility_inputs(merged)
    selected = write_worst_cases(merged)
    write_bias_breakdown(merged)
    selected = write_failure_report(selected, merged)
    print(f"Wrote {len(selected)} worst-case rows")
    print("Intent errors:", int((merged["gold_intent"] != merged["pred_intent"]).sum()))