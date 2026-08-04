import re

# --------------------------------------------
# Patterns used in filters
# --------------------------------------------

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

    # Additional policy language patterns
    r"\bfinal sale\b",
    r"\bmail-in refund\b",
    r"\bfee will be charged\b",
    r"\bmay be returned\b",
    r"\bmay not be returned\b",
    r"\bmay not be exchanged\b",
]

HEADING_PATTERNS = [
    r"^returns\s*&\s*exchanges$",
    r"^returns$",
    r"^refunds$",
    r"^shipping$",
    r"^delivery$",
    r"^exchanges$",
    r"^replacements$",
    r"^merch returns\s*&\s*exchanges$",
]

# Question patterns for reverse_logistics
QUESTION_PATTERNS = [
    r"^how do",
    r"^how long",
    r"^what should",
    r"^can i",
    r"\?$",
]

# Support/help-center patterns for filtering customer service instructions
SUPPORT_PATTERNS = [
    r"\blet us know\b",
    r"\breach out\b",
    r"\bcontact us\b",
    r"\bstill need help\b",
    r"\bsupport widget\b",
    r"\border status\b",
    r"\blost or damaged your order\b",
    r"reach out",
    r"still need help",
    r"support widget",
    r"order status",
    r"contact us",
    r"customer support team",
    r"hi@",
]

# Legal/Privacy patterns for reverse_logistics
LEGAL_PATTERNS = [
    r"privacy policy",
    r"terms of service",
    r"agree",
    r"happy returns",
    r"terms",
    r"agreement",
]

# --------------------------------------------
# Job title patterns for hiring detection
# --------------------------------------------

JOB_TITLE_PATTERNS = [
    r"manager",
    r"director",
    r"lead",
    r"analyst",
    r"coordinator",
    r"specialist",
    r"associate",
    r"customer service",
    r"customer support",
    r"customer experience",
    r"customer success",
    r"logistics",
    r"warehouse",
    r"fulfillment",
    r"supply chain",
    r"3pl",
    r"distribution",
    r"inventory",
    r"procurement",
    r"transportation",
    r"returns",
    r"operations",
]

# For backward compatibility and additional checking
JOB_TITLE_WORDS = [
    "manager",
    "lead",
    "director",
    "coordinator",
    "associate",
    "analyst",
    "operations",
    "logistics",
    "warehouse",
    "fulfillment",
    "distribution",
    "inventory",
    "procurement",
    "transportation",
    "3pl",
    "supply chain",
    "customer",
    "support",
    "experience",
    "success",
    "returns",
]

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

COMPETITOR_KEYWORDS = [
    "loop",
    "aftership",
    "narvar",
    "redo",
    "onward",
    "returnly",
    "happy returns",
    "shipstation",
    "shipbob",
    "easypost",
]

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

# --------------------------------------------
# Deterministic filters for returns_issue
# --------------------------------------------

RETURN_POLICY_PATTERNS = [
    r"unreadable barcode",
    r"responsibility.*customer",
    r"return policy",
    r"refund policy",
    r"return fee",
    r"within \d+ days",
    r"satisfaction guarantee",
    r"perishable",
    r"do not accept returns",
    r"cannot accept returns",
    r"please allow.*business days",
    r"customer responsibility",
]

# --------------------------------------------
# Deterministic filters for reverse_logistics
# --------------------------------------------

REVERSE_LOGISTICS_REJECT_PATTERNS = [
    r"returns\s*&\s*exchanges",
    r"merch returns",
    r"privacy policy",
    r"happy returns",
    r"terms",
    r"agreement",
    r"how do",
    r"how long",
    r"what should",
    r"return portal",
    r"get started",
    r"order number",
    r"zip code",
    r"click",
    r"enter your order",
    r"review the information",
    r"list this item",
    r"poshmark",
    r"all set",
]

# --------------------------------------------
# Hiring detection words
# --------------------------------------------

HIRING_WORDS = [
    "hiring",
    "join our team",
    "job",
    "position",
    "opening",
    "career",
    "apply",
    "customer service",
    "customer support",
    "customer experience",
    "customer success",
    "returns specialist",
]

# --------------------------------------------
# Filter functions
# --------------------------------------------

def keep_signal(signal):

    evidence = signal.get("evidence", "").strip().lower()
    signal_type = signal.get("signal")

    if not evidence:
        return False

    # ----------------------------
    # Generic headings
    # ----------------------------

    for pattern in HEADING_PATTERNS:
        if re.fullmatch(pattern, evidence):
            return False

    # ----------------------------
    # Support/help-center patterns for shipping/delivery/returns
    # ----------------------------

    if signal_type in {
        "shipping_issue",
        "delivery_issue",
        "returns_issue",
    }:
        for pattern in SUPPORT_PATTERNS:
            if re.search(pattern, evidence, re.IGNORECASE):
                return False

    # ----------------------------
    # Returns / reverse logistics
    # ----------------------------

    if signal_type in {
        "returns_issue",
        "reverse_logistics",
    }:

        # Deterministic filter - reject policy language
        for pattern in RETURN_POLICY_PATTERNS:
            if re.search(pattern, evidence, re.IGNORECASE):
                return False

        # Original filters
        for pattern in POSITIVE_PATTERNS:
            if re.search(pattern, evidence):
                return False

        if evidence.startswith("if your"):
            return False

        if evidence.startswith("if you"):
            return False

        if "please allow" in evidence:
            return False

        if "do not accept returns" in evidence:
            return False

        if "cannot accept returns" in evidence:
            return False

        if "perishable" in evidence:
            return False

    # ----------------------------
    # Reverse logistics specific filters - Consolidated
    # ----------------------------

    if signal_type == "reverse_logistics":

        # Consolidated reject patterns
        for pattern in REVERSE_LOGISTICS_REJECT_PATTERNS:
            if re.search(pattern, evidence, re.IGNORECASE):
                return False

    # ----------------------------
    # Hiring - Using patterns for cleaner matching
    # ----------------------------

    if signal_type in {
        "hiring_logistics",
        "hiring_customer_support",
    }:

        # Use patterns for more precise matching
        if not any(
            re.search(pattern, evidence, re.IGNORECASE)
            for pattern in JOB_TITLE_PATTERNS
        ):
            return False

    # ----------------------------
    # Hiring customer support specific filters
    # ----------------------------

    if signal_type == "hiring_customer_support":

        # Must contain hiring-related words
        if not any(word in evidence for word in HIRING_WORDS):
            return False

        # Reject customer support instructions
        for pattern in SUPPORT_PATTERNS:
            if re.search(pattern, evidence, re.IGNORECASE):
                return False

    # ----------------------------
    # Carrier partnership
    # ----------------------------

    if signal_type == "carrier_partnership":

        if not any(
            partner in evidence
            for partner in LOGISTICS_PARTNERS
        ):
            return False

    # ----------------------------
    # Trigger event
    # ----------------------------

    if signal_type == "trigger_event":

        if not any(
            title in evidence
            for title in EXECUTIVE_KEYWORDS
        ):
            return False

    # ----------------------------
    # Competitor stack
    # ----------------------------

    if signal_type == "competitor_stack":

        if not any(
            tool in evidence
            for tool in COMPETITOR_KEYWORDS
        ):
            return False

    # ----------------------------
    # Growth
    # ----------------------------

    if signal_type == "growth_signal":

        if not any(
            keyword in evidence
            for keyword in GROWTH_KEYWORDS
        ):
            return False

    return True


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