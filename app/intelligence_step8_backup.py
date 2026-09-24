from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re
from difflib import SequenceMatcher
from typing import Any


STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "for",
    "from",
    "with",
    "into",
    "over",
    "after",
    "before",
    "amid",
    "during",
    "this",
    "that",
    "these",
    "those",
    "their",
    "they",
    "them",
    "will",
    "would",
    "could",
    "should",
    "has",
    "have",
    "had",
    "was",
    "were",
    "are",
    "is",
    "be",
    "been",
    "being",
    "its",
    "it's",
    "on",
    "in",
    "at",
    "to",
    "of",
    "by",
    "as",
    "an",
    "about",
    "says",
    "say",
    "said",
    "new",
    "latest",
    "live",
    "updates",
    "update",
    "breaking",
}


ENTITY_TERMS = {
    "trump",
    "modi",
    "putin",
    "zelenskyy",
    "zelensky",
    "biden",
    "harris",
    "musk",
    "google",
    "microsoft",
    "apple",
    "amazon",
    "meta",
    "openai",
    "nvidia",
    "tesla",
    "tata",
    "reliance",
    "adani",
    "infosys",
    "wipro",
    "israel",
    "iran",
    "ukraine",
    "russia",
    "china",
    "india",
    "pakistan",
    "europe",
    "united",
    "states",
    "supreme",
    "court",
    "parliament",
    "government",
    "president",
    "prime",
    "minister",
    "election",
    "elections",
    "nasa",
    "isro",
    "spacex",
}


def clean_text(value: str | None) -> str:
    if not value:
        return ""

    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def normalize_title(title: str | None) -> str:
    text = clean_text(title).lower()

    text = re.sub(
        r"https?://\S+",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def title_tokens(title: str | None) -> set[str]:
    normalized = normalize_title(title)

    tokens = {
        token
        for token in normalized.split()
        if len(token) > 2
        and token not in STOP_WORDS
    }

    return tokens


def extract_entities(title: str | None) -> set[str]:
    tokens = title_tokens(title)

    return {
        token
        for token in tokens
        if token in ENTITY_TERMS
    }


def jaccard_similarity(
    first: set[str],
    second: set[str],
) -> float:
    if not first or not second:
        return 0.0

    union = first | second

    if not union:
        return 0.0

    return len(first & second) / len(union)


def token_overlap_similarity(
    first: set[str],
    second: set[str],
) -> float:
    if not first or not second:
        return 0.0

    smaller = min(
        len(first),
        len(second),
    )

    if smaller == 0:
        return 0.0

    return len(first & second) / smaller


def sequence_similarity(
    first: str,
    second: str,
) -> float:
    if not first or not second:
        return 0.0

    return SequenceMatcher(
        None,
        first,
        second,
    ).ratio()


def time_similarity(
    first: datetime | None,
    second: datetime | None,
) -> float:
    if not first or not second:
        return 0.5

    if first.tzinfo is None:
        first = first.replace(
            tzinfo=timezone.utc
        )

    if second.tzinfo is None:
        second = second.replace(
            tzinfo=timezone.utc
        )

    difference_hours = abs(
        (first - second).total_seconds()
    ) / 3600

    if difference_hours <= 2:
        return 1.0

    if difference_hours <= 6:
        return 0.85

    if difference_hours <= 12:
        return 0.70

    if difference_hours <= 24:
        return 0.50

    if difference_hours <= 48:
        return 0.25

    return 0.0


def category_similarity(
    first: str | None,
    second: str | None,
) -> float:
    if not first or not second:
        return 0.5

    return (
        1.0
        if first.lower() == second.lower()
        else 0.0
    )


def calculate_similarity(
    first_title: str,
    second_title: str,
    first_category: str | None = None,
    second_category: str | None = None,
    first_time: datetime | None = None,
    second_time: datetime | None = None,
) -> float:

    first_tokens = title_tokens(first_title)
    second_tokens = title_tokens(second_title)

    first_entities = extract_entities(first_title)
    second_entities = extract_entities(second_title)

    token_score = jaccard_similarity(
        first_tokens,
        second_tokens,
    )

    overlap_score = token_overlap_similarity(
        first_tokens,
        second_tokens,
    )

    entity_score = jaccard_similarity(
        first_entities,
        second_entities,
    )

    sequence_score = sequence_similarity(
        normalize_title(first_title),
        normalize_title(second_title),
    )

    time_score = time_similarity(
        first_time,
        second_time,
    )

    category_score = category_similarity(
        first_category,
        second_category,
    )

    score = (
        (token_score * 0.25)
        + (overlap_score * 0.20)
        + (entity_score * 0.25)
        + (sequence_score * 0.15)
        + (time_score * 0.10)
        + (category_score * 0.05)
    )

    return round(
        min(score, 1.0),
        4,
    )


def should_cluster(
    first: dict[str, Any],
    second: dict[str, Any],
) -> bool:

    first_title = first.get("title", "")
    second_title = second.get("title", "")

    first_tokens = title_tokens(first_title)
    second_tokens = title_tokens(second_title)

    shared_tokens = first_tokens & second_tokens

    first_entities = extract_entities(
        first_title
    )

    second_entities = extract_entities(
        second_title
    )

    shared_entities = (
        first_entities &
        second_entities
    )

    score = calculate_similarity(
        first_title,
        second_title,
        first.get("category"),
        second.get("category"),
        first.get("published_at"),
        second.get("published_at"),
    )

    if shared_entities and score >= 0.38:
        return True

    if len(shared_tokens) >= 3 and score >= 0.46:
        return True

    if score >= 0.58:
        return True

    return False


def article_datetime(article) -> datetime | None:
    value = getattr(
        article,
        "published_at",
        None,
    )

    if not value:
        return None

    if value.tzinfo is None:
        return value.replace(
            tzinfo=timezone.utc
        )

    return value


def article_record(article) -> dict[str, Any]:
    source = getattr(
        article,
        "source",
        None,
    )

    return {
        "id": article.id,
        "title": clean_text(article.title),
        "summary": clean_text(article.summary),
        "url": article.url,
        "category": article.category,
        "published_at": article_datetime(article),
        "source": (
            source.name
            if source
            else "Unknown"
        ),
        "source_id": (
            source.id
            if source
            else None
        ),
    }


def cluster_score(
    articles: list[dict[str, Any]],
) -> float:

    if len(articles) < 2:
        return 0.0

    representative = articles[0]

    scores = []

    for article in articles[1:]:
        scores.append(
            calculate_similarity(
                representative["title"],
                article["title"],
                representative["category"],
                article["category"],
                representative["published_at"],
                article["published_at"],
            )
        )

    if not scores:
        return 0.0

    return round(
        sum(scores) / len(scores),
        4,
    )


def source_diversity(
    articles: list[dict[str, Any]],
) -> int:

    sources = {
        article.get("source")
        for article in articles
        if article.get("source")
    }

    return len(sources)


def category_for_cluster(
    articles: list[dict[str, Any]],
) -> str:

    categories = [
        article.get("category")
        for article in articles
        if article.get("category")
    ]

    if not categories:
        return "General"

    return Counter(categories).most_common(1)[0][0]


def latest_cluster_time(
    articles: list[dict[str, Any]],
) -> datetime | None:

    dates = [
        article.get("published_at")
        for article in articles
        if article.get("published_at")
    ]

    if not dates:
        return None

    return max(dates)


def relevance_score(
    articles: list[dict[str, Any]],
) -> float:

    if not articles:
        return 0.0

    source_count = source_diversity(
        articles
    )

    article_count = len(articles)

    cluster_quality = cluster_score(
        articles
    )

    source_signal = min(
        source_count / 5,
        1.0,
    )

    volume_signal = min(
        article_count / 6,
        1.0,
    )

    score = (
        source_signal * 0.40
        + volume_signal * 0.15
        + cluster_quality * 0.45
    )

    return round(
        min(score, 1.0),
        4,
    )


def build_event_clusters(
    db,
    limit: int = 500,
) -> list[dict[str, Any]]:

    from app.models import Article

    articles = (
        db.query(Article)
        .order_by(
            Article.published_at.desc()
        )
        .limit(limit)
        .all()
    )

    records = [
        article_record(article)
        for article in articles
    ]

    clusters: list[list[dict[str, Any]]] = []

    for record in records:

        assigned = False

        for cluster in clusters:

            representative = cluster[0]

            if should_cluster(
                representative,
                record,
            ):
                cluster.append(record)
                assigned = True
                break

        if not assigned:
            clusters.append([record])

    result = []

    for index, cluster in enumerate(clusters, start=1):

        representative = cluster[0]

        sources = sorted(
            {
                article["source"]
                for article in cluster
                if article.get("source")
            }
        )

        result.append(
            {
                "event_id": f"event-{index}",
                "title": representative["title"],
                "category": category_for_cluster(
                    cluster
                ),
                "published_at": (
                    latest_cluster_time(
                        cluster
                    )
                ),
                "article_count": len(cluster),
                "source_count": len(sources),
                "sources": sources,
                "similarity": cluster_score(
                    cluster
                ),
                "relevance": relevance_score(
                    cluster
                ),
                "articles": cluster,
            }
        )

    result.sort(
        key=lambda event: (
            event["relevance"],
            event["source_count"],
            event["article_count"],
        ),
        reverse=True,
    )

    return result


def get_multi_source_events(
    db,
    limit: int = 20,
) -> list[dict[str, Any]]:

    clusters = build_event_clusters(
        db,
        limit=500,
    )

    events = [
        cluster
        for cluster in clusters
        if cluster["source_count"] >= 2
    ]

    return events[:limit]


def get_intelligence_summary(db) -> dict[str, Any]:

    clusters = build_event_clusters(
        db,
        limit=500,
    )

    multi_source = [
        cluster
        for cluster in clusters
        if cluster["source_count"] >= 2
    ]

    category_counts = Counter(
        cluster["category"]
        for cluster in clusters
    )

    source_coverage = Counter()

    for cluster in multi_source:
        for source in cluster["sources"]:
            source_coverage[source] += 1

    return {
        "event_clusters": len(clusters),
        "multi_source_events": len(
            multi_source
        ),
        "categories_with_events": dict(
            category_counts
        ),
        "source_event_coverage": dict(
            source_coverage.most_common()
        ),
    }
