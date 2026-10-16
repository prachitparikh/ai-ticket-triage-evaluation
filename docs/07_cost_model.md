# Cost model

| | |
|---|---|
| Document ID | TRI-07 |
| Programme | Support triage improvement (TRI) |
| Client | Northstar Systems, Inc. (fictional) |
| Version | 1.0 |
| Date | 2026-10-16 |
| Author (role) | Senior Technical Business Analyst, Support Operations |
| Reviewed by | Robert Chen, Finance Business Partner |
| Status | For the go/no-go meeting on 21 October |

> Fictional client. Model prices are the published list prices, retrieved on 16 October 2026 (`config/model_prices.csv`). Token counts are the ones the API returned for each test request. People costs come from the September time study (`config/current_state_model.json`) and the assumptions agreed with Finance (`config/business_case.json`).

## In one line

The model is the cheap part. Claude Haiku 5.5 costs about $0.38 a month at 2027 volume; the people time it saves is worth about $2,200 to $3,900 a month; the build is $18,000.

## What one ticket costs

Measured on the 500 test tickets. A ticket sends about 180 tokens of its own text; the prompt and the tool definition (about 2,400 tokens) are the same for every ticket and are cached.

| | Claude Haiku 5.5 | Claude Sonnet 5.5 |
|---|---:|---:|
| Ticket text, tokens per ticket | 181 | 181 |
| Prompt read from cache, tokens per ticket | 2,403 | 2,403 |
| Output, tokens per ticket | 382 | 287 |
| Cost of the 500 test tickets | $0.12 | $1.76 |
| **Cost per ticket** | **$0.00023** | **$0.0035** |
| Cost per ticket without prompt caching | $0.00045 | $0.0080 |
| Share of the cost that is output | 82% | 82% |

Two things drive the cost:

- **Output, not input.** The triage tool is offered, not forced (DEC-TRI-007), so each model writes a few sentences before it answers. That is about four fifths of the bill. Asking for no preamble would cut it, but it has not been tested whether that costs accuracy, so it is left for the pilot.
- **Caching.** Without it Haiku would cost about twice as much and Sonnet about 2.3 times as much. Sonnet would then be at $0.008 a ticket, close to the $0.01 bar in AC-7. Caching has to stay switched on in the build (NFR-TRI-04).

## Per month

At the 2027 forecast of 1,650 tickets a month:

| | Claude Haiku 5.5 | Claude Sonnet 5.5 |
|---|---:|---:|
| Model, 1,650 tickets | $0.38 | $5.80 |
| Model, if volume grew tenfold | $3.84 | $58.03 |
| Model, if list prices doubled | $0.77 | $11.61 |
| Running it: weekly report and 50-ticket blind sample, 6 hours at $55 | $330 | $330 |

The model cost is under 0.1% of the running cost for Haiku and about 1% for Sonnet. Price changes and growth do not change the decision.

## People time, which is the real cost

The same queue model as docs/02, applied to each option's answers on the test set, at 1,650 tickets a month and $42 an agent hour:

| Option | Reassignments a month | Agent hours reassigning | Agent hours checking new tickets | Monthly cost, people and model | Saving against today's rules |
|---|---:|---:|---:|---:|---:|
| A. Today's rules | 673 | 67.3 | 41.2 | $4,559.94 | |
| B. In-house text model | 462 | 46.2 | 33.8 | $3,691.05 | $868.89 |
| C. Claude Haiku 5.5 | 7 | 0.7 | 6.6 | $635.30 | $3,924.64 |
| D. Claude Sonnet 5.5 | 0 | 0.0 | 6.4 | $602.61 | $3,957.33 |

Source: `results/business_case.csv`. "Checking" is the minute and a half an agent spends on each ticket that is not auto-routed.

This is the optimistic view: the test set over-represents hard tickets, so the rules look worse on it than in a normal week (65% team accuracy against 73% in the history). The cautious view in docs/01 uses the history's misroute rate for today and the pilot's own bars for the model.

Sonnet's $33 lower monthly cost comes from one ticket: Haiku sent one of 500 test tickets to the wrong team, Sonnet none. That ticket was flagged for a person anyway. One ticket in 500 is not a difference the evaluation can detect, so the comparison treats the two as equal on people time (DEC-TRI-012).

## One-off cost

| Item | Cost |
|---|---:|
| Helpdesk webhook, redaction including names (FR-TRI-02a), internal-note posting, override logging, weekly report: about 30 developer days at $600 | $18,000 |

The in-house text model would need much of the same build plus retraining as wording drifts (finding F-1 in docs/06), so it does not save on this line.

## What the evaluation itself cost

| | Requests | Spend at list price |
|---|---:|---:|
| Claude Haiku 5.5, four dev rounds | 1,500 | $0.31 |
| Claude Haiku 5.5, test | 500 | $0.12 |
| Claude Sonnet 5.5, dev rounds 2 to 4 | 900 | $3.20 |
| Claude Sonnet 5.5, test | 500 | $1.76 |
| **Total** | **3,400** | **$5.38** |

Source: `results/evaluation_spend.json`. The 300 Sonnet requests the API rejected in dev round 1 were not billed.

The estimate before the runs was about $3. It was low for two reasons: the estimate assumed 110 output tokens a ticket, against the 290 to 380 the models actually wrote, and dev took four rounds where the plan expected one or two.
