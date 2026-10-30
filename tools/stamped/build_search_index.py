#!/usr/bin/env python3
"""Write the search index for the Stamped! city guides and school pages.

    python3 tools/stamped/build_search_index.py [--app ~/Documents/Stamped-A-City-Passport]

One compact file, stamped-cities/search-index.json, lists every continent, city, school,
architect page and landmark with a link to its page. stamped-cities/search.js loads it the first
time a visitor uses a search box and searches it in the browser, so no outside service sees what
people type. Run it after build_city_pages.py and build_campus_pages.py, since it only lists
pages that exist.

Each item is [type, name, detail, url, extra words]:
    type   "continent", "city", "school", "architect" or "landmark" (see TYPES)
    detail the grey line under the name ("France · 26 landmarks")
    url    from the site root ("stamped-cities/paris.html#paris-eiffel-tower")
    extra  more words that should find it but aren't shown (style, aliases), or ""
"""
import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_city_pages import CONTINENTS, OUT as CITIES_OUT, PLACES, known, slug, year_label
from build_campus_pages import COUNTRIES, OUT as COLLEGES_OUT, group_of

INDEX = CITIES_OUT / "search-index.json"
# Hand-written pages with a search box: their links to search.js and search.css get ?v=<hash>
# here (the generated pages get theirs from quiz_search.py)
HAND_WRITTEN = [CITIES_OUT.parent / "stamped-colleges.html"]
TYPES = ["continent", "city", "school", "architect", "landmark"]


def plural(count: int, word: str, words: str = "") -> str:
    """"1 city", "2 cities": `words` is the plural when it isn't just word + "s"."""
    return f"{count} {word if count == 1 else (words or word + 's')}"


def architect_pages() -> list[list]:
    """Every architect page the city builder wrote, read back from the page itself."""
    items = []
    for page in sorted(CITIES_OUT.glob("architect-*.html")):
        text = page.read_text(encoding="utf-8")
        name = re.search(r"<h1>(.*?)</h1>", text)
        count = re.search(r"Architect · (\d+) buildings?", text)
        if name:
            detail = f"Architect · {plural(int(count.group(1)), 'building')}" if count else "Architect"
            items.append(["architect", html.unescape(name.group(1)), detail, f"stamped-cities/{page.name}", ""])
    return items


def stamp_hand_written_pages() -> None:
    """Point the hand-written pages at the current search.js and search.css, so browsers reload them."""
    for page in HAND_WRITTEN:
        text = page.read_text(encoding="utf-8")
        for name in ("search.js", "search.css"):
            stamp = hashlib.sha1((CITIES_OUT / name).read_bytes()).hexdigest()[:8]
            text = re.sub(rf'stamped-cities/{re.escape(name)}\?v=\w+', f"stamped-cities/{name}?v={stamp}", text)
        page.write_text(text, encoding="utf-8")


def landmark_item(landmark: dict, place: str, url: str) -> list:
    detail = " · ".join(part for part in [
        place,
        year_label(landmark["yearBuilt"]) if landmark.get("yearBuilt") else "",
        str(landmark["architect"]).strip() if known(landmark.get("architect")) else "",
    ] if part)
    extra = str(landmark["buildingStyle"]).strip() if known(landmark.get("buildingStyle")) else ""
    return ["landmark", landmark["name"], detail, f"{url}#{landmark['id']}", extra]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default=str(Path.home() / "Documents/Stamped-A-City-Passport"))
    args = parser.parse_args()
    app = Path(args.app).expanduser()
    resources = app / "Stamped! A City Passport" / "Resources"
    registry = json.loads((resources / "BuildingRegistry.json").read_text(encoding="utf-8"))
    details = json.loads((resources / "CityDetails.json").read_text(encoding="utf-8"))
    campuses = [campus for file in sorted((app / "tools" / "campus-data" / "campuses").glob("*.json"))
                for campus in json.loads(file.read_text(encoding="utf-8"))]

    # Only places with a page: a new city in the app has none until the city builder knows it
    cities = sorted((c for c in registry if c in PLACES and (CITIES_OUT / f"{slug(c)}.html").exists()), key=slug)
    schools = sorted((c for c in campuses if c["name"] in registry and (COLLEGES_OUT / f"{slug(c['name'])}.html").exists()),
                     key=lambda c: c["name"].lower())

    items = []
    for continent in CONTINENTS:
        count = sum(1 for c in cities if PLACES[c][1] == continent)
        if (CITIES_OUT / f"{slug(continent)}.html").exists():
            items.append(["continent", continent, f"Continent · {plural(count, 'city', 'cities')}",
                          f"stamped-cities/{slug(continent)}.html", ""])
    for city in cities:
        country = PLACES[city][0]
        nickname = details.get(city, {}).get("nickname")
        items.append(["city", city, f"{country} · {plural(len(registry[city]), 'landmark')}",
                      f"stamped-cities/{slug(city)}.html", nickname if known(nickname) else ""])
    for campus in schools:
        name = campus["name"]
        nickname = campus.get("details", {}).get("nickname")
        extra = " ".join([*campus.get("aliases", []), nickname if known(nickname) else ""]).strip()
        items.append(["school", name, f"{group_of(campus)} · {COUNTRIES[campus['country']]}",
                      f"stamped-colleges/{slug(name)}.html", extra])
    items += architect_pages()
    for city in cities:
        items += [landmark_item(l, city, f"stamped-cities/{slug(city)}.html") for l in registry[city]]
    for campus in schools:
        name = campus["name"]
        items += [landmark_item(l, name, f"stamped-colleges/{slug(name)}.html") for l in registry[name]]

    INDEX.write_text(json.dumps({"items": items}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    stamp_hand_written_pages()
    counts = {t: sum(1 for item in items if item[0] == t) for t in TYPES}
    print(f"wrote {INDEX.relative_to(CITIES_OUT.parent)} ({INDEX.stat().st_size // 1024} KB): "
          + ", ".join(plural(n, t, "cities" if t == "city" else "") for t, n in counts.items()))


if __name__ == "__main__":
    main()
