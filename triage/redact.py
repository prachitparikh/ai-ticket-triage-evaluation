"""Remove personal and payment data from ticket text before it leaves Northstar (BR-TRI-06).

Customers paste all sorts into tickets: phone numbers in signatures, their email
address, now and then a full card number. None of it helps decide the category,
team or priority, so it is replaced with a tag before the text is sent to an
outside model. Names are left alone: they are everywhere in support text and the
data protection review (DEC-TRI-004) accepted that.
"""

from __future__ import annotations

import re

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<!\w)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\w)")
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")


def _luhn_ok(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


def _card(m: re.Match) -> str:
    digits = re.sub(r"\D", "", m.group(0))
    return "[CARD]" if 13 <= len(digits) <= 19 and _luhn_ok(digits) else m.group(0)


def redact(text: str) -> tuple[str, dict[str, int]]:
    counts = {}
    text, counts["card"] = CARD.subn(_card, text)
    counts["card"] = text.count("[CARD]")
    text, counts["email"] = EMAIL.subn("[EMAIL]", text)
    text, counts["phone"] = PHONE.subn("[PHONE]", text)
    return text, counts
