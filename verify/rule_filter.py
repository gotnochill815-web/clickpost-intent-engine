import re

POSITIVE_PATTERNS = [
    r"\beasy\b",
    r"\bquick\b",
    r"\bsimple\b",
    r"\bseamless\b",
    r"\bno hassle\b",
    r"\bfree returns\b",
    r"\bwithin \d+ days\b",
    r"\breturn fee\b",
    r"\brefund\b",
    r"\bexchange\b",
    r"\breturn policy\b",
]

HEADING_PATTERNS = [
    r"^returns\s*&\s*exchanges$",
    r"^returns$",
    r"^refunds$",
]


def keep_signal(signal):

    evidence = signal.get("evidence", "").strip().lower()
    signal_type = signal.get("signal")

    if signal_type in {"returns_issue", "reverse_logistics"}:

        for pattern in HEADING_PATTERNS:
            if re.fullmatch(pattern, evidence):
                return False

        for pattern in POSITIVE_PATTERNS:
            if re.search(pattern, evidence):
                return False

    if signal_type == "hiring_customer_support":

        hiring_words = [
            "hiring",
            "join our team",
            "job",
            "position",
            "opening",
            "career",
            "apply",
        ]

        if not any(word in evidence for word in hiring_words):
            return False

    return True


def filter_signals(signals):
    return [s for s in signals if keep_signal(s)]