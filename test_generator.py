from outreach.generator import OutreachGenerator
from openai import OpenAI

client = OpenAI()

generator = OutreachGenerator(client)

scoring_result = {
    "brand": "Graza",
    "score": 6,
    "signals": [
        {
            "signal": "hiring_logistics",
            "evidence": "3PL Analyst",
            "weight": 6,
            "source": "careers"
        }
    ],
    "error": None
}

print(generator.generate(scoring_result))