# Triage taxonomy and labeling guide

| | |
|---|---|
| Document ID | TRI-03 |
| Programme | Support triage improvement (TRI) |
| Client | Northstar Systems, Inc. (fictional) |
| Version | 1.2 |
| Date | 2026-10-16 |
| Author (role) | Senior Technical Business Analyst, Support Operations |
| Approved by | Mei Tanaka, Support Operations Lead; Owen Delacroix, Director of Customer Support |
| Status | Baselined |

> The machine-readable version is `config/taxonomy.json`; the rules as code are in `triage/labeling.py`, and a test checks the two agree. The same rules are the model prompt (`prompts/triage_v2.md`).

## Revision history

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-10-05 | Agreed in the triage workshop with Support Ops, Tier 1, Tier 2, Billing Ops and Trust and Security |
| 1.1 | 2026-10-09 | Routing exceptions RX-1 (SSO) and RX-2 (Enterprise billing disputes) added; mixed-ticket and unclear-ticket rules added |
| 1.2 | 2026-10-16 | Four clarifications from dev round 1 (docs/06): billing questions stay BILLING, "how do I reach support" is GENERAL, invite errors are ACCESS, a stated workaround caps priority at P3. No label changed. |

## Why a guide

Before this, "category" meant whatever the closing agent thought, and 6% of closed tickets disagreed with any sensible reading. A model, a rule set or a new hire can only be judged against an agreed answer, so the answer is written down here first.

## Categories and default teams

| Category | What belongs here | Default team |
|---|---|---|
| BILLING | Charges, invoices, refunds, tax, payment methods, plan prices and quotes. Questions about these are BILLING, not HOW_TO. | Billing Operations |
| ACCESS | Passwords, two-factor, locked accounts, user invites and seats (including invite links that show an error), SSO sign-in | Tier 1 Support |
| BUG | A feature behaves wrongly or shows an error, but the product is up | Tier 2 Support |
| OUTAGE | The product or a module is down, timing out, or too slow to use | Tier 2 Support |
| INTEGRATION | Salesforce, HubSpot, QuickBooks, calendars, Slack, Teams, Zapier, webhooks, the API, when something is failing | Integrations Support |
| DATA | Imports, exports, bulk updates, records missing or duplicated, when something is failing or data is gone | Tier 2 Support |
| HOW_TO | How do I do X, where nothing is broken, whatever the topic | Tier 1 Support |
| FEATURE | Asks for something the product does not do, or gives feedback | Customer Success |
| SECURITY | Suspected compromise, data in the wrong account, phishing, deletion or DPA requests, security questionnaires, vulnerability reports | Trust and Security |
| CANCELLATION | Cancel, downgrade, seats or terms at renewal | Customer Success |
| GENERAL | Does not say what is wrong, fits nothing above, or asks how to reach support | Tier 1 Support |

## Routing exceptions

| ID | Rule | Why |
|---|---|---|
| RX-1 | SSO or SAML sign-in problems are ACCESS but go to Integrations Support | Integrations owns identity-provider set-up; Tier 1 was forwarding every one of them |
| RX-2 | Billing disputes (duplicate or wrong charge) from Enterprise customers go to Customer Success | The account manager owns the Enterprise contract and wants to hear about disputes first |

## Priority

Judge what the ticket says about who is affected and whether they can work, not how urgent the customer sounds.

| Priority | First response target | When |
|---|---|---|
| P1 Critical | 30 minutes | Everyone at the customer cannot use the product or a core part of it; or a security incident is in progress (compromised account, data in the wrong account); or data has been lost |
| P2 High | 2 hours | A group of users is blocked with no workaround; an Enterprise customer is blocked with no workaround, even one person; a duplicate or incorrect charge (any plan); an integration has stopped and a group cannot work |
| P3 Normal | 8 hours | One person on a non-Enterprise plan; anything with a workaround; account and billing admin; cancellations; privacy requests and phishing reports with no compromise; unclear tickets |
| P4 Low | 24 hours | How-to questions, feature requests, feedback, price quotes |

Rules that came up often enough to write down:

- **Workaround.** If the ticket says there is a way to keep working, it is P3 at most, however many people are affected. Security incidents and lost data are the exception.
- **Wrong charge.** A duplicate or incorrect charge is P2 on every plan. RX-2 changes the team for Enterprise, not the priority.
- **Who is affected.** If the ticket does not say, assume one person. "We" and "our team" on their own do not mean a group.
- **Tone.** "URGENT" on a how-to question is P4. "Quick one, none of us can log in" is P1.

## Tickets with two issues

Label the issue with the higher priority. If they are equal, label the one mentioned first. The other issue is handled by whoever picks the ticket up, as today.

## Text addressed to the triage

Some customers write "mark this P1" or address an AI directly. That text is ignored; the ticket is labeled on what it is about. The evaluation includes such tickets on purpose (docs/05, AC-5).

## Worked examples

| Ticket (shortened) | Plan | Label | Why |
|---|---|---|---|
| "We were charged twice for September, $1,240 both times." | Professional | BILLING / Billing Operations / P2 | Wrong charge, any plan |
| Same ticket | Enterprise | BILLING / Customer Success / P2 | RX-2 changes the team only |
| "Since this morning our Okta login sends us back to the sign-in page. Nobody in our company can sign in." | Business | ACCESS / Integrations Support / P1 | SSO (RX-1); whole account blocked |
| "The calendar view is blank in Safari. It works in Chrome." | Enterprise | BUG / Tier 2 / P3 | Workaround |
| "URGENT!! How do I change the week start day to Monday?" | Starter | HOW_TO / Tier 1 / P4 | Tone does not set priority |
| "Please send PDFs of the last three invoices." | Business | BILLING / Billing Operations / P3 | Billing admin |
| "Is there a phone number for support?" | Business | GENERAL / Tier 1 / P3 | Contact question |
| "Someone logged into my account from another country and changed the email." | Starter | SECURITY / Trust and Security / P1 | Incident in progress |
| "We got an email that looks like Northstar asking for card details. Is it from you?" | Business | SECURITY / Trust and Security / P3 | Phishing report, no compromise |
| "Hi, it's not working again, please call me." | Professional | GENERAL / Tier 1 / P3 | Does not say what is wrong |

## How the dev and test sets were labeled

In the scenario, two senior agents labeled each dev and test ticket against this guide and Mei Tanaka settled the disagreements. In this repository the tickets are generated, and the generator sets each label with the functions in `triage/labeling.py`, which encode exactly the rules above.
