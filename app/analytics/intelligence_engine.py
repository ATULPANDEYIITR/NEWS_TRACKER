from __future__ import annotations

import hashlib
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from sqlalchemy import text

from app.database.session import SessionLocal


# ============================================================
# CONFIGURATION
# ============================================================

SIMILARITY_THRESHOLD = 0.72
MAX_RELATIONSHIPS_PER_ARTICLE = 5
TRENDING_LOOKBACK_HOURS = 24


# ============================================================
# TEXT NORMALIZATION
# ============================================================

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "from",
    "at",
    "by",
    "as",
    "is",
    "are",
    "was",
    "were",
    "has",
    "have",
    "had",
    "this",
    "that",
    "these",
    "those",
    "after",
    "before",
    "into",
    "over",
    "under",
    "new",
    "news",
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower()

    value = re.sub(
        r"https?://\S+",
        " ",
        value,
    )

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    words = [
        word
        for word in value.split()
        if word not in STOPWORDS
    ]

    return " ".join(words)


def text_similarity(
    first: str,
    second: str,
) -> float:

    first = normalize_text(first)
    second = normalize_text(second)

    if not first or not second:
        return 0.0

    return SequenceMatcher(
        None,
        first,
        second,
    ).ratio()


def stable_hash(value: str) -> str:
    return hashlib.sha256(
        value.encode(
            "utf-8",
            errors="ignore",
        )
    ).hexdigest()


# ============================================================
# DATABASE STRUCTURE
# ============================================================

def create_intelligence_tables(db):

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS daily_metrics (
                id BIGSERIAL PRIMARY KEY,
                metric_date DATE NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                metric_value DOUBLE PRECISION NOT NULL DEFAULT 0,
                dimension VARCHAR(100),
                dimension_value VARCHAR(255),
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_daily_metric
                    UNIQUE (
                        metric_date,
                        metric_name,
                        dimension,
                        dimension_value
                    )
            )
            """
        )
    )

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS article_relationships (
                id BIGSERIAL PRIMARY KEY,
                article_id BIGINT NOT NULL,
                related_article_id BIGINT NOT NULL,
                relationship_type VARCHAR(100) NOT NULL,
                similarity_score DOUBLE PRECISION,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT uq_article_relationship
                    UNIQUE (
                        article_id,
                        related_article_id,
                        relationship_type
                    )
            )
            """
        )
    )

    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_daily_metrics_date
            ON daily_metrics(metric_date)
            """
        )
    )

    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_daily_metrics_name
            ON daily_metrics(metric_name)
            """
        )
    )

    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_article_relationships_article
            ON article_relationships(article_id)
            """
        )
    )

    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_article_relationships_related
            ON article_relationships(related_article_id)
            """
        )
    )


# ============================================================
# ARTICLE RELATIONSHIP DETECTION
# ============================================================

def build_article_relationships(db):

    articles = db.execute(
        text(
            """
            SELECT
                id,
                headline,
                description,
                published_at,
                source_id
            FROM articles
            WHERE headline IS NOT NULL
            ORDER BY published_at DESC NULLS LAST, id DESC
            LIMIT 1000
            """
        )
    ).mappings().all()

    if len(articles) < 2:
        return 0

    created = 0

    # Compare recent articles against a bounded window.
    # This keeps processing practical as the database grows.
    for index, article in enumerate(articles):

        current_text = " ".join(
            filter(
                None,
                [
                    article["headline"],
                    article["description"],
                ],
            )
        )

        if not current_text:
            continue

        candidates = []

        for other in articles[index + 1:]:

            # Do not compare articles indefinitely far apart.
            if (
                article["published_at"]
                and other["published_at"]
            ):
                difference = abs(
                    article["published_at"]
                    - other["published_at"]
                )

                if difference > timedelta(days=7):
                    continue

            other_text = " ".join(
                filter(
                    None,
                    [
                        other["headline"],
                        other["description"],
                    ],
                )
            )

            similarity = text_similarity(
                current_text,
                other_text,
            )

            if similarity >= SIMILARITY_THRESHOLD:

                candidates.append(
                    (
                        similarity,
                        other["id"],
                    )
                )

        candidates.sort(
            reverse=True
        )

        for similarity, related_id in candidates[
            :MAX_RELATIONSHIPS_PER_ARTICLE
        ]:

            if article["id"] == related_id:
                continue

            existing = db.execute(
                text(
                    """
                    SELECT id
                    FROM article_relationships
                    WHERE article_id = :article_id
                      AND related_article_id = :related_id
                      AND relationship_type = 'similar_story'
                    """
                ),
                {
                    "article_id": article["id"],
                    "related_id": related_id,
                },
            ).first()

            if existing:
                db.execute(
                    text(
                        """
                        UPDATE article_relationships
                        SET similarity_score = :score
                        WHERE id = :id
                        """
                    ),
                    {
                        "score": similarity,
                        "id": existing.id,
                    },
                )

            else:

                db.execute(
                    text(
                        """
                        INSERT INTO article_relationships
                        (
                            article_id,
                            related_article_id,
                            relationship_type,
                            similarity_score
                        )
                        VALUES
                        (
                            :article_id,
                            :related_id,
                            'similar_story',
                            :score
                        )
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {
                        "article_id": article["id"],
                        "related_id": related_id,
                        "score": similarity,
                    },
                )

                created += 1

    return created


# ============================================================
# DAILY METRICS
# ============================================================

def save_metric(
    db,
    metric_date,
    metric_name,
    value,
    dimension=None,
    dimension_value=None,
):

    db.execute(
        text(
            """
            INSERT INTO daily_metrics
            (
                metric_date,
                metric_name,
                metric_value,
                dimension,
                dimension_value
            )
            VALUES
            (
                :metric_date,
                :metric_name,
                :value,
                :dimension,
                :dimension_value
            )
            ON CONFLICT
            (
                metric_date,
                metric_name,
                dimension,
                dimension_value
            )
            DO UPDATE SET
                metric_value = EXCLUDED.metric_value,
                updated_at = NOW()
            """
        ),
        {
            "metric_date": metric_date,
            "metric_name": metric_name,
            "value": float(value),
            "dimension": dimension,
            "dimension_value": dimension_value,
        },
    )


def calculate_daily_metrics(db):

    today = datetime.now(
        timezone.utc
    ).date()

    start_of_day = datetime.combine(
        today,
        datetime.min.time(),
        tzinfo=timezone.utc,
    )

    total_articles = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM articles
            WHERE published_at >= :start
            """
        ),
        {
            "start": start_of_day,
        },
    ).scalar() or 0

    total_sources = db.execute(
        text(
            """
            SELECT COUNT(DISTINCT source_id)
            FROM articles
            WHERE published_at >= :start
            """
        ),
        {
            "start": start_of_day,
        },
    ).scalar() or 0

    articles_24h = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM articles
            WHERE published_at >= :start
            """
        ),
        {
            "start": datetime.now(
                timezone.utc
            ) - timedelta(hours=24),
        },
    ).scalar() or 0

    save_metric(
        db,
        today,
        "articles_published",
        total_articles,
    )

    save_metric(
        db,
        today,
        "active_sources",
        total_sources,
    )

    save_metric(
        db,
        today,
        "articles_last_24_hours",
        articles_24h,
    )

    # Category metrics
    category_rows = db.execute(
        text(
            """
            SELECT
                c.name,
                COUNT(*) AS article_count
            FROM articles a
            JOIN article_categories ac
                ON ac.article_id = a.id
            JOIN categories c
                ON c.id = ac.category_id
            WHERE a.published_at >= :start
            GROUP BY c.name
            ORDER BY article_count DESC
            """
        ),
        {
            "start": start_of_day,
        },
    ).mappings().all()

    for row in category_rows:

        save_metric(
            db,
            today,
            "category_articles",
            row["article_count"],
            "category",
            row["name"],
        )

    # Country metrics
    country_rows = db.execute(
        text(
            """
            SELECT
                country,
                COUNT(*) AS article_count
            FROM articles
            WHERE published_at >= :start
              AND country IS NOT NULL
              AND TRIM(country) <> ''
            GROUP BY country
            ORDER BY article_count DESC
            LIMIT 100
            """
        ),
        {
            "start": start_of_day,
        },
    ).mappings().all()

    for row in country_rows:

        save_metric(
            db,
            today,
            "country_articles",
            row["article_count"],
            "country",
            row["country"],
        )

    # Region metrics
    region_rows = db.execute(
        text(
            """
            SELECT
                region,
                COUNT(*) AS article_count
            FROM articles
            WHERE published_at >= :start
              AND region IS NOT NULL
              AND TRIM(region) <> ''
            GROUP BY region
            ORDER BY article_count DESC
            """
        ),
        {
            "start": start_of_day,
        },
    ).mappings().all()

    for row in region_rows:

        save_metric(
            db,
            today,
            "region_articles",
            row["article_count"],
            "region",
            row["region"],
        )

    return {
        "articles_today": total_articles,
        "sources_today": total_sources,
        "articles_24h": articles_24h,
        "categories": len(category_rows),
        "countries": len(country_rows),
        "regions": len(region_rows),
    }


# ============================================================
# TRENDING TOPICS
# ============================================================

def calculate_trending_topics(db):

    start = datetime.now(
        timezone.utc
    ) - timedelta(hours=TRENDING_LOOKBACK_HOURS)

    rows = db.execute(
        text(
            """
            SELECT
                headline,
                description
            FROM articles
            WHERE published_at >= :start
            ORDER BY published_at DESC
            LIMIT 5000
            """
        ),
        {
            "start": start,
        },
    ).mappings().all()

    words = Counter()

    for row in rows:

        combined = " ".join(
            filter(
                None,
                [
                    row["headline"],
                    row["description"],
                ],
            )
        )

        normalized = normalize_text(
            combined
        )

        for word in normalized.split():

            if len(word) >= 4 and not word.isdigit():
                words[word] += 1

    return words.most_common(30)


# ============================================================
# BREAKING / DEVELOPING SIGNALS
# ============================================================

BREAKING_TERMS = {
    "breaking",
    "urgent",
    "live",
    "developing",
    "just in",
    "alert",
    "latest",
}

CONFLICT_TERMS = {
    "war",
    "attack",
    "strike",
    "missile",
    "bombing",
    "killed",
    "conflict",
    "fighting",
    "ceasefire",
    "military",
}

POLITICAL_TERMS = {
    "president",
    "prime minister",
    "minister",
    "election",
    "government",
    "parliament",
    "senate",
    "congress",
    "policy",
}

ECONOMIC_TERMS = {
    "economy",
    "inflation",
    "interest rate",
    "gdp",
    "market",
    "stocks",
    "shares",
    "bank",
    "trade",
    "tariff",
}


def calculate_signal_counts(db):

    start = datetime.now(
        timezone.utc
    ) - timedelta(hours=24)

    rows = db.execute(
        text(
            """
            SELECT headline
            FROM articles
            WHERE published_at >= :start
            """
        ),
        {
            "start": start,
        },
    ).scalars().all()

    counts = {
        "breaking_signals": 0,
        "conflict_signals": 0,
        "political_signals": 0,
        "economic_signals": 0,
    }

    for headline in rows:

        text_value = normalize_text(
            headline
        )

        if any(
            term in text_value
            for term in BREAKING_TERMS
        ):
            counts["breaking_signals"] += 1

        if any(
            term in text_value
            for term in CONFLICT_TERMS
        ):
            counts["conflict_signals"] += 1

        if any(
            term in text_value
            for term in POLITICAL_TERMS
        ):
            counts["political_signals"] += 1

        if any(
            term in text_value
            for term in ECONOMIC_TERMS
        ):
            counts["economic_signals"] += 1

    return counts


# ============================================================
# MAIN
# ============================================================

def run_intelligence():

    db = SessionLocal()

    try:

        print()
        print(
            "Creating intelligence tables..."
        )

        create_intelligence_tables(
            db
        )

        db.commit()

        print(
            "Intelligence tables: OK"
        )

        print()
        print(
            "Building article relationships..."
        )

        relationships = (
            build_article_relationships(db)
        )

        db.commit()

        print(
            f"New relationships: {relationships}"
        )

        print()
        print(
            "Calculating historical metrics..."
        )

        metrics = calculate_daily_metrics(
            db
        )

        signals = calculate_signal_counts(
            db
        )

        for name, value in signals.items():

            save_metric(
                db,
                datetime.now(
                    timezone.utc
                ).date(),
                name,
                value,
            )

        db.commit()

        print()
        print(
            "Daily metrics:"
        )

        for name, value in metrics.items():
            print(
                f"  {name}: {value}"
            )

        print()
        print(
            "24-hour intelligence signals:"
        )

        for name, value in signals.items():
            print(
                f"  {name}: {value}"
            )

        print()
        print(
            "Trending terms:"
        )

        trending = calculate_trending_topics(
            db
        )

        for index, (word, count) in enumerate(
            trending[:20],
            start=1,
        ):
            print(
                f"  {index:02d}. {word} ({count})"
            )

        print()
        print(
            "NEWS INTELLIGENCE ENGINE: COMPLETE"
        )

    except Exception:

        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    run_intelligence()
