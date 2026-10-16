# Business case: model-assisted ticket triage

| | |
|---|---|
| Document ID | TRI-01 |
| Programme | Support triage improvement (TRI) |
| Client | Northstar Systems, Inc. (fictional) |
| Version | 1.0 |
| Date | 2026-10-16 |
| Sponsor | Owen Delacroix, Director of Customer Support |
| Author (role) | Senior Technical Business Analyst, Support Operations |
| Reviewed by | Robert Chen, Finance Business Partner; Mei Tanaka, Support Operations Lead |
| Status | For the go/no-go meeting on 21 October |

> Fictional client; generated tickets. Figures come from `results/` and are explained in docs/02 (today), docs/06 (the evaluation) and docs/07 (costs).

## The decision we need

Approve an $18,000 build and a four-week shadow pilot of Claude Haiku 5.5 proposing the category, team and priority of every new support ticket. Nothing is routed without a person until the pilot's first gate is passed on real tickets.

## The problem

Ten keyword rules written in 2021 route about 1,490 tickets a month (docs/02):

- 27% go to the wrong team first: about 470 reassignments a month, each adding a median three hours of delay.
- 19% of P1 tickets are rated P1. The median P1 waits 5.8 hours for a first reply against a 30-minute target; 11% make it.
- 42% of security reports reach Trust and Security on first routing.
- Agents spend about 85 hours a month checking and forwarding tickets.

The rules react to the words customers use, not to what is happening. Every new rule fixes one case and breaks another.

## What was compared

Four options on the same 500 held-out tickets, against acceptance criteria agreed and committed before any model was run (docs/05):

| Option | Acceptance criteria | All three labels right | P1 tickets rated P1 | Security to Trust |
|---|---|---:|---:|---:|
| A. Today's rules | Fails AC-1 to AC-5 | 34% | 34% | 36% |
| B. In-house text model | Fails AC-1 to AC-5 | 45% | 18% | 68% |
| C. Claude Haiku 5.5 | Passes all eight | 99.0% | 97% | 100% |
| D. Claude Sonnet 5.5 | Passes all eight | 99.4% | 97% | 100% |

Neither Claude model followed any of the 19 instructions planted in tickets to jump the queue. The in-house model fails because it learns wording: on new wording it falls from 88% to 45% (docs/06, F-1).

## What it is worth

Two views, both at the 2027 forecast of 1,650 tickets a month and $42 an agent hour.

| | Today | With Claude Haiku 5.5 | Saving a month | Payback on $18,000 |
|---|---:|---:|---:|---:|
| **Cautious**: today from six months of history; the model only as good as the pilot's own bars (92% team right, 60% auto-routed) | $3,902 | $1,661 | **$2,241** | **8.0 months** |
| As measured on the test set | $4,560 | $635 | $3,925 | 4.6 months |

The cautious view is the one to plan on. The test set over-represents hard tickets and was generated from the same guide the prompt contains, so its figures are a ceiling.

The people time is what moves: about 93 agent hours a month spent checking and reassigning today, about 32 in the cautious view. The model costs $0.38 a month (docs/07).

For customers, the test set's queue model shows the median P1 first reply falling from 4.8 hours to 24 minutes. Triage alone cannot get most P1s inside 30 minutes, because the P1 queue itself has a median wait of 25 minutes; the page to the on-call lead (BR-TRI-04) has to do the rest (docs/06, F-7).

## Why Haiku and not Sonnet

The rule in docs/05, set before the results: if both pass, take the cheaper one unless the larger is clearly better on AC-2 to AC-5. They tie on all four. Haiku's model cost is about a fifteenth of Sonnet's, and its answers come back faster (3.2 against 4.2 seconds at the 95th percentile).

It is a close call and an easy one to reverse. Sonnet got one more test ticket right on team (500 of 500 against 499) and so shows $33 a month less people time; one ticket in 500 is noise. Both models sit behind the same interface, so switching is a configuration change. Sonnet is the named fallback if Haiku misses a pilot gate (DEC-TRI-012).

## Conditions

1. Names are removed before anything is sent: the customer's company name and the sender's name, which today reach the model through signatures (FR-TRI-02a, F-5). Pilot entry criterion.
2. The one P1 both models missed, a core screen broken for everyone, is added to the labeling guide's worked examples before the shadow phase (F-4).
3. P1 and security tickets page the on-call lead whatever set the label (BR-TRI-04).
4. Rules stay in place as the fallback, one setting away (BR-TRI-07).

## Risks

The register is docs/08. The two that matter most for this decision:

- **The evaluation flatters the model (R-09).** Generated tickets are cleaner than real ones. The four-week shadow phase measures accuracy on real tickets against agents' final labels before anything is routed without a person.
- **A P1 or security ticket is mislabeled (R-01, R-02).** No P1 or security ticket is auto-routed until phase 3; all of them page the on-call lead; any mislabeled one that is not caught within its target turns auto-routing off the same day.

## Plan and cost

| Phase | When | Cost |
|---|---|---|
| Build | 2 weeks from 2 November | $18,000 |
| Shadow | 4 weeks | about $330 a month of Support Ops time, model under $1 a month |
| Assisted | 4 weeks | as above |
| Routing | from week 11 | as above |

Details and gates in docs/09.
