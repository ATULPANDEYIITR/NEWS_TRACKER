from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import text

from app.database.session import SessionLocal


STOP_WORDS = {
    "about", "after", "again", "against", "among", "because",
    "before", "being", "between", "could", "during", "first",
    "from", "have", "into", "more", "most", "other", "over",
    "said", "same", "some", "than", "that", "their", "there",
    "these", "they", "this", "those", "through", "under",
    "very", "what", "when", "where", "which", "while", "with",
    "would", "your", "will", "been", "were", "also", "such",
    "only", "many", "much", "each", "just", "like", "news",
}


TOPIC_KEYWORDS = {
    "artificial intelligence": {
        "ai", "artificial intelligence", "machine learning",
        "generative ai", "large language model", "llm",
        "neural network", "chatbot", "deep learning",
    },
    "cybersecurity": {
        "cybersecurity", "cyber attack", "cyberattack",
        "ransomware", "malware", "phishing", "hacker",
        "data breach", "vulnerability", "zero day",
    },
    "geopolitics": {
        "geopolitics", "diplomacy", "sanctions", "summit",
        "foreign policy", "bilateral", "alliance",
        "territory", "international relations",
    },
    "economy": {
        "economy", "economic growth", "inflation", "gdp",
        "recession", "interest rates", "unemployment",
        "fiscal", "monetary policy",
    },
    "business": {
        "company", "corporate", "merger", "acquisition",
        "startup", "executive", "revenue", "profit",
        "investment", "shareholders",
    },
    "finance": {
        "stock market", "stocks", "shares", "bank",
        "banking", "bond", "currency", "markets",
        "financial", "interest rate",
    },
    "climate": {
        "climate change", "global warming", "carbon",
        "emissions", "greenhouse gas", "climate",
        "drought", "flood", "heatwave",
    },
    "environment": {
        "environment", "pollution", "biodiversity",
        "forest", "wildlife", "ecosystem", "conservation",
    },
    "science": {
        "science", "research", "scientist", "laboratory",
        "study", "experiment", "discovery",
    },
    "space": {
        "space", "nasa", "isro", "satellite", "rocket",
        "orbit", "moon", "mars", "astronaut",
    },
    "health": {
        "health", "hospital", "disease", "medical",
        "medicine", "doctor", "patient", "vaccine",
        "public health",
    },
    "education": {
        "education", "school", "university", "college",
        "student", "teacher", "exam", "curriculum",
    },
    "technology": {
        "technology", "software", "hardware", "chip",
        "semiconductor", "cloud computing", "internet",
        "smartphone", "computer",
    },
    "energy": {
        "energy", "oil", "gas", "electricity", "solar",
        "wind power", "nuclear energy", "renewable energy",
        "battery",
    },
    "defense": {
        "defense", "military", "army", "navy", "air force",
        "missile", "weapons", "defence",
    },
    "conflict": {
        "war", "conflict", "battle", "fighting", "attack",
        "ceasefire", "troops", "bombing", "invasion",
    },
    "politics": {
        "election", "government", "parliament", "president",
        "prime minister", "minister", "political", "politics",
        "party", "vote", "voting", "legislation",
    },
    "crime": {
        "crime", "criminal", "police", "arrest", "murder",
        "fraud", "theft", "investigation", "court",
    },
    "sports": {
        "football", "cricket", "tennis", "basketball",
        "olympics", "athlete", "match", "tournament",
        "championship", "sports",
    },
}


ENTITY_PATTERNS = [
    r"\b(?:United States|United Kingdom|European Union|United Nations)\b",
    r"\b(?:India|China|Russia|Ukraine|Israel|Iran|Japan|Australia|Canada|Germany|France|Brazil)\b",
    r"\b(?:NASA|ISRO|NATO|WHO|IMF|World Bank|OECD|UNESCO|UNICEF)\b",
    r"\b(?:OpenAI|Microsoft|Google|Apple|Amazon|Meta|NVIDIA|Tesla)\b",
]


def create_table():

    db = SessionLocal()

    try:

        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS article_intelligence (
                    article_id INTEGER PRIMARY KEY
                        REFERENCES articles(id)
                        ON DELETE CASCADE,

                    primary_topic VARCHAR(255),

                    topics TEXT,

                    entities TEXT,

                    geographic_signals TEXT,

                    political_signal BOOLEAN NOT NULL DEFAULT FALSE,

                    economic_signal BOOLEAN NOT NULL DEFAULT FALSE,

                    technology_signal BOOLEAN NOT NULL DEFAULT FALSE,

                    conflict_signal BOOLEAN NOT NULL DEFAULT FALSE,

                    health_signal BOOLEAN NOT NULL DEFAULT FALSE,

                    climate_signal BOOLEAN NOT NULL DEFAULT FALSE,

                    breaking_signal BOOLEAN NOT NULL DEFAULT FALSE,

                    keyword_count INTEGER NOT NULL DEFAULT 0,

                    analyzed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )

        db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                ix_article_intelligence_primary_topic
                ON article_intelligence(primary_topic)
                """
            )
        )

        db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                ix_article_intelligence_analyzed_at
                ON article_intelligence(analyzed_at)
                """
            )
        )

        db.commit()

    finally:

        db.close()


def normalize(text_value: str) -> str:

    return re.sub(
        r"\s+",
        " ",
        re.sub(
            r"[^a-zA-Z0-9\s-]",
            " ",
            text_value.lower(),
        ),
    ).strip()


def detect_topics(text_value: str):

    normalized = normalize(text_value)

    scores = {}

    for topic, keywords in TOPIC_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if " " in keyword:

                if keyword in normalized:
                    score += 2

            else:

                if re.search(
                    rf"\b{re.escape(keyword)}\b",
                    normalized,
                ):
                    score += 1

        if score > 0:
            scores[topic] = score

    ordered = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return ordered


def detect_entities(text_value: str):

    entities = set()

    for pattern in ENTITY_PATTERNS:

        for match in re.findall(
            pattern,
            text_value,
            flags=re.IGNORECASE,
        ):

            entities.add(match)

    return sorted(entities)


def detect_geography(text_value: str):

    countries = [
        "India",
        "United States",
        "United Kingdom",
        "China",
        "Russia",
        "Ukraine",
        "Israel",
        "Iran",
        "Japan",
        "Australia",
        "Canada",
        "Germany",
        "France",
        "Brazil",
        "Mexico",
        "South Africa",
        "Saudi Arabia",
        "United Arab Emirates",
        "Pakistan",
        "Bangladesh",
        "Sri Lanka",
    ]

    normalized = text_value.lower()

    found = []

    for country in countries:

        if country.lower() in normalized:
            found.append(country)

    return sorted(set(found))


def keyword_count(text_value: str):

    words = re.findall(
        r"\b[a-zA-Z]{4,}\b",
        text_value.lower(),
    )

    useful = [
        word
        for word in words
        if word not in STOP_WORDS
    ]

    return len(useful)


def analyze_article(article):

    combined = " ".join(
        value
        for value in [
            article["headline"],
            article["description"] or "",
            article["content"] or "",
        ]
        if value
    )

    topics = detect_topics(combined)

    topic_names = [
        topic
        for topic, _ in topics[:8]
    ]

    primary_topic = (
        topics[0][0]
        if topics
        else "general"
    )

    entities = detect_entities(
        combined
    )

    geography = detect_geography(
        combined
    )

    normalized = normalize(
        combined
    )

    return {
        "article_id":
            article["id"],

        "primary_topic":
            primary_topic,

        "topics":
            ", ".join(topic_names),

        "entities":
            ", ".join(entities),

        "geographic_signals":
            ", ".join(geography),

        "political_signal":
            "politics" in topic_names,

        "economic_signal":
            any(
                topic in topic_names
                for topic in [
                    "economy",
                    "business",
                    "finance",
                ]
            ),

        "technology_signal":
            any(
                topic in topic_names
                for topic in [
                    "technology",
                    "artificial intelligence",
                    "cybersecurity",
                ]
            ),

        "conflict_signal":
            "conflict" in topic_names,

        "health_signal":
            "health" in topic_names,

        "climate_signal":
            any(
                topic in topic_names
                for topic in [
                    "climate",
                    "environment",
                ]
            ),

        "breaking_signal":
            any(
                phrase in normalized
                for phrase in [
                    "breaking news",
                    "just in",
                    "breaking",
                    "urgent",
                ]
            ),

        "keyword_count":
            keyword_count(combined),
    }


def run(limit: int = 1000):

    create_table()

    db = SessionLocal()

    try:

        articles = db.execute(
            text(
                """
                SELECT
                    a.id,
                    a.headline,
                    a.description,
                    a.content
                FROM articles a
                LEFT JOIN article_intelligence ai
                    ON ai.article_id = a.id
                WHERE ai.article_id IS NULL
                ORDER BY a.published_at DESC NULLS LAST
                LIMIT :limit
                """
            ),
            {"limit": limit},
        ).mappings().all()

        processed = 0

        for article in articles:

            result = analyze_article(
                article
            )

            db.execute(
                text(
                    """
                    INSERT INTO article_intelligence
                    (
                        article_id,
                        primary_topic,
                        topics,
                        entities,
                        geographic_signals,
                        political_signal,
                        economic_signal,
                        technology_signal,
                        conflict_signal,
                        health_signal,
                        climate_signal,
                        breaking_signal,
                        keyword_count
                    )
                    VALUES
                    (
                        :article_id,
                        :primary_topic,
                        :topics,
                        :entities,
                        :geographic_signals,
                        :political_signal,
                        :economic_signal,
                        :technology_signal,
                        :conflict_signal,
                        :health_signal,
                        :climate_signal,
                        :breaking_signal,
                        :keyword_count
                    )
                    ON CONFLICT (article_id)
                    DO UPDATE SET
                        primary_topic =
                            EXCLUDED.primary_topic,
                        topics =
                            EXCLUDED.topics,
                        entities =
                            EXCLUDED.entities,
                        geographic_signals =
                            EXCLUDED.geographic_signals,
                        political_signal =
                            EXCLUDED.political_signal,
                        economic_signal =
                            EXCLUDED.economic_signal,
                        technology_signal =
                            EXCLUDED.technology_signal,
                        conflict_signal =
                            EXCLUDED.conflict_signal,
                        health_signal =
                            EXCLUDED.health_signal,
                        climate_signal =
                            EXCLUDED.climate_signal,
                        breaking_signal =
                            EXCLUDED.breaking_signal,
                        keyword_count =
                            EXCLUDED.keyword_count,
                        analyzed_at =
                            NOW()
                    """
                ),
                result,
            )

            processed += 1

            if processed % 100 == 0:

                db.commit()

        db.commit()

        print()
        print(
            "INTELLIGENCE ENRICHMENT COMPLETE"
        )
        print(
            f"Articles analyzed: {processed}"
        )

        return processed

    finally:

        db.close()


if __name__ == "__main__":

    run()
