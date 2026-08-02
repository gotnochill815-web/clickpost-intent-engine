import json
import logging
import re

from google.genai import types

from extract.prompts import EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

MAX_DOCUMENT_CHARS = 15000


def parse_json(text):
    """
    Extract the first JSON object from a Gemini response.

    Handles:
    - Markdown code fences
    - Extra explanatory text
    """

    if text is None:
        raise json.JSONDecodeError(
            "Response is None",
            "",
            0,
        )

    text = str(text).strip()

    text = re.sub(
        r"^```json",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()

    text = re.sub(
        r"^```",
        "",
        text,
    ).strip()

    text = re.sub(
        r"```$",
        "",
        text,
    ).strip()

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise json.JSONDecodeError(
            "No JSON object found",
            text,
            0,
        )

    return json.loads(match.group(0))


# --------------------------------------------
# Signal Filtering
# --------------------------------------------

INVALID_HEADINGS = {
    "open roles",
    "careers",
    "jobs",
    "join us",
    "opportunities",
    "returns & exchanges",
    "do it online.",
    "do it in store.",
    "do it online",
    "do it in store",
}

POSITIVE_WORDS = [
    "easy",
    "quick",
    "simple",
    "hassle-free",
    "no hassle",
    "free return",
    "free returns",
    "free exchange",
    "free exchanges",
    "no fee",
]

POLICY_PHRASES = [
    "within 30 days",
    "only offer returns",
    "domestic orders",
    "international orders",
    "return fee",
    "refund policy",
]


def filter_signals(signals):
    filtered = []

    for signal in signals:

        evidence = signal.get("evidence", "").strip()
        evidence_lower = evidence.lower()

        signal_type = signal.get("signal", "")

        # ------------------------------
        # Remove generic headings
        # ------------------------------
        if evidence_lower in INVALID_HEADINGS:
            continue

        # ------------------------------
        # Only filter returns-related signals
        # ------------------------------
        if signal_type in {
            "returns_issue",
            "reverse_logistics",
        }:

            # ---------------------------------
            # Ignore navigation instructions
            # ---------------------------------
            if evidence_lower in {
                "do it online.",
                "do it online",
                "do it in store.",
                "do it in store",
            }:
                continue

            # Easy / positive language
            if any(word in evidence_lower for word in POSITIVE_WORDS):
                # More precise check for "no fee"
                if (
                    "no fee" in evidence_lower
                    and "mail-in refund" in evidence_lower
                    and not any(
                        x in evidence_lower
                        for x in [
                            "delay",
                            "lost",
                            "barcode",
                            "damaged",
                            "unable",
                            "cannot",
                            "failed",
                        ]
                    )
                ):
                    continue
                continue

            # Neutral policy statements
            if any(p in evidence_lower for p in POLICY_PHRASES):

                # Keep genuine operational pain
                if not any(
                    x in evidence_lower
                    for x in [
                        "unable",
                        "cannot",
                        "failed",
                        "delay",
                        "lost",
                        "barcode",
                        "perishable",
                        "damaged",
                        "exception",
                    ]
                ):
                    continue

        filtered.append(signal)

    return filtered


class SignalExtractor:

    def __init__(self, client):
        self.client = client

    def extract(
        self,
        brand_name,
        text,
        source,
    ):

        # --------------------------------------------
        # Validate
        # --------------------------------------------

        if not text or not text.strip():
            return {
                "signals": [],
                "error": "EMPTY_DOCUMENT",
            }

        if len(text) > MAX_DOCUMENT_CHARS:

            logger.warning(
                "Truncating %s (%s): %d -> %d chars",
                brand_name,
                source,
                len(text),
                MAX_DOCUMENT_CHARS,
            )

            text = text[:MAX_DOCUMENT_CHARS]

        # --------------------------------------------
        # Prompt
        # --------------------------------------------

        prompt = f"""
{EXTRACTION_PROMPT}

Target brand:
{brand_name}

Document type:
{source}

Only extract signals referring to the TARGET BRAND.

Document:

{text}

Return ONLY valid JSON.

Output:

{{
  "signals":[
    {{
      "signal":"...",
      "evidence":"..."
    }}
  ]
}}

If there are no signals return exactly:

{{"signals":[]}}
"""

        # --------------------------------------------
        # GPT-5.4-mini
        # --------------------------------------------

        try:

            response = self.client.responses.create(
                model="gpt-5.4-mini",
                input=prompt,
                temperature=0,
            )

            response_text = response.output_text

            if not response_text:

                return {
                    "signals": [],
                    "error": "EMPTY_MODEL_RESPONSE",
                }

        except Exception as e:

            logger.exception(
                "GPT API failed for %s (%s)",
                brand_name,
                source,
            )

            return {
                "signals": [],
                "error": f"API_ERROR: {e}",
            }

        # --------------------------------------------
        # Parse JSON
        # --------------------------------------------

        try:

            data = parse_json(response_text)

        except Exception as e:

            logger.exception(
                "Failed parsing GPT output for %s (%s)",
                brand_name,
                source,
            )

            logger.error(
                "Raw GPT response:\n%s",
                response_text,
            )

            return {
                "signals": [],
                "error": f"PARSE_ERROR: {e}",
            }

        # --------------------------------------------
        # Normalize
        # --------------------------------------------

        if not isinstance(data, dict):
            data = {"signals": []}

        signals = data.get("signals", [])

        if not isinstance(signals, list):
            signals = []

        normalized = []

        for signal in signals:

            if not isinstance(signal, dict):
                continue

            evidence = signal.get(
                "evidence",
                "",
            )

            if isinstance(evidence, str):
                evidence = evidence.strip()
            else:
                evidence = ""

            normalized.append(
                {
                    "signal": signal.get(
                        "signal",
                        "",
                    ),
                    "evidence": evidence,
                    "brand": brand_name,
                    "source": source,
                }
            )

        # --------------------------------------------
        # Apply rule-based filtering
        # --------------------------------------------
        normalized = filter_signals(normalized)

        return {
            "signals": normalized,
            "error": None,
        }