
"""
Official/public RSS or Atom endpoints currently configured for collection.

The 132-source registry remains in PostgreSQL.
Feed URLs are added here only when a usable public feed endpoint is known.
Sources without a feed are safely skipped until a verified RSS/API endpoint
is configured.
"""

FEEDS = {
    "The Hindu": [
        "https://www.thehindu.com/news/national/feeder/default.rss",
        "https://www.thehindu.com/news/international/feeder/default.rss",
        "https://www.thehindu.com/sci-tech/science/feeder/default.rss",
        "https://www.thehindu.com/business/feeder/default.rss",
    ],
    "The Indian Express": [
        "https://indianexpress.com/feed/",
    ],
    "Hindustan Times": [
        "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
        "https://www.hindustantimes.com/feeds/rss/world-news/rssfeed.xml",
        "https://www.hindustantimes.com/feeds/rss/business/rssfeed.xml",
        "https://www.hindustantimes.com/feeds/rss/technology/rssfeed.xml",
    ],
    "NDTV": [
        "https://feeds.feedburner.com/ndtvnews-top-stories",
    ],
    "India Today": [
        "https://www.indiatoday.in/rss/home",
    ],
    "The Economic Times": [
        "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
    ],
    "Business Standard": [
        "https://www.business-standard.com/rss/latest.rss",
    ],
    "Mint": [
        "https://www.livemint.com/rss/news",
    ],
    "ANI": [
        "https://www.aninews.in/rss/",
    ],
    "The New York Times": [
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    ],
    "The Washington Post": [
        "https://feeds.washingtonpost.com/rss/world",
        "https://feeds.washingtonpost.com/rss/business",
        "https://feeds.washingtonpost.com/rss/technology",
    ],
    "NPR": [
        "https://feeds.npr.org/1001/rss.xml",
        "https://feeds.npr.org/1004/rss.xml",
        "https://feeds.npr.org/1019/rss.xml",
    ],
    "CNN": [
        "http://rss.cnn.com/rss/edition.rss",
        "http://rss.cnn.com/rss/edition_world.rss",
        "http://rss.cnn.com/rss/edition_technology.rss",
    ],
    "BBC News": [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.bbci.co.uk/news/business/rss.xml",
        "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    ],
    "The Guardian": [
        "https://www.theguardian.com/world/rss",
        "https://www.theguardian.com/business/rss",
        "https://www.theguardian.com/technology/rss",
        "https://www.theguardian.com/science/rss",
    ],
    "Financial Times": [
        "https://www.ft.com/rss/home",
    ],
    "Sky News": [
        "https://feeds.skynews.com/feeds/rss/home.xml",
        "https://feeds.skynews.com/feeds/rss/world.xml",
        "https://feeds.skynews.com/feeds/rss/business.xml",
        "https://feeds.skynews.com/feeds/rss/technology.xml",
    ],
    "Reuters": [
        "https://feeds.reuters.com/reuters/topNews",
    ],
    "France 24": [
        "https://www.france24.com/en/rss",
    ],
    "Deutsche Welle": [
        "https://rss.dw.com/rdf/rss-en-all",
    ],
    "Euronews": [
        "https://www.euronews.com/rss",
    ],
    "NHK World": [
        "https://www3.nhk.or.jp/rss/news/cat0.xml",
    ],
    "South China Morning Post": [
        "https://www.scmp.com/rss/91/feed",
    ],
    "Al Jazeera": [
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "The National": [
        "https://www.thenationalnews.com/rss",
    ],
    "ABC News Australia": [
        "https://www.abc.net.au/news/feed/51120/rss.xml",
    ],
    "RNZ": [
        "https://www.rnz.co.nz/rss/national.xml",
        "https://www.rnz.co.nz/rss/world.xml",
    ],
    "TechCrunch": [
        "https://techcrunch.com/feed/",
    ],
    "The Verge": [
        "https://www.theverge.com/rss/index.xml",
    ],
    "Ars Technica": [
        "https://feeds.arstechnica.com/arstechnica/index",
    ],
    "MIT Technology Review": [
        "https://www.technologyreview.com/feed/",
    ],
    "Wired": [
        "https://www.wired.com/feed/rss",
    ],
    "NASA": [
        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    ],
    "Nature": [
        "https://www.nature.com/nature.rss",
    ],
    "Science": [
        "https://www.science.org/rss/news_current.xml",
    ],
    "CISA": [
        "https://www.cisa.gov/cybersecurity-advisories/all.xml",
    ],
    "United Nations": [
        "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
    ],
    "World Health Organization": [
        "https://www.who.int/rss-feeds/news-english.xml",
    ],
}
