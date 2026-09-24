from sqlalchemy import select
from app.database.session import SessionLocal
from app.models import Source

SOURCES = [
    # INDIA
    {"name":"The Hindu","website_url":"https://www.thehindu.com/","country":"India","region":"Asia","language":"English","source_type":"news","description":"Indian national newspaper covering domestic and international news."},
    {"name":"The Indian Express","website_url":"https://indianexpress.com/","country":"India","region":"Asia","language":"English","source_type":"news","description":"Indian newspaper covering national and international news."},
    {"name":"Hindustan Times","website_url":"https://www.hindustantimes.com/","country":"India","region":"Asia","language":"English","source_type":"news","description":"Indian newspaper covering national, business and international news."},
    {"name":"Times of India","website_url":"https://timesofindia.indiatimes.com/","country":"India","region":"Asia","language":"English","source_type":"news","description":"Indian newspaper covering national and international news."},
    {"name":"NDTV","website_url":"https://www.ndtv.com/","country":"India","region":"Asia","language":"English","source_type":"news","description":"Indian television and digital news organization."},
    {"name":"India Today","website_url":"https://www.indiatoday.in/","country":"India","region":"Asia","language":"English","source_type":"news","description":"Indian news organization covering politics, business and society."},
    {"name":"The Telegraph India","website_url":"https://www.telegraphindia.com/","country":"India","region":"Asia","language":"English","source_type":"news","description":"Indian newspaper covering national and regional news."},
    {"name":"Deccan Herald","website_url":"https://www.deccanherald.com/","country":"India","region":"Asia","language":"English","source_type":"news","description":"Indian newspaper covering national and regional news."},
    {"name":"The Economic Times","website_url":"https://economictimes.indiatimes.com/","country":"India","region":"Asia","language":"English","source_type":"business","description":"Indian business and financial news organization."},
    {"name":"Business Standard","website_url":"https://www.business-standard.com/","country":"India","region":"Asia","language":"English","source_type":"business","description":"Indian business and financial newspaper."},
    {"name":"Mint","website_url":"https://www.livemint.com/","country":"India","region":"Asia","language":"English","source_type":"business","description":"Indian business and financial news publication."},
    {"name":"Moneycontrol","website_url":"https://www.moneycontrol.com/","country":"India","region":"Asia","language":"English","source_type":"business","description":"Indian financial and business news platform."},
    {"name":"ANI","website_url":"https://www.aninews.in/","country":"India","region":"Asia","language":"English","source_type":"news_agency","description":"Indian multimedia news agency."},
    {"name":"Press Information Bureau","website_url":"https://pib.gov.in/","country":"India","region":"Asia","language":"English","source_type":"government","description":"Official Government of India information service."},
    {"name":"DD News","website_url":"https://ddnews.gov.in/","country":"India","region":"Asia","language":"English","source_type":"public_broadcaster","description":"Indian public service news broadcaster."},
    {"name":"All India Radio","website_url":"https://www.newsonair.gov.in/","country":"India","region":"Asia","language":"English","source_type":"public_broadcaster","description":"Indian public service radio news organization."},
    {"name":"The Wire","website_url":"https://thewire.in/","country":"India","region":"Asia","language":"English","source_type":"digital_news","description":"Indian digital news publication."},
    {"name":"Scroll.in","website_url":"https://scroll.in/","country":"India","region":"Asia","language":"English","source_type":"digital_news","description":"Indian digital news publication."},
    {"name":"The Print","website_url":"https://theprint.in/","country":"India","region":"Asia","language":"English","source_type":"digital_news","description":"Indian digital news organization."},
    {"name":"Firstpost","website_url":"https://www.firstpost.com/","country":"India","region":"Asia","language":"English","source_type":"digital_news","description":"Indian digital news publication."},

    # INTERNATIONAL AGENCIES
    {"name":"Reuters","website_url":"https://www.reuters.com/","country":"International","region":"Global","language":"English","source_type":"news_agency","description":"International news agency covering global events and markets."},
    {"name":"Associated Press","website_url":"https://apnews.com/","country":"United States","region":"North America","language":"English","source_type":"news_agency","description":"International news cooperative."},
    {"name":"Agence France-Presse","website_url":"https://www.afp.com/","country":"France","region":"Europe","language":"French","source_type":"news_agency","description":"International French news agency."},
    {"name":"United Press International","website_url":"https://www.upi.com/","country":"United States","region":"North America","language":"English","source_type":"news_agency","description":"International news agency."},
    {"name":"Bloomberg","website_url":"https://www.bloomberg.com/","country":"United States","region":"North America","language":"English","source_type":"business","description":"Global financial and business news organization."},

    # UNITED STATES
    {"name":"The New York Times","website_url":"https://www.nytimes.com/","country":"United States","region":"North America","language":"English","source_type":"newspaper","description":"Major US newspaper covering global and domestic affairs."},
    {"name":"The Washington Post","website_url":"https://www.washingtonpost.com/","country":"United States","region":"North America","language":"English","source_type":"newspaper","description":"Major US newspaper covering politics and world affairs."},
    {"name":"The Wall Street Journal","website_url":"https://www.wsj.com/","country":"United States","region":"North America","language":"English","source_type":"business","description":"US business and financial newspaper."},
    {"name":"USA Today","website_url":"https://www.usatoday.com/","country":"United States","region":"North America","language":"English","source_type":"newspaper","description":"US national newspaper."},
    {"name":"NPR","website_url":"https://www.npr.org/","country":"United States","region":"North America","language":"English","source_type":"public_media","description":"US nonprofit media organization."},
    {"name":"PBS NewsHour","website_url":"https://www.pbs.org/newshour/","country":"United States","region":"North America","language":"English","source_type":"public_media","description":"US public media news program."},
    {"name":"CNN","website_url":"https://www.cnn.com/","country":"United States","region":"North America","language":"English","source_type":"television","description":"International television and digital news organization."},
    {"name":"NBC News","website_url":"https://www.nbcnews.com/","country":"United States","region":"North America","language":"English","source_type":"television","description":"US television and digital news organization."},
    {"name":"CBS News","website_url":"https://www.cbsnews.com/","country":"United States","region":"North America","language":"English","source_type":"television","description":"US television and digital news organization."},
    {"name":"ABC News","website_url":"https://abcnews.go.com/","country":"United States","region":"North America","language":"English","source_type":"television","description":"US television and digital news organization."},
    {"name":"Politico","website_url":"https://www.politico.com/","country":"United States","region":"North America","language":"English","source_type":"political_news","description":"US politics and policy news organization."},
    {"name":"The Hill","website_url":"https://thehill.com/","country":"United States","region":"North America","language":"English","source_type":"political_news","description":"US politics and policy publication."},
    {"name":"Axios","website_url":"https://www.axios.com/","country":"United States","region":"North America","language":"English","source_type":"digital_news","description":"US digital news organization."},
    {"name":"ProPublica","website_url":"https://www.propublica.org/","country":"United States","region":"North America","language":"English","source_type":"investigative","description":"US nonprofit investigative journalism organization."},
    {"name":"The Atlantic","website_url":"https://www.theatlantic.com/","country":"United States","region":"North America","language":"English","source_type":"magazine","description":"US publication covering politics, culture and world affairs."},

    # UNITED KINGDOM
    {"name":"BBC","website_url":"https://www.bbc.com/","country":"United Kingdom","region":"Europe","language":"English","source_type":"public_broadcaster","description":"UK public service broadcaster with global news coverage."},
    {"name":"The Guardian","website_url":"https://www.theguardian.com/","country":"United Kingdom","region":"Europe","language":"English","source_type":"newspaper","description":"UK newspaper with international coverage."},
    {"name":"Financial Times","website_url":"https://www.ft.com/","country":"United Kingdom","region":"Europe","language":"English","source_type":"business","description":"International business and financial newspaper."},
    {"name":"The Times","website_url":"https://www.thetimes.com/","country":"United Kingdom","region":"Europe","language":"English","source_type":"newspaper","description":"UK newspaper covering domestic and international affairs."},
    {"name":"The Telegraph","website_url":"https://www.telegraph.co.uk/","country":"United Kingdom","region":"Europe","language":"English","source_type":"newspaper","description":"UK newspaper covering national and international affairs."},
    {"name":"Sky News","website_url":"https://news.sky.com/","country":"United Kingdom","region":"Europe","language":"English","source_type":"television","description":"UK television and digital news organization."},
    {"name":"The Independent","website_url":"https://www.independent.co.uk/","country":"United Kingdom","region":"Europe","language":"English","source_type":"digital_news","description":"UK digital news publication."},

    # EUROPE
    {"name":"Deutsche Welle","website_url":"https://www.dw.com/","country":"Germany","region":"Europe","language":"German","source_type":"public_broadcaster","description":"German international broadcaster."},
    {"name":"Der Spiegel","website_url":"https://www.spiegel.de/","country":"Germany","region":"Europe","language":"German","source_type":"magazine","description":"German news magazine."},
    {"name":"France 24","website_url":"https://www.france24.com/","country":"France","region":"Europe","language":"French","source_type":"television","description":"French international news broadcaster."},
    {"name":"Le Monde","website_url":"https://www.lemonde.fr/","country":"France","region":"Europe","language":"French","source_type":"newspaper","description":"French newspaper covering international and domestic affairs."},
    {"name":"Le Figaro","website_url":"https://www.lefigaro.fr/","country":"France","region":"Europe","language":"French","source_type":"newspaper","description":"French newspaper."},
    {"name":"Euronews","website_url":"https://www.euronews.com/","country":"International","region":"Europe","language":"English","source_type":"television","description":"European international news broadcaster."},
    {"name":"Politico Europe","website_url":"https://www.politico.eu/","country":"Belgium","region":"Europe","language":"English","source_type":"political_news","description":"European politics and policy publication."},
    {"name":"The Local Europe","website_url":"https://www.thelocal.com/","country":"International","region":"Europe","language":"English","source_type":"digital_news","description":"European regional news network."},
    {"name":"Swissinfo","website_url":"https://www.swissinfo.ch/","country":"Switzerland","region":"Europe","language":"English","source_type":"public_media","description":"Swiss international public media organization."},
    {"name":"RTBF","website_url":"https://www.rtbf.be/","country":"Belgium","region":"Europe","language":"French","source_type":"public_broadcaster","description":"Belgian French-language public broadcaster."},
    {"name":"NOS","website_url":"https://nos.nl/","country":"Netherlands","region":"Europe","language":"Dutch","source_type":"public_broadcaster","description":"Dutch public broadcaster."},
    {"name":"SVT","website_url":"https://www.svt.se/","country":"Sweden","region":"Europe","language":"Swedish","source_type":"public_broadcaster","description":"Swedish public broadcaster."},
    {"name":"NRK","website_url":"https://www.nrk.no/","country":"Norway","region":"Europe","language":"Norwegian","source_type":"public_broadcaster","description":"Norwegian public broadcaster."},
    {"name":"Yle","website_url":"https://yle.fi/","country":"Finland","region":"Europe","language":"Finnish","source_type":"public_broadcaster","description":"Finnish public broadcaster."},
    {"name":"DR","website_url":"https://www.dr.dk/","country":"Denmark","region":"Europe","language":"Danish","source_type":"public_broadcaster","description":"Danish public broadcaster."},
    {"name":"RTV Slovenia","website_url":"https://www.rtvslo.si/","country":"Slovenia","region":"Europe","language":"Slovenian","source_type":"public_broadcaster","description":"Slovenian public broadcaster."},
    {"name":"Rai News","website_url":"https://www.rainews.it/","country":"Italy","region":"Europe","language":"Italian","source_type":"public_broadcaster","description":"Italian public news service."},
    {"name":"ANSA","website_url":"https://www.ansa.it/","country":"Italy","region":"Europe","language":"Italian","source_type":"news_agency","description":"Italian news agency."},
    {"name":"El Pais","website_url":"https://elpais.com/","country":"Spain","region":"Europe","language":"Spanish","source_type":"newspaper","description":"Spanish newspaper with international coverage."},
    {"name":"El Mundo","website_url":"https://www.elmundo.es/","country":"Spain","region":"Europe","language":"Spanish","source_type":"newspaper","description":"Spanish newspaper."},
    {"name":"EFE","website_url":"https://efe.com/","country":"Spain","region":"Europe","language":"Spanish","source_type":"news_agency","description":"Spanish international news agency."},

    # ASIA
    {"name":"NHK World","website_url":"https://www3.nhk.or.jp/nhkworld/","country":"Japan","region":"Asia","language":"English","source_type":"public_broadcaster","description":"Japanese international public broadcaster."},
    {"name":"The Japan Times","website_url":"https://www.japantimes.co.jp/","country":"Japan","region":"Asia","language":"English","source_type":"newspaper","description":"English-language Japanese newspaper."},
    {"name":"Kyodo News","website_url":"https://english.kyodonews.net/","country":"Japan","region":"Asia","language":"English","source_type":"news_agency","description":"Japanese news agency."},
    {"name":"Xinhua","website_url":"https://english.news.cn/","country":"China","region":"Asia","language":"English","source_type":"news_agency","description":"Chinese international news agency."},
    {"name":"China Daily","website_url":"https://www.chinadaily.com.cn/","country":"China","region":"Asia","language":"English","source_type":"newspaper","description":"Chinese English-language newspaper."},
    {"name":"South China Morning Post","website_url":"https://www.scmp.com/","country":"Hong Kong","region":"Asia","language":"English","source_type":"newspaper","description":"Asian newspaper covering China and international affairs."},
    {"name":"Korea Herald","website_url":"https://www.koreaherald.com/","country":"South Korea","region":"Asia","language":"English","source_type":"newspaper","description":"South Korean English-language newspaper."},
    {"name":"Yonhap News Agency","website_url":"https://en.yna.co.kr/","country":"South Korea","region":"Asia","language":"English","source_type":"news_agency","description":"South Korean news agency."},
    {"name":"CNA","website_url":"https://www.channelnewsasia.com/","country":"Singapore","region":"Asia","language":"English","source_type":"television","description":"Singapore-based international news broadcaster."},
    {"name":"The Straits Times","website_url":"https://www.straitstimes.com/","country":"Singapore","region":"Asia","language":"English","source_type":"newspaper","description":"Singapore newspaper covering Asian and global affairs."},
    {"name":"Bangkok Post","website_url":"https://www.bangkokpost.com/","country":"Thailand","region":"Asia","language":"English","source_type":"newspaper","description":"Thai English-language newspaper."},
    {"name":"The Nation Thailand","website_url":"https://www.nationthailand.com/","country":"Thailand","region":"Asia","language":"English","source_type":"digital_news","description":"Thai news organization."},
    {"name":"Dawn","website_url":"https://www.dawn.com/","country":"Pakistan","region":"Asia","language":"English","source_type":"newspaper","description":"Pakistani newspaper."},
    {"name":"The News International","website_url":"https://www.thenews.com.pk/","country":"Pakistan","region":"Asia","language":"English","source_type":"newspaper","description":"Pakistani newspaper."},
    {"name":"Dhaka Tribune","website_url":"https://www.dhakatribune.com/","country":"Bangladesh","region":"Asia","language":"English","source_type":"newspaper","description":"Bangladeshi English-language newspaper."},
    {"name":"The Daily Star Bangladesh","website_url":"https://www.thedailystar.net/","country":"Bangladesh","region":"Asia","language":"English","source_type":"newspaper","description":"Bangladeshi English-language newspaper."},
    {"name":"The Kathmandu Post","website_url":"https://kathmandupost.com/","country":"Nepal","region":"Asia","language":"English","source_type":"newspaper","description":"Nepalese English-language newspaper."},
    {"name":"The Manila Times","website_url":"https://www.manilatimes.net/","country":"Philippines","region":"Asia","language":"English","source_type":"newspaper","description":"Philippine newspaper."},
    {"name":"Philippine Daily Inquirer","website_url":"https://newsinfo.inquirer.net/","country":"Philippines","region":"Asia","language":"English","source_type":"newspaper","description":"Philippine newspaper."},
    {"name":"The Star Malaysia","website_url":"https://www.thestar.com.my/","country":"Malaysia","region":"Asia","language":"English","source_type":"newspaper","description":"Malaysian newspaper."},
    {"name":"Jakarta Post","website_url":"https://www.thejakartapost.com/","country":"Indonesia","region":"Asia","language":"English","source_type":"newspaper","description":"Indonesian English-language newspaper."},

    # MIDDLE EAST
    {"name":"Al Jazeera","website_url":"https://www.aljazeera.com/","country":"Qatar","region":"Middle East","language":"English","source_type":"television","description":"International news organization based in Qatar."},
    {"name":"Al Arabiya English","website_url":"https://english.alarabiya.net/","country":"Saudi Arabia","region":"Middle East","language":"English","source_type":"television","description":"Middle Eastern international news organization."},
    {"name":"Arab News","website_url":"https://www.arabnews.com/","country":"Saudi Arabia","region":"Middle East","language":"English","source_type":"newspaper","description":"Saudi Arabian English-language newspaper."},
    {"name":"Middle East Eye","website_url":"https://www.middleeasteye.net/","country":"International","region":"Middle East","language":"English","source_type":"digital_news","description":"Digital publication covering Middle Eastern affairs."},
    {"name":"The National UAE","website_url":"https://www.thenationalnews.com/","country":"United Arab Emirates","region":"Middle East","language":"English","source_type":"newspaper","description":"UAE-based English-language newspaper."},
    {"name":"Gulf News","website_url":"https://gulfnews.com/","country":"United Arab Emirates","region":"Middle East","language":"English","source_type":"newspaper","description":"UAE-based newspaper."},
    {"name":"Iran International","website_url":"https://www.iranintl.com/","country":"Iran","region":"Middle East","language":"English","source_type":"digital_news","description":"International news organization covering Iran and the region."},
    {"name":"Al Monitor","website_url":"https://www.al-monitor.com/","country":"International","region":"Middle East","language":"English","source_type":"digital_news","description":"Publication focused on Middle Eastern politics and affairs."},

    # AFRICA
    {"name":"Daily Maverick","website_url":"https://www.dailymaverick.co.za/","country":"South Africa","region":"Africa","language":"English","source_type":"digital_news","description":"South African digital news organization."},
    {"name":"News24","website_url":"https://www.news24.com/","country":"South Africa","region":"Africa","language":"English","source_type":"digital_news","description":"South African digital news organization."},
    {"name":"Mail and Guardian","website_url":"https://mg.co.za/","country":"South Africa","region":"Africa","language":"English","source_type":"newspaper","description":"South African newspaper."},
    {"name":"SABC News","website_url":"https://www.sabcnews.com/","country":"South Africa","region":"Africa","language":"English","source_type":"public_broadcaster","description":"South African public broadcaster news service."},
    {"name":"The EastAfrican","website_url":"https://www.theeastafrican.co.ke/","country":"Kenya","region":"Africa","language":"English","source_type":"newspaper","description":"East African regional newspaper."},
    {"name":"Daily Nation Kenya","website_url":"https://nation.africa/","country":"Kenya","region":"Africa","language":"English","source_type":"newspaper","description":"Kenyan newspaper and digital news organization."},
    {"name":"Premium Times","website_url":"https://www.premiumtimesng.com/","country":"Nigeria","region":"Africa","language":"English","source_type":"digital_news","description":"Nigerian digital news publication."},
    {"name":"Channels Television","website_url":"https://www.channelstv.com/","country":"Nigeria","region":"Africa","language":"English","source_type":"television","description":"Nigerian television news organization."},
    {"name":"Africanews","website_url":"https://www.africanews.com/","country":"International","region":"Africa","language":"English","source_type":"television","description":"Pan-African international news organization."},
    {"name":"The Citizen Tanzania","website_url":"https://www.thecitizen.co.tz/","country":"Tanzania","region":"Africa","language":"English","source_type":"newspaper","description":"Tanzanian newspaper."},

    # LATIN AMERICA
    {"name":"Agencia Brasil","website_url":"https://agenciabrasil.ebc.com.br/","country":"Brazil","region":"South America","language":"Portuguese","source_type":"public_media","description":"Brazilian public news agency."},
    {"name":"Folha de Sao Paulo","website_url":"https://www.folha.uol.com.br/","country":"Brazil","region":"South America","language":"Portuguese","source_type":"newspaper","description":"Brazilian newspaper."},
    {"name":"O Globo","website_url":"https://oglobo.globo.com/","country":"Brazil","region":"South America","language":"Portuguese","source_type":"newspaper","description":"Brazilian newspaper."},
    {"name":"Clarin","website_url":"https://www.clarin.com/","country":"Argentina","region":"South America","language":"Spanish","source_type":"newspaper","description":"Argentine newspaper."},
    {"name":"La Nacion Argentina","website_url":"https://www.lanacion.com.ar/","country":"Argentina","region":"South America","language":"Spanish","source_type":"newspaper","description":"Argentine newspaper."},
    {"name":"El Comercio Peru","website_url":"https://elcomercio.pe/","country":"Peru","region":"South America","language":"Spanish","source_type":"newspaper","description":"Peruvian newspaper."},
    {"name":"El Tiempo Colombia","website_url":"https://www.eltiempo.com/","country":"Colombia","region":"South America","language":"Spanish","source_type":"newspaper","description":"Colombian newspaper."},
    {"name":"La Tercera Chile","website_url":"https://www.latercera.com/","country":"Chile","region":"South America","language":"Spanish","source_type":"newspaper","description":"Chilean newspaper."},
    {"name":"Prensa Latina","website_url":"https://www.prensa-latina.cu/","country":"Cuba","region":"Caribbean","language":"Spanish","source_type":"news_agency","description":"Cuban international news agency."},

    # OCEANIA
    {"name":"ABC News Australia","website_url":"https://www.abc.net.au/news/","country":"Australia","region":"Oceania","language":"English","source_type":"public_broadcaster","description":"Australian public broadcaster news service."},
    {"name":"SBS News","website_url":"https://www.sbs.com.au/news/","country":"Australia","region":"Oceania","language":"English","source_type":"public_broadcaster","description":"Australian multicultural public broadcaster."},
    {"name":"The Sydney Morning Herald","website_url":"https://www.smh.com.au/","country":"Australia","region":"Oceania","language":"English","source_type":"newspaper","description":"Australian newspaper."},
    {"name":"The Australian","website_url":"https://www.theaustralian.com.au/","country":"Australia","region":"Oceania","language":"English","source_type":"newspaper","description":"Australian national newspaper."},
    {"name":"RNZ","website_url":"https://www.rnz.co.nz/","country":"New Zealand","region":"Oceania","language":"English","source_type":"public_broadcaster","description":"New Zealand public service broadcaster."},
    {"name":"The New Zealand Herald","website_url":"https://www.nzherald.co.nz/","country":"New Zealand","region":"Oceania","language":"English","source_type":"newspaper","description":"New Zealand newspaper."},

    # SCIENCE / TECHNOLOGY / SPECIALIZED
    {"name":"Nature","website_url":"https://www.nature.com/","country":"United Kingdom","region":"Europe","language":"English","source_type":"science","description":"International scientific publication."},
    {"name":"Science","website_url":"https://www.science.org/","country":"United States","region":"North America","language":"English","source_type":"science","description":"International scientific journal and news source."},
    {"name":"MIT Technology Review","website_url":"https://www.technologyreview.com/","country":"United States","region":"North America","language":"English","source_type":"technology","description":"Technology publication from MIT."},
    {"name":"Ars Technica","website_url":"https://arstechnica.com/","country":"United States","region":"North America","language":"English","source_type":"technology","description":"Technology news and analysis publication."},
    {"name":"TechCrunch","website_url":"https://techcrunch.com/","country":"United States","region":"North America","language":"English","source_type":"technology","description":"Technology and startup news publication."},
    {"name":"The Verge","website_url":"https://www.theverge.com/","country":"United States","region":"North America","language":"English","source_type":"technology","description":"Technology and digital culture publication."},
    {"name":"Wired","website_url":"https://www.wired.com/","country":"United States","region":"North America","language":"English","source_type":"technology","description":"Technology and science publication."},
    {"name":"IEEE Spectrum","website_url":"https://spectrum.ieee.org/","country":"United States","region":"North America","language":"English","source_type":"technology","description":"Engineering and technology publication."},
    {"name":"Space.com","website_url":"https://www.space.com/","country":"United States","region":"North America","language":"English","source_type":"space","description":"Space and astronomy news publication."},
    {"name":"NASA","website_url":"https://www.nasa.gov/","country":"United States","region":"North America","language":"English","source_type":"government","description":"Official US space agency information and news."},
    {"name":"ESA","website_url":"https://www.esa.int/","country":"International","region":"Europe","language":"English","source_type":"government","description":"European Space Agency information and news."},

    # CLIMATE / ENVIRONMENT
    {"name":"Carbon Brief","website_url":"https://www.carbonbrief.org/","country":"United Kingdom","region":"Europe","language":"English","source_type":"climate","description":"Climate science and policy publication."},
    {"name":"Inside Climate News","website_url":"https://insideclimatenews.org/","country":"United States","region":"North America","language":"English","source_type":"climate","description":"Nonprofit climate journalism organization."},
    {"name":"Climate Home News","website_url":"https://www.climatechangenews.com/","country":"United Kingdom","region":"Europe","language":"English","source_type":"climate","description":"International climate policy news organization."},

    # CYBERSECURITY
    {"name":"CISA","website_url":"https://www.cisa.gov/","country":"United States","region":"North America","language":"English","source_type":"government","description":"US cybersecurity and infrastructure security agency."},
    {"name":"KrebsOnSecurity","website_url":"https://krebsonsecurity.com/","country":"United States","region":"North America","language":"English","source_type":"cybersecurity","description":"Cybersecurity news and investigative publication."},
    {"name":"The Record","website_url":"https://therecord.media/","country":"United States","region":"North America","language":"English","source_type":"cybersecurity","description":"Cybersecurity and national security news publication."},

    # INTERNATIONAL ORGANIZATIONS
    {"name":"United Nations","website_url":"https://news.un.org/","country":"International","region":"Global","language":"English","source_type":"international_organization","description":"Official United Nations news service."},
    {"name":"World Health Organization","website_url":"https://www.who.int/","country":"International","region":"Global","language":"English","source_type":"international_organization","description":"Official World Health Organization information and news."},
    {"name":"World Bank","website_url":"https://www.worldbank.org/","country":"International","region":"Global","language":"English","source_type":"international_organization","description":"International development and economic information."},
    {"name":"International Monetary Fund","website_url":"https://www.imf.org/","country":"International","region":"Global","language":"English","source_type":"international_organization","description":"International financial organization."},
    {"name":"World Trade Organization","website_url":"https://www.wto.org/","country":"International","region":"Global","language":"English","source_type":"international_organization","description":"International trade organization."},
    {"name":"UNESCO","website_url":"https://www.unesco.org/","country":"International","region":"Global","language":"English","source_type":"international_organization","description":"UN organization covering education, science and culture."},
    {"name":"UNICEF","website_url":"https://www.unicef.org/","country":"International","region":"Global","language":"English","source_type":"international_organization","description":"UN organization focused on children and humanitarian issues."},
    {"name":"International Atomic Energy Agency","website_url":"https://www.iaea.org/","country":"International","region":"Global","language":"English","source_type":"international_organization","description":"International organization covering nuclear energy and safety."},
    {"name":"International Labour Organization","website_url":"https://www.ilo.org/","country":"International","region":"Global","language":"English","source_type":"international_organization","description":"UN organization focused on labour and employment."},
]

def main():
    print(f"Source registry contains {len(SOURCES)} records.")

    names = [item["name"] for item in SOURCES]
    if len(names) != len(set(names)):
        duplicates = sorted({name for name in names if names.count(name) > 1})
        raise RuntimeError(f"Duplicate source names found: {duplicates}")

    with SessionLocal() as db:
        existing_sources = {
            source.name: source
            for source in db.scalars(select(Source)).all()
        }

        added = 0
        updated = 0

        for item in SOURCES:
            source = existing_sources.get(item["name"])

            if source is None:
                db.add(Source(**item))
                added += 1
            else:
                source.website_url = item["website_url"]
                source.country = item["country"]
                source.region = item["region"]
                source.language = item["language"]
                source.source_type = item["source_type"]
                source.description = item["description"]
                source.is_active = True
                updated += 1

        db.commit()

        total = db.scalar(select(Source).count()) if False else len(db.scalars(select(Source)).all())

    print(f"Added: {added}")
    print(f"Updated: {updated}")
    print(f"Total sources in database: {total}")

    if total < 132:
        raise RuntimeError(
            f"Database contains only {total} sources. Expected at least 132."
        )

    print("132+ GLOBAL SOURCES LOADED SUCCESSFULLY.")

if __name__ == "__main__":
    main()
