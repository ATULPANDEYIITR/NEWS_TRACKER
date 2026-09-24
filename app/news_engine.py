from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import yaml
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.config import MAX_ARTICLES_PER_SOURCE, SOURCES_FILE
from app.models import Article, Source


TRACKING_PARAMETERS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


CATEGORY_KEYWORDS = {
    "Technology": {
        "ai",
        "artificial intelligence",
        "software",
        "chip",
        "semiconductor",
        "cyber",
        "technology",
        "google",
        "microsoft",
        "apple",
        "openai",
        "robot",
    },
    "Business": {
        "business",
        "company",
        "corporate",
        "economy",
        "economic",
        "trade",
        "market",
        "bank",
        "finance",
        "stock",
        "investment",
        "earnings",
    },
    "Science": {
        "science",
        "research",
        "space",
        "nasa",
        "physics",
        "biology",
        "climate",
        "scientist",
        "study",
    },
    "Security": {
        "security",
        "cybersecurity",
        "attack",
        "hacker",
        "malware",
        "ransomware",
        "defence",
        "defense",
        "military",
        "terror",
    },
    "Markets": {
        "market",
        "stocks",
        "shares",
        "sensex",
        "nifty",
        "nasdaq",
        "dow",
        "bond",
        "currency",
    },
    "Climate": {
        "climate",
        "weather",
        "flood",
        "drought",
        "heatwave",
        "storm",
        "hurricane",
        "environment",
        "emissions",
    },
    "India": {
        "india",
        "indian",
        "delhi",
        "mumbai",
        "lucknow",
        "bihar",
        "uttar pradesh",
        "modi",
        "parliament",
        "supreme court",
    },
}


def clean_text(value):
    if not value:
        return ""

    text = BeautifulSoup(str(value), "html.parser").get_text(
        " ",
        strip=True,
    )

    return " ".join(text.split())


def normalize_url(url):
    if not url:
        return ""

    try:
        parts = urlsplit(url.strip())

        query_items = [
            item
            for item in parse_qsl(parts.query, keep_blank_values=True)
            if item[0].lower() not in TRACKING_PARAMETERS
        ]

        query = urlencode(query_items)

        path = parts.path.rstrip("/") or "/"

        return urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                path,
                query,
                "",
            )
        )
    except Exception:
        return url.strip()


def make_hash(value):
    return sha256(
        value.encode("utf-8", errors="ignore")
    ).hexdigest()


def parse_date(entry):
    parsed = entry.get("published_parsed") or entry.get(
        "updated_parsed"
    )

    if parsed:
        try:
            return datetime(
                parsed.tm_year,
                parsed.tm_mon,
                parsed.tm_mday,
                parsed.tm_hour,
                parsed.tm_min,
                parsed.tm_sec,
                tzinfo=timezone.utc,
            ).replace(tzinfo=None)
        except Exception:
            pass

    return datetime.utcnow()


def categorize(title, summary, source_category):
    text = f"{title} {summary}".lower()

    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if keyword in text:
                score += 1

        scores[category] = score

    best_category = max(
        scores,
        key=scores.get,
    )

    if scores[best_category] == 0:
        return source_category or "World"

    return best_category


def load_source_registry():
    if not Path(SOURCES_FILE).exists():
        return []

    with open(
        SOURCES_FILE,
        "r",
        encoding="utf-8",
    ) as handle:
        data = yaml.safe_load(handle) or {}

    return data.get("sources", [])


def sync_sources(db):
    registry = load_source_registry()

    for item in registry:
        source = db.scalar(
            select(Source).where(
                Source.name == item["name"]
            )
        )

        if source is None:
            source = Source(
                name=item["name"],
                url=item["url"],
                feed_url=item["feed_url"],
                category=item.get(
                    "category",
                    "World",
                ),
                country=item.get("country"),
                source_type=item.get(
                    "source_type",
                    "media",
                ),
                active=item.get(
                    "active",
                    True,
                ),
            )

            db.add(source)

        else:
            source.url = item["url"]
            source.feed_url = item["feed_url"]
            source.category = item.get(
                "category",
                "World",
            )
            source.country = item.get("country")
            source.source_type = item.get(
                "source_type",
                "media",
            )
            source.active = item.get(
                "active",
                True,
            )

    db.commit()

    return registry


def fetch_feed(feed_url):
    parsed = feedparser.parse(feed_url)

    if getattr(parsed, "bozo", False):
        # Feedparser can mark malformed feeds as bozo
        # while still returning usable entries.
        pass

    return parsed


def collect_source(db, source):
    source.last_checked = datetime.utcnow()

    try:
        feed = fetch_feed(source.feed_url)

        entries = list(
            getattr(feed, "entries", [])
        )[:MAX_ARTICLES_PER_SOURCE]

        inserted = 0

        for entry in entries:
            title = clean_text(
                entry.get("title", "")
            )

            url = normalize_url(
                entry.get("link", "")
            )

            summary = clean_text(
                entry.get("summary")
                or entry.get("description")
                or ""
            )

            if not title or not url:
                continue

            content_hash = make_hash(
                f"{title}|{url}"
            )

            existing = db.scalar(
                select(Article).where(
                    Article.normalized_url == url
                )
            )

            if existing:
                continue

            category = categorize(
                title,
                summary,
                source.category,
            )

            article = Article(
                source_id=source.id,
                title=title[:1000],
                url=url[:2000],
                normalized_url=url[:2000],
                summary=summary[:5000],
                category=category,
                published_at=parse_date(entry),
                content_hash=content_hash,
                author=clean_text(
                    entry.get("author", "")
                )[:300],
                image_url=(
                    entry.get("media_content", [{}])[0]
                    .get("url")
                    if entry.get("media_content")
                    else None
                ),
            )

            db.add(article)
            inserted += 1

        source.last_success = datetime.utcnow()
        source.last_error = None
        source.article_count = (
            db.query(Article)
            .filter(
                Article.source_id == source.id
            )
            .count()
            + inserted
        )

        db.commit()

        return {
            "source": source.name,
            "inserted": inserted,
            "status": "success",
        }

    except Exception as exc:
        db.rollback()

        source.last_error = str(exc)[:2000]
        source.last_checked = datetime.utcnow()

        db.commit()

        return {
            "source": source.name,
            "inserted": 0,
            "status": "error",
            "error": str(exc),
        }


def collect_news(db):
    sync_sources(db)

    sources = (
        db.query(Source)
        .filter(Source.active.is_(True))
        .all()
    )

    results = []

    for source in sources:
        results.append(
            collect_source(
                db,
                source,
            )
        )

    return {
        "sources": len(sources),
        "results": results,
        "inserted": sum(
            item.get("inserted", 0)
            for item in results
        ),
    }
