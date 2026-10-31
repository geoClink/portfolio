"""The campus cards the app shows, as sections of a Stamped! school page: History, Student Life,
Game Day and Campus Events. build_campus_pages.py calls `campus_cards()` for each school.

Data, all from the app repo or written next to the pages:
- History: stamped-colleges/history.json (fetch_campus_history.py, the app's Wikipedia/Wikidata rule)
- Student Life: Resources/CampusStudentLife.json
- Game Day: Resources/CampusAthletics.json (athletics site, stadium photos with credit, NCAA titles).
  Upcoming home games need the ticket sellers' keys, which can't go in a public page, so the site
  links to the athletics site for the schedule and live scores instead.
- Campus Events: Models/CampusEventFeeds.swift. Localist calendars allow any site to read them, so
  campus-events.js loads the next few weeks live in the browser; other feeds get a link.
"""
import json
import re
from pathlib import Path

from build_city_pages import e

# The app's Student Life headings (CampusStudentLife.swift), in the app's order
LIFE_HEADINGS = [("housing", "Where Students Live"), ("union", "Student Union"), ("study", "Study Spots"),
                 ("dining", "Dining Halls"), ("hangout", "Hangouts")]


class CampusData:
    """Everything the cards need, loaded once."""

    def __init__(self, app: Path, out: Path):
        resources = app / "Stamped! A City Passport" / "Resources"
        self.history = _load(out / "history.json")
        self.student_life = _load(resources / "CampusStudentLife.json")
        self.athletics = _load(resources / "CampusAthletics.json").get("campuses", {})
        self.feeds = _event_feeds(app / "Stamped! A City Passport" / "Models" / "CampusEventFeeds.swift")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _event_feeds(swift: Path) -> dict:
    """enumCase -> ("localist", host, name) or ("ical", calendar page, name), read from the app's Swift file."""
    text = swift.read_text(encoding="utf-8") if swift.exists() else ""
    feeds = {}
    for case, host, name in re.findall(
            r'\.(\w+):\s*CampusEventFeed\(source: \.localist\(host: "([^"]+)"\), calendarName: "([^"]+)"\)', text):
        feeds[case] = ("localist", host, name)
    for case, url, name in re.findall(
            r'\.(\w+): CampusEventFeed\(\s*source: \.ical\(url: URL\(string: "([^"]+)"\)!\),\s*calendarName: "([^"]+)"', text):
        # LibCal's subscribe link -> its calendar page, which people can read
        page = re.sub(r"/ical_subscribe\.php\?src=p&cid=(\d+).*", r"/calendar?cid=\1", url)
        feeds[case] = ("ical", page, name)
    return feeds


def _section(key: str, title: str, body: str, extra_class: str = "") -> str:
    return f"""
    <section class="campus-card {key}{(' ' + extra_class) if extra_class else ''}" aria-labelledby="{key}-title">
        <div class="container">
            <h2 id="{key}-title" class="section-title">{title}</h2>{body}
        </div>
    </section>
"""


def history_card(name: str, data: CampusData) -> str:
    history = data.history.get(name)
    if not history or not history.get("summary"):
        return ""
    year = (f'\n            <p class="founded">Founded {history["foundedYear"]}</p>'
            if history.get("foundedYear") else "")
    links = []
    if history.get("website"):
        # The school's own site (Wikidata P856, checked to load when fetched)
        links.append(f'<a href="{e(history["website"])}" rel="noopener">Official website <span aria-hidden="true">↗</span></a>')
    if history.get("url"):
        links.append(f'<a href="{e(history["url"])}" rel="noopener">Read more on Wikipedia <span aria-hidden="true">↗</span></a>')
    link = f'\n            <p class="card-link">{" · ".join(links)}</p>' if links else ""
    return _section("history", "History", f"""{year}
            <p class="source-note">From Wikipedia</p>
            <p class="history-text">{e(history["summary"])}</p>{link}""")


def student_life_card(name: str, data: CampusData) -> str:
    places = data.student_life.get(name) or []
    if not places:
        return ""
    groups = []
    for category, heading in LIFE_HEADINGS:
        items = [p for p in places if p.get("category") == category]
        if not items:
            continue
        lis = "".join(
            f'\n                    <li><h4>{e(p["name"])}</h4><p>{e(p["description"])}</p>'
            f'<a class="map-link" href="https://maps.apple.com/?ll={p["latitude"]},{p["longitude"]}&amp;q={e(p["name"])}" '
            f'rel="noopener">Open in Maps</a></li>' for p in items)
        groups.append(f"""
            <h3 class="life-heading">{heading}</h3>
            <ul class="life-list">{lis}
            </ul>""")
    return _section("student-life", "Student life", "".join(groups))


def game_day_card(name: str, data: CampusData) -> str:
    athletics = data.athletics.get(name)
    if not athletics:
        return ""
    parts = []
    photos = [v for v in athletics.get("venues") or [] if v.get("photo")]
    if photos:
        figures = "".join(f"""
                <figure>
                    <img src="{e(v['photo']['imageURL'])}" alt="{e(v['name'])}" loading="lazy" />
                    <figcaption><strong>{e(v['name'])}</strong>
                        <a href="{e(v['photo']['filePageURL'])}" rel="noopener">Photo: {e(v['photo']['author'])}, {e(v['photo']['license'])}</a></figcaption>
                </figure>""" for v in photos)
        parts.append(f"""
            <div class="venue-photos">{figures}
            </div>""")
    championships = athletics.get("championships")
    if championships and championships.get("titles"):
        total = sum(len(t["years"]) for t in championships["titles"])
        rows = []
        for title in championships["titles"]:
            shared = set(title.get("sharedYears") or [])
            years = ", ".join(f"{y} (shared)" if y in shared else str(y) for y in title["years"])
            rows.append(f'\n                <li><strong>{e(title["sport"])}</strong><span>{years}</span></li>')
        parts.append(f"""
            <h3 class="titles-heading">NCAA team championships <span class="count">{total}</span></h3>
            <ul class="title-list">{''.join(rows)}
            </ul>
            <p class="source-note"><a href="{e(championships['sourceURL'])}" rel="noopener">Source: {e(championships['source'])}</a></p>""")
    if athletics.get("athleticsURL"):
        parts.append(f"""
            <p class="card-link"><a href="{e(athletics['athleticsURL'])}" rel="noopener">Schedule and live scores <span aria-hidden="true">↗</span></a></p>""")
    return _section("game-day", "Game day", "".join(parts)) if parts else ""


def events_card(campus: dict, data: CampusData) -> str:
    feed = data.feeds.get(campus.get("enumCase"))
    if not feed:
        return ""
    kind, where, calendar = feed
    if kind == "localist":
        # Filled in by campus-events.js; stays hidden if the calendar can't be reached or has nothing
        return f"""
    <section class="campus-card campus-events" aria-labelledby="campus-events-title" data-localist="{e(where)}" hidden>
        <div class="container">
            <h2 id="campus-events-title" class="section-title">Campus events</h2>
            <ul class="event-list" aria-live="polite"></ul>
            <p class="source-note">From the <a href="https://{e(where)}" rel="noopener">{e(calendar)} calendar</a></p>
        </div>
    </section>
"""
    return _section("campus-events", "Campus events", f"""
            <p class="card-link"><a href="{e(where)}" rel="noopener">See what's on in the {e(calendar)} calendar <span aria-hidden="true">↗</span></a></p>""")


def campus_cards(campus: dict, data: CampusData) -> tuple[str, bool]:
    """The cards for one school, and whether the page needs campus-events.js."""
    name = campus["name"]
    events = events_card(campus, data)
    html = history_card(name, data) + student_life_card(name, data) + game_day_card(name, data) + events
    return html, "data-localist=" in events
