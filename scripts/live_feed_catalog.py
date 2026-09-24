from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.models.source import Source


LIVE_FEEDS = {

    # INDIA
    "The Hindu":
        "https://www.thehindu.com/news/feeder/default.rss",

    "The Indian Express":
        "https://indianexpress.com/feed/",

    "Hindustan Times":
        "https://www.hindustantimes.com/feeds/rss/latest/rssfeed.xml",

    "NDTV":
        "https://feeds.feedburner.com/ndtvnews-latest",

    # GLOBAL
    "BBC News":
        "https://feeds.bbci.co.uk/news/world/rss.xml",

    "Al Jazeera":
        "https://www.aljazeera.com/xml/rss/all.xml",

    "The Guardian":
        "https://www.theguardian.com/world/rss",

    "Deutsche Welle":
        "https://rss.dw.com/rdf/rss-en-all",

    "Euronews":
        "https://www.euronews.com/rss",

    "France 24":
        "https://www.france24.com/en/rss",

    # UNITED STATES
    "NPR":
        "https://feeds.npr.org/1004/rss.xml",

    "PBS NewsHour":
        "https://www.pbs.org/newshour/feeds/rss/headlines",

    # TECHNOLOGY
    "TechCrunch":
        "https://techcrunch.com/feed/",

    "The Verge":
        "https://www.theverge.com/rss/index.xml",

    "Ars Technica":
        "https://feeds.arstechnica.com/arstechnica/index",

    # SPACE / SCIENCE
    "NASA":
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",

    "Nature":
        "https://www.nature.com/nature.rss",

    # AUSTRALIA
    "ABC News Australia":
        "https://www.abc.net.au/news/feed/51120/rss.xml",

    "The Sydney Morning Herald":
        "https://www.smh.com.au/rss/feed.xml",

    # NEW ZEALAND
    "RNZ":
        "https://www.rnz.co.nz/rss/world.xml",

    # CANADA
    "CBC News":
        "https://www.cbc.ca/cmlink/rss-world",

    # ASIA
    "South China Morning Post":
        "https://www.scmp.com/rss/91/feed",

    "The Japan Times":
        "https://www.japantimes.co.jp/feed/",

    "Korea Herald":
        "https://www.koreaherald.com/common/rss_xml.php",

    "Channel NewsAsia":
        "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",

    # MIDDLE EAST
    "Arab News":
        "https://www.arabnews.com/rss.xml",

    # AFRICA
    "Africanews":
        "https://www.africanews.com/feed/",

    # INTERNATIONAL ORGANIZATIONS
    "United Nations":
        "https://news.un.org/feed/subscribe/en/news/all/rss.xml",

    "World Health Organization":
        "https://www.who.int/rss-feeds/news-english.xml",

    "World Bank":
        "https://www.worldbank.org/en/news/all?format=rss",

    # FINANCE / ECONOMY
    "Federal Reserve":
        "https://www.federalreserve.gov/feeds/press_all.xml",

    "European Central Bank":
        "https://www.ecb.europa.eu/rss/press.html",

    # SPORTS
    "ESPN":
        "https://www.espn.com/espn/rss/news",

    "BBC Sport":
        "https://feeds.bbci.co.uk/sport/rss.xml",
}


def normalize_name(name: str) -> str:
    return " ".join(name.lower().split())


def update_database():
    db: Session = SessionLocal()

    updated = 0
    missing = 0

    try:
        sources = db.scalars(
            select(Source)
        ).all()

        source_map = {
            normalize_name(source.name): source
            for source in sources
        }

        for name, feed_url in LIVE_FEEDS.items():

            source = source_map.get(
                normalize_name(name)
            )

            if source is None:
                print(
                    f"[NOT FOUND] {name}"
                )
                missing += 1
                continue

            source.feed_url = feed_url
            source.is_active = True

            updated += 1

            print(
                f"[UPDATED] {source.name}"
            )
            print(
                f"          {feed_url}"
            )

        db.commit()

        print()
        print(
            f"Sources updated : {updated}"
        )
        print(
            f"Sources missing : {missing}"
        )

    finally:
        db.close()


if __name__ == "__main__":
    update_database()
