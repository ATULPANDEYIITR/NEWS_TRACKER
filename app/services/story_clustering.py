from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.story_cluster import StoryCluster


# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

DEFAULT_SIMILARITY_THRESHOLD = 0.45
DEFAULT_LOOKBACK_HOURS = 96
DEFAULT_BATCH_SIZE = 500

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "but",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "here",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "may",
    "might",
    "more",
    "most",
    "much",
    "must",
    "my",
    "no",
    "not",
    "of",
    "on",
    "or",
    "our",
    "out",
    "over",
    "said",
    "says",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "under",
    "up",
    "us",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "would",
    "you",
    "your",
    "after",
    "before",
    "during",
    "amid",
    "around",
    "against",
    "between",
    "following",
    "latest",
    "new",
    "news",
    "report",
    "reports",
    "according",
    "officials",
}


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------

def normalize_text(text: str | None) -> str:
    if not text:
        return ""

    text = text.lower()

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
    ).strip()

    return text


def tokenize(text: str | None) -> set[str]:
    normalized = normalize_text(text)

    if not normalized:
        return set()

    return {
        word
        for word in normalized.split()
        if len(word) >= 3 and word not in STOP_WORDS
    }


def keyword_counter(text: str | None) -> Counter[str]:
    return Counter(tokenize(text))


# ---------------------------------------------------------
# SIMILARITY ENGINE
# ---------------------------------------------------------

def jaccard_similarity(
    text_a: str | None,
    text_b: str | None,
) -> float:
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    union = tokens_a | tokens_b

    if not union:
        return 0.0

    return len(tokens_a & tokens_b) / len(union)


def containment_similarity(
    text_a: str | None,
    text_b: str | None,
) -> float:
    """
    Measures how much of the smaller headline is contained
    in the larger headline.
    """

    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    smaller = min(
        len(tokens_a),
        len(tokens_b),
    )

    if smaller == 0:
        return 0.0

    return len(tokens_a & tokens_b) / smaller


def shared_keywords(
    text_a: str | None,
    text_b: str | None,
) -> set[str]:
    return tokenize(text_a) & tokenize(text_b)


def keyword_similarity(
    text_a: str | None,
    text_b: str | None,
) -> float:
    """
    Weighted keyword similarity.

    Longer, meaningful keywords contribute more than tiny generic words.
    """

    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    shared = tokens_a & tokens_b

    if not shared:
        return 0.0

    total_weight = sum(
        max(len(word) - 2, 1)
        for word in tokens_a | tokens_b
    )

    shared_weight = sum(
        max(len(word) - 2, 1)
        for word in shared
    )

    if total_weight == 0:
        return 0.0

    return shared_weight / total_weight


def headline_similarity(
    headline_a: str | None,
    headline_b: str | None,
) -> float:
    """
    Combined headline similarity.

    Uses several signals instead of one raw metric.
    """

    jaccard = jaccard_similarity(
        headline_a,
        headline_b,
    )

    containment = containment_similarity(
        headline_a,
        headline_b,
    )

    keywords = keyword_similarity(
        headline_a,
        headline_b,
    )

    # Containment is particularly useful for:
    #
    # "India launches new semiconductor policy"
    # "India launches new semiconductor policy to boost chip industry"
    #
    score = (
        (jaccard * 0.35)
        + (containment * 0.40)
        + (keywords * 0.25)
    )

    return min(score, 1.0)


# ---------------------------------------------------------
# TIME SIMILARITY
# ---------------------------------------------------------

def article_datetime(
    article: Article,
) -> datetime | None:
    return article.published_at or article.collected_at


def time_similarity(
    article_a: Article,
    article_b: Article,
    lookback_hours: int = DEFAULT_LOOKBACK_HOURS,
) -> float:
    time_a = article_datetime(article_a)
    time_b = article_datetime(article_b)

    if not time_a or not time_b:
        return 0.5

    try:
        difference_hours = abs(
            (time_a - time_b).total_seconds()
        ) / 3600
    except TypeError:
        return 0.5

    if difference_hours > lookback_hours:
        return 0.0

    return max(
        0.0,
        1.0 - (
            difference_hours
            / lookback_hours
        ),
    )


# ---------------------------------------------------------
# COMPLETE ARTICLE SCORE
# ---------------------------------------------------------

def article_match_score(
    article: Article,
    candidate: Article,
    lookback_hours: int = DEFAULT_LOOKBACK_HOURS,
) -> float:
    headline_score = headline_similarity(
        article.headline,
        candidate.headline,
    )

    shared = shared_keywords(
        article.headline,
        candidate.headline,
    )

    time_score = time_similarity(
        article,
        candidate,
        lookback_hours,
    )

    # Strong headline overlap is the dominant signal.
    score = (
        headline_score * 0.80
        + time_score * 0.20
    )

    # A meaningful number of shared keywords gives a useful boost.
    if len(shared) >= 3:
        score += 0.05

    if len(shared) >= 5:
        score += 0.05

    return min(score, 1.0)


# ---------------------------------------------------------
# CLUSTER HELPERS
# ---------------------------------------------------------

def get_cluster_articles(
    db: Session,
    cluster_id: int,
) -> list[Article]:
    statement = (
        select(Article)
        .where(
            Article.cluster_id == cluster_id
        )
        .order_by(
            Article.published_at.asc(),
            Article.id.asc(),
        )
    )

    return list(
        db.scalars(statement).all()
    )


def choose_cluster_title(
    articles: Iterable[Article],
) -> str:
    articles = list(articles)

    headlines = [
        article.headline.strip()
        for article in articles
        if article.headline
        and article.headline.strip()
    ]

    if not headlines:
        return "Untitled Story"

    def score(headline: str) -> tuple:
        tokens = tokenize(headline)

        # Prefer informative headlines.
        meaningful_length = len(tokens)

        # Avoid extremely long headlines.
        length_penalty = abs(
            len(headline) - 100
        )

        return (
            meaningful_length,
            -length_penalty,
        )

    return max(
        headlines,
        key=score,
    )[:500]


def choose_cluster_description(
    articles: Iterable[Article],
) -> str:
    articles = list(articles)

    descriptions = []

    for article in articles:
        if not article.description:
            continue

        description = re.sub(
            r"\s+",
            " ",
            article.description,
        ).strip()

        if description:
            descriptions.append(description)

    if not descriptions:
        return ""

    # Prefer a reasonably detailed description.
    descriptions.sort(
        key=len,
        reverse=True,
    )

    return descriptions[0][:2000]


def update_cluster_metadata(
    db: Session,
    cluster: StoryCluster,
) -> None:
    articles = get_cluster_articles(
        db,
        cluster.cluster_id,
    )

    cluster.title = choose_cluster_title(
        articles
    )

    cluster.description = (
        choose_cluster_description(
            articles
        )
    )


# ---------------------------------------------------------
# CANDIDATE SEARCH
# ---------------------------------------------------------

def find_candidate_articles(
    db: Session,
    article: Article,
    lookback_hours: int = DEFAULT_LOOKBACK_HOURS,
    limit: int = 250,
) -> list[Article]:

    article_time = article_datetime(article)

    statement = (
        select(Article)
        .where(
            Article.id != article.id,
            Article.headline.is_not(None),
        )
    )

    if article_time:
        lower_bound = (
            article_time
            - timedelta(hours=lookback_hours)
        )

        upper_bound = (
            article_time
            + timedelta(hours=lookback_hours)
        )

        statement = statement.where(
            func.coalesce(
                Article.published_at,
                Article.collected_at,
            ).between(
                lower_bound,
                upper_bound,
            )
        )

    statement = (
        statement
        .order_by(
            Article.published_at.desc(),
            Article.id.desc(),
        )
        .limit(limit)
    )

    return list(
        db.scalars(statement).all()
    )


# ---------------------------------------------------------
# CLUSTER CREATION
# ---------------------------------------------------------

def create_cluster(
    db: Session,
    article: Article,
) -> StoryCluster:

    cluster = StoryCluster(
        title=(
            article.headline
            or "Untitled Story"
        )[:500],
        description=(
            article.description
            or ""
        )[:2000],
    )

    db.add(cluster)
    db.flush()

    article.cluster_id = (
        cluster.cluster_id
    )

    return cluster


def add_article_to_cluster(
    db: Session,
    article: Article,
    cluster: StoryCluster,
) -> None:

    article.cluster_id = (
        cluster.cluster_id
    )

    db.flush()

    update_cluster_metadata(
        db,
        cluster,
    )


# ---------------------------------------------------------
# SINGLE ARTICLE CLUSTERING
# ---------------------------------------------------------

def cluster_article(
    db: Session,
    article: Article,
    similarity_threshold: float = (
        DEFAULT_SIMILARITY_THRESHOLD
    ),
    lookback_hours: int = (
        DEFAULT_LOOKBACK_HOURS
    ),
) -> StoryCluster:

    if article.cluster_id:
        existing = db.get(
            StoryCluster,
            article.cluster_id,
        )

        if existing:
            return existing

    candidates = find_candidate_articles(
        db,
        article,
        lookback_hours,
    )

    cluster_scores: dict[int, float] = {}

    for candidate in candidates:

        if not candidate.cluster_id:
            continue

        score = article_match_score(
            article,
            candidate,
            lookback_hours,
        )

        current_score = cluster_scores.get(
            candidate.cluster_id,
            0.0,
        )

        if score > current_score:
            cluster_scores[
                candidate.cluster_id
            ] = score

    if cluster_scores:

        best_cluster_id, best_score = max(
            cluster_scores.items(),
            key=lambda item: item[1],
        )

        if best_score >= similarity_threshold:

            cluster = db.get(
                StoryCluster,
                best_cluster_id,
            )

            if cluster:
                add_article_to_cluster(
                    db,
                    article,
                    cluster,
                )

                return cluster

    return create_cluster(
        db,
        article,
    )


# ---------------------------------------------------------
# BATCH PROCESSING
# ---------------------------------------------------------

def cluster_unassigned_articles(
    db: Session,
    limit: int = DEFAULT_BATCH_SIZE,
    similarity_threshold: float = (
        DEFAULT_SIMILARITY_THRESHOLD
    ),
    lookback_hours: int = (
        DEFAULT_LOOKBACK_HOURS
    ),
) -> int:

    statement = (
        select(Article)
        .where(
            Article.cluster_id.is_(None),
            Article.headline.is_not(None),
        )
        .order_by(
            Article.published_at.asc(),
            Article.id.asc(),
        )
        .limit(limit)
    )

    articles = list(
        db.scalars(statement).all()
    )

    processed = 0

    for article in articles:

        cluster_article(
            db=db,
            article=article,
            similarity_threshold=(
                similarity_threshold
            ),
            lookback_hours=lookback_hours,
        )

        processed += 1

        # Keep transactions manageable.
        if processed % 100 == 0:
            db.commit()

    db.commit()

    return processed


# ---------------------------------------------------------
# STATISTICS
# ---------------------------------------------------------

def get_cluster_statistics(
    db: Session,
) -> dict[str, int]:

    total_clusters = db.scalar(
        select(
            func.count(StoryCluster.cluster_id)
        )
    ) or 0

    clustered_articles = db.scalar(
        select(
            func.count(Article.id)
        ).where(
            Article.cluster_id.is_not(None)
        )
    ) or 0

    unclustered_articles = db.scalar(
        select(
            func.count(Article.id)
        ).where(
            Article.cluster_id.is_(None)
        )
    ) or 0

    return {
        "clusters": int(total_clusters),
        "clustered_articles": int(
            clustered_articles
        ),
        "unclustered_articles": int(
            unclustered_articles
        ),
    }


__all__ = [
    "normalize_text",
    "tokenize",
    "jaccard_similarity",
    "containment_similarity",
    "keyword_similarity",
    "shared_keywords",
    "headline_similarity",
    "time_similarity",
    "article_match_score",
    "get_cluster_articles",
    "choose_cluster_title",
    "choose_cluster_description",
    "update_cluster_metadata",
    "find_candidate_articles",
    "create_cluster",
    "add_article_to_cluster",
    "cluster_article",
    "cluster_unassigned_articles",
    "get_cluster_statistics",
]
