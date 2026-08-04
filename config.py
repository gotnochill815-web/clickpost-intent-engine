import os

# ---------------------------------------------------------
# Project Root
# ---------------------------------------------------------

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------
# HTTP Headers
# ---------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )
}

# ---------------------------------------------------------
# Brands
# ---------------------------------------------------------

BRANDS = [
    {
        "name": "Brooklinen",
        "website": "https://brooklinen.com",
    },
    {
        "name": "Vuori",
        "website": "https://vuoriclothing.com",
    },
    {
        "name": "Rothy's",
        "website": "https://rothys.com",
    },
    {
        "name": "Solo Stove",
        "website": "https://solostove.com",
    },
    {
        "name": "Blueland",
        "website": "https://www.blueland.com",
    },
    {
        "name": "Caraway",
        "website": "https://www.carawayhome.com",
    },
    {
        "name": "Graza",
        "website": "https://graza.co",
    },
    {
        "name": "Kosas",
        "website": "https://kosas.com",
    },

    # ---------------- New Brands ----------------

    {
        "name": "Jones Road Beauty",
        "website": "https://www.jonesroadbeauty.com",
    },
    {
        "name": "Liquid Death",
        "website": "https://liquiddeath.com",
    },
    {
        "name": "Our Place",
        "website": "https://fromourplace.com",
    },
    {
        "name": "Magic Spoon",
        "website": "https://magicspoon.com",
    },
]