# Current state: how tickets are triaged today

| | |
|---|---|
| Document ID | TRI-02 |
| Programme | Support triage improvement (TRI) |
| Client | Northstar Systems, Inc. (fictional) |
| Version | 1.0 |
| Date | 2026-10-09 |
| Author (role) | Senior Technical Business Analyst, Support Operations |
| Reviewed by | Mei Tanaka, Support Operations Lead; Carlos Mendoza, Tier 1 Team Lead |
| Status | Final |

> Fictional client; generated tickets. The routing figures come from running Northstar's actual helpdesk rules over six months of tickets (`scripts/analyze_current_state.py`, output in `results/current_state/`). The response times come from a queue model whose assumptions are listed below and in `config/current_state_model.json`.

## How it works now

1. A customer writes in by email, the web form or chat. About 1,490 tickets a month, growing about 3% a month.
2. Ten keyword rules in the helpdesk set a category and a team (`config/current_routing_rules.csv`). The first rule that matches wins. Four more rules set the priority from words like "urgent", "down" or "can't" (`config/current_priority_rules.csv`).
3. The ticket lands in that team's queue in priority order.
4. If it is the wrong team, an agent reads it, works out where it belongs and reassigns it. It then waits in the next queue.
5. The agent who closes the ticket sets the final category, team and priority.

Nobody owns triage as a job. Tier 1 agents glance at new tickets between their own work, which the time study put at about a minute and a half per ticket.

The rules were written in 2021 and patched as problems came up. Billing's rule went first because Billing Operations asked for "everything with money words", so any ticket that mentions an invoice goes to Billing, including fake-invoice phishing reports.

## What the history shows

Today's rules applied to the 8,926 tickets from April to September 2026, compared with the labeling guide (docs/03):

| Measure | Result |
|---|---:|
| Category right | 70% |
| Team right (so no reassignment needed) | 73% |
| Priority right | 46% |
| Tickets sent to the wrong team | 27%, about 470 reassignments a month |
| P1 tickets the rules rate P1 | 19% |
| Security tickets that reach Trust and Security | 42% |

Where the misroutes come from:

| Gold category | Tickets | Sent to the wrong team | Why |
|---|---:|---:|---|
| Bug | 1,368 | 56% | Bug reports rarely say "bug"; they describe what happened, and words like "save" or "sync" pull them elsewhere |
| Security | 450 | 58% | "Invoice", "login" and "export" rules fire first |
| Integration | 689 | 4% | Integration names are distinctive |
| Cancellation | 373 | 13% | |

The priority rules are the weakest part. They react to the customer's tone, not the situation: "URGENT" on a question about changing a logo becomes P1, while "hi, quick one, none of us can log in" stays P3.

## What it costs

Queue model, using the September time study (`config/current_state_model.json`):

| Assumption | Value |
|---|---:|
| Time to check a new ticket's routing | 1.5 minutes |
| Agent time to reassign a ticket | 6 minutes |
| Extra wait when a ticket is reassigned | median 3 hours |
| Share of misrouted tickets reassigned twice | 15% |
| Median wait in queue, by the priority the rules gave it | P1 25 min, P2 95 min, P3 6 h, P4 18 h |
| Loaded agent cost | $42 an hour |

| Result | Per month |
|---|---:|
| Agent hours spent reassigning | 47.3 |
| Agent hours spent checking new tickets | 37.2 |
| P1 tickets | about 86 |
| P1 tickets answered within the 30-minute target | 11% |
| Median first response for a P1 | 5.8 hours |

That last line is the problem the Director of Customer Support raised: a customer whose whole company cannot work waits, on average, most of a working day for a first reply, because the rules either missed the urgency or sent the ticket to the wrong team first.

## The labels agents set at close

The history's closing labels are what any model trained on Northstar's own data would learn from, so they were checked against the labeling guide:

| Field | Agrees with the guide |
|---|---:|
| Category | 94% |
| Team | 97% |
| Priority | 92% |

Good enough to train on, but about one ticket in twelve teaches the wrong priority.

## Pain points, in Support's words

| From | Pain point |
|---|---|
| Owen Delacroix, Director of Customer Support | "Our worst customer experiences start with a P1 sitting in the wrong queue." |
| Carlos Mendoza, Tier 1 Team Lead | Tier 1 spends time forwarding tickets it was never meant to see, especially SSO problems that belong to Integrations. |
| Jonas Berg, Tier 2 Support Manager | Bug reports arrive late, often after a detour through Billing or Tier 1. |
| Ade Okonkwo, Trust and Security Lead | Compromise reports reach Trust and Security less than half the time on first routing. |
| Mei Tanaka, Support Operations Lead | Every new rule fixes one case and breaks another. The rule table is at the limit of what keywords can do. |

## What would good look like

Set with Owen Delacroix and Mei Tanaka before any option was looked at:

- Team right first time for at least nine tickets in ten.
- Almost every P1 recognised as P1, and none treated as routine.
- Security tickets always reach Trust and Security.
- No customer able to game the triage by what they write.

These became the acceptance criteria in docs/05.
