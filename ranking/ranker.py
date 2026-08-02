import json
import os


class Ranker:
    """
    Loads all scored accounts, filters ICP-eligible brands,
    and ranks them by intent score.
    """

    def __init__(self):

        self.project_root = os.path.dirname(
            os.path.dirname(__file__)
        )

        self.scored_dir = os.path.join(
            self.project_root,
            "data",
            "scored",
        )

    def rank(self):

        ranked = []

        if not os.path.exists(self.scored_dir):
            return ranked

        for brand in os.listdir(self.scored_dir):

            score_file = os.path.join(
                self.scored_dir,
                brand,
                "intent_score.json",
            )

            if not os.path.exists(score_file):
                continue

            with open(score_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Only keep ICP-eligible brands
            if not data["icp"]["eligible"]:
                continue

            ranked.append(data)

        ranked.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        for idx, account in enumerate(ranked, start=1):
            account["rank"] = idx

        return ranked

    def save(self, ranked):

        output_dir = os.path.join(
            self.project_root,
            "data",
            "final",
        )

        os.makedirs(output_dir, exist_ok=True)

        output_file = os.path.join(
            output_dir,
            "ranked_accounts.json",
        )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                ranked,
                f,
                indent=4,
            )

        return output_file