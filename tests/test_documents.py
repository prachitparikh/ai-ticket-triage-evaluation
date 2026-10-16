"""The headline numbers in the documents match the results they were written from.

If a result changes (a re-run, a fix to the scoring), these fail until the documents are updated.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from triage import RESULTS

ROOT = Path(__file__).resolve().parents[1]
HAIKU, SONNET = "llm_claude-haiku-5-5", "llm_claude-sonnet-5-5"


def doc(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def pct(x: float, places: int = 1) -> str:
    return f"{x * 100:.{places}f}%"


def money(x: float) -> str:
    return f"${x:,.0f}"


comp = pd.read_csv(RESULTS / "comparison_test.csv").set_index("method")
bc = json.loads((RESULTS / "business_case.json").read_text())
options = {o["method"]: o for o in bc["options"]}
cautious = bc["cautious_view"]
spend = json.loads((RESULTS / "evaluation_spend.json").read_text())
facts = {m: json.loads((RESULTS / "llm" / m.removeprefix("llm_") / "test_triage_v3_run_facts.json").read_text())
         for m in (HAIKU, SONNET)}
rounds = pd.read_csv(RESULTS / "dev_rounds.csv")
accept = json.loads((RESULTS / "acceptance_test_summary.json").read_text())

EXPECTED = [
    ("README.md", pct(comp.loc[HAIKU, "team_accuracy"]) + " sent to the right team"),
    ("README.md", f"{round(comp.loc[HAIKU, 'p1_recall'] * 38)} of 38 P1 tickets rated P1"),
    ("README.md", f"against {round(comp.loc['rules', 'p1_recall'] * 38)} for the rules"),
    ("README.md", f"${options[HAIKU]['model_cost_per_month_usd']:.2f} a month in model cost"),
    ("README.md", f"${spend['total_usd']:.2f} for {spend['requests']:,} requests"),
    ("docs/01_business_case.md", f"**{money(cautious['monthly_saving_usd'])}**"),
    ("docs/01_business_case.md", f"**{cautious['payback_months']} months**"),
    ("docs/01_business_case.md", f"| {money(options[HAIKU]['monthly_saving_vs_today_usd'])} | {options[HAIKU]['payback_months']} months |"),
    ("docs/01_business_case.md", f"| C. Claude Haiku 5.5 | Passes all eight | {pct(comp.loc[HAIKU, 'all_three_right'])} |"),
    ("docs/01_business_case.md", f"| D. Claude Sonnet 5.5 | Passes all eight | {pct(comp.loc[SONNET, 'all_three_right'])} |"),
    ("docs/06_evaluation_results.md", f"| {pct(comp.loc['rules', 'team_accuracy'])} ✗ | {pct(comp.loc['ml', 'team_accuracy'])} ✗ | {pct(comp.loc[HAIKU, 'team_accuracy'])} ✓ |"),
    ("docs/06_evaluation_results.md", f"| {pct(comp.loc[HAIKU, 'all_three_right'])} | {pct(comp.loc[SONNET, 'all_three_right'])} |"),
    ("docs/06_evaluation_results.md", f"{facts[HAIKU]['latency_ms_p95'] / 1000:.1f} s ✓ | {facts[SONNET]['latency_ms_p95'] / 1000:.1f} s ✓"),
    ("docs/06_evaluation_results.md", "300 of 300 / " + pct(rounds.query("round == 4 and model == 'claude-haiku-5-5'")["all_three_right"].iloc[0])),
    ("docs/07_cost_model.md", f"**${facts[HAIKU]['cost_usd_per_ticket']:.5f}** | **${facts[SONNET]['cost_usd_per_ticket']:.4f}**"),
    ("docs/07_cost_model.md", f"**{spend['requests']:,}** | **${spend['total_usd']:.2f}**"),
    ("docs/07_cost_model.md", f"| C. Claude Haiku 5.5 | {options[HAIKU]['reassignments_per_month']} |"),
]


@pytest.mark.parametrize("name,text", EXPECTED, ids=[f"{n}:{t[:40]}" for n, t in EXPECTED])
def test_document_states_the_current_result(name, text):
    assert text in doc(name)


def test_recommendation_is_the_one_the_rule_picks():
    assert bc["recommended_method"] == HAIKU
    assert "Recommend Claude Haiku 5.5" in doc("docs/10_decision_log.md")


def test_documents_claim_a_pass_only_where_the_table_shows_one():
    assert accept[HAIKU]["passes_all"] and accept[SONNET]["passes_all"]
    assert accept["rules"]["failed"] == ["AC-1", "AC-2", "AC-3", "AC-4", "AC-5"]
    assert accept["ml"]["failed"] == ["AC-1", "AC-2", "AC-3", "AC-4", "AC-5"]
    assert "Both Claude models pass all eight acceptance criteria" in doc("docs/06_evaluation_results.md")


def test_every_test_miss_is_explained():
    text = doc("docs/06_evaluation_results.md")
    for m in (HAIKU, SONNET):
        for ticket in pd.read_csv(RESULTS / "errors" / f"{m}__test.csv")["ticket_id"]:
            assert ticket in text, ticket
