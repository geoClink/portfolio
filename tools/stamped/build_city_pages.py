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
# Guided-tour clips recorded in the app (assets/videos/stamped/), shown on these city pages
TOUR_VIDEOS = {
    "Paris": ("stamped-tour-paris", 1070, "Palais Garnier, the Louvre, Sainte-Chapelle, the Centre Pompidou, the Panthéon and the Eiffel Tower"),
    "Chicago": ("stamped-tour-chicago", 1070, "the Carbide and Carbon Building, the Wrigley Building, Tribune Tower and the St. Regis"),
    "London": ("stamped-tour-london", 1070, "Tate Modern, St Paul's Cathedral, the Barbican, the Gherkin and the Lloyd's Building"),
    "Rome": ("stamped-tour-rome", 1070, "the Pantheon, Palazzo Doria Pamphilj, the Altare della Patria and San Carlo alle Quattro Fontane"),
    "New York": ("stamped-3d-map-screen", 1078, "the Empire State Building and down to street level on Fifth Avenue"),
}

PLACES_BY_ID = {}   # landmark id -> city, filled in by main()

CONTINENTS = ["Europe", "Asia", "North America", "South America", "Africa", "Oceania"]


# Shared files the pages link to. Each link gets ?v=<hash of the file>, so browsers fetch the new
# copy after every change instead of a stale one (GitHub Pages lets them cache files for a day).
ASSETS = ["cities.css", "map.js", "map-token.js", "suggest.js"]


def versioned(page, folder=OUT, prefix=""):
    """`page` with every link to a shared file stamped with that file's content hash."""
    import hashlib
    for name in ASSETS + (["campus.css"] if folder != OUT else []):
        path = (folder if name == "campus.css" else OUT) / name
        if not path.exists():
            continue
        stamp = hashlib.sha1(path.read_bytes()).hexdigest()[:8]
        link = (prefix if name != "campus.css" else "") + name
        page = page.replace(f'"{link}"', f'"{link}?v={stamp}"')
    return page


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
    <meta name="apple-itunes-app" content="app-id=6759680336, app-argument={url}" />
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
            <p>Landmark details come from the Stamped! app. Photos are openly licensed, mostly from Wikimedia Commons; each is credited with its author, license and source. Apple, the Apple logo and iPhone are trademarks of Apple Inc. App Store is a service mark of Apple Inc.</p>
            <p>© 2026 George Clinkscales Jr.</p>
        </div>
    </footer>
{scripts}</body>
</html>
"""


def jsonld(items):
    return "\n".join("    " + line for line in json.dumps(items, ensure_ascii=False, indent=4).splitlines())


def photo_figure(photo, name, eager=False):
    """A landmark photo with its required credit line (author, license, link to the file page)."""
    if not photo:
        return ""
    license_html = e(photo["license"])
    if photo.get("licenseUrl"):
        license_html = f'<a href="{e(photo["licenseUrl"])}" rel="license noopener">{license_html}</a>'
    loading = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<figure class="landmark-photo"><img src="{e(photo["src"])}" width="{photo["width"]}" height="{photo["height"]}" '
            f'alt="{e(name)}" {loading} referrerpolicy="no-referrer" />'
            f'<figcaption>Photo: <a href="{e(photo["page"])}" rel="noopener">{e(photo["author"])}</a>, {license_html}, via {e(photo.get("site", "Wikimedia Commons"))}</figcaption></figure>')


def suggest_section(place, url, heading, intro, kinds):
    """A short form that opens the visitor's own email app with the suggestion filled in (suggest.js)."""
    options = "".join(
        f'\n                    <label><input type="radio" name="kind" value="{e(k)}"{" checked" if i == 0 else ""} /> '
        f'{"An" if k[0] in "AEIOU" else "A"} {e(k.lower())}</label>'
        for i, k in enumerate(kinds))
    return f"""
    <section class="suggest" aria-labelledby="suggest-title">
        <div class="container">
            <h2 id="suggest-title" class="section-title">{e(heading)}</h2>
            <p class="map-hint">{e(intro)}</p>
            <form class="suggest-form" data-place="{e(place)}" data-page="{url}">
                <fieldset>
                    <legend class="fact-label">I'm suggesting</legend>{options}
                </fieldset>
                <label>What is it, and where?<textarea name="details" rows="4" maxlength="2000" required></textarea></label>
                <label>A link we can check (optional)<input type="url" name="source" maxlength="300" placeholder="https://" /></label>
                <button type="submit">Write the email</button>
                <p class="suggest-note">Opens your email app with this filled in, addressed to GeorgeClinkscalesDev@proton.me.</p>
                <p class="suggest-status" aria-live="polite"></p>
            </form>
        </div>
    </section>
"""


def city_page(city, landmarks, details, siblings, photos):
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
            <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">City guides</a> <span aria-hidden="true">/</span> <a href="{slug(continent)}.html">{e(continent)}</a> <span aria-hidden="true">/</span> {e(country)}</nav>
            <p class="kicker">{e(details.get('nickname') or 'City guide')}</p>
            <h1>{e(city)} architecture</h1>
            <p class="lead">{e(details.get('funFact', ''))}</p>
            <ul class="stats">
                <li><strong>{n}</strong><span>{noun.title()}</span></li>""")
    hero_photos = [l for l in landmarks if l["id"] in photos][:3]
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
            </ul>""")
    if hero_photos:
        tiles = "".join(
            f'<li><a href="#{e(l["id"])}"><img src="{e(photos[l["id"]]["src"])}" width="{photos[l["id"]]["width"]}" '
            f'height="{photos[l["id"]]["height"]}" alt="{e(l["name"])}" {"fetchpriority=\"high\"" if i == 0 else "loading=\"lazy\""} '
            f'referrerpolicy="no-referrer" /><span>{e(l["name"])}</span></a></li>'
            for i, l in enumerate(hero_photos))
        out.append(f"""
            <ul class="hero-photos count-{len(hero_photos)}">{tiles}</ul>""")
    out.append("""
        </div>
    </section>
""")

    # Live Apple Map with Look Around (filled in by map.js; stays hidden without a token or if MapKit fails)
    pins = [l for l in landmarks if isinstance(l.get("latitude"), (int, float)) and isinstance(l.get("longitude"), (int, float))]
    if pins:
        map_data = {"landmarks": [
            {"id": l["id"], "name": l["name"], "lat": l["latitude"], "lng": l["longitude"],
             "subtitle": " · ".join(x for x in [year_label(l["yearBuilt"]), str(l["architect"]) if known(l.get("architect")) else ""] if x)}
            for l in pins]}
        out.append(f"""
    <section class="city-map-section" data-city-map hidden aria-labelledby="map-title">
        <div class="container">
            <h2 id="map-title" class="section-title">Map and Look Around</h2>
            <p class="map-hint">Tap a numbered pin to see that landmark from the street with Apple Look Around.</p>
            <div class="map-layout">
                <div class="city-map" role="region" aria-label="Map of the landmarks in {e(city)}"></div>
                <div class="look-around-wrap">
                    <div class="look-around"></div>
                    <p class="look-around-status" aria-live="polite"></p>
                </div>
            </div>
        </div>
        <script type="application/json" id="map-data">{json.dumps(map_data, ensure_ascii=False).replace("</", "<\\/")}</script>
    </section>
""")

    # Arrival facts
    facts = []
    if known(details.get("airportName")):
        code = details.get("airportCode")
        code = f" ({e(code)})" if known(code) and code.strip() != details["airportName"].strip() else ""
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

    # Guided tour clip, when one was recorded for this city
    if city in TOUR_VIDEOS:
        name, height, stops = TOUR_VIDEOS[city]
        out.append(f"""
    <section class="tour" aria-labelledby="tour-title">
        <div class="container tour-layout">
            <div>
                <p class="kicker">Recorded in the app</p>
                <h2 id="tour-title" class="section-title">Fly the {e(city)} tour</h2>
                <p class="tour-text">Press play on the guided tour and Stamped! flies you over {e(city)} in photoreal 3D, past {e(stops)}, with a card and a Look Around preview at every stop.</p>
            </div>
            <div class="phone">
                <video src="../assets/videos/stamped/{name}.mp4" poster="../assets/videos/stamped/{name}-poster.jpg" width="492" height="{height}"
                       controls muted playsinline preload="none" aria-label="Stamped! guided tour of {e(city)} on iPhone"></video>
            </div>
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
                <li id="{e(l['id'])}"{' class="has-photo"' if l['id'] in photos else ''}>
                    {photo_figure(photos.get(l['id']), l['name'])}
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

    out.append(suggest_section(
        city, url, f"Know {city} well?",
        "Locals know their city best. Suggest a landmark we're missing or a fix to one we have. "
        "Every suggestion is checked against a source before it goes into the app.",
        ["Landmark", "Correction"]))

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
        scripts=('    <script src="map-token.js"></script>\n    <script src="map.js"></script>\n' if pins else "")
                + '    <script src="suggest.js" defer></script>\n',
        app_store=APP_STORE,
        cta_title=f"Stamp all {n} in Stamped!" if n > 1 else "Stamp it in Stamped!",
        cta_text=f"Fly through {e(city)} in photoreal 3D, take its 10-question quiz, plan your days and earn a passport stamp at every landmark. Free on iPhone and iPad."))
    return "".join(out)


CONTINENT_INTROS = {
    "Europe": "From Roman temples to glass towers, Europe packs two thousand years of architecture into cities you can explore on foot.",
    "Asia": "Ancient temples, imperial palaces and some of the tallest towers on Earth, from the shrines of Kyoto to the skyline of Dubai.",
    "North America": "Art Deco skyscrapers, Prairie houses and bold new museums, from Havana to Honolulu.",
    "South America": "Modernist capitals, colonial churches and concrete landmarks, from Brasília to Cartagena.",
    "Africa": "The pyramids of Giza, Moroccan medinas and striking new museums, from Cairo to Cape Town.",
    "Oceania": "Harbor icons and modern landmarks, from the Sydney Opera House to the lakeside town of Queenstown.",
}


def continent_page(continent, cities, registry, details, photos):
    """One page per continent: every city in it, with a photo, nickname and landmark count."""
    s_cont = slug(continent)
    url = f"{SITE}/stamped-cities/{s_cont}.html"
    landmarks = [l for c in cities for l in registry[c]]
    countries = sorted({PLACES[c][0] for c in cities})
    dated = [(year_sort(l["yearBuilt"]), l) for l in landmarks if year_sort(l["yearBuilt"]) is not None]
    oldest = min(dated, key=lambda x: x[0])[1] if dated else None
    title = f"{continent} Architecture: {len(cities)} Cities, {len(landmarks):,} Landmarks | Stamped!"
    description = (f"Architecture guides to {len(cities)} cities in {continent}, from {cities[0]} to {cities[-1]}: "
                   f"{len(landmarks):,} landmarks with architects, build dates, styles and history, from the Stamped! app.")
    ld = [{"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Stamped!", "item": f"{SITE}/stamped-app.html"},
        {"@type": "ListItem", "position": 2, "name": "City guides", "item": f"{SITE}/stamped-cities/index.html"},
        {"@type": "ListItem", "position": 3, "name": continent, "item": url}]}]

    def city_photo(city):
        for l in registry[city]:
            if l["id"] in photos:
                return l, photos[l["id"]]
        return None, None

    # Hero mosaic: the first photo from the three cities with the most landmarks
    hero = [city_photo(c) for c in sorted(cities, key=lambda c: -len(registry[c]))]
    hero = [(l, ph) for l, ph in hero if l][:3]

    out = [HEAD.format(title=e(title), description=e(description), url=url, site=SITE,
                       jsonld=jsonld(ld), app_store=APP_STORE)]
    out.append(f"""
    <main id="main">
    <section class="hero">
        <div class="container">
            <nav class="crumbs" aria-label="Breadcrumb"><a href="index.html">City guides</a> <span aria-hidden="true">/</span> {e(continent)}</nav>
            <p class="kicker">Continent guide · Stamped!</p>
            <h1>{e(continent)}</h1>
            <p class="lead">{e(CONTINENT_INTROS.get(continent, ""))}</p>
            <ul class="stats">
                <li><strong>{len(cities)}</strong><span>Cities</span></li>
                <li><strong>{len(landmarks):,}</strong><span>Landmarks</span></li>
                <li><strong>{len(countries)}</strong><span>Countries</span></li>""")
    if oldest:
        out.append(f"""
                <li><strong>{e(year_label(oldest['yearBuilt']))}</strong><span>Oldest · {e(oldest['name'])}</span></li>""")
    out.append("""
            </ul>""")
    if hero:
        tiles = "".join(
            f'<li><a href="{slug(PLACES_BY_ID[l["id"]])}.html#{e(l["id"])}"><img src="{e(ph["src"])}" width="{ph["width"]}" height="{ph["height"]}" '
            f'alt="{e(l["name"])}" {"fetchpriority=\"high\"" if i == 0 else "loading=\"lazy\""} referrerpolicy="no-referrer" />'
            f'<span>{e(l["name"])} · {e(PLACES_BY_ID[l["id"]])}</span></a></li>'
            for i, (l, ph) in enumerate(hero))
        out.append(f"""
            <ul class="hero-photos count-{len(hero)}">{tiles}</ul>
            <p class="photo-note">{"; ".join(e(l["name"]) + ": " + e(credit_text(ph)) for l, ph in hero)}</p>""")
    out.append("""
        </div>
    </section>

    <section class="landmarks" aria-labelledby="cities-title">
        <div class="container">""")
    out.append(f"""
            <h2 id="cities-title" class="section-title">{len(cities)} cities in {e(continent)}</h2>
            <ul class="city-cards">""")
    for city in cities:
        l, ph = city_photo(city)
        img = (f'<img src="{e(ph["src"])}" width="{ph["width"]}" height="{ph["height"]}" alt="{e(l["name"])}, {e(city)}" '
               f'loading="lazy" decoding="async" referrerpolicy="no-referrer" />') if ph else '<span class="no-photo" aria-hidden="true"></span>'
        nick = details.get(city, {}).get("nickname")
        n = len(registry[city])
        out.append(f"""
                <li><a href="{slug(city)}.html">{img}<span class="city-card-text"><strong>{e(city)}</strong>{f"<em>{e(nick)}</em>" if known(nick) else ""}<small>{e(PLACES[city][0])} · {n} landmark{"s" if n != 1 else ""}</small>{f'<span class="card-credit">{e(credit_text(ph))}</span>' if ph else ""}</span></a></li>""")
    out.append("""
            </ul>
        </div>
    </section>
""")
    others = "".join(f'<li><a href="{slug(k)}.html">{e(k)}</a></li>' for k in CONTINENTS if k != continent)
    out.append(f"""
    <section class="more-cities" aria-labelledby="more-title">
        <div class="container">
            <h2 id="more-title" class="section-title">Other continents</h2>
            <ul class="city-chips">{others}</ul>
        </div>
    </section>
""")
    out.append(FOOT.format(scripts="", app_store=APP_STORE, cta_title=f"Fly through {continent} in 3D.",
                           cta_text=f"All {len(cities)} cities, {len(landmarks):,} landmarks and a passport stamp for every one you visit. Free on iPhone and iPad."))
    return "".join(out)


# Architects featured on stamped-app.html: name -> (match substrings, ASCII-folded and lowercased; one-line intro)
ARCHITECTS = {
    "Frank Lloyd Wright": (["frank lloyd wright"], "American architect (1867–1959) who pioneered the Prairie style and \"organic architecture\". He designed Fallingwater and the Guggenheim Museum in New York."),
    "Oscar Niemeyer": (["niemeyer"], "Brazilian modernist (1907–2012) known for sweeping concrete curves. He designed the major civic buildings of Brasília."),
    "Frank Gehry": (["gehry"], "Canadian-American architect, born in 1929, known for sculptural forms like the Guggenheim Bilbao and Walt Disney Concert Hall."),
    "I. M. Pei": (["i. m. pei", "i.m. pei", "im pei", "pei cobb", "pei partnership"], "Chinese-American modernist (1917–2019) behind the Louvre Pyramid and Hong Kong's Bank of China Tower."),
    "Zaha Hadid": (["zaha hadid"], "Iraqi-British architect (1950–2016) known for fluid, futuristic forms. In 2004 she became the first woman to win the Pritzker Prize."),
    "Herzog & de Meuron": (["herzog"], "Swiss firm founded in Basel by Jacques Herzog and Pierre de Meuron, known for Tate Modern in London and the National Stadium in Beijing."),
    "Mies van der Rohe": (["mies van der rohe"], "German-American modernist (1886–1969) and a master of steel and glass, remembered for the motto \"less is more\"."),
    "Renzo Piano": (["renzo piano"], "Italian architect, born in 1937, who co-designed the Centre Pompidou in Paris and designed the Shard in London."),
    "Jean Nouvel": (["jean nouvel"], "French architect, born in 1945, known for light-filtering designs like the Louvre Abu Dhabi. He won the Pritzker Prize in 2008."),
    "Santiago Calatrava": (["calatrava"], "Spanish architect and engineer, born in 1951, known for skeletal, bird-like structures like the Oculus in New York."),
    "Le Corbusier": (["le corbusier"], "Swiss-French pioneer of modern architecture (1887–1965). Seventeen of his works are listed together as a UNESCO World Heritage Site."),
    "Antoni Gaudí": (["gaudi"], "Catalan architect (1852–1926) and the master of Modernisme behind the Sagrada Família in Barcelona."),
    "Adrian Smith": (["adrian smith"], "American architect, born in 1944, who designed the Burj Khalifa while at Skidmore, Owings & Merrill. In 2006 he co-founded Adrian Smith + Gordon Gill Architecture in Chicago."),
}


def credit_text(photo):
    """Plain-text credit for photos inside links (a link can't hold another link)."""
    return f"Photo: {photo['author']}, {photo['license']}, {photo.get('site', 'Wikimedia Commons')}"


def fold(text):
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()


def architect_slug(name):
    return "architect-" + slug(name.replace("&", "and"))


def architect_page(name, intro, works, photos):
    """Every building by one architect in the app, linking to its city guide."""
    url = f"{SITE}/stamped-cities/{architect_slug(name)}.html"
    places = sorted({place for place, _ in works})
    title = f"{name}: {len(works)} Buildings to See | Stamped!"
    description = f"{len(works)} buildings by {name} in the Stamped! app, in {', '.join(places[:4])}{' and more' if len(places) > 4 else ''}. {intro}"
    ld = [{"@context": "https://schema.org", "@type": "Person", "name": name, "description": intro, "url": url}]
    out = [HEAD.format(title=e(title), description=e(description[:300]), url=url, site=SITE, jsonld=jsonld(ld), app_store=APP_STORE)]
    out.append(f"""
    <main id="main">
    <section class="hero">
        <div class="container">
            <nav class="crumbs" aria-label="Breadcrumb"><a href="../stamped-app.html">Stamped!</a> <span aria-hidden="true">/</span> Architects</nav>
            <p class="kicker">Architect · {len(works)} buildings in Stamped!</p>
            <h1>{e(name)}</h1>
            <p class="lead">{e(intro)}</p>
        </div>
    </section>

    <section class="landmarks" aria-labelledby="works-title">
        <div class="container">
            <h2 id="works-title" class="section-title">{len(works)} buildings in the app</h2>
            <ul class="city-cards">""")
    for place, l in works:
        ph = photos.get(l["id"])
        img = (f'<img src="{e(ph["src"])}" width="{ph["width"]}" height="{ph["height"]}" alt="{e(l["name"])}" '
               f'loading="lazy" decoding="async" referrerpolicy="no-referrer" />') if ph else '<span class="no-photo" aria-hidden="true"></span>'
        meta = " · ".join(x for x in [e(place), e(year_label(l["yearBuilt"])), e(l["buildingStyle"]) if known(l.get("buildingStyle")) else ""] if x)
        credit = f'<span class="card-credit">{e(credit_text(ph))}</span>' if ph else ""
        inner = f'{img}<span class="city-card-text"><strong>{e(l["name"])}</strong><small>{meta}</small>{credit}</span>'
        href = f'{slug(place)}.html#{e(l["id"])}' if place in PLACES else None
        out.append(f"""
                <li>{f'<a href="{href}">{inner}</a>' if href else f'<div class="card-static">{inner}</div>'}</li>""")
    others = "".join(f'<li><a href="{architect_slug(a)}.html">{e(a)}</a></li>' for a in ARCHITECTS if a != name)
    out.append(f"""
            </ul>
        </div>
    </section>

    <section class="more-cities" aria-labelledby="more-title">
        <div class="container">
            <h2 id="more-title" class="section-title">More architects</h2>
            <ul class="city-chips">{others}</ul>
        </div>
    </section>
""")
    out.append(FOOT.format(scripts="", app_store=APP_STORE, cta_title=f"Collect every {name} building.",
                           cta_text="Stamped! keeps track of whose buildings you've seen and shows your favorite architect. Free on iPhone and iPad."))
    return "".join(out)


# Proves to impact.com (the affiliate network SeatGeek and Ticketmaster use) that this site
# is ours. It's checked on the city guides homepage, which is the property registered there.
IMPACT_VERIFICATION = "    <meta name='impact-site-verification' value='49a266fc-7cfd-457d-a3ab-bb4d22fb638d'>"


def index_page(by_continent, counts):
    total = sum(counts.values())
    title = "City Guides: 140 Cities of Great Architecture | Stamped!"
    description = (f"Architecture guides to 140 cities on six continents, with {total:,} landmarks: "
                   "architects, build dates, styles and history, from the Stamped! app.")
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Stamped! city guides",
           "url": f"{SITE}/stamped-cities/index.html", "description": description}]
    head = HEAD.format(title=e(title), description=e(description), url=f"{SITE}/stamped-cities/index.html",
                       site=SITE, jsonld=jsonld(ld), app_store=APP_STORE)
    out = [head.replace("</head>", IMPACT_VERIFICATION + "\n</head>", 1)]
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
            <h2 id="{slug(continent)}" class="section-title"><a href="{slug(continent)}.html">{e(continent)}</a> <span>{len(cities)} cities</span></h2>
            <ul class="city-grid">{items}</ul>
        </div>
    </section>
""")
    out.append(FOOT.format(scripts="", app_store=APP_STORE, cta_title="Your passport is waiting.",
                           cta_text="Fly through all 140 cities in photoreal 3D and earn a stamp at every landmark you visit. Free on iPhone and iPad."))
    return "".join(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default=str(Path.home() / "Documents/Stamped-A-City-Passport"))
    args = parser.parse_args()
    resources = Path(args.app).expanduser() / "Stamped! A City Passport" / "Resources"
    registry = json.loads((resources / "BuildingRegistry.json").read_text(encoding="utf-8"))
    details = json.loads((resources / "CityDetails.json").read_text(encoding="utf-8"))
    photos_file = OUT / "photos.json"   # written by fetch_photos.py
    photos = json.loads(photos_file.read_text(encoding="utf-8")) if photos_file.exists() else {}

    cities = [c for c in registry if c in PLACES]
    skipped = [c for c in registry if c not in PLACES
               and not re.search(r"Universit|College|Institute|Leuven|Sorbonne|Virginia Tech", c)]
    if skipped:
        raise SystemExit(f"Add these cities to PLACES: {skipped}")

    PLACES_BY_ID.update({l["id"]: c for c in cities for l in registry[c]})
    by_continent = {k: sorted((c for c in cities if PLACES[c][1] == k), key=slug) for k in CONTINENTS}
    counts = {c: len(registry[c]) for c in cities}

    OUT.mkdir(exist_ok=True)
    for city in cities:
        siblings = [c for c in by_continent[PLACES[city][1]] if c != city]
        page = city_page(city, registry[city], details.get(city, {}), siblings, photos)
        (OUT / f"{slug(city)}.html").write_text(versioned(page), encoding="utf-8")
    (OUT / "index.html").write_text(versioned(index_page(by_continent, counts)), encoding="utf-8")
    for name, (patterns, intro) in ARCHITECTS.items():
        works = [(place, l) for place, items in registry.items() for l in items
                 if any(pattern in fold(l["architect"]) for pattern in patterns)]
        (OUT / f"{architect_slug(name)}.html").write_text(versioned(architect_page(name, intro, works, photos)), encoding="utf-8")
    for continent in CONTINENTS:
        page = continent_page(continent, by_continent[continent], registry, details, photos)
        (OUT / f"{slug(continent)}.html").write_text(versioned(page), encoding="utf-8")
    print(f"wrote {len(cities)} city pages and index.html to {OUT.relative_to(ROOT)}/ "
          f"({sum(counts.values()):,} landmarks)")
    for k in CONTINENTS:
        print(f"  {k}: {len(by_continent[k])}")


if __name__ == "__main__":
    main()
