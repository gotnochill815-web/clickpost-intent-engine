import re

VALID_SIGNALS = {
    # Existing
    "shipping_issue",
    "delivery_issue",
    "returns_issue",
    "reverse_logistics",
    "hiring_logistics",
    "hiring_customer_support",
    "warehouse_expansion",
    "carrier_partnership",

    # New
    "competitor_stack",
    "growth_signal",
    "trigger_event",
}


def normalize_text(text):
    """
    Normalize whitespace for reliable substring matching.
    """

    if not isinstance(text, str):
        return ""

    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


class SignalVerifier:

    def verify(self, extraction_result, source_text):

        # -----------------------------------------
        # Determine brand
        # -----------------------------------------

        brand = extraction_result.get("brand")

        if brand is None and extraction_result.get("signals"):
            first_signal = extraction_result["signals"][0]
            if isinstance(first_signal, dict):
                brand = first_signal.get("brand")

        # -----------------------------------------
        # Propagate extraction errors
        # -----------------------------------------

        if extraction_result.get("error"):

            return {
                "brand": brand,
                "signals": [],
                "error": extraction_result["error"],
            }

        source_text = normalize_text(source_text)

        verified = []
        seen = set()

        # -----------------------------------------
        # Verify each extracted signal
        # -----------------------------------------

        for signal in extraction_result.get("signals", []):

            if not isinstance(signal, dict):
                continue

            signal_name = signal.get("signal")
            evidence = normalize_text(
                signal.get("evidence", "")
            )

            if signal_name not in VALID_SIGNALS:
                continue

            if not evidence:
                continue

            key = (
                signal_name,
                evidence,
            )

            if key in seen:
                continue

            seen.add(key)

            # -----------------------------------------
            # Verification
            # -----------------------------------------

            if evidence in source_text:
                signal["verification"] = "verified"
            else:
                signal["verification"] = "manual_review"

            verified.append(signal)

        # -----------------------------------------
        # Return verified signals
        # -----------------------------------------

        return {
            "brand": brand,
            "signals": verified,
            "error": None,
        }