"""The API path without the API: request shape, parsing and file handling."""

import csv
import json
from types import SimpleNamespace as NS

from triage import DATA
from triage.llm import estimate, load_predictions, output_schema, parse, run, tool_definition


def fake_client(answer: dict, stop="tool_use"):
    class Messages:
        calls = []

        def create(self, **kw):
            self.calls.append(kw)
            return NS(content=[NS(type="tool_use", name="record_triage", input=answer)],
                      usage=NS(input_tokens=1000, output_tokens=80, cache_creation_input_tokens=0, cache_read_input_tokens=900),
                      stop_reason=stop, model="claude-haiku-5-5", _request_id="req_x")
    return NS(messages=Messages())


GOOD = {"category": "BILLING", "team": "BILLING_OPS", "priority": "P2", "confidence": 0.9, "needs_human": False, "reason": "Duplicate charge."}


def rows(n=3):
    with open(DATA / "eval" / "dev.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))[:n]


def test_parse_accepts_valid_and_rejects_invalid():
    schema = output_schema()
    assert parse(NS(content=[NS(type="tool_use", name="record_triage", input=GOOD)]), schema)[0] == "ok"
    bad = dict(GOOD, category="MONEY")
    assert parse(NS(content=[NS(type="tool_use", name="record_triage", input=bad)]), schema)[0] == "schema_error"
    assert parse(NS(content=[NS(type="text", text="hello")]), schema)[0] == "no_tool_use"


def test_run_writes_one_record_per_ticket_and_resumes(tmp_path):
    client = fake_client(GOOD)
    out = tmp_path / "r.jsonl"
    first = run(client, "claude-haiku-5-5", rows(), out, prompt_version="triage_v3", progress=lambda *a: None)
    again = run(client, "claude-haiku-5-5", rows(), out, prompt_version="triage_v3", progress=lambda *a: None)
    assert first["ok"] == 3 and again["skipped_already_done"] == 3
    recs = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(recs) == 3 and all(r["prompt"] == "triage_v3" and r["cost_usd"] > 0 for r in recs)
    sent = client.messages.calls[0]
    assert sent["tool_choice"] == {"type": "auto"} and "temperature" not in sent
    assert sent["tools"][0] == tool_definition()


def test_load_predictions_prefers_a_good_answer(tmp_path):
    f = tmp_path / "x.jsonl"
    f.write_text(json.dumps({"ticket_id": "T1", "status": "api_error"}) + "\n" +
                 json.dumps({"ticket_id": "T1", "status": "ok", "output": GOOD}) + "\n")
    assert load_predictions(f)[0]["status"] == "ok"


def test_estimate_is_a_few_cents_for_haiku():
    assert 0 < estimate("claude-haiku-5-5", rows(300))["usd"] < 1
