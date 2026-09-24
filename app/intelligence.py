import re
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher

from sqlalchemy import select

from app.models import Article, Source


STOP_WORDS = {
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
    "from",
    "with",
    "by",
    "at",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "after",
    "before",
    "into",
    "over",
    "under",
    "about",
    "amid",
    "new",
    "latest",
    "says",
    "say",
    "will",
    "may",
    "can",
    "its",
    "their",
    "this",
    "that",
    "has",
    "have",
    "had",
    "not",
    "but",
    "than",
    "how",
    "what",
    "why",
}


ENTITY_TERMS = {
    "india",
    "china",
    "russia",
    "ukraine",
    "israel",
    "iran",
    "pakistan",
    "america",
    "united states",
    "united kingdom",
    "europe",
    "delhi",
    "mumbai",
    "bihar",
    "lucknow",
    "washington",
    "london",
    "beijing",
    "moscow",
    "donald trump",
    "trump",
    "modi",
    "narendra modi",
    "elon musk",
    "google",
    "microsoft",
    "apple",
    "openai",
    "meta",
    "nvidia",
    "tesla",
    "amazon",
    "supreme court",
    "parliament",
    "congress",
    "nasa",
}


def clean_text(value):
    if not value:
        return ""

    value = str(value).lower()

    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    return " ".join(value.split())


def normalize_title(title):
    return clean_text(title)


def title_tokens(title):
    words = normalize_title(title).split()

    return {
        word
        for word in words
        if len(word) > 2
        and word not in STOP_WORDS
    }


def extract_entities(text):
    original = str(text or "").lower()

    entities = set()

    for term in ENTITY_TERMS:
        if term in original:
            entities.add(term)

    return entities


def jaccard_similarity(first, second):
    if not first and not second:
        return 1.0

    union = first | second

    if not union:
        return 0.0

    return len(first & second) / len(union)


def token_overlap_similarity(first, second):
    if not first or not second:
        return 0.0

    smaller = min(
        len(first),
        len(second),
    )

    if smaller == 0:
        return 0.0

    return len(first & second) / smaller


def sequence_similarity(first_title, second_title):
    return SequenceMatcher(
        None,
        normalize_title(first_title),
        normalize_title(second_title),
    ).ratio()


def time_similarity(first_date, second_date):
    if not first_date or not second_date:
        return 0.5

    difference = abs(
        (first_date - second_date).total_seconds()
    ) / 3600

    if difference <= 2:
        return 1.0

    if difference <= 6:
        return 0.85

    if difference <= 12:
        return 0.70

    if difference <= 24:
        return 0.50

    if difference <= 48:
        return 0.25

    return 0.0


def category_similarity(first, second):
    return 1.0 if first == second else 0.0


def calculate_similarity(first, second):
    first_tokens = title_tokens(
        first["title"]
    )

    second_tokens = title_tokens(
        second["title"]
    )

    first_entities = extract_entities(
        first["title"]
    )

    second_entities = extract_entities(
        second["title"]
    )

    token_jaccard = jaccard_similarity(
        first_tokens,
        second_tokens,
    )

    token_overlap = token_overlap_similarity(
        first_tokens,
        second_tokens,
    )

    entity_jaccard = jaccard_similarity(
        first_entities,
        second_entities,
    )

    sequence = sequence_similarity(
        first["title"],
        second["title"],
    )

    time_score = time_similarity(
        first.get("published_at"),
        second.get("published_at"),
    )

    category_score = category_similarity(
        first.get("category"),
        second.get("category"),
    )

    score = (
        0.25 * token_jaccard
        + 0.20 * token_overlap
        + 0.25 * entity_jaccard
        + 0.15 * sequence
        + 0.10 * time_score
        + 0.05 * category_score
    )

    return round(score, 4)


def should_cluster(first, second):
    first_tokens = title_tokens(
        first["title"]
    )

    second_tokens = title_tokens(
        second["title"]
    )

    shared_tokens = first_tokens & second_tokens

    first_entities = extract_entities(
        first["title"]
    )

    second_entities = extract_entities(
        second["title"]
    )

    shared_entities = (
        first_entities & second_entities
    )

    score = calculate_similarity(
        first,
        second,
    )

    if (
        shared_entities
        and score >= 0.38
    ):
        return True

    if (
        len(shared_tokens) >= 3
        and score >= 0.46
    ):
        return True

    if score >= 0.58:
        return True

    return False


def article_datetime(article):
    return article.published_at or article.collected_at


def article_record(article, source_name=None):
    return {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "summary": article.summary or "",
        "category": article.category,
        "published_at": article_datetime(article),
        "source_id": article.source_id,
        "source": source_name or "",
    }


def cluster_score(cluster):
    if not cluster:
        return 0.0

    values = [
        item.get("similarity", 0.0)
        for item in cluster
        if item.get("similarity") is not None
    ]

    if not values:
        return 0.0

    return round(
        sum(values) / len(values),
        4,
    )


def source_diversity(cluster):
    return len(
        {
            item.get("source")
            for item in cluster
            if item.get("source")
        }
    )


def category_for_cluster(cluster):
    categories = [
        item.get("category")
        for item in cluster
        if item.get("category")
    ]

    if not categories:
        return "World"

    return Counter(categories).most_common(1)[0][0]


def latest_cluster_time(cluster):
    dates = [
        item.get("published_at")
        for item in cluster
        if item.get("published_at")
    ]

    if not dates:
        return None

    return max(dates)


def relevance_score(
    article_count,
    source_count,
    similarity,
):
    """
    Transparent event relevance signal.

    This is NOT a truth score.
    It combines:
    - number of articles
    - source diversity
    - cluster similarity
    """

    article_signal = min(
        article_count / 5,
        1.0,
    )

    source_signal = min(
        source_count / 4,
        1.0,
    )

    quality_signal = similarity

    score = (
        0.40 * source_signal
        + 0.30 * article_signal
        + 0.30 * quality_signal
    )

    return round(
        score * 100,
        1,
    )


def build_event_clusters(db, limit=500):
    rows = (
        db.query(
            Article,
            Source.name,
        )
        .join(
            Source,
            Article.source_id == Source.id,
        )
        .order_by(
            Article.published_at.desc()
        )
        .limit(limit)
        .all()
    )

    articles = [
        article_record(
            article,
            source_name,
        )
        for article, source_name in rows
    ]

    clusters = []

    for article in articles:
        best_cluster = None
        best_score = 0.0

        for cluster in clusters:
            representative = cluster[0]

            score = calculate_similarity(
                article,
                representative,
            )

            if should_cluster(
                article,
                representative,
            ) and score > best_score:
                best_score = score
                best_cluster = cluster

        if best_cluster is None:
            clusters.append(
                [
                    {
                        **article,
                        "similarity": 1.0,
                    }
                ]
            )
        else:
            best_cluster.append(
                {
                    **article,
                    "similarity": best_score,
                }
            )

    events = []

    for index, cluster in enumerate(
        clusters,
        start=1,
    ):
        sources = sorted(
            {
                item["source"]
                for item in cluster
                if item.get("source")
            }
        )

        average_similarity = cluster_score(
            cluster
        )

        source_count = len(sources)
        article_count = len(cluster)

        representative = max(
            cluster,
            key=lambda item: (
                item.get("published_at")
                or datetime.min
            ),
        )

        relevance = relevance_score(
            article_count,
            source_count,
            average_similarity,
        )

        events.append(
            {
                "event_id": index,
                "title": representative["title"],
                "category": category_for_cluster(
                    cluster
                ),
                "published_at": latest_cluster_time(
                    cluster
                ),
                "article_count": article_count,
                "source_count": source_count,
                "sources": sources,
                "similarity": average_similarity,
                "relevance": relevance,
                "articles": cluster,
            }
        )

    events.sort(
        key=lambda item: (
            item["relevance"],
            item["article_count"],
            item["source_count"],
        ),
        reverse=True,
    )

    return events


def get_multi_source_events(db, limit=20):
    events = build_event_clusters(
        db,
        limit=500,
    )

    return [
        event
        for event in events
        if event["source_count"] >= 2
    ][:limit]


def get_intelligence_summary(db):
    events = build_event_clusters(
        db,
        limit=500,
    )

    multi_source = [
        event
        for event in events
        if event["source_count"] >= 2
    ]

    category_counts = Counter(
        event["category"]
        for event in events
    )

    source_event_coverage = Counter()

    for event in multi_source:
        for source in event["sources"]:
            source_event_coverage[source] += 1

    return {
        "event_clusters": len(events),
        "multi_source_events": len(
            multi_source
        ),
        "categories_with_events": dict(
            category_counts
        ),
        "source_event_coverage": dict(
            source_event_coverage
        ),
    }
