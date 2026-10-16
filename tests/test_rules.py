from triage.rules import classify, priority_rules, routing_rules


def test_rule_tables_end_with_a_default():
    assert routing_rules()[-1].pattern is None and priority_rules()[-1].pattern is None


def test_first_match_wins_which_is_the_known_weakness():
    # A phishing report about a fake invoice goes to Billing, because the billing rule runs first (docs/02).
    out = classify("Is this from you?", "Someone sent our finance team a fake Northstar invoice with different bank details.")
    assert out["team"] == "BILLING_OPS"


def test_tone_drives_priority():
    assert classify("URGENT", "How do I change the logo?")["priority"] == "P1"
    assert classify("quick one", "none of us can log in since this morning")["priority"] == "P3"
