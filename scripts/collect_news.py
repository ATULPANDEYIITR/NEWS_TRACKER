import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal, init_db
from app.news_engine import collect_news


def main():
    init_db()

    db = SessionLocal()

    try:
        result = collect_news(db)

        print("")
        print("=" * 60)
        print("NEWS TRACKER COLLECTION")
        print("=" * 60)
        print(
            "SOURCES:",
            result["sources"],
        )
        print(
            "NEW ARTICLES:",
            result["inserted"],
        )

        for item in result["results"]:
            print(
                f'{item["source"]}: '
                f'{item["status"]} '
                f'{item.get("inserted", 0)}'
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()
