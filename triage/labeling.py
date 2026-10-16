"""The labeling guide (docs/03) as code.

The generator uses these functions to set the gold labels, so the labels in
data/ follow exactly the rules a person would apply from the guide. Keeping the
rules here, rather than inside the generator, means a test can check the guide
and the data against each other.
"""

from __future__ import annotations

import json
from functools import lru_cache

from . import CONFIG

PRIORITY_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}


@lru_cache(maxsize=1)
def taxonomy() -> dict:
    with open(CONFIG / "taxonomy.json", encoding="utf-8") as f:
        return json.load(f)


def category_codes() -> list[str]:
    return [c["code"] for c in taxonomy()["categories"]]


def team_codes() -> list[str]:
    return [t["code"] for t in taxonomy()["teams"]]


def default_team(category: str) -> str:
    for c in taxonomy()["categories"]:
        if c["code"] == category:
            return c["team"]
    raise KeyError(category)


def gold_team(category: str, plan: str, sso: bool = False, dispute: bool = False) -> str:
    """Default team for the category, with the two routing exceptions."""
    if category == "ACCESS" and sso:
        return "INTEGRATIONS"                       # RX-1
    if category == "BILLING" and dispute and plan == "Enterprise":
        return "CUSTOMER_SUCCESS"                   # RX-2
    return default_team(category)


def gold_priority(kind: str, scope: str = "user", blocking: bool = False, plan: str = "Starter") -> str:
    """Priority from what the ticket says.

    kind      what sort of problem it is (see the generator's intent table)
    scope     'user' (one person), 'team' (a group of users), 'account' (everyone at the customer)
    blocking  True when the ticket says they cannot work and has no workaround
    """
    enterprise_blocked = plan == "Enterprise" and blocking
    if kind in ("security_incident", "data_loss"):
        return "P1"
    if kind in ("outage", "defect", "access"):
        if scope == "account" and blocking:
            return "P1"
        if (scope == "team" and blocking) or enterprise_blocked:
            return "P2"
        return "P3"
    if kind in ("integration", "data_issue"):
        if (scope in ("team", "account") and blocking) or enterprise_blocked:
            return "P2"
        return "P3"
    if kind == "billing_error":
        return "P2"
    if kind in ("billing_admin", "security_request", "cancellation", "general"):
        return "P3"
    if kind in ("howto", "feature", "quote"):
        return "P4"
    raise ValueError(f"unknown kind {kind!r}")


def combine(first: dict, second: dict) -> dict:
    """Mixed-ticket rule: keep the issue with the higher priority; on a tie, the first."""
    return second if PRIORITY_ORDER[second["priority"]] < PRIORITY_ORDER[first["priority"]] else first
