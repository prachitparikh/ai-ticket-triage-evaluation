"""The labeling guide (docs/03), the taxonomy file, the prompt and the code must say the same thing."""

import json
import re

import pytest

from triage import CONFIG, PROMPTS
from triage.labeling import category_codes, combine, default_team, gold_priority, gold_team, team_codes

FINAL_PROMPT = json.loads((CONFIG / "evaluation.json").read_text())["final_prompt"]


def test_every_default_team_exists():
    assert {default_team(c) for c in category_codes()} <= set(team_codes())


def test_final_prompt_names_every_category_and_team():
    text = (PROMPTS / f"{FINAL_PROMPT}.md").read_text(encoding="utf-8")
    for code in category_codes() + team_codes():
        assert re.search(rf"\b{code}\b", text), code


def test_schema_enums_match_taxonomy():
    schema = json.loads((CONFIG / "triage_output.schema.json").read_text())
    assert schema["properties"]["category"]["enum"] == category_codes()
    assert set(schema["properties"]["team"]["enum"]) == set(team_codes())


@pytest.mark.parametrize("kind,scope,blocking,plan,core,expected", [
    ("billing_error", "user", False, "Starter", True, "P2"),          # wrong charge, any plan
    ("billing_error", "user", False, "Enterprise", True, "P2"),
    ("access", "account", True, "Business", True, "P1"),              # nobody can sign in
    ("access", "team", False, "Business", True, "P3"),                # workaround
    ("defect", "user", True, "Enterprise", True, "P2"),               # Enterprise blocked
    ("defect", "user", True, "Professional", True, "P3"),             # one person, not Enterprise
    ("defect", "account", True, "Business", False, "P2"),             # side feature stops at P2
    ("outage", "account", True, "Starter", True, "P1"),
    ("security_incident", "user", False, "Starter", True, "P1"),
    ("security_request", "user", False, "Starter", True, "P3"),
    ("howto", "user", False, "Enterprise", True, "P4"),
    ("general", "user", False, "Starter", True, "P3"),
])
def test_priority_rules_from_the_guide(kind, scope, blocking, plan, core, expected):
    assert gold_priority(kind, scope, blocking, plan, core=core) == expected


def test_routing_exceptions():
    assert gold_team("ACCESS", "Starter", sso=True) == "INTEGRATIONS"                       # RX-1
    assert gold_team("BILLING", "Enterprise", dispute=True) == "CUSTOMER_SUCCESS"           # RX-2
    assert gold_team("BILLING", "Business", dispute=True) == "BILLING_OPS"
    assert gold_team("BILLING", "Enterprise", dispute=False) == "BILLING_OPS"


def test_mixed_ticket_rule():
    first, second = {"priority": "P3", "id": 1}, {"priority": "P2", "id": 2}
    assert combine(first, second)["id"] == 2
    assert combine({"priority": "P3", "id": 1}, {"priority": "P3", "id": 2})["id"] == 1
