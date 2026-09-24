from __future__ import annotations

import time

import feedparser
import requests

from app.collectors.database_feeds import get_database_feeds


def test_feed(feed):

    url = feed["feed_url"]

    started = time.perf_counter()

    try:

        response = requests.get(
            url,
            timeout=20,
            headers={
                "User-Agent":
                    "GlobalNewsTracker/1.0 "
                    "(RSS reader; contact through application owner)"
            },
        )

        elapsed = time.perf_counter() - started

        if response.status_code != 200:

            return {
                "status": "HTTP_ERROR",
                "http_status": response.status_code,
                "items": 0,
                "seconds": round(elapsed, 2),
            }

        parsed = feedparser.parse(
            response.content
        )

        return {
            "status": "OK" if parsed.entries else "EMPTY",
            "http_status": response.status_code,
            "items": len(parsed.entries),
            "seconds": round(elapsed, 2),
        }

    except Exception as exc:

        elapsed = time.perf_counter() - started

        return {
            "status": "ERROR",
            "http_status": None,
            "items": 0,
            "seconds": round(elapsed, 2),
            "error": str(exc),
        }


def main():

    feeds = get_database_feeds()

    working = 0
    failed = 0

    print()
    print(
        "=========================================="
    )
    print(
        "LIVE FEED HEALTH TEST"
    )
    print(
        "=========================================="
    )

    for feed in feeds:

        result = test_feed(feed)

        print(
            f"{feed['source_name']:<35} "
            f"{result['status']:<12} "
            f"items={result['items']:<4} "
            f"time={result['seconds']}s"
        )

        if result["status"] in (
            "OK",
            "EMPTY",
        ):
            working += 1
        else:
            failed += 1

    print()
    print(
        f"Working/available feeds : {working}"
    )
    print(
        f"Failed feeds             : {failed}"
    )


if __name__ == "__main__":
    main()
