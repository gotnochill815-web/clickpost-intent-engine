SIGNAL_WEIGHTS = {
    "shipping_issue": 8,
    "delivery_issue": 8,
    "returns_issue": 7,
    "reverse_logistics": 7,
    "hiring_logistics": 6,
    "hiring_customer_support": 5,
    "warehouse_expansion": 9,
    "carrier_partnership": 9,
}

class IntentScorer:

    def score(self, verification_result):
        brand = verification_result.get("brand")
        error = verification_result.get("error")
        data_status = "INCOMPLETE" if error else "COMPLETE"

        if error:
            return {
                "brand": brand,
                "score": 0,
                "signals": [],
                "error": error,
                "data_status": data_status,
            }

        total = 0
        accepted = []
        seen_signal_types = set()

        for signal in verification_result.get("signals", []):
            signal_name = signal.get("signal")

            # Skip additional occurrences of an already-counted category
            if signal_name in seen_signal_types:
                continue
            seen_signal_types.add(signal_name)

            weight = SIGNAL_WEIGHTS.get(signal_name, 0)
            signal["weight"] = weight
            total += weight
            accepted.append(signal)

            if brand is None:
                brand = signal.get("brand")

        return {
            "brand": brand,
            "score": total,
            "signals": accepted,
            "error": None,
            "data_status": data_status,
        }
