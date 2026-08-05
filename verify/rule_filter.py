import re

# ---------------------------------------------------------
# Obvious positive / informational policy language
# ---------------------------------------------------------

POSITIVE_PATTERNS = [
    r"\beasy\b",
    r"\bquick\b",
    r"\bsimple\b",
    r"\bseamless\b",
    r"\bno hassle\b",
    r"\bfree returns\b",
    r"\bwithin \d+ days\b",
    r"\breturn fee\b",
    r"\breturn fees\b",
    r"\brestocking fee\b",
    r"\brestocking fees\b",
    r"\brefund\b",
    r"\bexchange\b",
    r"\breturn policy\b",
]

# ---------------------------------------------------------
# Generic headings
# ---------------------------------------------------------

HEADING_PATTERNS = [
    r"^returns\s*&\s*exchanges$",
    r"^returns$",
    r"^refunds$",
    r"^shipping$",
    r"^delivery$",
    r"^exchanges$",
    r"^replacements$",
]

# ---------------------------------------------------------
# Generic hiring pages (not real job evidence)
# ---------------------------------------------------------

INVALID_HIRING_PHRASES = {
    "apply now",
    "careers",
    "career",
    "work with us",
    "join our team",
    "join the team",
    "open positions",
    "view openings",
    "see openings",
    "open roles",
}

# ---------------------------------------------------------
# Job title keywords
# ---------------------------------------------------------

JOB_TITLE_PATTERNS = [
    r"\bmanager\b",
    r"\bdirector\b",
    r"\blead\b",
    r"\banalyst\b",
    r"\bcoordinator\b",
    r"\bspecialist\b",
    r"\bassociate\b",
    r"\bcustomer service\b",
    r"\bcustomer support\b",
    r"\bcustomer experience\b",
    r"\bcustomer success\b",
    r"\blogistics\b",
    r"\bwarehouse\b",
    r"\bfulfillment\b",
    r"\bsupply chain\b",
    r"\b3pl\b",
    r"\bdistribution\b",
    r"\binventory\b",
    r"\bprocurement\b",
    r"\btransportation\b",
    r"\boperations\b",
]

# ---------------------------------------------------------
# Carrier partners
# ---------------------------------------------------------

LOGISTICS_PARTNERS = [
    "dhl",
    "ups",
    "fedex",
    "usps",
    "shipbob",
    "flexport",
    "easypost",
    "narvar",
    "loop",
    "aftership",
    "redo",
    "onward",
]

# ---------------------------------------------------------
# Executive trigger events
# ---------------------------------------------------------

EXECUTIVE_KEYWORDS = [
    "ceo",
    "coo",
    "cto",
    "chief customer officer",
    "chief supply chain",
    "vp operations",
    "vp fulfillment",
    "head of logistics",
    "head of customer experience",
    "director supply chain",
]

# ---------------------------------------------------------
# Competitor stack
# ---------------------------------------------------------

COMPETITOR_KEYWORDS = [
    "loop",
    "aftership",
    "narvar",
    "redo",
    "onward",
    "returnly",
    "shipstation",
    "shipbob",
    "easypost",
]

# ---------------------------------------------------------
# Growth
# ---------------------------------------------------------

GROWTH_KEYWORDS = [
    "series",
    "funding",
    "raised",
    "acquired",
    "acquisition",
    "expanding into",
    "new market",
    "international expansion",
    "retail expansion",
    "warehouse expansion",
    "fulfillment center",
]

# ---------------------------------------------------------
# Main filter
# ---------------------------------------------------------

def keep_signal(signal):

    evidence = signal.get("evidence", "").strip().lower()
    signal_type = signal.get("signal")

    if not evidence:
        return False

    # --------------------------------------
    # Remove generic headings
    # --------------------------------------

    for pattern in HEADING_PATTERNS:
        if re.fullmatch(pattern, evidence):
            return False

    # --------------------------------------
    # Returns / Reverse logistics
    # --------------------------------------

    if signal_type in {"returns_issue", "reverse_logistics"}:

        for pattern in POSITIVE_PATTERNS:
            if re.search(pattern, evidence, re.IGNORECASE):
                return False

    # --------------------------------------
    # Hiring
    # --------------------------------------

    if signal_type in {
        "hiring_logistics",
        "hiring_customer_support",
    }:

        if evidence in INVALID_HIRING_PHRASES:
            return False

        if not any(
            re.search(pattern, evidence, re.IGNORECASE)
            for pattern in JOB_TITLE_PATTERNS
        ):
            return False

    # --------------------------------------
    # Carrier partnership
    # --------------------------------------

    if signal_type == "carrier_partnership":

        if not any(
            partner in evidence
            for partner in LOGISTICS_PARTNERS
        ):
            return False

    # --------------------------------------
    # Trigger events
    # --------------------------------------

    if signal_type == "trigger_event":

        if not any(
            title in evidence
            for title in EXECUTIVE_KEYWORDS
        ):
            return False

    # --------------------------------------
    # Competitor stack
    # --------------------------------------

    if signal_type == "competitor_stack":

        if not any(
            tool in evidence
            for tool in COMPETITOR_KEYWORDS
        ):
            return False

    # --------------------------------------
    # Growth
    # --------------------------------------

    if signal_type == "growth_signal":

        if not any(
            keyword in evidence
            for keyword in GROWTH_KEYWORDS
        ):
            return False

    return True


# ---------------------------------------------------------
# Remove duplicates
# ---------------------------------------------------------

def filter_signals(signals):

    seen = set()
    filtered = []

    for signal in signals:

        key = (
            signal.get("signal"),
            signal.get("evidence", "").strip().lower(),
        )

        if key in seen:
            continue

        seen.add(key)

        if keep_signal(signal):
            filtered.append(signal)

    return filtered