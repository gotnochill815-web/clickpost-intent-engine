import json
import os


class ICPGate:
    """
    Deterministic ICP eligibility gate.

    Brands are considered ICP-eligible if they satisfy at least
    2 of the 3 ICP criteria:

      - D2C brand
      - Mid-market
      - Physical products

    ICP metadata is loaded from:

        data/sources/icp_data.json
    """

    def __init__(self):

        project_root = os.path.dirname(
            os.path.dirname(__file__)
        )

        icp_file = os.path.join(
            project_root,
            "data",
            "sources",
            "icp_data.json",
        )

        with open(icp_file, "r", encoding="utf-8") as f:
            self.icp_data = json.load(f)

    def evaluate(self, brand):

        # -----------------------------------------
        # Brand missing from ICP dataset
        # -----------------------------------------

        if brand not in self.icp_data:
            return {
                "eligible": False,
                "checks": {
                    "dtc": False,
                    "mid_market": False,
                    "physical_products": False,
                },
                "passed": 0,
                "flagged_for_review": False,
                "reason": "Brand not found in ICP dataset.",
            }

        data = self.icp_data[brand]

        # -----------------------------------------
        # Only score ICP criteria
        # Ignore metadata fields
        # -----------------------------------------

        checks = {
            "dtc": data["dtc"],
            "mid_market": data["mid_market"],
            "physical_products": data["physical_products"],
        }

        passed = sum(bool(v) for v in checks.values())

        # Assignment guidance:
        # Assume brands qualify unless evidence
        # clearly suggests otherwise.
        eligible = passed >= 2

        # -----------------------------------------
        # Reason
        # -----------------------------------------

        if data.get("reason"):
            reason = data["reason"]
        elif eligible:
            reason = "Passed ICP eligibility gate."
        else:
            reason = f"Only {passed}/3 ICP criteria met."

        # -----------------------------------------
        # Output
        # -----------------------------------------

        return {
            "eligible": eligible,
            "checks": checks,
            "passed": passed,
            "flagged_for_review": data.get(
                "flagged_for_review",
                False,
            ),
            "reason": reason,
        }