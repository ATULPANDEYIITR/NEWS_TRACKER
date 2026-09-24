from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.collectors.rss_collector import collect_news

if __name__ == "__main__":
    collect_news()
