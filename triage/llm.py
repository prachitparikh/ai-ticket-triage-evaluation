"""Triage with a Claude model through the Anthropic API.

One request per ticket. The system prompt (prompts/triage_v1.md) carries the
labeling guide; the ticket goes in the user turn after redaction; the model must
answer through a single tool whose input schema is config/triage_output.schema.json,
and the answer is validated against that schema again before it is used.

Every response is appended to a JSONL file as it arrives, with token usage,
latency and the request id, so a run can be stopped and resumed, re-scored any
time without calling the API again, and audited afterwards.
"""

from __future__ import annotations

import csv
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

from . import CONFIG, PROMPTS
from .redact import redact

TOOL_NAME = "record_triage"
MAX_TOKENS = 2000   # 400 truncated a third of the answers once the tool was no longer forced (dev round 2)


def load_prompt(version: str = "triage_v1") -> tuple[str, str]:
    text = (PROMPTS / f"{version}.md").read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    body = text[match.end():] if match else text
    return version, body.strip()


def output_schema() -> dict:
    with open(CONFIG / "triage_output.schema.json", encoding="utf-8") as f:
        return json.load(f)


def tool_definition() -> dict:
    schema = output_schema()
    return {"name": TOOL_NAME, "description": schema["description"],
            "input_schema": {k: v for k, v in schema.items() if k not in ("$schema", "title", "description")}}


def ticket_message(row: dict) -> tuple[str, dict]:
    subject, c1 = redact(row["subject"] or "")
    body, c2 = redact(row["body"] or "")
    counts = {k: c1[k] + c2[k] for k in c1}
    # Only what triage needs: no company name, customer id or contact email (BR-TRI-06).
    text = (f"<ticket>\nplan: {row['plan']}\nchannel: {row['channel']}\nsubject: {subject}\n"
            f"body:\n{body}\n</ticket>")
    return text, counts


def prices() -> dict[str, dict[str, float]]:
    with open(CONFIG / "model_prices.csv", newline="", encoding="utf-8") as f:
        return {r["model"]: {k: float(v) for k, v in r.items() if k.endswith("_mtok")} for r in csv.DictReader(f)}


def cost_usd(model: str, usage: dict) -> float:
    p = prices()[model]
    return round((usage.get("input_tokens", 0) * p["input_per_mtok"]
                  + usage.get("output_tokens", 0) * p["output_per_mtok"]
                  + usage.get("cache_creation_input_tokens", 0) * p["cache_write_5m_per_mtok"]
                  + usage.get("cache_read_input_tokens", 0) * p["cache_read_per_mtok"]) / 1_000_000, 6)


def estimate(model: str, rows: list[dict], prompt_version: str = "triage_v1") -> dict:
    """Rough cost before a run: about 4 characters per token, no caching assumed."""
    _, system = load_prompt(prompt_version)
    fixed = len(system) + len(json.dumps(tool_definition()))
    chars = sum(fixed + len(ticket_message(r)[0]) for r in rows)
    usage = {"input_tokens": chars / 4, "output_tokens": 110 * len(rows)}
    return {"tickets": len(rows), "input_tokens": int(usage["input_tokens"]), "output_tokens": usage["output_tokens"],
            "usd": round(cost_usd(model, usage), 2)}


def parse(response, schema: dict) -> tuple[str, dict | None, str | None]:
    block = next((b for b in response.content if getattr(b, "type", None) == "tool_use" and b.name == TOOL_NAME), None)
    if block is None:
        return "no_tool_use", None, "the model did not call record_triage"
    try:
        jsonschema.validate(block.input, schema)
    except jsonschema.ValidationError as e:
        return "schema_error", dict(block.input), f"{'/'.join(map(str, e.absolute_path))}: {e.message}"
    return "ok", dict(block.input), None


def classify_one(client, model: str, row: dict, system: str, prompt_version: str, schema: dict, tool: dict,
                 temperature: float | None = None, sdk: str | None = None) -> dict:
    user, redactions = ticket_message(row)
    kwargs = dict(model=model, max_tokens=MAX_TOKENS,
                  system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                  tools=[tool], tool_choice={"type": "auto"},  # Sonnet 5.5 rejects a forced tool choice (dev round 1)
                  messages=[{"role": "user", "content": user}])
    if temperature is not None:
        kwargs["temperature"] = temperature
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    record = {"ticket_id": row["ticket_id"], "model": model, "prompt": prompt_version, "sdk": sdk,
              "temperature": temperature if temperature is not None else "model default",
              "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"), "redactions": redactions}
    try:
        response = client.messages.create(**kwargs)
    except Exception as e:  # noqa: BLE001 - every failure is recorded, the run carries on
        record.update(status="api_error", error=f"{type(e).__name__}: {str(e)[:300]}",
                      latency_ms=int((time.perf_counter() - t0) * 1000), output=None, usage=None)
        return record
    usage = {k: getattr(response.usage, k, 0) or 0 for k in
             ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")}
    status, output, error = parse(response, schema)
    text = " ".join(getattr(b, "text", "") for b in response.content if getattr(b, "type", None) == "text").strip()
    record.update(status=status, error=error, output=output, usage=usage, cost_usd=cost_usd(model, usage),
                  latency_ms=int((time.perf_counter() - t0) * 1000), stop_reason=response.stop_reason,
                  request_id=getattr(response, "_request_id", None), response_model=response.model,
                  text_before_tool=text[:500] or None)
    return record


def done_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with open(path, encoding="utf-8") as f:
        return {json.loads(line)["ticket_id"] for line in f if line.strip() and json.loads(line)["status"] != "api_error"}


def run(client, model: str, rows: list[dict], out: Path, prompt_version: str = "triage_v1", workers: int = 4,
        temperature: float | None = None, sdk: str | None = None, progress=print) -> dict:
    out.parent.mkdir(parents=True, exist_ok=True)
    _, system = load_prompt(prompt_version)
    schema, tool = output_schema(), tool_definition()
    todo = [r for r in rows if r["ticket_id"] not in done_ids(out)]
    lock = threading.Lock()
    counts = {"ok": 0, "schema_error": 0, "no_tool_use": 0, "api_error": 0}
    with ThreadPoolExecutor(max_workers=workers) as pool, open(out, "a", encoding="utf-8", newline="\n") as f:
        futures = [pool.submit(classify_one, client, model, r, system, prompt_version, schema, tool, temperature, sdk)
                   for r in todo]
        for i, fut in enumerate(as_completed(futures), start=1):
            rec = fut.result()
            with lock:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                counts[rec["status"]] += 1
            if i % 25 == 0 or i == len(futures):
                progress(f"  {i}/{len(futures)} done  {counts}")
    return {"skipped_already_done": len(rows) - len(todo), **counts}


def load_predictions(path: Path) -> list[dict]:
    """One prediction per ticket from a responses file; the last good answer wins if a ticket was retried."""
    best: dict[str, dict] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["ticket_id"] not in best or rec["status"] == "ok":
                best[rec["ticket_id"]] = rec
    return list(best.values())
