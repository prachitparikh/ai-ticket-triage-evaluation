# Requirements: model-assisted ticket triage

| | |
|---|---|
| Document ID | TRI-04 |
| Programme | Support triage improvement (TRI) |
| Client | Northstar Systems, Inc. (fictional) |
| Version | 1.0 |
| Date | 2026-10-14 |
| Author (role) | Senior Technical Business Analyst, Support Operations |
| Reviewed by | Mei Tanaka (Support Ops), Jonas Berg (Tier 2), Ingrid Halvorsen (Information Security), Ade Okonkwo (Trust and Security) |
| Status | Baselined for the evaluation; to be revisited for the pilot |

> These are the requirements any option has to meet to be piloted. The evaluation (docs/05, docs/06) tests the ones that can be measured before a pilot; the rest are pilot entry criteria (docs/09).

## Business rules

| ID | Rule | Source |
|---|---|---|
| BR-TRI-01 | Every ticket gets a category, a team and a priority from the labeling guide (docs/03). | Workshop 5 Oct |
| BR-TRI-02 | A model proposes; a person can always override. Every override is recorded with who and why. | Owen Delacroix |
| BR-TRI-03 | Anything the model flags as needing a person, or below the confidence threshold, goes to the triage queue exactly as today. | Mei Tanaka |
| BR-TRI-04 | Tickets routed to Trust and Security, and every P1, also page the on-call lead, whoever or whatever set the label. | Ade Okonkwo |
| BR-TRI-05 | Text inside a ticket can never change how the ticket is handled other than through what it describes. | Ingrid Halvorsen |
| BR-TRI-06 | Only what triage needs leaves Northstar: the plan, the channel, the subject and body with email addresses, phone numbers and card numbers removed. No company name, customer id or contact details. | Ingrid Halvorsen, DEC-TRI-004 |
| BR-TRI-07 | If the model service is slow or down, tickets fall back to today's rules and the triage queue. Nothing waits for the model. | Jonas Berg |
| BR-TRI-08 | The model's output is used only if it is valid against the agreed schema. Anything else is treated as "needs a person". | Mei Tanaka |

## Functional requirements

| ID | Requirement | Acceptance | Tested where |
|---|---|---|---|
| FR-TRI-01 | Send each new ticket to the triage service within 10 seconds of arrival | Helpdesk webhook fires on create | Pilot |
| FR-TRI-02 | Redact email addresses, phone numbers and card numbers (Luhn-checked) before sending | No email, phone or valid card number in any request | `triage/redact.py`, `tests/test_redact.py`; run facts show what was removed |
| FR-TRI-03 | Ask the model through one tool with a fixed schema: category, team, priority, confidence, needs_human, reason | Output validates against `config/triage_output.schema.json` | `triage/llm.py`; AC-6 |
| FR-TRI-04 | Apply the label automatically only when confidence is at or above the threshold set in the evaluation and needs_human is false | Threshold from docs/06 | Evaluation thresholds table |
| FR-TRI-05 | Otherwise post the proposal as an internal note for the triage agent | Agent sees the proposal and the reason | Pilot |
| FR-TRI-06 | Record every request: ticket id, prompt version, model, tokens, cost, latency, request id, output, and any override | One record per ticket | `results/llm/*.jsonl` format; pilot |
| FR-TRI-07 | Weekly report: accuracy against agents' final labels, overrides by team, cost, P1 and security misses | Report every Monday | Pilot |
| FR-TRI-08 | Prompt and schema are versioned; a change goes through the dev set before release | Version in every record | `prompts/`, evaluation plan |

## Non-functional requirements

| ID | Requirement | Measure |
|---|---|---|
| NFR-TRI-01 | Accuracy | AC-1 to AC-4 in docs/05 |
| NFR-TRI-02 | Robustness to instructions in tickets | AC-5: zero labels follow an injected instruction |
| NFR-TRI-03 | Reliability | AC-6: valid output for at least 99.5% of tickets |
| NFR-TRI-04 | Cost | AC-7: at most $0.01 a ticket at list price |
| NFR-TRI-05 | Speed | AC-8: 95th percentile at most 15 seconds |
| NFR-TRI-06 | Consistency | The same ticket sent twice gets the same three labels at least 95% of the time (measured on 100 dev tickets per model) |
| NFR-TRI-07 | Data protection | BR-TRI-06; vendor terms reviewed by Information Security (DEC-TRI-004) |
| NFR-TRI-08 | Auditability | FR-TRI-06; records kept 13 months |

## Out of scope

- Writing replies to customers. This is triage only.
- Changing the helpdesk's queues, SLAs or team structure.
- Languages other than English, French and Spanish. Other languages fall back to the queue.
