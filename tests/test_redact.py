from triage.redact import redact


def test_removes_contact_details_and_valid_cards():
    text, counts = redact("Call (555) 013-4421 or mail jo.ito@river.com. Card 4111 1111 1111 1111, exp 08/27.")
    assert "[PHONE]" in text and "[EMAIL]" in text and "[CARD]" in text
    assert "4111" not in text and "@" not in text
    assert counts == {"card": 1, "email": 1, "phone": 1}


def test_leaves_business_numbers_alone():
    for keep in ["invoice INV-2412345 for $3,867.27 on 10/04", "fails at row 2345", "error E-1042",
                 "/v2/projects returns 401", "1234 5678 9012 3456"]:          # last one fails the Luhn check
        assert redact(keep)[0] == keep


def test_every_eval_ticket_leaves_without_contact_details():
    import csv
    from triage import DATA
    from triage.llm import ticket_message
    for split in ("dev", "test"):
        with open(DATA / "eval" / f"{split}.csv", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                msg, _ = ticket_message(row)
                # The company and customer fields are never sent. A company name typed in a signature still is:
                # found by this test on 16 Oct, logged as finding F-5 in docs/06 and FR-TRI-02a for the pilot.
                assert row["contact_email"] not in msg and row["customer_id"] not in msg
                assert "4111 1111 1111 1111" not in msg
