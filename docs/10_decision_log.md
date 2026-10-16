# Decision log

| | |
|---|---|
| Document ID | TRI-10 |
| Programme | Support triage improvement (TRI) |
| Client | Northstar Systems, Inc. (fictional) |
| Owner (role) | Senior Technical Business Analyst, Support Operations |
| Status | Current |

| ID | Date | Decision | Why | Decided by |
|---|---|---|---|---|
| DEC-TRI-001 | 2026-10-05 | The labeling guide (docs/03) is the answer every option is scored against, not the labels agents set at close | Closing labels disagree with any sensible reading about 6% of the time (docs/02) | Owen Delacroix, Mei Tanaka |
| DEC-TRI-002 | 2026-10-09 | Compare three options on the same tickets: today's rules, an in-house text model, and two sizes of Claude | Finance asked whether a model we run ourselves would do; the answer needed evidence | Owen Delacroix, Robert Chen |
| DEC-TRI-003 | 2026-10-09 | Dev and test tickets use different wording from the history | A model that only recognises familiar phrasing would fail on the first new product or new customer | Senior Technical BA |
| DEC-TRI-004 | 2026-10-14 | What may be sent to the model provider: plan, channel, subject and body with emails, phones and card numbers removed. Names in text accepted for the evaluation | Triage needs the text and nothing else. The provider's commercial data terms were reviewed by Information Security | Ingrid Halvorsen |
| DEC-TRI-005 | 2026-10-15 | Acceptance criteria AC-1 to AC-8 baselined and committed before any model call | So the bar cannot move after the results are seen | Owen Delacroix, Ingrid Halvorsen |
| DEC-TRI-006 | 2026-10-16 | Run the models without a temperature setting and measure consistency instead (same 100 tickets sent twice) | The Anthropic Python SDK in use (1.15.0) no longer accepts a temperature argument; the first attempt failed before sending anything | Senior Technical BA |
| DEC-TRI-007 | 2026-10-16 | Offer the triage tool to both models without forcing it, and say in the prompt that it must be used | Claude Sonnet 5.5 rejects a forced tool choice. Both models get the same request so the comparison stays fair | Senior Technical BA |
| DEC-TRI-008 | 2026-10-16 | Raise the output cap from 400 to 2,000 tokens | Without a forced tool the models reason briefly first; 400 truncated about a third of Haiku's answers in dev round 2 | Senior Technical BA |
| DEC-TRI-009 | 2026-10-16 | Fix the ticket generator after dev round 1 and regenerate dev and test (the test set had not been run) | Some generated tickets contradicted themselves ("502 on every page" plus "we have a workaround"); one invoice request read as a how-to question | Senior Technical BA, Mei Tanaka |
| DEC-TRI-010 | 2026-10-16 | Fix three labeling details after dev round 3 and regenerate (test still not run): problems in side features (notifications, a report, the mobile app) stop at P2; MFA and invite problems cannot be company-wide; the French outage ticket says "l'entreprise", not "l'équipe" | Both models disagreed with the gold label in the same way, and on reading the tickets the models were right | Senior Technical BA, Mei Tanaka |
| DEC-TRI-011 | 2026-10-16 | Freeze prompt v3 and run the test set once per model | v3 adds one definition ("blocked means the ticket says they cannot work"); Haiku reached 97% all-three-right on dev and Sonnet 100 of 100 on its dev check | Senior Technical BA |
| DEC-TRI-012 | 2026-10-16 | Recommend Claude Haiku 5.5 for the pilot, with Claude Sonnet 5.5 as the fallback if Haiku misses a G1 gate | Both pass AC-1 to AC-8 and tie on AC-2 to AC-5; Haiku's model cost is about a fifteenth of Sonnet's. Sonnet's one extra correct team in 500 is noise | Owen Delacroix, Robert Chen (proposed; for the 21 Oct meeting) |
| DEC-TRI-013 | 2026-10-16 | Leave test labels as generated, including the three that read wrongly, and report them in docs/06 | Correcting labels after seeing the answers would favour the model. The generator gets fixed before any re-run instead | Senior Technical BA, Mei Tanaka |
