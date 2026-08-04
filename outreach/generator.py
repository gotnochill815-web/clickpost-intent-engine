import json
import logging

from .prompts import OUTREACH_PROMPT

logger = logging.getLogger(__name__)


class OutreachGenerator:

    def __init__(self, client=None):
        self.client = client

    def generate(self, scoring_result):

        # -----------------------------------------
        # Validate scoring result
        # -----------------------------------------

        if scoring_result.get("error"):
            return {
                "email": None,
                "linkedin": None,
                "error": scoring_result["error"],
            }

        brand = scoring_result.get("brand")
        score = scoring_result.get("score", 0)
        signals = scoring_result.get("signals", [])

        if not signals:
            return {
                "email": None,
                "linkedin": None,
                "error": "NO_SIGNALS",
            }

        # -----------------------------------------
        # Keep only verified information
        # -----------------------------------------

        verified_signals = []

        for signal in signals:
            verified_signals.append(
                {
                    "signal": signal.get("signal"),
                    "evidence": signal.get("evidence"),
                    "source": signal.get("source"),
                }
            )

        # -----------------------------------------
        # Build prompt
        # -----------------------------------------

        prompt = f"""
{OUTREACH_PROMPT}

Brand:
{brand}

Intent Score:
{score}

Verified Signals:
{json.dumps(verified_signals, indent=2)}
"""

        # -----------------------------------------
        # GPT Generation
        # -----------------------------------------

        try:

            response = self.client.responses.create(
                model="gpt-5-mini",
                input=prompt,
            )

            output = response.output_text.strip()

            print("========== MODEL OUTPUT ==========")
            print(output)
            print("==================================")

            # Remove markdown fences if present
            if output.startswith("```"):
                output = output.replace("```json", "").replace("```", "").strip()

            result = json.loads(output)

            return {
                "email": f"Subject: {result['email']['subject']}\n\n{result['email']['body']}",
                "linkedin": result["linkedin"],
                "error": None,
            }

        except Exception as e:

            logger.warning(f"GPT outreach failed: {e}")

            top = verified_signals[0]

            subject = f"ClickPost for {brand}"

            body = f"""Hi {brand} Team,

I noticed the following publicly available update:

"{top['evidence']}"

ClickPost helps retail brands improve post-purchase experiences through shipment tracking, proactive notifications, carrier integrations, and returns workflow automation.

If you're evaluating solutions in this area, I'd be happy to share how ClickPost works.

Would you be open to a brief conversation?

Best,
[Your Name]
"""

            linkedin = (
                f"Hi! I came across '{top['evidence']}' about {brand}. "
                "Thought I'd reach out in case ClickPost's post-purchase platform is relevant. "
                "Happy to connect!"
            )

            return {
                "email": f"Subject: {subject}\n\n{body}",
                "linkedin": linkedin,
                "error": str(e),
            }