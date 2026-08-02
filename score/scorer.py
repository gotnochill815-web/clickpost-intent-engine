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

        # -----------------------------------------
        # Brand
        # -----------------------------------------

        brand = verification_result.get("brand")

        # -----------------------------------------
        # Determine data status
        # -----------------------------------------

        error = verification_result.get("error")

        if error:
            data_status = "INCOMPLETE"
        else:
            data_status = "COMPLETE"

        # -----------------------------------------
        # If verification failed, stop here
        # -----------------------------------------

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

        # -----------------------------------------
        # Score verified signals
        # -----------------------------------------

        for signal in verification_result.get("signals", []):

            signal_name = signal.get("signal")

            weight = SIGNAL_WEIGHTS.get(signal_name, 0)

            signal["weight"] = weight

            total += weight

            accepted.append(signal)

            if brand is None:
                brand = signal.get("brand")

        # -----------------------------------------
        # Return score
        # -----------------------------------------

        return {
            "brand": brand,
            "score": total,
            "signals": accepted,
            "error": None,
            "data_status": data_status,
        }