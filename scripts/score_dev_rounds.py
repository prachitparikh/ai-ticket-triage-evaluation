"""Score every dev round, including the ones before the prompt was frozen, and add up the API spend.

    python scripts/score_dev_rounds.py

The dev rounds are kept so the path to prompt v3 can be checked, not just the end point. Each round
is scored against the dev labels that were current when it ran (data/eval/archive/), because the
generator was corrected twice between rounds (DEC-TRI-009, DEC-TRI-010).

Writes results/dev_rounds.csv and results/evaluation_spend.json.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triage import DATA, RESULTS  # noqa: E402
from triage.evaluate import llm_predictions, merged, scores, write_json  # noqa: E402
from triage.llm import load_predictions  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_all import consistency  # noqa: E402

# (round, prompt, response file stem, labels it ran against)
ROUNDS = [
    (1, "triage_v1", "dev_round1_triage_v1", "archive/dev_round1.csv"),
    (2, "triage_v2", "dev_round2_triage_v2", "archive/dev_round2_3.csv"),
    (3, "triage_v2", "dev_round3_triage_v2", "archive/dev_round2_3.csv"),
    (4, "triage_v3", "dev_triage_v3", "dev.csv"),
]


def main() -> None:
    rows = []
    for model_dir in sorted((RESULTS / "llm").glob("claude-*")):
        for rnd, prompt, stem, labels in ROUNDS:
            f = model_dir / f"{stem}_responses.jsonl"
            if not f.exists():
                continue
            records = load_predictions(f)
            gold = pd.read_csv(DATA / "eval" / labels, keep_default_na=False)
            sent = {r["ticket_id"] for r in records}
            s = scores(merged(gold[gold["ticket_id"].isin(sent)], llm_predictions(records)))
            row = {"model": model_dir.name, "round": rnd, "prompt": prompt, "tickets": s["tickets"],
                   "valid_answers": s["answered"], "team_accuracy": s["team_accuracy"],
                   "priority_accuracy": s["priority_accuracy"], "all_three_right": s["all_three_right"],
                   "p1_recall": s["p1_recall"], "repeat_same_all_three": None}
            repeat = f.with_name(f"{stem}_repeat_responses.jsonl")
            if repeat.exists():
                c = consistency(records, load_predictions(repeat))
                row["repeat_same_all_three"] = f"{c['same_all_three']}/{c['tickets_compared']}"
            rows.append(row)
    df = pd.DataFrame(rows).sort_values(["round", "model"])
    df.to_csv(RESULTS / "dev_rounds.csv", index=False, float_format="%.4f", lineterminator="\n")

    spend: dict = {"by_file": {}, "by_model": {}, "requests": 0, "total_usd": 0.0}
    for f in sorted((RESULTS / "llm").glob("claude-*/*_responses.jsonl")):
        records = load_predictions(f)
        usd = round(sum(r.get("cost_usd") or 0 for r in records), 4)
        spend["by_file"][f"{f.parent.name}/{f.name}"] = {"requests": len(records), "usd": usd}
        spend["by_model"][f.parent.name] = round(spend["by_model"].get(f.parent.name, 0) + usd, 4)
        spend["requests"] += len(records)
        spend["total_usd"] = round(spend["total_usd"] + usd, 4)
    spend["note"] = ("List price from config/model_prices.csv, computed from the token counts the API returned. "
                     "Requests the API rejected (dev round 1, Claude Sonnet 5.5) were not billed and are not in these files.")
    write_json(RESULTS / "evaluation_spend.json", spend)
    print(df.to_string(index=False))
    print(spend["by_model"], spend["total_usd"])


if __name__ == "__main__":
    main()
