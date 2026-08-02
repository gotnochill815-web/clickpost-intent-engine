import json

from fetch.fetch_pages import fetch_page


def load_reddit_sources(path):
    """Load manually curated Reddit URLs."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_reddit_posts(brand_name, source_file):
    """
    Fetch manually curated Reddit discussions for a brand.

    Returns:
        posts: Successfully fetched Reddit posts.
        failures: URLs that could not be fetched.
    """

    sources = load_reddit_sources(source_file)

    posts = []
    failures = []

    for entry in sources.get(brand_name, []):

        page = fetch_page(entry["url"])

        if page["success"]:

            posts.append(
                {
                    "query": entry["query"],
                    "url": entry["url"],
                    "text": page["text"],
                }
            )

        else:

            failures.append(
                {
                    "query": entry["query"],
                    "url": entry["url"],
                    "error": page["error"],
                }
            )

    return posts, failures