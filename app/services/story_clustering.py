from __future__ import annotations

import re
from collections import Counter
from datetime import datetime
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.article import Article
from app.models.story_cluster import StoryCluster


# Common words that add little value when comparing news headlines.
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "was",
    "were",
    "will",
    "with",
    "after",
    "before",
    "over",
    "under",
    "about",
    "amid",
    "during",
    "new",
    "latest",
    "says",
    "said",
}


def normalize_text(text: str | None) -> str:
    """
    Normalize headline text for comparison.
    """

    if not text:
        return ""

    text = text.lower()

    # Remove URLs.
    text = re.sub(r"https?://\S+", " ", text)

    # Keep letters, numbers and spaces.
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def tokenize(text: str | None) -> set[str]:
    """
    Convert text into meaningful unique tokens.
    """

    normalized = normalize_text(text)

    if not normalized:
        return set()

    return {
        token
        for token in normalized.split()
        if len(token) >= 3 and token not in STOP_WORDS
    }


def headline_similarity(
    headline_a: str | None,
    headline_b: str | None,
) -> float:
    """
    Calculate Jaccard similarity between two headlines.

    Returns:
        Value from 0.0 to 1.0.
    """

    tokens_a = tokenize(headline_a)
    tokens_b = tokenize(headline_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a.intersection(tokens_b)
    union = tokens_a.union(tokens_b)

    if not union:
        return 0.0

    return len(intersection) / len(union)


def shared_keywords(
    headline_a: str | None,
    headline_b: str | None,
) -> set[str]:
    """
    Return meaningful keywords shared by two headlines.
    """

    return tokenize(headline_a).intersection(tokenize(headline_b))


def choose_cluster_title(
    articles: Iterable[Article],
) -> str:
    """
    Choose the most informative headline as the cluster title.

    Short headlines are preferred over extremely long headlines,
    while preserving meaningful news wording.
    """

    article_list = list(articles)

    if not article_list:
        return "Untitled Story"

    candidates = [
        article.headline.strip()
        for article in article_list
        if article.headline and article.headline.strip()
    ]

    if not candidates:
        return "Untitled Story"

    # Prefer headlines with useful information without being excessively long.
    scored = []

    for headline in candidates:
        tokens = tokenize(headline)

        score = (
            len(tokens) * 2
            - max(0, len(headline) - 140) * 0.01
        )

        scored.append((score, headline))

    scored.sort(reverse=True)

    return scored[0][1][:500]


def build_cluster_description(
    articles: Iterable[Article],
) -> str:
    """
    Build a compact description from the strongest available article
    descriptions.
    """

    article_list = list(articles)

    descriptions = []

    for article in article_list:
        if article.description:
            cleaned = re.sub(r"\s+", " ", article.description).strip()

            if cleaned:
                descriptions.append(cleaned)

    if not descriptions:
        return ""

    # Prefer the first useful description.
    description = descriptions[0]

    return description[:2000]


def article_similarity_to_cluster(
    article: Article,
    cluster_articles: Iterable[Article],
) -> float:
    """
    Compare an article against the existing articles in a cluster.

    The maximum similarity is used so that a new article only needs
    to strongly match one established article in the cluster.
    """

    similarities = [
        headline_similarity(article.headline, existing.headline)
        for existing in cluster_articles
        if existing.id != article.id
    ]

    if not similarities:
        return 0.0

    return max(similarities)


def find_candidate_articles(
    db: Session,
    article: Article,
    lookback_hours: int = 72,
    limit: int = 100,
) -> list[Article]:
    """
    Find recent articles that may belong to the same story.
    """

    query = (
        select(Article)
        .where(
            Article.id != article.id,
            Article.headline.is_not(None),
        )
        .order_by(Article.published_at.desc())
        .limit(limit)
    )

    candidates = list(db.scalars(query).all())

    if not candidates:
        return []

    article_time = article.published_at or article.collected_at

    if not article_time:
        return candidates

    filtered = []

    for candidate in candidates:
        candidate_time = (
            candidate.published_at or candidate.collected_at
        )

        if not candidate_time:
            filtered.append(candidate)
            continue

        difference = abs(
            (article_time - candidate_time).total_seconds()
        )

        if difference <= lookback_hours * 3600:
            filtered.append(candidate)

    return filtered


def get_cluster_articles(
    db: Session,
    cluster_id: int,
) -> list[Article]:
    """
    Load all articles currently assigned to a cluster.
    """

    query = (
        select(Article)
        .where(Article.cluster_id == cluster_id)
        .order_by(Article.published_at.asc())
    )

    return list(db.scalars(query).all())


def create_cluster(
    db: Session,
    article: Article,
) -> StoryCluster:
    """
    Create a new cluster for an article.
    """

    cluster = StoryCluster(
        title=(article.headline or "Untitled Story")[:500],
        description=(article.description or "")[:2000],
    )

    db.add(cluster)
    db.flush()

    article.cluster_id = cluster.cluster_id

    return cluster


def add_article_to_cluster(
    db: Session,
    article: Article,
    cluster: StoryCluster,
) -> None:
    """
    Assign an article to a cluster.
    """

    article.cluster_id = cluster.cluster_id

    existing_articles = get_cluster_articles(
        db,
        cluster.cluster_id,
    )

    all_articles = existing_articles + [article]

    cluster.title = choose_cluster_title(all_articles)
    cluster.description = build_cluster_description(all_articles)


def cluster_article(
    db: Session,
    article: Article,
    similarity_threshold: float = 0.35,
    lookback_hours: int = 72,
) -> StoryCluster:
    """
    Assign one article to an existing story cluster or create a new one.

    Workflow:
        1. Find recent candidate articles.
        2. Compare headline similarity.
        3. Reuse the strongest matching cluster.
        4. Otherwise create a new cluster.
    """

    if article.cluster_id:
        existing_cluster = db.get(
            StoryCluster,
            article.cluster_id,
        )

        if existing_cluster:
            return existing_cluster

    candidates = find_candidate_articles(
        db=db,
        article=article,
        lookback_hours=lookback_hours,
    )

    cluster_scores: dict[int, float] = {}

    for candidate in candidates:
        if not candidate.cluster_id:
            continue

        score = headline_similarity(
            article.headline,
            candidate.headline,
        )

        current_score = cluster_scores.get(
            candidate.cluster_id,
            0.0,
        )

        cluster_scores[candidate.cluster_id] = max(
            current_score,
            score,
        )

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

    return create_cluster(db, article)


def cluster_unassigned_articles(
    db: Session,
    limit: int = 500,
    similarity_threshold: float = 0.35,
    lookback_hours: int = 72,
) -> int:
    """
    Process unassigned articles in publication order.

    Returns:
        Number of articles assigned to clusters.
    """

    query = (
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

    articles = list(db.scalars(query).all())

    processed = 0

    for article in articles:
        cluster_article(
            db=db,
            article=article,
            similarity_threshold=similarity_threshold,
            lookback_hours=lookback_hours,
        )

        processed += 1

    db.commit()

    return processed


def rebuild_clusters(
    db: Session,
    similarity_threshold: float = 0.35,
    lookback_hours: int = 72,
) -> int:
    """
    Rebuild story clustering from scratch.

    Existing cluster assignments are cleared and fresh clusters
    are generated from article headlines.
    """

    articles = list(
        db.scalars(
            select(Article)
            .where(Article.headline.is_not(None))
            .order_by(
                Article.published_at.asc(),
                Article.id.asc(),
            )
        ).all()
    )

    # Remove article assignments first.
    for article in articles:
        article.cluster_id = None

    db.flush()

    # Remove old clusters.
    old_clusters = list(
        db.scalars(
            select(StoryCluster)
        ).all()
    )

    for cluster in old_clusters:
        db.delete(cluster)

    db.flush()

    processed = 0

    for article in articles:
        cluster_article(
            db=db,
            article=article,
            similarity_threshold=similarity_threshold,
            lookback_hours=lookback_hours,
        )

        processed += 1

    db.commit()

    return processed


__all__ = [
    "normalize_text",
    "tokenize",
    "headline_similarity",
    "shared_keywords",
    "choose_cluster_title",
    "build_cluster_description",
    "article_similarity_to_cluster",
    "find_candidate_articles",
    "get_cluster_articles",
    "create_cluster",
    "add_article_to_cluster",
    "cluster_article",
    "cluster_unassigned_articles",
    "rebuild_clusters",
]
