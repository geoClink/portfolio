#!/usr/bin/env python3
"""Build the Stamped! school pages from the app's own data.

    python3 tools/stamped/build_campus_pages.py [--app ~/Documents/Stamped-A-City-Passport]

Reads the app's Resources/BuildingRegistry.json (campus buildings), Resources/CampusTraditions.json
and tools/campus-data/campuses/*.json (conference, school colors, nickname, airport) and writes one
page per campus to stamped-colleges/<slug>.html. It also rewrites the school list on
stamped-colleges.html, so every name links to its page and the counts match the app, and refreshes
the school pages in sitemap.xml. Re-run after the app's campus data changes.

Photos come from stamped-colleges/photos.json, written by `fetch_photos.py --campuses`, and the
History card from stamped-colleges/history.json, written by `fetch_campus_history.py`. The other
campus cards (Student life, Game day, Campus events) are in campus_cards.py.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_city_pages import (APP_STORE, FOOT, HEAD, SITE, ArchitectLinks, architect_html, e, height_label,
                              jsonld, known, photo_figure, slug, suggest_section, versioned, year_label, year_sort)
from campus_cards import CampusData, campus_cards

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "stamped-colleges"
LANDING = ROOT / "stamped-colleges.html"
SITEMAP = ROOT / "sitemap.xml"

# Groups in the order the landing page shows them. US campuses without a conference are
# "More U.S. schools"; everything outside the US is "Around the world".
CONFERENCES = {"bigTen": "Big Ten", "sec": "SEC", "acc": "ACC", "big12": "Big 12", "ivyLeague": "Ivy League"}
GROUPS = [*CONFERENCES.values(), "More U.S. schools", "Around the world"]

# CityLocation.Country cases used by campuses -> the country shown on the page
COUNTRIES = {
    "unitedStates": "United States", "canada": "Canada", "mexico": "Mexico",
    "england": "England", "scotland": "Scotland", "ireland": "Ireland", "belgium": "Belgium",
    "finland": "Finland", "france": "France", "italy": "Italy", "sweden": "Sweden",
    "newSouthWales": "Australia", "victoria": "Australia",
}

# The city guide header and footer, pointed at the college pages instead
CAMPUS_HEAD = HEAD.replace('href="cities.css"', 'href="../stamped-cities/cities.css" />\n    <link rel="stylesheet" href="campus.css"') \
                  .replace('<a href="index.html">City guides</a>', '<a href="../stamped-colleges.html#schools">All schools</a>') \
                  .replace('href="../stamped-app.html">', 'href="../stamped-colleges.html">', 1)
CAMPUS_FOOT = FOOT.replace('<a href="index.html">All city guides</a>', '<a href="../stamped-colleges.html#schools">All schools</a>') \
                  .replace("<p>Landmark details come from the Stamped! app.",
                           "<p>Stamped! is not affiliated with or endorsed by any university. Building details come from the Stamped! app.")
assert CAMPUS_HEAD.count("campus.css") == 1 and "All schools" in CAMPUS_HEAD and "All schools" in CAMPUS_FOOT


def group_of(campus):
    if campus["country"] != "unitedStates":
        return "Around the world"
    return CONFERENCES.get(campus.get("conference"), "More U.S. schools")


def sort_name(name):
    """Sorted the way the landing page lists schools (plain alphabetical)."""
    return name.lower()


def campus_page(campus, buildings, traditions, siblings, photos, data, architect_links=None):
    name = campus["name"]
    details = campus.get("details", {})
    group = group_of(campus)
    country = COUNTRIES[campus["country"]]
    s = slug(name)
    url = f"{SITE}/stamped-colleges/{s}.html"
    n = len(buildings)
    t = len(traditions)
    names = [b["name"] for b in buildings]
    title = f"{name} Campus Visit Guide: Architecture and Traditions | Stamped!"
    description = (f"A campus visit guide to {name}: {', '.join(names[:3])}" + (" and more" if n > 3 else "")
                   + (f", plus {t} campus tradition{'s' if t != 1 else ''} to try" if t else "")
                   + ". Architects, build dates and history, from the Stamped! app.")

    dated = [(year_sort(b["yearBuilt"]), b) for b in buildings if year_sort(b["yearBuilt"]) is not None]
    oldest = min(dated, key=lambda x: x[0])[1] if dated else None
    newest = max(dated, key=lambda x: x[0])[1] if dated else None

    ld = [
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "College visits", "item": f"{SITE}/stamped-colleges.html"},
            {"@type": "ListItem", "position": 2, "name": name, "item": url}]},
        {"@context": "https://schema.org", "@type": "CollegeOrUniversity", "name": name,
         **({"sameAs": f"https://en.wikipedia.org/wiki/{campus['wiki'].replace(' ', '_')}"} if campus.get("wiki") else {})},
        {"@context": "https://schema.org", "@type": "ItemList", "name": f"Buildings to see at {name}",
         "numberOfItems": n, "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": {
                "@type": "LandmarksOrHistoricalBuildings", "name": b["name"],
                **({"address": b["address"]} if known(b.get("address")) else {})}}
            for i, b in enumerate(buildings)]},
    ]

    colors = "".join(f'<span style="background:{e(c)}"></span>' for c in campus.get("colors", []))
    head = CAMPUS_HEAD.format(title=e(title), description=e(description), url=url, site=SITE,
                              jsonld=jsonld(ld), app_store=APP_STORE)
    # Shared links preview the school's own photo instead of the app's
    share = next((photos[b["id"]] for b in buildings if b["id"] in photos), None)
    if share:
        head = head.replace(f'content="{SITE}/assets/images/stamped/app/og-image.png"', f'content="{e(share["src"])}"')
    out = [head]
    out.append(f"""
    <main id="main">
    <section class="hero">
        <div class="container">
            <nav class="crumbs" aria-label="Breadcrumb"><a href="../stamped-colleges.html">College visits</a> <span aria-hidden="true">/</span> <a href="../stamped-colleges.html#schools">{e(group)}</a> <span aria-hidden="true">/</span> {e(country)}</nav>
            <p class="kicker"><span class="school-colors" aria-hidden="true">{colors}</span>{e(details.get('nickname') or 'Campus guide')}</p>
            <h1>{e(name)}</h1>
            <p class="lead">{e(details.get('funFact', ''))}</p>
            <ul class="stats">
                <li><strong>{n}</strong><span>Buildings</span></li>""")
    if t:
        out.append(f"""
                <li><strong>{t}</strong><span>Tradition{'s' if t != 1 else ''}</span></li>""")
    if oldest:
        out.append(f"""
                <li><strong>{e(year_label(oldest['yearBuilt']))}</strong><span>Oldest · {e(oldest['name'])}</span></li>""")
    if newest and newest is not oldest:
        out.append(f"""
                <li><strong>{e(year_label(newest['yearBuilt']))}</strong><span>Newest · {e(newest['name'])}</span></li>""")
    out.append("""
            </ul>""")
    hero_photos = [b for b in buildings if b["id"] in photos][:3]
    if hero_photos:
        tiles = "".join(
            f'<li><a href="#{e(b["id"])}"><img src="{e(photos[b["id"]]["src"])}" width="{photos[b["id"]]["width"]}" '
            f'height="{photos[b["id"]]["height"]}" alt="{e(b["name"])}" {"fetchpriority=\"high\"" if i == 0 else "loading=\"lazy\""} '
            f'referrerpolicy="no-referrer" /><span>{e(b["name"])}</span></a></li>'
            for i, b in enumerate(hero_photos))
        out.append(f"""
            <ul class="hero-photos count-{len(hero_photos)}">{tiles}</ul>""")
    out.append("""
        </div>
    </section>
""")

    # Live Apple Map with Look Around (filled in by map.js; stays hidden without a token or if MapKit fails)
    pins = [b for b in buildings if isinstance(b.get("latitude"), (int, float)) and isinstance(b.get("longitude"), (int, float))]
    if pins:
        map_data = {"landmarks": [
            {"id": b["id"], "name": b["name"], "lat": b["latitude"], "lng": b["longitude"],
             "subtitle": " · ".join(x for x in [year_label(b["yearBuilt"]), str(b["architect"]) if known(b.get("architect")) else ""] if x)}
            for b in pins]}
        out.append(f"""
    <section class="city-map-section" data-city-map hidden aria-labelledby="map-title">
        <div class="container">
            <h2 id="map-title" class="section-title">Campus map and Look Around</h2>
            <p class="map-hint">Tap a numbered pin to see that building from the street with Apple Look Around.</p>
            <div class="map-layout">
                <div class="city-map" role="region" aria-label="Map of the buildings at {e(name)}"></div>
                <div class="look-around-wrap">
                    <div class="look-around"></div>
                    <p class="look-around-status" aria-live="polite"></p>
                </div>
            </div>
        </div>
        <script type="application/json" id="map-data">{json.dumps(map_data, ensure_ascii=False).replace("</", "<\\/")}</script>
    </section>
""")

    # Getting there
    facts = []
    if known(details.get("airportName")):
        code = details.get("airportCode")
        code = f" ({e(code)})" if known(code) and code.strip() != details["airportName"].strip() else ""
        facts.append(("Fly into", e(details["airportName"]) + code, details.get("airportInfo")))
    if known(details.get("transportation")):
        facts.append(("Getting around", e(details["transportation"]), details.get("transportationFact")))
    if known(details.get("languageInfo")):
        facts.append(("Colors and teams", "", details.get("languageInfo")))
    if facts:
        out.append("""
    <section class="facts" aria-labelledby="facts-title">
        <div class="container">
            <h2 id="facts-title" class="section-title">Planning the visit</h2>
            <ul class="fact-grid">""")
        for label, value, more in facts:
            value_html = f"<strong>{value}</strong>" if value else ""
            more_html = f"<p>{e(more)}</p>" if known(more) else ""
            out.append(f"""
                <li><span class="fact-label">{label}</span>{value_html}{more_html}</li>""")
        out.append("""
            </ul>
        </div>
    </section>
""")

    # Buildings
    out.append(f"""
    <section class="landmarks" aria-labelledby="landmarks-title">
        <div class="container">
            <h2 id="landmarks-title" class="section-title">{n} buildings to stamp</h2>
            <ol class="landmark-list">""")
    for i, b in enumerate(buildings, 1):
        meta = [("Built", year_label(b["yearBuilt"]))]
        if known(b.get("architect")):
            meta.append(("Architect", b["architect"]))
        if known(b.get("buildingStyle")):
            meta.append(("Style", b["buildingStyle"]))
        h = height_label(b.get("height"))
        if h:
            meta.append(("Height", h))
        if isinstance(b.get("numberOfStories"), int) and b["numberOfStories"] > 0:
            meta.append(("Stories", f"{b['numberOfStories']:,}"))
        if known(b.get("newUse")):
            meta.append(("Today", b["newUse"]))
        # Architect names with a page link to it (architect pages live with the city guides)
        meta_html = "".join(
            f"<div><dt>{e(k)}</dt><dd>{architect_html(b, architect_links, '../stamped-cities/') if k == 'Architect' and architect_links else e(v)}</dd></div>"
            for k, v in meta)
        address = f'<p class="address">{e(b["address"])}</p>' if known(b.get("address")) else ""
        out.append(f"""
                <li id="{e(b['id'])}"{' class="has-photo"' if b['id'] in photos else ''}>
                    {photo_figure(photos.get(b['id']), b['name'])}
                    <span class="landmark-number" aria-hidden="true">{i:02d}</span>
                    <h3>{e(b['name'])}</h3>
                    {address}
                    <p>{e(b['description'])}</p>
                    <dl>{meta_html}</dl>
                </li>""")
    out.append("""
            </ol>
        </div>
    </section>
""")

    # Traditions, as the checklist the app shows
    if traditions:
        items = "".join(f"""
                <li><h3>{e(tr['name'])}</h3><p>{e(tr['description'])}</p></li>""" for tr in traditions)
        out.append(f"""
    <section class="traditions" aria-labelledby="traditions-title">
        <div class="container">
            <h2 id="traditions-title" class="section-title">{t} tradition{'s' if t != 1 else ''} to check off</h2>
            <p class="map-hint">Stamped! keeps these as a checklist, so you can tick each one off on the visit.</p>
            <ul class="tradition-list">{items}
            </ul>
        </div>
    </section>
""")

    # The app's campus cards: History, Student life, Game day, Campus events
    cards, live_events = campus_cards(campus, data)
    out.append(cards)

    out.append(suggest_section(
        name, url, f"Know {name} well?",
        "Students and alumni know the traditions best. Suggest one we're missing, a building worth a stamp, "
        "a fix, or your own photo of a building. Every suggestion is checked before it goes into the app.",
        ["Tradition", "Building", "Correction", "Photo"]))

    if siblings:
        links = "".join(f'<li><a href="{slug(c)}.html">{e(c)}</a></li>' for c in siblings)
        heading = "More schools around the world" if group == "Around the world" else (
            "More U.S. schools" if group == "More U.S. schools" else f"More {group} schools")
        out.append(f"""
    <section class="more-cities" aria-labelledby="more-title">
        <div class="container">
            <h2 id="more-title" class="section-title">{e(heading)}</h2>
            <ul class="city-chips">{links}</ul>
        </div>
    </section>
""")

    out.append(CAMPUS_FOOT.format(
        scripts=('    <script src="../stamped-cities/map-token.js"></script>\n    <script src="../stamped-cities/map.js"></script>\n' if pins else "")
                + '    <script src="../stamped-cities/suggest.js" defer></script>\n'
                + ('    <script src="campus-events.js" defer></script>\n' if live_events else ""),
        app_store=APP_STORE,
        cta_title=f"Stamp all {n} on your visit.",
        cta_text=f"Tour {e(name)} in 3D before you go, add it to a college road trip and earn a passport stamp at every building. Free on iPhone and iPad."))
    return "".join(out)


def school_list_html(groups):
    """The <li class="school-group"> items for the landing page, each name linking to its page."""
    out = []
    for group in GROUPS:
        names = groups[group]
        links = "".join(f'<li><a href="stamped-colleges/{slug(c)}.html">{e(c)}</a></li>' for c in names)
        out.append(f"""
                    <li class="school-group">
                        <h3>{e(group)}<span>{len(names)}</span></h3>
                        <ul>{links}</ul>
                    </li>""")
    return "".join(out) + "\n                "


def update_landing(groups, total):
    page = LANDING.read_text(encoding="utf-8")
    start = page.index('<ul class="school-groups reveal" role="list">') + len('<ul class="school-groups reveal" role="list">')
    end = page.index("</ul>\n            </div>\n        </section>", start)
    page = page[:start] + school_list_html(groups) + page[end:]
    page = re.sub(r"Every school · \d+ campuses", f"Every school · {total} campuses", page)
    LANDING.write_text(page, encoding="utf-8")


def update_sitemap(slugs):
    xml = SITEMAP.read_text(encoding="utf-8")
    xml = re.sub(r"  <url>\n    <loc>[^<]*/stamped-colleges/[^<]*</loc>\n(?:    <[^\n]*\n)*?  </url>\n", "", xml)
    anchor = re.search(r"  <url>\n    <loc>[^<]*/stamped-colleges\.html</loc>\n(?:    <[^\n]*\n)*?  </url>\n", xml)
    today = date.today().isoformat()
    entries = "".join(f"""  <url>
    <loc>{SITE}/stamped-colleges/{s}.html</loc>
    <lastmod>{today}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
""" for s in slugs)
    xml = xml[:anchor.end()] + entries + xml[anchor.end():]
    SITEMAP.write_text(xml, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default=str(Path.home() / "Documents/Stamped-A-City-Passport"))
    args = parser.parse_args()
    app = Path(args.app).expanduser()
    resources = app / "Stamped! A City Passport" / "Resources"
    registry = json.loads((resources / "BuildingRegistry.json").read_text(encoding="utf-8"))
    traditions = json.loads((resources / "CampusTraditions.json").read_text(encoding="utf-8"))
    campuses = [c for f in sorted((app / "tools" / "campus-data" / "campuses").glob("*.json"))
                for c in json.loads(f.read_text(encoding="utf-8"))]
    photos_file = OUT / "photos.json"   # written by fetch_photos.py --campuses
    photos = json.loads(photos_file.read_text(encoding="utf-8")) if photos_file.exists() else {}
    data = CampusData(app, OUT)   # History, Student life, Game day and event feeds for the cards

    missing = [c["name"] for c in campuses if c["name"] not in registry]
    if missing:
        raise SystemExit(f"Not in BuildingRegistry.json (rebuild the app's campus data first): {missing}")
    unknown = sorted({c["country"] for c in campuses} - COUNTRIES.keys())
    if unknown:
        raise SystemExit(f"Add these countries to COUNTRIES: {unknown}")

    groups = {g: sorted((c["name"] for c in campuses if group_of(c) == g), key=sort_name) for g in GROUPS}
    OUT.mkdir(exist_ok=True)
    architect_links = ArchitectLinks(registry)
    for campus in campuses:
        name = campus["name"]
        siblings = [c for c in groups[group_of(campus)] if c != name]
        page = campus_page(campus, registry[name], traditions.get(name, []), siblings, photos, data, architect_links)
        (OUT / f"{slug(name)}.html").write_text(versioned(page, OUT, "../stamped-cities/"), encoding="utf-8")
    update_landing(groups, len(campuses))
    update_sitemap(sorted(slug(c["name"]) for c in campuses))
    with_photos = sum(1 for c in campuses if any(b["id"] in photos for b in registry[c["name"]]))
    print(f"wrote {len(campuses)} school pages to {OUT.relative_to(ROOT)}/ ({with_photos} with photos), "
          f"updated {LANDING.name} and {SITEMAP.name}")
    for g in GROUPS:
        print(f"  {g}: {len(groups[g])}")


if __name__ == "__main__":
    main()
