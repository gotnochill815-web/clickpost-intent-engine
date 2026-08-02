import re
import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )
}


def clean_html(html):
    """
    Convert HTML into cleaned text.
    """

    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    lines = []
    seen = set()

    for line in text.splitlines():

        line = " ".join(line.split())

        if not line:
            continue

        if line in seen:
            continue

        seen.add(line)
        lines.append(line)

    return "\n".join(lines)


def find_external_careers_page(html):
    """
    Look for external ATS providers inside careers page HTML.
    """

    patterns = [
        r'https://careers\.smartrecruiters\.com/[^\s"\']+',
        r'https://boards\.greenhouse\.io/[^\s"\']+',
        r'https://jobs\.lever\.co/[^\s"\']+',
    ]

    for pattern in patterns:

        match = re.search(pattern, html)

        if match:
            return match.group(0)

    return None


def fetch_page(url: str, page_type=None, timeout: int = 20):
    """
    Fetch webpage.

    Automatically follows external ATS pages
    (SmartRecruiters / Greenhouse / Lever)
    if the careers landing page appears to contain
    only marketing content.

    Returns:
        {
            "success": bool,
            "status_code": int,
            "url": str,
            "text": str,
            "error": str
        }
    """

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
        )

        response.raise_for_status()

        ats_followed = False
        ats_url = None
        likely_incomplete = False

        final_url = url

        html = response.text

        clean_text = clean_html(html)

        # --------------------------------------------------
        # ATS fallback
        # --------------------------------------------------

        if (
            page_type == "careers"
            and len(clean_text) < 3000
        ):

            ats_url = find_external_careers_page(html)

            if ats_url:

                ats_followed = True

                print(f"Following ATS page: {ats_url}")

                ats_response = requests.get(
                    ats_url,
                    headers=HEADERS,
                    timeout=timeout,
                )

                ats_response.raise_for_status()

                final_url = ats_url

                clean_text = clean_html(
                    ats_response.text
                )

            else:
                likely_incomplete = True

        return {
            "success": True,
            "status_code": response.status_code,
            "url": final_url,
            "text": clean_text,
            "error": None,
            "ats_followed": ats_followed,
            "ats_url": ats_url,
            "likely_incomplete": likely_incomplete,
        }

    except Exception as e:

        return {
            "success": False,
            "status_code": None,
            "url": url,
            "text": "",
            "error": str(e),
        }