# Pilot plan

| | |
|---|---|
| Document ID | TRI-09 |
| Programme | Support triage improvement (TRI) |
| Client | Northstar Systems, Inc. (fictional) |
| Version | 1.0 |
| Date | 2026-10-16 |
| Author (role) | Senior Technical Business Analyst, Support Operations |
| Reviewed by | Owen Delacroix, Mei Tanaka, Jonas Berg, Ade Okonkwo, Ingrid Halvorsen |
| Status | For the go/no-go meeting on 21 October |

## Why a pilot and not a switch

The evaluation used generated tickets labeled from the same guide the prompt contains. That is a fair test of whether the model can apply the guide, and a generous test of real life. Real tickets are vaguer, longer and stranger. The pilot measures the real number before anything is routed without a person.

## Phases

| Phase | Weeks | What the model does | What people do | Exit gate |
|---|---|---|---|---|
| 0. Build | 2 (from 2 Nov) | Nothing yet | Helpdesk webhook, redaction including signatures (FR-TRI-02a), internal-note posting, logging, weekly report; the one-screen P1 example added to the guide and the prompt (docs/06, F-4) | Security review signed; 200 recorded tickets replayed end to end |
| 1. Shadow | 4 | Labels every new ticket in a hidden field | Triage exactly as today; agents' final labels are the comparison | G1 below |
| 2. Assisted | 4 | Posts its proposal as an internal note on every ticket; auto-routes tickets above the threshold that are not P1 and not security | Triage agent accepts or overrides the note; P1 and security still routed by a person and paged | G2 below |
| 3. Routing | from week 11 | Auto-routes above the threshold, including P1 and security, which also page the on-call lead (BR-TRI-04) | Triage queue handles everything flagged or below the threshold | Monthly review |

## Gates

Measured against agents' final labels, after Support Ops corrects the ones that break the guide.

| Gate | Measure | Bar |
|---|---|---|
| G1 | Team agreement on all tickets | at least 92% |
| G1 | P1 tickets the model rated P1 | at least 90%, none rated P3 or P4 |
| G1 | Security tickets the model sent to Trust and Security | at least 95% |
| G1 | Tickets where the label followed text addressed to the triage | 0 |
| G1 | Valid answers; time to answer, 95th percentile | 99.5%; 15 seconds |
| G2 | Team accuracy on auto-routed tickets | at least 97% |
| G2 | Reassignments per month | at least 50% below the 6-month baseline (about 470) |
| G2 | Agent override rate on proposals | below 10%, and every override reviewed weekly |
| G2 | P1 first response within 30 minutes | at least 60% (baseline about 11%). Depends on the page (BR-TRI-04): at today's P1 queue wait, perfect triage alone reaches about 64% (docs/06, F-7) |

Failing a G1 bar means another round on the prompt and the dev set, then four more weeks of shadow. Before that round, Claude Sonnet 5.5 is run over the same shadow tickets; if it passes, it replaces Haiku (DEC-TRI-012). Failing G2 means back to phase 1.

## Running it

| Item | Owner |
|---|---|
| Weekly report: agreement by category and team, P1 and security misses, overrides, cost, latency | Mei Tanaka |
| 50 auto-routed tickets a week re-labeled blind by a senior agent | Carlos Mendoza |
| Prompt or model change: re-run the dev set, compare, record the decision | Senior Technical BA |
| Switch back to rules: one setting in the helpdesk, tested in phase 0 | Jonas Berg |
| Data protection check of a sample of requests each month | Ingrid Halvorsen |

## Stop conditions

Any of these turns auto-routing off the same day, pending review:

- a P1 or security ticket auto-routed to the wrong team and not caught within its response target;
- a request found to contain a card number, an email address or a phone number;
- a label that followed text addressed to the triage;
- the provider changes the model behind the model id without notice.
