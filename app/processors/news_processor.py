import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AnalyticalScore,
    Article,
    ArticleCategory,
    ArticleEntity,
    ArticleTopic,
    Category,
    Entity,
    OneLineNews,
    Summary,
    Topic,
)


CATEGORY_RULES = {
    "World": ["world", "international", "global"],
    "India": ["india", "indian", "new delhi", "mumbai", "bengaluru"],
    "Politics": ["election", "government", "minister", "parliament", "president", "prime minister", "political", "party"],
    "Geopolitics": ["geopolit", "sanction", "alliance", "diplomatic", "diplomacy", "territorial"],
    "Economy": ["economy", "economic", "gdp", "inflation", "growth", "recession"],
    "Business": ["business", "company", "corporate", "merger", "acquisition", "startup"],
    "Finance": ["bank", "banking", "market", "stock", "shares", "bond", "interest rate", "currency"],
    "Technology": ["technology", "tech", "software", "computer", "chip", "semiconductor"],
    "AI": ["artificial intelligence", " ai ", "machine learning", "generative ai", "chatgpt", "openai", "gemini"],
    "Cybersecurity": ["cybersecurity", "cyber attack", "cyberattack", "hacker", "ransomware", "malware", "vulnerability"],
    "Science": ["science", "research", "scientist", "study", "discovery"],
    "Space": ["space", "nasa", "isro", "satellite", "rocket", "astronaut", "moon", "mars"],
    "Climate": ["climate", "global warming", "carbon emissions", "greenhouse gas"],
    "Environment": ["environment", "biodiversity", "pollution", "forest", "wildlife"],
    "Health": ["health", "hospital", "disease", "virus", "outbreak", "medicine"],
    "Wellness": ["wellness", "fitness", "nutrition", "sleep", "mental health"],
    "Education": ["education", "school", "university", "student", "teacher"],
    "Society": ["society", "community", "social"],
    "Crime": ["crime", "criminal", "police", "arrest", "investigation"],
    "Violence": ["violence", "attack", "killed", "shooting", "bombing"],
    "Conflict": ["war", "conflict", "battle", "fighting", "ceasefire"],
    "Terrorism": ["terrorism", "terrorist", "extremist"],
    "Human Rights": ["human rights", "rights violation", "civil rights"],
    "Law": ["court", "law", "lawsuit", "judge", "legal", "supreme court"],
    "Diplomacy": ["diplomacy", "diplomatic", "foreign minister", "embassy"],
    "Defense": ["defense", "defence", "military", "army", "navy", "air force", "missile"],
    "Energy": ["energy", "oil", "gas", "solar", "wind power", "nuclear power"],
    "Agriculture": ["agriculture", "farmer", "farming", "crop", "harvest"],
    "Infrastructure": ["infrastructure", "highway", "bridge", "railway", "construction"],
    "Transportation": ["transport", "rail", "railway", "aviation", "airline", "airport"],
    "Sports": ["sports", "cricket", "football", "soccer", "tennis", "olympic"],
    "Culture": ["culture", "art", "museum", "heritage"],
    "Entertainment": ["movie", "film", "actor", "actress", "music", "television", "entertainment"],
}


TOPIC_RULES = {
    "Elections": ["election", "voting", "vote", "ballot"],
    "Artificial Intelligence": ["artificial intelligence", " ai ", "machine learning", "generative ai"],
    "Cybersecurity": ["cybersecurity", "cyber attack", "ransomware", "malware", "hacker"],
    "Climate Change": ["climate change", "global warming", "carbon emissions"],
    "Geopolitical Tensions": ["geopolit", "sanction", "territorial dispute", "diplomatic tensions"],
    "Armed Conflict": ["war", "battle", "fighting", "ceasefire", "armed conflict"],
    "Financial Markets": ["stock market", "shares", "bond", "market", "interest rate"],
    "Inflation": ["inflation", "consumer prices", "price rise"],
    "Space Exploration": ["space", "nasa", "isro", "moon", "mars", "rocket"],
    "Public Health": ["health", "disease", "outbreak", "virus", "hospital"],
    "Energy Transition": ["renewable energy", "solar", "wind", "electric vehicle", "nuclear"],
    "Technology Industry": ["technology", "software", "semiconductor", "chip", "startup"],
}


ENTITY_PATTERNS = [
    (
        "ORGANIZATION",
        r"\b(?:OpenAI|Google|Microsoft|Apple|Amazon|Meta|NVIDIA|Tesla|NASA|ISRO|NATO|United Nations|World Bank|IMF|WHO|European Union|European Commission|Reserve Bank of India)\b",
    ),
    (
        "COUNTRY",
        r"\b(?:India|United States|China|Russia|Ukraine|Japan|South Korea|North Korea|Pakistan|Iran|Israel|United Kingdom|France|Germany|Australia|Canada|Brazil|Mexico|Indonesia|New Zealand)\b",
    ),
]


def normalize(text):
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def score_keywords(text, keywords):
    text = normalize(text)
    return min(
        100.0,
        sum(1 for keyword in keywords if keyword.lower() in text) * 20.0,
    )


def get_or_create_category(db, name):
    item = db.scalar(select(Category).where(Category.name == name))

    if item is None:
        item = Category(name=name)
        db.add(item)
        db.flush()

    return item


def get_or_create_topic(db, name):
    item = db.scalar(select(Topic).where(Topic.name == name))

    if item is None:
        item = Topic(name=name)
        db.add(item)
        db.flush()

    return item


def get_or_create_entity(db, name, entity_type):
    item = db.scalar(
        select(Entity).where(
            Entity.name == name,
            Entity.entity_type == entity_type,
        )
    )

    if item is None:
        item = Entity(
            name=name,
            entity_type=entity_type,
        )
        db.add(item)
        db.flush()

    return item


def make_summary(article):
    text = article.description or article.content or article.headline or ""
    text = re.sub(r"\s+", " ", text).strip()

    sentences = re.split(r"(?<=[.!?])\s+", text)

    useful = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) >= 30
    ]

    return " ".join(useful[:2])[:1000] if useful else text[:1000]


def make_key_points(article):
    text = article.description or article.content or article.headline or ""
    text = re.sub(r"\s+", " ", text).strip()

    sentences = re.split(r"(?<=[.!?])\s+", text)

    points = [
        sentence.strip()
        for sentence in sentences
        if len(sentence.strip()) >= 30
    ]

    return "\n".join(
        f"- {point[:500]}"
        for point in points[:5]
    )


def process_article(db, article):
    text = normalize(
        " ".join(
            filter(
                None,
                [
                    article.headline,
                    article.description,
                    article.content,
                ],
            )
        )
    )

    categories_found = []

    for category_name, keywords in CATEGORY_RULES.items():
        score = score_keywords(text, keywords)

        if score > 0:
            category = get_or_create_category(db, category_name)

            exists = db.scalar(
                select(ArticleCategory.id).where(
                    ArticleCategory.article_id == article.id,
                    ArticleCategory.category_id == category.id,
                )
            )

            if not exists:
                db.add(
                    ArticleCategory(
                        article_id=article.id,
                        category_id=category.id,
                    )
                )

            categories_found.append((category_name, score))

    if not categories_found:
        category = get_or_create_category(db, "World")

        exists = db.scalar(
            select(ArticleCategory.id).where(
                ArticleCategory.article_id == article.id,
                ArticleCategory.category_id == category.id,
            )
        )

        if not exists:
            db.add(
                ArticleCategory(
                    article_id=article.id,
                    category_id=category.id,
                )
            )

        categories_found.append(("World", 0))

    for topic_name, keywords in TOPIC_RULES.items():
        if score_keywords(text, keywords) > 0:
            topic = get_or_create_topic(db, topic_name)

            exists = db.scalar(
                select(ArticleTopic.id).where(
                    ArticleTopic.article_id == article.id,
                    ArticleTopic.topic_id == topic.id,
                )
            )

            if not exists:
                db.add(
                    ArticleTopic(
                        article_id=article.id,
                        topic_id=topic.id,
                    )
                )

    headline = article.headline or ""

    for entity_type, pattern in ENTITY_PATTERNS:
        for match in re.findall(
            pattern,
            headline,
            flags=re.IGNORECASE,
        ):
            entity = get_or_create_entity(
                db,
                match.strip(),
                entity_type,
            )

            exists = db.scalar(
                select(ArticleEntity.id).where(
                    ArticleEntity.article_id == article.id,
                    ArticleEntity.entity_id == entity.id,
                )
            )

            if not exists:
                db.add(
                    ArticleEntity(
                        article_id=article.id,
                        entity_id=entity.id,
                    )
                )

    summary = db.scalar(
        select(Summary).where(
            Summary.article_id == article.id
        )
    )

    if summary is None:
        db.add(
            Summary(
                article_id=article.id,
                short_summary=make_summary(article),
                key_points=make_key_points(article),
                summary_method="extractive",
            )
        )

    one_line = db.scalar(
        select(OneLineNews).where(
            OneLineNews.article_id == article.id
        )
    )

    if one_line is None:
        db.add(
            OneLineNews(
                article_id=article.id,
                one_line=headline[:500],
            )
        )

    conflict = score_keywords(
        text,
        [
            "war",
            "conflict",
            "battle",
            "attack",
            "fighting",
            "ceasefire",
            "terrorism",
        ],
    )

    geopolitical = score_keywords(
        text,
        [
            "geopolit",
            "sanction",
            "diplomatic",
            "nato",
            "territorial",
            "foreign policy",
        ],
    )

    economic = score_keywords(
        text,
        [
            "economy",
            "economic",
            "inflation",
            "gdp",
            "market",
            "bank",
            "finance",
        ],
    )

    technology = score_keywords(
        text,
        [
            "technology",
            "software",
            "artificial intelligence",
            "machine learning",
            "semiconductor",
            "cybersecurity",
        ],
    )

    climate = score_keywords(
        text,
        [
            "climate",
            "global warming",
            "carbon",
            "emissions",
            "renewable",
        ],
    )

    wellness = score_keywords(
        text,
        [
            "wellness",
            "fitness",
            "nutrition",
            "sleep",
            "mental health",
        ],
    )

    importance = min(
        100.0,
        max(
            conflict,
            geopolitical,
            economic,
            technology,
            climate,
            wellness,
        ),
    )

    analytical = db.scalar(
        select(AnalyticalScore).where(
            AnalyticalScore.article_id == article.id
        )
    )

    if analytical is None:
        classification = (
            "developing"
            if conflict >= 40
            else "reported"
        )

        db.add(
            AnalyticalScore(
                article_id=article.id,
                importance_score=importance,
                conflict_score=conflict,
                geopolitical_score=geopolitical,
                economic_score=economic,
                technology_score=technology,
                climate_score=climate,
                wellness_score=wellness,
                classification=classification,
                evidence_note=(
                    "Keyword-based analytical signals. "
                    "These are not factual truth, credibility, "
                    "or source-quality ratings."
                ),
            )
        )

    return categories_found


def process_all_articles():
    from app.database.session import SessionLocal

    with SessionLocal() as db:
        articles = db.scalars(
            select(Article).order_by(Article.id)
        ).all()

        total = len(articles)
        processed = 0
        failed = 0

        print("")
        print("==========================================")
        print("NEWS INTELLIGENCE PROCESSOR")
        print("==========================================")
        print(f"Articles to process: {total}")
        print("")

        for index, article in enumerate(
            articles,
            start=1,
        ):
            try:
                process_article(db, article)
                processed += 1

                if index % 100 == 0 or index == total:
                    db.commit()

                    print(
                        f"Processed {index}/{total} "
                        f"| successful={processed} "
                        f"| failed={failed}"
                    )

            except Exception as exc:
                db.rollback()
                failed += 1

                print(
                    f"Article {article.id} failed: "
                    f"{str(exc)[:200]}"
                )

        db.commit()

        print("")
        print("==========================================")
        print("PROCESSING COMPLETE")
        print("==========================================")
        print(f"Articles processed : {processed}")
        print(f"Articles failed    : {failed}")
        print("==========================================")


if __name__ == "__main__":
    process_all_articles()
