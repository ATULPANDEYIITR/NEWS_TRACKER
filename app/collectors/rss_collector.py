
import hashlib
import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import feedparser
import httpx
from dateutil import parser as date_parser
from sqlalchemy import select

from app.collectors.feed_registry import FEEDS

# DATABASE_LIVE_FEED_DISCOVERY
try:
    _database_live_feeds = get_database_feeds()

    for _database_feed in _database_live_feeds:

        _source_name = _database_feed["source_name"]
        _feed_url = _database_feed["feed_url"]

        if _source_name not in FEEDS:
            FEEDS[_source_name] = _feed_url

except Exception:
    _database_live_feeds = []
from app.collectors.database_feeds import get_database_feeds
from app.core.logging import get_logger
from app.database.session import SessionLocal
from app.models import Article, IngestionLog, Source, SourceHealth

logger = get_logger(__name__)

USER_AGENT = "GlobalNewsTracker/0.1"
TIMEOUT = 20.0


def clean_text(value):
    if not value:
        return None

    text = unescape(str(value))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text or None


def normalize_url(url):
    if not url:
        return ""

    parts = urlsplit(url.strip())

    query_items = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_")
        and key.lower() not in {
            "fbclid",
            "gclid",
            "mc_cid",
            "mc_eid",
        }
    ]

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(query_items),
            "",
        )
    )


def normalize_title(title):
    title = clean_text(title) or ""
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_datetime(entry):
    for field in ("published", "updated", "created"):
        value = entry.get(field)

        if value:
            try:
                parsed = date_parser.parse(value)

                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)

                return parsed.astimezone(timezone.utc)
            except Exception:
                pass

    for field in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(field)

        if value:
            try:
                return datetime(*value[:6], tzinfo=timezone.utc)
            except Exception:
                pass

    return None


def entry_to_article(source, entry):
    headline = clean_text(entry.get("title"))
    link = entry.get("link")

    if not headline or not link:
        return None

    canonical_url = normalize_url(link)

    description = clean_text(
        entry.get("summary")
        or entry.get("description")
    )

    content = None

    if entry.get("content"):
        try:
            content = clean_text(entry.content[0].value)
        except Exception:
            content = None

    if not content:
        content = description

    normalized_title = normalize_title(headline)

    return {
        "source_id": source.id,
        "headline": headline[:1000],
        "canonical_url": canonical_url[:2000],
        "original_url": link[:2000],
        "author": clean_text(entry.get("author")),
        "description": description,
        "content": content,
        "published_at": parse_datetime(entry),
        "language": source.language,
        "country": source.country,
        "region": source.region,
        "content_hash": sha256_text(content or description or headline),
        "normalized_title_hash": sha256_text(normalized_title),
    }


def get_or_create_health(db, source_id):
    health = db.scalar(
        select(SourceHealth).where(
            SourceHealth.source_id == source_id
        )
    )

    if health is None:
        health = SourceHealth(
            source_id=source_id,
            is_healthy=True,
            consecutive_failures=0,
            total_attempts=0,
            successful_attempts=0,
        )
        db.add(health)
        db.flush()

    return health


def collect_source(db, source):
    feed_urls = FEEDS.get(source.name, [])

    if not feed_urls:
        return {
            "status": "not_configured",
            "found": 0,
            "added": 0,
            "skipped": 0,
            "message": "No public RSS/API endpoint configured.",
        }

    total_found = 0
    total_added = 0
    total_skipped = 0
    errors = []

    health = get_or_create_health(db, source.id)

    for feed_url in feed_urls:
        try:
            health.total_attempts += 1

            response = httpx.get(
                feed_url,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT,
                follow_redirects=True,
            )

            health.last_status_code = response.status_code
            health.last_checked_at = datetime.now(timezone.utc)

            response.raise_for_status()

            parsed = feedparser.parse(response.content)

            if parsed.bozo and not parsed.entries:
                raise RuntimeError("Feed could not be parsed.")

            health.successful_attempts += 1
            health.consecutive_failures = 0
            health.is_healthy = True
            health.last_error = None
            health.last_success_at = datetime.now(timezone.utc)

            for entry in parsed.entries:
                article_data = entry_to_article(source, entry)

                if article_data is None:
                    total_skipped += 1
                    continue

                total_found += 1

                existing_url = db.scalar(
                    select(Article.id).where(
                        Article.source_id == source.id,
                        Article.canonical_url
                        == article_data["canonical_url"],
                    )
                )

                if existing_url:
                    total_skipped += 1
                    continue

                existing_hash = db.scalar(
                    select(Article.id).where(
                        Article.content_hash
                        == article_data["content_hash"]
                    )
                )

                if existing_hash:
                    total_skipped += 1
                    continue

                existing_title = db.scalar(
                    select(Article.id).where(
                        Article.normalized_title_hash
                        == article_data["normalized_title_hash"]
                    )
                )

                if existing_title:
                    total_skipped += 1
                    continue

                db.add(Article(**article_data))
                total_added += 1

        except Exception as exc:
            error_message = f"{feed_url}: {str(exc)[:500]}"
            errors.append(error_message)

            health.consecutive_failures += 1
            health.is_healthy = False
            health.last_error = error_message
            health.last_checked_at = datetime.now(timezone.utc)

            logger.warning(
                "Feed failed | source=%s | error=%s",
                source.name,
                error_message,
            )

    if errors and total_found == 0:
        status = "failed"
    else:
        status = "success"

    return {
        "status": status,
        "found": total_found,
        "added": total_added,
        "skipped": total_skipped,
        "message": "; ".join(errors) if errors else "Collection completed.",
    }


def collect_news():
    started = datetime.now(timezone.utc)

    with SessionLocal() as db:
        sources = db.scalars(
            select(Source).where(
                Source.is_active.is_(True)
            )
        ).all()

        totals = {
            "sources": len(sources),
            "configured": 0,
            "successful": 0,
            "failed": 0,
            "not_configured": 0,
            "found": 0,
            "added": 0,
            "skipped": 0,
        }

        print("")
        print("==========================================")
        print("GLOBAL NEWS COLLECTOR")
        print("==========================================")
        print(f"Active sources: {len(sources)}")
        print("")

        for number, source in enumerate(sources, start=1):
            print(
                f"[{number:03d}/{len(sources):03d}] "
                f"{source.name}"
            )

            try:
                result = collect_source(db, source)

                if result["status"] == "not_configured":
                    totals["not_configured"] += 1
                    print("       NOT CONFIGURED")
                elif result["status"] == "failed":
                    totals["failed"] += 1
                    totals["configured"] += 1
                    print(
                        f"       FAILED | "
                        f"found={result['found']} "
                        f"added={result['added']}"
                    )
                else:
                    totals["successful"] += 1
                    totals["configured"] += 1
                    print(
                        f"       OK | "
                        f"found={result['found']} "
                        f"added={result['added']} "
                        f"skipped={result['skipped']}"
                    )

                totals["found"] += result["found"]
                totals["added"] += result["added"]
                totals["skipped"] += result["skipped"]

                db.add(
                    IngestionLog(
                        source_id=source.id,
                        status=result["status"],
                        articles_found=result["found"],
                        articles_added=result["added"],
                        articles_skipped=result["skipped"],
                        message=result["message"],
                        started_at=started,
                        completed_at=datetime.now(timezone.utc),
                    )
                )

                db.commit()

            except Exception as exc:
                db.rollback()

                totals["failed"] += 1

                print(
                    f"       SOURCE ERROR: {str(exc)[:300]}"
                )

                try:
                    db.add(
                        IngestionLog(
                            source_id=source.id,
                            status="failed",
                            articles_found=0,
                            articles_added=0,
                            articles_skipped=0,
                            message=str(exc)[:2000],
                            started_at=started,
                            completed_at=datetime.now(timezone.utc),
                        )
                    )
                    db.commit()
                except Exception:
                    db.rollback()

        print("")
        print("==========================================")
        print("COLLECTION COMPLETE")
        print("==========================================")
        print(f"Sources                  : {totals['sources']}")
        print(f"Feeds configured         : {totals['configured']}")
        print(f"Successful sources      : {totals['successful']}")
        print(f"Failed sources          : {totals['failed']}")
        print(f"Not configured          : {totals['not_configured']}")
        print(f"Articles found          : {totals['found']}")
        print(f"Articles added          : {totals['added']}")
        print(f"Articles skipped        : {totals['skipped']}")
        print("==========================================")


if __name__ == "__main__":
    collect_news()

