import json
import os


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def save_text(path, text):
    ensure_dir(os.path.dirname(path))

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def save_json(path, data):
    ensure_dir(os.path.dirname(path))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def find_first_working_page(base_url, candidates, fetch_fn):
    """
    Try multiple URL paths and return the first successful page.
    """

    for path in candidates:

        url = base_url.rstrip("/") + path

        result = fetch_fn(url)

        if result["success"]:
            return result

    return None