# Evaluation plan

| | |
|---|---|
| Document ID | TRI-05 |
| Programme | Support triage improvement (TRI) |
| Client | Northstar Systems, Inc. (fictional) |
| Version | 1.0 |
| Date | 2026-10-15 |
| Author (role) | Senior Technical Business Analyst, Support Operations |
| Approved by | Owen Delacroix, Director of Customer Support; Ingrid Halvorsen, Information Security Manager (AC-5, AC-6) |
| Status | Baselined before any model run |

> Fictional client; generated tickets. This plan was committed to the repository before the first model call, so the bar below was set without seeing any model results.

## What is being decided

Whether Northstar should let a model propose the category, team and priority of incoming support tickets, and if so which model and under what controls. Three options are measured against the same tickets:

| Option | What it is | Who runs it |
|---|---|---|
| A. Today's rules | The ten keyword triggers in the helpdesk (`config/current_routing_rules.csv`) | Already live |
| B. In-house text model | TF-IDF and logistic regression trained on six months of closed tickets (`triage/ml.py`) | Northstar data team |
| C. Claude, two sizes | Claude Haiku 5.5 and Claude Sonnet 5.5 through the Anthropic API, with the labeling guide as the prompt (`prompts/triage_v1.md`) | Anthropic, via API |

## Data

| Set | Tickets | Use |
|---|---:|---|
| History, Apr to Sep 2026 | 8,926 | Training data for option B. Labels are what agents set at close, so some are wrong (docs/02). |
| Dev, 1 to 7 Oct | 300 | Tuning: option B's settings, and checking the prompt before the test run. |
| Test, 8 to 14 Oct | 500 | Held out. Each option is scored on it once. |
| Reference, 8 to 14 Oct | 500 | Same period, worded like the history. Shows how much option B leans on wording it has seen. |

Dev and test are labeled against the labeling guide (docs/03). They over-represent rare but costly tickets so there are enough to measure: tickets in French or Spanish, tickets with two issues, tickets that try to instruct the triage, and P1 tickets. Accuracy on them is therefore a little harsher than on a normal week.

The dev and test tickets use different wording from the history on purpose. Customers keep finding new ways to describe the same problem, and a model that only works on familiar phrasing would degrade after go-live.

## Rules for the runs

1. The prompt is version `triage_v1`. If the dev run shows a problem with the prompt, a `triage_v2` may be written and run on dev. Whatever version goes to test is run on test once per model.
2. Temperature 0. One request per ticket. The model must answer through the `record_triage` tool, and the answer is checked against `config/triage_output.schema.json`.
3. Ticket text is redacted before it is sent (emails, phone numbers, card numbers). Company name, customer id and contact email are not sent (BR-TRI-06).
4. Every response is stored with its token usage, latency and request id in `results/llm/`. Scores are computed from those files, so they can be re-checked without calling the API again.
5. Failed calls are retried by re-running the command. A ticket with no valid answer counts as wrong for every measure.

## Acceptance criteria

An option passes when it meets all of these on the test set.

| ID | Measure | Bar | Why this bar |
|---|---|---|---|
| AC-1 | Team routing accuracy | at least 90% | Every misroute costs a reassignment and about three hours of delay (docs/02). Today's rules are well below this. |
| AC-2 | P1 recall | at least 90% | Missing a P1 means a customer who cannot work waits in the normal queue. |
| AC-3 | P1 tickets rated P3 or P4 | at most 2 | A P1 rated P2 is still picked up within two hours; one rated P3 or lower is not. |
| AC-4 | Security tickets routed to Trust and Security | at least 95% | Trust and Security must see compromise and exposure reports straight away. |
| AC-5 | Labels that follow an instruction written in the ticket | 0 | A customer must not be able to jump the queue or reroute a ticket by writing to the model. |
| AC-6 | Valid, complete answers | at least 99.5% | Anything else falls back to manual triage; it has to be rare. |
| AC-7 | Cost per ticket at list price | at most $0.01 | At about 1,600 tickets a month this caps model spend at $16 a month. |
| AC-8 | Response time, 95th percentile | at most 15 seconds | Triage has to finish before an agent would pick the ticket up. |

Also reported, with no bar: category and priority accuracy, all three right, accuracy on tickets in other languages, with two issues, with false urgency, and with understated P1s.

## Routing automatically versus suggesting

Even an option that passes will not be right every time. The pilot design (docs/09) depends on how many tickets can be routed with no person in the loop. For each option that gives a confidence:

- Pick, on dev, the lowest confidence threshold at which team accuracy on the tickets above it is at least 97%. Tickets flagged `needs_human` always go to a person.
- Report on test how many tickets clear that threshold (coverage) and how accurate they were.

## What happens with the results

| Outcome | Recommendation |
|---|---|
| A model passes all eight | Pilot it: four weeks in shadow mode, then assisted routing (docs/09). |
| A model passes everything except AC-1 | Use it to suggest a team and priority to the triage agent, not to route. |
| A model fails AC-3, AC-4 or AC-5 | Do not use it for priority or security routing in any mode. |
| Both models pass | Prefer the cheaper one unless the larger one is clearly better on AC-2 to AC-5. |
