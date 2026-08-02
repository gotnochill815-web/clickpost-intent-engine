import json
import logging
logger = logging.getLogger(__name__)
class OutreachGenerator:

    def __init__(self, client=None):
        self.client = client

    def _build_observation(self, signal):
        # Helper to extract signal description
        signal_type = signal.get("signal")
        evidence = signal.get("evidence", "").strip()
        return evidence or signal_type

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
        signals = scoring_result.get("signals", [])

        if not signals:
            return {
                "email": None,
                "linkedin": None,
                "error": "NO_SIGNALS",
            }

        # -----------------------------------------
        # Use highest-weight signal
        # -----------------------------------------

        signals = sorted(
            signals,
            key=lambda x: x.get("weight", 0),
            reverse=True,
        )

        top_signal = signals[0]
        signal_desc = self._build_observation(top_signal)

        # -----------------------------------------
        # Generate personalized outreach with GPT
        # -----------------------------------------

        try:
            prompt = f"""
            Generate a personalized outreach email and LinkedIn message for {brand}.

            Context: {brand} has a signal: {signal_desc}

            ClickPost helps retail brands improve post-purchase operations through:
            - Shipment tracking
            - Proactive shipment notifications
            - Carrier integrations
            - Returns workflows

            Generate:
            1. A professional email with subject line
            2. A short LinkedIn message

            Return the response as a JSON object with "email" and "linkedin" fields.
            """

            response = self.client.responses.create(
                model="gpt-5.4-mini",
                input=prompt,
                temperature=0.7,
            )

            result = json.loads(response.output_text)

            return {
                "email": result.get("email"),
                "linkedin": result.get("linkedin"),
                "error": None,
            }

        except Exception as e:
            # Fallback to template if GPT fails
            logger.warning(f"GPT outreach failed, using template: {e}")
            
            subject = f"Supporting Post-Purchase Operations at {brand}"
            
            email = f"""Subject: {subject}

Hi {brand} Team,

I noticed {brand} {signal_desc}.

ClickPost helps retail brands improve post-purchase operations through shipment tracking, proactive shipment notifications, carrier integrations, and returns workflows.

If you're evaluating tools in this area, I'd be happy to share how ClickPost works.

Would you be open to a brief conversation?

Best,
[Your Name]
"""

            linkedin = (
                f"Hi! I noticed {brand} {signal_desc}. "
                "Thought ClickPost's post-purchase platform might be relevant. "
                "Happy to connect and share more if useful."
            )

            return {
                "email": email,
                "linkedin": linkedin,
                "error": str(e) if str(e) else None,
            }