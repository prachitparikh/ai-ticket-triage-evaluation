"""Score every method that has predictions and write the comparison.

    python scripts/evaluate_all.py

Reads results/rules/, results/ml/ and every results/llm/<model>/<split>_responses.jsonl
that exists, and writes:

    results/scores/<method>__<split>.json      all measures for one method on one split
    results/comparison_<split>.csv              one row per method
    results/confusion/<method>__<split>__<field>.csv
    results/thresholds/<method>__<split>.csv    coverage vs accuracy when routing automatically
    results/calibration/<method>__<split>.csv   stated confidence vs how often it was right
    results/errors/<method>__test.csv           every test ticket the method got wrong
    results/llm/<model>/<split>_run_facts.json  tokens, cost, latency, validity per run
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triage import DATA, RESULTS  # noqa: E402
from triage.evaluate import (calibration, confusion, llm_predictions, merged, run_facts, scores,  # noqa: E402
                             threshold_table, write_json)
from triage.llm import load_predictions  # noqa: E402

SPLITS = {"dev": "dev.csv", "test": "test.csv", "reference_seen_wording": "reference_seen_wording.csv"}
HEADLINE = ["category_accuracy", "team_accuracy", "priority_accuracy", "all_three_right", "category_macro_f1",
            "p1_recall", "p1_precision", "p1_rated_p3_or_lower", "under_prioritised", "security_to_trust",
            "injection_followed", "other_language_all_three_right", "mixed_all_three_right",
            "false_urgency_priority_right", "understated_p1_right"]


def methods(split: str) -> dict[str, pd.DataFrame]:
    out = {}
    for name in ("rules", "ml"):
        f = RESULTS / name / f"{split}_predictions.csv"
        if f.exists():
            out[name] = pd.read_csv(f, keep_default_na=False, na_values=[""])
    for f in sorted((RESULTS / "llm").glob(f"*/{split}_responses.jsonl")):
        records = load_predictions(f)
        model = f.parent.name
        out[f"llm_{model}"] = llm_predictions(records)
        write_json(f.parent / f"{split}_run_facts.json", run_facts(records))
    return out


def save_csv(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index, lineterminator="\n", float_format="%.4f")


def main() -> None:
    for split, file in SPLITS.items():
        gold = pd.read_csv(DATA / "eval" / file, keep_default_na=False)
        rows = []
        for name, pred in methods(split).items():
            df = merged(gold, pred)
            s = scores(df)
            write_json(RESULTS / "scores" / f"{name}__{split}.json", s)
            rows.append({"method": name, "tickets": s["tickets"], "answered": s["answered"], **{k: s[k] for k in HEADLINE}})
            for field in ("category", "team", "priority"):
                save_csv(confusion(df, field), RESULTS / "confusion" / f"{name}__{split}__{field}.csv", index=True)
            if "confidence" in df and df["confidence"].notna().any():
                save_csv(threshold_table(df), RESULTS / "thresholds" / f"{name}__{split}.csv")
                save_csv(calibration(df), RESULTS / "calibration" / f"{name}__{split}.csv")
            if split == "test":
                wrong = df[(df["category"] != df["gold_category"]) | (df["team"] != df["gold_team"]) | (df["priority"] != df["gold_priority"])]
                keep = ["ticket_id", "plan", "subject", "body", "flags", "gold_category", "category", "gold_team", "team",
                        "gold_priority", "priority"] + [c for c in ("confidence", "needs_human", "reason") if c in df]
                save_csv(wrong[keep], RESULTS / "errors" / f"{name}__test.csv")
        save_csv(pd.DataFrame(rows), RESULTS / f"comparison_{split}.csv")
        print(f"{split}: scored {', '.join(r['method'] for r in rows)}")


if __name__ == "__main__":
    main()
