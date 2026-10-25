#!/usr/bin/env python3
"""Build the Stamped! city guide pages from the app's own data.

    python3 tools/stamped/build_city_pages.py [--app ~/Documents/Stamped-A-City-Passport]

Reads the app's Resources/BuildingRegistry.json (landmarks) and Resources/CityDetails.json
(nickname, fun fact, airport, currency, language, transit) and writes one page per city to
stamped-cities/<slug>.html plus stamped-cities/index.html. Campuses in the registry are
skipped. Re-run after the app's data changes.
"""
import argparse
import html
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "stamped-cities"
SITE = "https://georgeclinkscalesdev.com"
APP_STORE = "https://apps.apple.com/us/app/stamped-a-city-passport/id6759680336"

# City -> (country, continent). Continents match the groups on stamped-app.html.
PLACES = {
    # North America
    **{c: ("United States", "North America") for c in [
        "Detroit", "Los Angeles", "New Orleans", "Las Vegas", "Orlando", "Seattle", "Portland",
        "Washington D.C.", "Miami", "Atlanta", "Honolulu", "Chicago", "Boston", "Denver", "Pittsburgh",
        "Philadelphia", "Cleveland", "Cupertino", "Buffalo", "Houston", "New York", "San Francisco",
        "Dallas", "Nashville", "Phoenix", "Austin", "St. Louis", "Minnesota", "Asheville"]},
    **{c: ("Canada", "North America") for c in ["Vancouver", "Victoria", "Montreal", "Toronto", "Quebec City"]},
    "Mexico City": ("Mexico", "North America"), "Guadalajara": ("Mexico", "North America"),
    "Havana": ("Cuba", "North America"),
    # South America
    **{c: ("Brazil", "South America") for c in [
        "Campinas", "Curitiba", "Fortaleza", "Manaus", "Porto Alegre", "Recife", "Rio de Janeiro",
        "Brasília", "São Paulo"]},
    "Buenos Aires": ("Argentina", "South America"), "Santiago": ("Chile", "South America"),
    "Lima": ("Peru", "South America"), "Bogotá": ("Colombia", "South America"),
    "Medellín": ("Colombia", "South America"), "Cartagena": ("Colombia", "South America"),
    # Europe
    "Bath": ("United Kingdom", "Europe"), "London": ("United Kingdom", "Europe"),
    "Edinburgh": ("United Kingdom", "Europe"), "Berlin": ("Germany", "Europe"),
    "Amsterdam": ("Netherlands", "Europe"),
    **{c: ("Italy", "Europe") for c in ["Milan", "Rome", "Naples", "Florence", "Venice"]},
    "Copenhagen": ("Denmark", "Europe"),
    **{c: ("Spain", "Europe") for c in ["Barcelona", "Madrid", "Seville"]},
    "Cork": ("Ireland", "Europe"), "Dublin": ("Ireland", "Europe"),
    "Paris": ("France", "Europe"), "Nice": ("France", "Europe"),
    "Istanbul": ("Türkiye", "Europe"), "Vienna": ("Austria", "Europe"), "Salzburg": ("Austria", "Europe"),
    "Lisbon": ("Portugal", "Europe"), "Prague": ("Czech Republic", "Europe"), "Athens": ("Greece", "Europe"),
    "Budapest": ("Hungary", "Europe"), "Zurich": ("Switzerland", "Europe"), "Stockholm": ("Sweden", "Europe"),
    "Oslo": ("Norway", "Europe"), "Helsinki": ("Finland", "Europe"), "Brussels": ("Belgium", "Europe"),
    "Warsaw": ("Poland", "Europe"), "Reykjavik": ("Iceland", "Europe"), "St. Petersburg": ("Russia", "Europe"),
    "Tbilisi": ("Georgia", "Europe"),
    # Asia
    "Dubai": ("United Arab Emirates", "Asia"), "Abu Dhabi": ("United Arab Emirates", "Asia"),
    "Singapore": ("Singapore", "Asia"),
    **{c: ("India", "Asia") for c in ["Bengaluru", "Mumbai", "New Delhi", "Jaipur"]},
    "Hong Kong": ("China (Hong Kong SAR)", "Asia"),
    **{c: ("China", "Asia") for c in ["Beijing", "Shanghai", "Xi'an", "Chengdu"]},
    "Tel Aviv": ("Israel", "Asia"), "Bangkok": ("Thailand", "Asia"), "Chiang Mai": ("Thailand", "Asia"),
    "Dhaka": ("Bangladesh", "Asia"), "Riyadh": ("Saudi Arabia", "Asia"),
    **{c: ("Indonesia", "Asia") for c in ["Bali", "Batam", "Central Jakarta", "Surabaya", "Tangerang"]},
    "Pohang": ("South Korea", "Asia"), "Seoul": ("South Korea", "Asia"),
    **{c: ("Japan", "Asia") for c in ["Kyoto", "Tokyo", "Osaka", "Fukuoka"]},
    "Taipei": ("Taiwan", "Asia"), "Kuala Lumpur": ("Malaysia", "Asia"),
    "Ho Chi Minh City": ("Vietnam", "Asia"), "Doha": ("Qatar", "Asia"), "Amman": ("Jordan", "Asia"),
    "Muscat": ("Oman", "Asia"), "Manila": ("Philippines", "Asia"), "Sana'a": ("Yemen", "Asia"),
    "Kathmandu": ("Nepal", "Asia"), "Colombo": ("Sri Lanka", "Asia"),
    # Africa
    "Cairo": ("Egypt", "Africa"), "Cape Town": ("South Africa", "Africa"),
    "Johannesburg": ("South Africa", "Africa"), "Nairobi": ("Kenya", "Africa"),
    "Marrakech": ("Morocco", "Africa"), "Casablanca": ("Morocco", "Africa"), "Lagos": ("Nigeria", "Africa"),
    "Accra": ("Ghana", "Africa"), "Addis Ababa": ("Ethiopia", "Africa"), "Dakar": ("Senegal", "Africa"),
    "Zanzibar": ("Tanzania", "Africa"),
    # Oceania
    "Sydney": ("Australia", "Oceania"), "Melbourne": ("Australia", "Oceania"),
    "Brisbane": ("Australia", "Oceania"), "Auckland": ("New Zealand", "Oceania"),
    "Queenstown": ("New Zealand", "Oceania"),
}
CONTINENTS = ["Europe", "Asia", "North America", "South America", "Africa", "Oceania"]


def e(text):
    return html.escape(str(text), quote=True)


def slug(name):
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower().replace("'", "")).strip("-")


def year_label(year):
    if isinstance(year, int):
        return f"{-year} BC" if year < 0 else str(year)
    return str(year)


def year_sort(year):
    """A number for finding the oldest landmark; None when the year is text we can't read."""
    if isinstance(year, int):
        return year
    m = re.search(r"(\d{1,4})\s*(BCE|BC)?", str(year))
    if not m:
        return None
    if "century" in str(year).lower():
        return (int(m.group(1)) - 1) * 100
    n = int(m.group(1))
    return -n if m.group(2) else n


def height_label(h):
    if isinstance(h, (int, float)) and h > 0:
        return f"{round(h):,} m ({round(h * 3.28084):,} ft)"
    return None


def known(value):
    return value and str(value).strip().upper() not in {"N/A", "NA", "NONE", "-", "UNKNOWN"}


HEAD = """<!DOCTYPE HTML>
<html lang="en">
<head>
    <title>{title}</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="description" content="{description}" />
    <link rel="canonical" href="{url}" />
    <link rel="icon" href="../assets/images/stamped/app/icon.webp" type="image/webp" />
    <meta name="apple-itunes-app" content="app-id=6759680336" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:type" content="website" />
    <meta property="og:url" content="{url}" />
    <meta property="og:image" content="{site}/assets/images/stamped/app/og-image.png" />
    <meta name="twitter:card" content="summary_large_image" />
    <link rel="stylesheet" href="cities.css" />
    <script type="application/ld+json">
{jsonld}
    </script>
</head>
<body>
    <a class="skip-link" href="#main">Skip to content</a>
    <header class="site-header">
        <div class="container">
            <a class="brand" href="../stamped-app.html">
                <img src="../assets/images/stamped/app/icon.webp" alt="" width="32" height="32" />
                Stamped!
            </a>
            <nav class="header-nav" aria-label="Site">
                <a href="index.html">City guides</a>
                <a class="header-button" href="{app_store}">Get the app</a>
            </nav>
        </div>
    </header>
"""

FOOT = """
    <section class="cta" aria-labelledby="cta-title">
        <div class="container">
            <img class="cta-icon" src="../assets/images/stamped/app/icon.webp" alt="" width="72" height="72" loading="lazy" />
            <h2 id="cta-title">{cta_title}</h2>
            <p>{cta_text}</p>
            <a class="app-store-button" href="{app_store}">
                <svg viewBox="0 0 384 512" width="22" height="22" aria-hidden="true"><path fill="currentColor" d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z"/></svg>
                <span><small>Download on the</small><strong>App Store</strong></span>
            </a>
        </div>
    </section>
    </main>

    <footer class="site-footer">
        <div class="container">
            <nav aria-label="App links">
                <a href="../stamped-app.html">Stamped!</a>
                <a href="index.html">All city guides</a>
                <a href="../contact.html">Support</a>
                <a href="../privacy.html">Privacy</a>
            </nav>
            <p>Landmark details come from the Stamped! app. Apple, the Apple logo and iPhone are trademarks of Apple Inc. App Store is a service mark of Apple Inc.</p>
            <p>© 2026 George Clinkscales Jr.</p>
        </div>
    </footer>
</body>
</html>
"""


def jsonld(items):
    return "\n".join("    " + line for line in json.dumps(items, ensure_ascii=False, indent=4).splitlines())


def city_page(city, landmarks, details, siblings):
    country, continent = PLACES[city]
    s = slug(city)
    url = f"{SITE}/stamped-cities/{s}.html"
    n = len(landmarks)
    noun = "landmark" if n == 1 else "landmarks"
    title = f"{city} Architecture: {n} Landmarks to See | Stamped!"
    if n == 1:
        title = f"{city} Architecture: A Landmark to See | Stamped!"
    names = [l["name"] for l in landmarks]
    description = (f"A guide to {n} architectural {noun} in {city}, {country}: "
                   + ", ".join(names[:3]) + (" and more" if n > 3 else "")
                   + ". Architects, build dates, styles and history, from the Stamped! app.")

    dated = [(year_sort(l["yearBuilt"]), l) for l in landmarks if year_sort(l["yearBuilt"]) is not None]
    oldest = min(dated, key=lambda x: x[0])[1] if dated else None
    tall = [l for l in landmarks if isinstance(l["height"], (int, float)) and l["height"] > 0]
    tallest = max(tall, key=lambda l: l["height"]) if tall else None
    architects = {a.strip() for l in landmarks for a in re.split(r"\s*(?:/|;)\s*", str(l["architect"]))
                  if known(a) and "unknown" not in a.lower()}

    ld = [
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Stamped!", "item": f"{SITE}/stamped-app.html"},
            {"@type": "ListItem", "position": 2, "name": "City guides", "item": f"{SITE}/stamped-cities/index.html"},
            {"@type": "ListItem", "position": 3, "name": city, "item": url}]},
        {"@context": "https://schema.org", "@type": "ItemList", "name": f"Architectural landmarks in {city}",
         "numberOfItems": n, "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {
                "@type": "LandmarksOrHistoricalBuildings", "name": l["name"],
                **({"address": l["address"]} if known(l.get("address")) else {})}}
            for i, l in enumerate(landmarks)]},
    ]

    out = [HEAD.format(title=e(title), description=e(description), url=url, site=SITE,
                       jsonld=jsonld(ld), app_store=APP_STORE)]
    out.append(f"""
    <main id="main">
    <section class="hero">
        <div class="container">
            <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">City guides</a> <span aria-hidden="true">/</span> {e(continent)} <span aria-hidden="true">/</span> {e(country)}</nav>
            <p class="kicker">{e(details.get('nickname') or 'City guide')}</p>
            <h1>{e(city)} architecture</h1>
            <p class="lead">{e(details.get('funFact', ''))}</p>
            <ul class="stats">
                <li><strong>{n}</strong><span>{noun.title()}</span></li>""")
    if oldest:
        out.append(f"""
                <li><strong>{e(year_label(oldest['yearBuilt']))}</strong><span>Oldest · {e(oldest['name'])}</span></li>""")
    if tallest:
        out.append(f"""
                <li><strong>{round(tallest['height']):,} m</strong><span>Tallest · {e(tallest['name'])}</span></li>""")
    if architects:
        out.append(f"""
                <li><strong>{len(architects)}</strong><span>Architects</span></li>""")
    out.append("""
            </ul>
        </div>
    </section>
""")

    # Arrival facts
    facts = []
    if known(details.get("airportName")):
        code = f" ({e(details['airportCode'])})" if known(details.get("airportCode")) else ""
        facts.append(("Fly into", e(details["airportName"]) + code, details.get("airportInfo")))
    if known(details.get("currencyInfo")):
        facts.append(("Currency", e(details["currencyInfo"]), None))
    if known(details.get("language")):
        facts.append(("Language", e(details["language"]), details.get("languageInfo")))
    if known(details.get("transportation")):
        facts.append(("Getting around", e(details["transportation"]), details.get("transportationFact")))
    if facts:
        out.append("""
    <section class="facts" aria-labelledby="facts-title">
        <div class="container">
            <h2 id="facts-title" class="section-title">Before you go</h2>
            <ul class="fact-grid">""")
        for label, value, more in facts:
            more_html = f"<p>{e(more)}</p>" if known(more) else ""
            out.append(f"""
                <li><span class="fact-label">{label}</span><strong>{value}</strong>{more_html}</li>""")
        out.append("""
            </ul>
        </div>
    </section>
""")

    # Landmarks
    out.append(f"""
    <section class="landmarks" aria-labelledby="landmarks-title">
        <div class="container">
            <h2 id="landmarks-title" class="section-title">{n} {noun} in {e(city)}</h2>
            <ol class="landmark-list">""")
    for i, l in enumerate(landmarks, 1):
        meta = []
        meta.append(("Built", year_label(l["yearBuilt"])))
        if known(l.get("architect")):
            meta.append(("Architect", l["architect"]))
        if known(l.get("buildingStyle")):
            meta.append(("Style", l["buildingStyle"]))
        h = height_label(l.get("height"))
        if h:
            meta.append(("Height", h))
        elif known(l.get("height")) and not isinstance(l.get("height"), (int, float)):
            meta.append(("Height", l["height"]))
        if isinstance(l.get("numberOfStories"), int) and l["numberOfStories"] > 0:
            meta.append(("Stories", f"{l['numberOfStories']:,}"))
        use = l.get("newUse") if known(l.get("newUse")) else None
        if use:
            meta.append(("Today", use))
        meta_html = "".join(f"<div><dt>{e(k)}</dt><dd>{e(v)}</dd></div>" for k, v in meta)
        address = f'<p class="address">{e(l["address"])}</p>' if known(l.get("address")) else ""
        out.append(f"""
                <li id="{e(l['id'])}">
                    <span class="landmark-number" aria-hidden="true">{i:02d}</span>
                    <h3>{e(l['name'])}</h3>
                    {address}
                    <p>{e(l['description'])}</p>
                    <dl>{meta_html}</dl>
                </li>""")
    out.append("""
            </ol>
        </div>
    </section>
""")

    # More cities on the same continent
    if siblings:
        links = "".join(f'<li><a href="{slug(c)}.html">{e(c)}</a></li>' for c in siblings)
        out.append(f"""
    <section class="more-cities" aria-labelledby="more-title">
        <div class="container">
            <h2 id="more-title" class="section-title">More cities in {e(continent)}</h2>
            <ul class="city-chips">{links}</ul>
        </div>
    </section>
""")

    out.append(FOOT.format(
        app_store=APP_STORE,
        cta_title=f"Stamp all {n} in Stamped!" if n > 1 else "Stamp it in Stamped!",
        cta_text=f"Fly through {e(city)} in photoreal 3D, take its 10-question quiz, plan your days and earn a passport stamp at every landmark. Free on iPhone and iPad."))
    return "".join(out)


def index_page(by_continent, counts):
    total = sum(counts.values())
    title = "City Guides: 140 Cities of Great Architecture | Stamped!"
    description = (f"Architecture guides to 140 cities on six continents, with {total:,} landmarks: "
                   "architects, build dates, styles and history, from the Stamped! app.")
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Stamped! city guides",
           "url": f"{SITE}/stamped-cities/index.html", "description": description}]
    out = [HEAD.format(title=e(title), description=e(description), url=f"{SITE}/stamped-cities/index.html",
                       site=SITE, jsonld=jsonld(ld), app_store=APP_STORE)]
    out.append(f"""
    <main id="main">
    <section class="hero">
        <div class="container">
            <nav class="crumbs" aria-label="Breadcrumb"><a href="../stamped-app.html">Stamped!</a> <span aria-hidden="true">/</span> City guides</nav>
            <p class="kicker">City guides · Six continents</p>
            <h1>140 cities of great architecture</h1>
            <p class="lead">Every city in the Stamped! app, with its landmarks, architects, build dates and the story behind each building. {total:,} landmarks in all.</p>
        </div>
    </section>
""")
    for continent in CONTINENTS:
        cities = by_continent[continent]
        items = "".join(
            f'<li><a href="{slug(c)}.html"><strong>{e(c)}</strong><span>{e(PLACES[c][0])} · {counts[c]} landmark{"s" if counts[c] != 1 else ""}</span></a></li>'
            for c in cities)
        out.append(f"""
    <section class="continent" aria-labelledby="{slug(continent)}">
        <div class="container">
            <h2 id="{slug(continent)}" class="section-title">{e(continent)} <span>{len(cities)} cities</span></h2>
            <ul class="city-grid">{items}</ul>
        </div>
    </section>
""")
    out.append(FOOT.format(app_store=APP_STORE, cta_title="Your passport is waiting.",
                           cta_text="Fly through all 140 cities in photoreal 3D and earn a stamp at every landmark you visit. Free on iPhone and iPad."))
    return "".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default=str(Path.home() / "Documents/Stamped-A-City-Passport"))
    args = parser.parse_args()
    resources = Path(args.app).expanduser() / "Stamped! A City Passport" / "Resources"
    registry = json.loads((resources / "BuildingRegistry.json").read_text(encoding="utf-8"))
    details = json.loads((resources / "CityDetails.json").read_text(encoding="utf-8"))

    cities = [c for c in registry if c in PLACES]
    skipped = [c for c in registry if c not in PLACES
               and not re.search(r"Universit|College|Institute|Leuven|Sorbonne|Virginia Tech", c)]
    if skipped:
        raise SystemExit(f"Add these cities to PLACES: {skipped}")

    by_continent = {k: sorted((c for c in cities if PLACES[c][1] == k), key=slug) for k in CONTINENTS}
    counts = {c: len(registry[c]) for c in cities}

    OUT.mkdir(exist_ok=True)
    for city in cities:
        siblings = [c for c in by_continent[PLACES[city][1]] if c != city]
        page = city_page(city, registry[city], details.get(city, {}), siblings)
        (OUT / f"{slug(city)}.html").write_text(page, encoding="utf-8")
    (OUT / "index.html").write_text(index_page(by_continent, counts), encoding="utf-8")
    print(f"wrote {len(cities)} city pages and index.html to {OUT.relative_to(ROOT)}/ "
          f"({sum(counts.values()):,} landmarks)")
    for k in CONTINENTS:
        print(f"  {k}: {len(by_continent[k])}")


if __name__ == "__main__":
    main()
