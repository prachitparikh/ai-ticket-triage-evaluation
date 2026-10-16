# Risk register: model-assisted triage

| | |
|---|---|
| Document ID | TRI-08 |
| Programme | Support triage improvement (TRI) |
| Client | Northstar Systems, Inc. (fictional) |
| Version | 1.2 |
| Date | 2026-10-16 |
| Author (role) | Senior Technical Business Analyst, Support Operations |
| Reviewed by | Ingrid Halvorsen, Information Security Manager; Ade Okonkwo, Trust and Security Lead |
| Status | Current |

Scoring: likelihood and impact from 1 (low) to 3 (high). Residual is the score after the control.

| ID | Risk | L | I | Control | Evidence or owner | Residual |
|---|---|---:|---:|---|---|---|
| R-01 | A P1 is labeled lower and waits in the normal queue | 2 | 3 | AC-2 and AC-3 must pass; P1 and security labels are never auto-applied below P2 in the pilot; the triage queue still sees everything the model is unsure of (BR-TRI-03) | docs/06 P1 results; Mei Tanaka | Medium |
| R-02 | A security report is routed away from Trust and Security | 2 | 3 | AC-4; every ticket with security words in it also pages Trust and Security in the pilot, whatever the label | docs/06; Ade Okonkwo | Low |
| R-03 | A customer writes instructions to the model to jump the queue or reroute | 2 | 2 | Prompt treats ticket text as data; AC-5 measured on 19 planted test tickets; labels only from the fixed schema; P1 still needs the page to be answered by a person | docs/06 injection results; Ingrid Halvorsen | Low |
| R-04 | Personal or payment data sent to an outside service | 3 | 2 | Redaction before sending (FR-TRI-02); no company or contact fields sent (BR-TRI-06); vendor data terms reviewed (DEC-TRI-004). Gap found: company and sender names reach the model through signatures (docs/06, F-5); FR-TRI-02a closes it before the pilot | `triage/redact.py` and its tests; run facts count what was removed | Medium until FR-TRI-02a is built, then Low |
| R-05 | The model service is down or slow at a busy time | 2 | 2 | Fall back to today's rules and the queue (BR-TRI-07); 15-second timeout | Jonas Berg | Low |
| R-06 | Accuracy drifts as products and customers change | 2 | 2 | Weekly report against agents' final labels (FR-TRI-07); prompt changes go through the dev set first (FR-TRI-08) | Mei Tanaka | Low |
| R-07 | Agents stop checking and rubber-stamp the model | 2 | 2 | Pilot keeps a sample of 50 auto-routed tickets a week for a blind second look; override rate tracked | Carlos Mendoza | Medium |
| R-08 | The same ticket gets different labels on different days | 2 | 1 | Consistency measured on 100 dev tickets per model (NFR-TRI-06); confidence threshold sends borderline tickets to a person | docs/06 repeat runs | Low |
| R-09 | The evaluation flatters the model because the tickets are generated | 3 | 2 | Test wording differs from history; rare cases over-represented; four-week shadow pilot on real tickets before any auto-routing (docs/09) | docs/05, docs/09 | Medium |
| R-10 | Cost grows faster than volume (longer prompts, retries) | 1 | 1 | AC-7; cost per ticket in the weekly report; prompt caching kept on, without it cost per ticket roughly doubles (docs/07) | Robert Chen | Low |
| R-11 | The provider changes the model or its API behaviour | 2 | 2 | Model id and SDK version recorded on every request; dev set re-run before any model or SDK change. The evaluation already hit two such changes (no temperature setting; Sonnet 5.5 rejects a forced tool choice) | docs/06 run history | Low |
| R-12 | P1 tickets still miss the 30-minute target after triage is fixed, because the P1 queue itself waits a median 25 minutes | 3 | 2 | Page the on-call lead for every P1 (BR-TRI-04); G2 measures P1 first response separately from triage accuracy | docs/06, F-7; Owen Delacroix | Medium |
