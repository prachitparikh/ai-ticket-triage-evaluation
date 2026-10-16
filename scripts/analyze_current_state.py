"""How triage performs today: today's rules applied to six months of tickets.

    python scripts/analyze_current_state.py

The routing and priority decisions are real: the helpdesk rules are run over
every ticket in the history and compared with the gold labels. What a wrong
decision costs in time comes from a simple queue model whose assumptions are
in config/current_state_model.json (docs/02 explains them). Writes
results/current_state/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from triage import CONFIG, DATA, RESULTS  # noqa: E402
from triage.evaluate import write_json  # noqa: E402
from triage.labeling import PRIORITY_ORDER, taxonomy  # noqa: E402
from triage.rules import classify  # noqa: E402

SEED = 20261002


def main() -> dict:
    m = json.loads((CONFIG / "current_state_model.json").read_text(encoding="utf-8"))
    h = pd.read_csv(DATA / "history" / "tickets_2026_04_09.csv", keep_default_na=False)
    pred = pd.DataFrame([classify(r.subject, r.body) for r in h.itertuples()])
    h["rule_team"], h["rule_priority"], h["rule_category"] = pred["team"], pred["priority"], pred["category"]
    h["month"] = h["created_at"].str[:7]

    rng = np.random.default_rng(SEED)
    n = len(h)
    wait_median = h["rule_priority"].map(m["queue_wait_minutes_median_by_assigned_priority"]).astype(float)
    queue = wait_median * np.exp(rng.normal(0, m["queue_wait_spread"], n))
    misrouted = (h["rule_team"] != h["gold_team"]).to_numpy()
    bounces = misrouted.astype(int) + (misrouted & (rng.random(n) < m["second_bounce_share"])).astype(int)
    delay = np.zeros(n)
    for k in (1, 2):
        extra = m["reassignment_delay_hours_median"] * 60 * np.exp(rng.normal(0, m["reassignment_delay_spread"], n))
        delay += np.where(bounces >= k, extra, 0)
    h["first_response_minutes"] = np.round(queue + delay, 1)
    h["reassignments"] = bounces

    targets = {p["code"]: p["first_response_target_minutes"] for p in taxonomy()["priorities"]}
    h["target_minutes"] = h["gold_priority"].map(targets)
    h["met_target"] = h["first_response_minutes"] <= h["target_minutes"]

    months = h["month"].nunique()
    reassign_hours = h["reassignments"].sum() * m["reassignment_handling_minutes"] / 60
    triage_hours = n * m["triage_check_minutes_per_ticket"] / 60
    by_priority = (h.groupby("gold_priority")
                    .agg(tickets=("ticket_id", "size"), met_target=("met_target", "mean"),
                         median_first_response_min=("first_response_minutes", "median"),
                         misrouted=("reassignments", lambda s: float((s > 0).mean())),
                         rated_lower_by_rules=("rule_priority", lambda s: 0.0))
                    .reset_index())
    lower = h["rule_priority"].map(PRIORITY_ORDER) > h["gold_priority"].map(PRIORITY_ORDER)
    by_priority["rated_lower_by_rules"] = by_priority["gold_priority"].map(lower.groupby(h["gold_priority"]).mean())
    by_category = (h.groupby("gold_category")
                    .agg(tickets=("ticket_id", "size"), misrouted=("reassignments", lambda s: float((s > 0).mean())),
                         category_right=("rule_category", lambda s: 0.0)).reset_index())
    by_category["category_right"] = by_category["gold_category"].map(
        (h["rule_category"] == h["gold_category"]).groupby(h["gold_category"]).mean())
    monthly = (h.groupby("month").agg(tickets=("ticket_id", "size"), misrouted=("reassignments", lambda s: int((s > 0).sum())),
                                       reassignments=("reassignments", "sum")).reset_index())
    closed = {k: round(float((h[f"closed_{k}"] == h[f"gold_{k}"]).mean()), 4) for k in ("category", "team", "priority")}

    p1 = h[h["gold_priority"] == "P1"]
    summary = {
        "tickets": n, "months": months, "tickets_per_month": round(n / months),
        "misrouted_share": round(float(misrouted.mean()), 4),
        "reassignments_total": int(h["reassignments"].sum()),
        "reassignments_per_month": round(h["reassignments"].sum() / months),
        "agent_hours_per_month_on_reassignment": round(reassign_hours / months, 1),
        "agent_hours_per_month_on_triage_check": round(triage_hours / months, 1),
        "category_right_by_rules": round(float((h["rule_category"] == h["gold_category"]).mean()), 4),
        "priority_right_by_rules": round(float((h["rule_priority"] == h["gold_priority"]).mean()), 4),
        "p1_tickets": int(len(p1)), "p1_per_month": round(len(p1) / months, 1),
        "p1_rated_p1_by_rules": round(float((p1["rule_priority"] == "P1").mean()), 4),
        "p1_met_30_min_target": round(float(p1["met_target"].mean()), 4),
        "p1_median_first_response_min": round(float(p1["first_response_minutes"].median()), 1),
        "security_tickets_to_trust_by_rules": round(float((h.loc[h["gold_team"] == "TRUST", "rule_team"] == "TRUST").mean()), 4),
        "closed_label_agreement_with_guide": closed,
        "all_tickets_met_target": round(float(h["met_target"].mean()), 4),
        "model_assumptions": "config/current_state_model.json",
    }
    out = RESULTS / "current_state"
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "summary.json", summary)
    for name, df in (("by_priority", by_priority), ("by_category", by_category), ("by_month", monthly)):
        df.to_csv(out / f"{name}.csv", index=False, lineterminator="\n", float_format="%.4f")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
