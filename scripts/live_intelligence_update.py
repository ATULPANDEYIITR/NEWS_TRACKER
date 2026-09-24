from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.analytics.article_intelligence import run as run_intelligence


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BASE_UPDATE = PROJECT_ROOT / "scripts" / "run_news_update.py"


def run_base_news_update():

    print()
    print("========================================")
    print("BASE NEWS COLLECTION AND PROCESSING")
    print("========================================")

    result = subprocess.run(
        [
            sys.executable,
            str(BASE_UPDATE),
        ],
        cwd=str(PROJECT_ROOT),
    )

    return result.returncode


def run_article_intelligence():

    print()
    print("========================================")
    print("ARTICLE INTELLIGENCE ENRICHMENT")
    print("========================================")

    processed = run_intelligence(
        limit=5000
    )

    print()
    print(
        f"New articles intelligence analyzed: "
        f"{processed}"
    )

    return processed


def main():

    print()
    print("GLOBAL NEWS TRACKER")
    print("LIVE INTELLIGENCE PIPELINE")
    print("========================================")

    collection_result = (
        run_base_news_update()
    )

    if collection_result != 0:

        print()
        print(
            "Base news update returned an error."
        )

        print(
            "Intelligence enrichment will still "
            "attempt to process available articles."
        )

    try:

        run_article_intelligence()

    except Exception as exc:

        print()
        print(
            "ARTICLE INTELLIGENCE ERROR"
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )

        return 1

    print()
    print("========================================")
    print("LIVE INTELLIGENCE PIPELINE COMPLETE")
    print("========================================")

    if collection_result != 0:
        return collection_result

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
