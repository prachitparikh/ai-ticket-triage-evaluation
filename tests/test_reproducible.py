"""Everything in data/ and results/ can be rebuilt and matches what is committed."""

import filecmp
import json

import pytest

import generate_tickets
from triage import DATA, RESULTS


@pytest.fixture(scope="module")
def regenerated(tmp_path_factory):
    out = tmp_path_factory.mktemp("data")
    generate_tickets.main(out)
    return out


@pytest.mark.parametrize("rel", ["history/tickets_2026_04_09.csv", "eval/dev.csv", "eval/test.csv",
                                 "eval/reference_seen_wording.csv", "reference/customers.csv"])
def test_generator_reproduces_committed_data(regenerated, rel):
    assert filecmp.cmp(regenerated / rel, DATA / rel, shallow=False), rel


def test_history_and_eval_wording_never_overlap():
    g = generate_tickets.Gen(1)
    for intent in generate_tickets.INTENTS:
        for key in ("body", "subj"):
            items = intent[key]
            if len(items) < 2:
                continue
            g.wording = 0
            seen = {g.phrase(items) for _ in range(200)}
            g.wording = 1
            new = {g.phrase(items) for _ in range(200)}
            assert not seen & new, (intent["code"], key)


def test_test_set_has_the_rare_cases_the_plan_promises():
    import pandas as pd
    t = pd.read_csv(DATA / "eval" / "test.csv", keep_default_na=False)
    flags = t["flags"]
    assert (t["gold_priority"] == "P1").sum() >= 25
    assert flags.str.contains("injection").sum() >= 10
    assert flags.str.contains("lang_").sum() >= 10
    assert flags.str.contains("mixed").sum() >= 25


def test_every_test_response_belongs_to_a_test_ticket():
    import pandas as pd
    ids = set(pd.read_csv(DATA / "eval" / "test.csv")["ticket_id"])
    for f in (RESULTS / "llm").glob("*/test_*_responses.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            assert json.loads(line)["ticket_id"] in ids
