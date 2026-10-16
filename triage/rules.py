"""Today's triage: the keyword rules in Northstar's helpdesk.

config/current_routing_rules.csv and config/current_priority_rules.csv are the
helpdesk triggers as they stood on 2 October 2026. The first rule that matches
the subject or body wins. This is the baseline every other approach has to beat.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache

from . import CONFIG


@dataclass(frozen=True)
class Rule:
    rule_id: str
    pattern: re.Pattern | None
    values: tuple[str, ...]


def _load(name: str, value_cols: tuple[str, ...]) -> list[Rule]:
    with open(CONFIG / name, newline="", encoding="utf-8") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: int(r["order"]))
    return [Rule(r["rule_id"], re.compile(r["pattern"], re.I) if r["pattern"] else None,
                 tuple(r[c] for c in value_cols)) for r in rows]


@lru_cache(maxsize=1)
def routing_rules() -> list[Rule]:
    return _load("current_routing_rules.csv", ("set_category", "set_team"))


@lru_cache(maxsize=1)
def priority_rules() -> list[Rule]:
    return _load("current_priority_rules.csv", ("set_priority",))


def _first(rules: list[Rule], text: str) -> Rule:
    for rule in rules:
        if rule.pattern is None or rule.pattern.search(text):
            return rule
    raise RuntimeError("rule table has no default row")


def classify(subject: str, body: str) -> dict:
    text = f"{subject}\n{body}"
    route = _first(routing_rules(), text)
    prio = _first(priority_rules(), text)
    category, team = route.values
    return {"category": category, "team": team, "priority": prio.values[0],
            "rule": route.rule_id, "priority_rule": prio.rule_id}
