import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib.pyplot as plt
import pandas as pd


results = pd.read_csv("outputs/runs/full_agent_predictions_with_confidence.csv")
results["correct"] = results["gold_intent"] == results["pred_intent"]
results["confidence_bin"] = pd.cut(
    results["confidence"],
    bins=[0, 0.3, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    include_lowest=True,
)
calibration = results.groupby("confidence_bin", observed=False)["correct"].agg(
    ["mean", "count"]
)
print(calibration)
os.makedirs("report", exist_ok=True)
calibration["mean"].plot(kind="bar", title="Accuracy by Confidence Bin")
plt.ylabel("Accuracy")
plt.tight_layout()
plt.savefig("report/confidence_calibration.png")
print("Saved report/confidence_calibration.png")