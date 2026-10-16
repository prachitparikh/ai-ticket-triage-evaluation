"""Turn the test results into the monthly numbers the business case uses.

    python scripts/business_case.py

For each option scored on the test set:

1. Pick the auto-routing threshold on dev: the lowest confidence at which team
   accuracy on the tickets above it is at least 97% (docs/05). Options with no
   confidence (today's rules) route nothing automatically.
2. Run the same queue model as docs/02 over the 500 test tickets, using each
   option's team and priority, to get reassignments and P1 response times.
3. Scale to the 2027 monthly volume and price it with config/business_case.json
   and config/current_state_model.json.

Writes results/business_case.json and results/business_case.csv.
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
from triage.labeling import taxonomy  # noqa: E402

SEED = 20261002
LABELS = {"rules": "A. Today's rules", "ml": "B. In-house text model",
          "llm_claude-haiku-5-5": "C. Claude Haiku 5.5", "llm_claude-sonnet-5-5": "D. Claude Sonnet 5.5"}


def predictions(split: str) -> dict[str, pd.DataFrame]:
    settings = json.loads((CONFIG / "evaluation.json").read_text())
    out = {"rules": pd.read_csv(RESULTS / "rules" / f"{split}_predictions.csv"),
           "ml": pd.read_csv(RESULTS / "ml" / f"{split}_predictions.csv")}
    from triage.evaluate import llm_predictions
    from triage.llm import load_predictions
    for model in settings["models"]:
        f = RESULTS / "llm" / model / f"{split}_{settings['final_prompt']}_responses.jsonl"
        if f.exists():
            out[f"llm_{model}"] = llm_predictions(load_predictions(f))
    return out


def pick_threshold(dev: pd.DataFrame, target: float) -> float | None:
    if "confidence" not in dev or dev["confidence"].isna().all():
        return None
    flagged = dev["needs_human"].fillna(False).astype(bool) if "needs_human" in dev else pd.Series(False, index=dev.index)
    for t in sorted(dev["confidence"].dropna().unique()):
        auto = (dev["confidence"] >= t) & ~flagged & dev["team"].notna()
        if auto.sum() >= 20 and (dev.loc[auto, "team"] == dev.loc[auto, "gold_team"]).mean() >= target:
            return float(t)
    return None


def queue(df: pd.DataFrame, m: dict, rng) -> pd.DataFrame:
    n = len(df)
    assigned = df["priority"].fillna("P3")
    wait = assigned.map(m["queue_wait_minutes_median_by_assigned_priority"]).astype(float).to_numpy()
    queue_min = wait * np.exp(rng.normal(0, m["queue_wait_spread"], n))
    wrong = (df["team"] != df["gold_team"]).to_numpy()
    bounces = wrong.astype(int) + (wrong & (rng.random(n) < m["second_bounce_share"])).astype(int)
    delay = np.zeros(n)
    for k in (1, 2):
        extra = m["reassignment_delay_hours_median"] * 60 * np.exp(rng.normal(0, m["reassignment_delay_spread"], n))
        delay += np.where(bounces >= k, extra, 0)
    return pd.DataFrame({"first_response": queue_min + delay, "bounces": bounces})


def main() -> dict:
    qm = json.loads((CONFIG / "current_state_model.json").read_text())
    bc = json.loads((CONFIG / "business_case.json").read_text())
    targets = {p["code"]: p["first_response_target_minutes"] for p in taxonomy()["priorities"]}
    gold = {s: pd.read_csv(DATA / "eval" / f"{s}.csv", keep_default_na=False) for s in ("dev", "test")}
    dev_pred, test_pred = predictions("dev"), predictions("test")
    volume = bc["monthly_tickets_2027"]
    rows = []
    for name, pred in test_pred.items():
        test = gold["test"].merge(pred, on="ticket_id", how="left")
        dev = gold["dev"].merge(dev_pred[name], on="ticket_id", how="inner") if name in dev_pred else None
        t = pick_threshold(dev, bc["auto_route_target_team_accuracy"]) if dev is not None else None
        if t is None:
            auto = pd.Series(False, index=test.index)
        else:
            flagged = (test["needs_human"].fillna(False).astype(bool) if "needs_human" in test
                       else pd.Series(False, index=test.index))
            auto = (test["confidence"] >= t) & ~flagged & test["team"].notna()
        q = queue(test, qm, np.random.default_rng(SEED))
        p1 = (test["gold_priority"] == "P1").to_numpy()
        scale = volume / len(test)
        reassign = q["bounces"].sum() * scale
        hours_reassign = reassign * qm["reassignment_handling_minutes"] / 60
        hours_check = (len(test) - auto.sum()) * scale * qm["triage_check_minutes_per_ticket"] / 60
        model_cost = float(pred["cost_usd"].sum()) * scale if "cost_usd" in pred else 0.0
        agent_cost = (hours_reassign + hours_check) * qm["loaded_cost_per_agent_hour_usd"]
        overhead = 0.0 if name == "rules" else bc["monthly_run_overhead_hours"] * bc["analyst_cost_per_hour_usd"]
        rows.append({
            "option": LABELS.get(name, name), "method": name,
            "auto_route_threshold": t, "auto_routed_share_test": round(float(auto.mean()), 4),
            "auto_routed_team_accuracy_test": round(float((test.loc[auto, "team"] == test.loc[auto, "gold_team"]).mean()), 4) if auto.any() else None,
            "team_accuracy_test": round(float((test["team"] == test["gold_team"]).mean()), 4),
            "reassignments_per_month": round(reassign),
            "agent_hours_reassigning_per_month": round(hours_reassign, 1),
            "agent_hours_checking_per_month": round(hours_check, 1),
            "p1_within_30_min": round(float((q["first_response"][p1] <= targets["P1"]).mean()), 4),
            "p1_median_first_response_min": round(float(np.median(q["first_response"][p1])), 1),
            "model_cost_per_month_usd": round(model_cost, 2),
            "run_overhead_per_month_usd": round(overhead, 2),
            "monthly_cost_usd": round(agent_cost + model_cost + overhead, 2),
        })
    df = pd.DataFrame(rows)

    # Recommendation rule from docs/05: of the models that pass every criterion, the cheapest,
    # unless a dearer one is clearly better on AC-2 to AC-5 (here: more than 2 points on P1 recall
    # or security routing, or fewer injections followed).
    accept = json.loads((RESULTS / "acceptance_test_summary.json").read_text())
    passing = [m for m in df["method"] if m.startswith("llm_") and accept.get(m, {}).get("passes_all")]
    comp = pd.read_csv(RESULTS / "comparison_test.csv").set_index("method")
    recommended = None
    if passing:
        by_cost = sorted(passing, key=lambda m: df.set_index("method").loc[m, "model_cost_per_month_usd"])
        recommended = by_cost[0]
        for other in by_cost[1:]:
            better = (comp.loc[other, "p1_recall"] - comp.loc[recommended, "p1_recall"] > 0.02
                      or comp.loc[other, "security_to_trust"] - comp.loc[recommended, "security_to_trust"] > 0.02
                      or comp.loc[other, "injection_followed"] < comp.loc[recommended, "injection_followed"])
            if better:
                recommended = other
                break

    # A cautious view for the decision: history's real misroute rate as today's baseline, and for the
    # recommended model only the pilot's own bars (92% team agreement, 60% auto-routed).
    hist = json.loads((RESULTS / "current_state" / "summary.json").read_text())
    def monthly(misroute: float, auto_share: float, model_cost: float, overhead: float) -> dict:
        reassign = volume * misroute * (1 + qm["second_bounce_share"])
        hours = reassign * qm["reassignment_handling_minutes"] / 60 + volume * (1 - auto_share) * qm["triage_check_minutes_per_ticket"] / 60
        return {"reassignments": round(reassign), "agent_hours": round(hours, 1),
                "monthly_cost_usd": round(hours * qm["loaded_cost_per_agent_hour_usd"] + model_cost + overhead, 2)}
    today = monthly(hist["misrouted_share"], 0.0, 0.0, 0.0)
    rec_cost = float(df.set_index("method").loc[recommended, "model_cost_per_month_usd"]) if recommended else 0.0
    cautious = monthly(0.08, 0.60, rec_cost, bc["monthly_run_overhead_hours"] * bc["analyst_cost_per_hour_usd"])
    saving = round(today["monthly_cost_usd"] - cautious["monthly_cost_usd"], 2)
    cautious_view = {"today_from_history": today, "recommended_at_pilot_bars": cautious, "monthly_saving_usd": saving,
                     "payback_months": round(bc["one_off_build_cost_usd"] / saving, 1) if saving > 0 else None,
                     "assumptions": "today: history misroute rate; model: 8% misrouted (92% team agreement, the pilot gate), 60% auto-routed"}
    base = df.loc[df["method"] == "rules", "monthly_cost_usd"].iloc[0]
    df["monthly_saving_vs_today_usd"] = (base - df["monthly_cost_usd"]).round(2)
    df["payback_months"] = df["monthly_saving_vs_today_usd"].apply(
        lambda s: round(bc["one_off_build_cost_usd"] / s, 1) if s > 0 else None)
    df.loc[df["method"] == "rules", "payback_months"] = None
    out = {"monthly_tickets": volume, "one_off_build_cost_usd": bc["one_off_build_cost_usd"],
           "recommended_method": recommended, "cautious_view": cautious_view,
           "note": "Test set over-represents rare and costly tickets, so misroute rates here are harsher than a normal week.",
           "options": df.to_dict(orient="records")}
    write_json(RESULTS / "business_case.json", out)
    df.to_csv(RESULTS / "business_case.csv", index=False, lineterminator="\n")
    print(df.drop(columns=["method"]).to_string(index=False))
    return out


if __name__ == "__main__":
    main()
