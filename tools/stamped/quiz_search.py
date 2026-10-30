"""Adds the architecture quiz and the site search to the generated Stamped! pages.

build_city_pages.versioned() calls `decorate()` on every page it writes, for the city guides and
the school pages, so this is the only hook in the page builders. It adds:

- every page: search.css and search.js, which put a Search button in the header
- the city guides index: a search box under the intro
- city and school pages: a quiz section before "Know this place well?", and quiz.js

The quiz questions come from stamped-cities/quiz/<slug>.json and stamped-colleges/quiz/<slug>.json
(build_quiz_data.py) and the search from stamped-cities/search-index.json (build_search_index.py).
Both scripts stay hidden until their data loads, so a page built before the data exists still works.
"""
import hashlib
import html
import re
from pathlib import Path

CITIES = Path(__file__).resolve().parents[2] / "stamped-cities"
# The same App Store link as APP_STORE in build_city_pages.py
APP_STORE = "https://apps.apple.com/us/app/stamped-a-city-passport/id6759680336"


def asset(name: str, prefix: str) -> str:
    """Link to a shared file in stamped-cities/, with ?v=<content hash> so browsers get new copies."""
    path = CITIES / name
    stamp = hashlib.sha1(path.read_bytes()).hexdigest()[:8] if path.exists() else "0"
    return f"{prefix}{name}?v={stamp}"


def quiz_section(place: str, page_slug: str) -> str:
    name = html.escape(place, quote=True)
    return f"""
    <section class="quiz" data-quiz="quiz/{page_slug}.json" data-app-store="{APP_STORE}" hidden aria-labelledby="quiz-title">
        <div class="container">
            <p class="kicker">The app's quiz · 10 questions</p>
            <h2 id="quiz-title" class="section-title">How well do you know {name}?</h2>
            <p class="map-hint">The same quiz as in Stamped!: name the landmark, its architect, its style or the year it was finished. Every round is different.</p>
            <div class="quiz-card"></div>
        </div>
    </section>
"""


def decorate(page: str, folder: Path, prefix: str = "") -> str:
    """`page` with the search (every page) and the quiz (city and school pages) added."""
    page = page.replace("</head>", f'    <link rel="stylesheet" href="{asset("search.css", prefix)}" />\n</head>', 1)
    scripts = f'    <script src="{asset("search.js", prefix)}" defer></script>\n'

    canonical = re.search(r'<link rel="canonical" href="[^"]*/([a-z0-9-]+)\.html"', page)
    page_slug = canonical.group(1) if canonical else ""

    # The city guides index: a search box under the intro (search.js fills it in)
    if folder == CITIES and page_slug == "index":
        page = re.sub(r'(<p class="lead">.*?</p>)',
                      r'\1\n            <div class="site-search" data-site-search hidden></div>', page, count=1, flags=re.S)

    # City and school pages: the landmark list and the suggestion form name the place
    place = re.search(r'<form class="suggest-form" data-place="([^"]*)"', page)
    if place and 'class="landmark-list"' in page and page_slug:
        section = quiz_section(html.unescape(place.group(1)), page_slug)
        page = page.replace('\n    <section class="suggest"', section + '\n    <section class="suggest"', 1)
        scripts += f'    <script src="{asset("quiz.js", prefix)}" defer></script>\n'

    return page.replace("</body>", scripts + "</body>", 1)
