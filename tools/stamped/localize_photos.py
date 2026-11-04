#!/usr/bin/env python3
"""Keep a small local WebP copy of every landmark photo, so pages stop hotlinking Wikimedia.

    python3 tools/stamped/localize_photos.py [--app ~/Documents/Stamped-A-City-Passport]

Reads stamped-cities/photos.json and stamped-colleges/photos.json (written by fetch_photos.py)
and the stadium photos in the app's Resources/CampusAthletics.json (campus_cards.py), downloads each photo once, shrinks it to at most MAX_WIDTH x MAX_HEIGHT and saves it as WebP in
stamped-cities/photos/. stamped-cities/photos/manifest.json maps each original address to its
local file and size; build_city_pages.py and build_campus_pages.py read it (local_photos()).
The credit line (author, license, source page) is untouched: only the image address changes.

It also points the landmark strip on stamped-app.html at the local copies (re-run
build_translations.py afterwards). Photos already downloaded are skipped, so re-running after
fetch_photos.py only fetches the new ones. Files no page uses any more are deleted.
Needs `requests` and `Pillow`.
"""
import argparse
import hashlib
import html
import io
import json
import re
import time
import unicodedata
from pathlib import Path
from urllib.parse import unquote

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [ROOT / "stamped-cities" / "photos.json", ROOT / "stamped-colleges" / "photos.json"]
LANDING = ROOT / "stamped-app.html"
ATHLETICS = Path("Stamped! A City Passport") / "Resources" / "CampusAthletics.json"   # inside the app repo
PHOTO_DIR = ROOT / "stamped-cities" / "photos"
MANIFEST = PHOTO_DIR / "manifest.json"
# Photos show at most ~440 CSS px wide in a landmark card and ~700 px in a hero tile, so 640 px
# looks sharp on phones and most screens. Tall photos are capped too: they're cropped to a
# landscape box anyway, and a 1440 px tall portrait would be the heaviest file on the page.
MAX_WIDTH = 640
MAX_HEIGHT = 800
QUALITY = 68
USER_AGENT = "StampedSiteBuilder/1.0 (https://georgeclinkscalesdev.com; local copies of credited landmark photos)"


def file_name(src):
    """A readable, unique name: the Commons file name as a slug, plus a short hash of the address."""
    last = unquote(src.split("?", 1)[0].rstrip("/").split("/")[-1])
    last = re.sub(r"^\d+px-", "", last).rsplit(".", 1)[0]
    ascii_name = unicodedata.normalize("NFKD", last).encode("ascii", "ignore").decode().lower()
    stem = re.sub(r"[^a-z0-9]+", "-", ascii_name).strip("-")[:48].strip("-") or "photo"
    return f"{stem}-{hashlib.sha1(src.encode()).hexdigest()[:6]}.webp"


def landing_sources(page):
    return [html.unescape(src) for src in re.findall(r'<img src="(https://[^"]+)"', page)]


def download(session, src):
    """The image bytes, retrying politely when the server asks us to slow down."""
    response = None
    for attempt in range(4):
        try:
            response = session.get(src, timeout=60)
        except requests.RequestException as error:   # a dropped connection: wait and try again
            print(f"  retrying after {type(error).__name__}: {src}")
            time.sleep(5 * (attempt + 1))
            continue
        if response.status_code == 200:
            return response.content
        if response.status_code in (429, 503):
            time.sleep(5 * (attempt + 1))
            continue
        break
    print(f"  skipped ({f'HTTP {response.status_code}' if response is not None else 'no connection'}): {src}")
    return None


def to_webp(data, out):
    """Shrink to fit MAX_WIDTH x MAX_HEIGHT (never enlarge) and save. Returns (width, height)."""
    image = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))   # upright, if the camera tagged it
    image = image.convert("RGB")
    image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)   # keeps the aspect ratio
    image.save(out, "WEBP", quality=QUALITY, method=6)
    return image.size


def update_landing(manifest):
    """Point the hotlinked <img> tags on stamped-app.html at their local copies, with the real size."""
    page = LANDING.read_text(encoding="utf-8")

    def swap(match):
        entry = manifest.get(html.unescape(match.group(1)))
        if not entry:
            return match.group(0)
        return f'<img src="stamped-cities/photos/{entry["file"]}" width="{entry["width"]}" height="{entry["height"]}"'

    new_page = re.sub(r'<img src="(https://[^"]+)" width="\d+" height="\d+"', swap, page)
    if new_page != page:
        LANDING.write_text(new_page, encoding="utf-8")
        print(f"updated {LANDING.name}")


def venue_sources(app):
    """The Game Day stadium photos campus_cards.py shows."""
    path = app / ATHLETICS
    if not path.exists():
        return []
    campuses = json.loads(path.read_text(encoding="utf-8")).get("campuses", {})
    return [venue["photo"]["imageURL"] for campus in campuses.values()
            for venue in campus.get("venues") or [] if venue.get("photo")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default=str(Path.home() / "Documents/Stamped-A-City-Passport"))
    args = parser.parse_args()
    PHOTO_DIR.mkdir(exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    wanted = []
    for source in SOURCES:
        if source.exists():
            wanted += [photo["src"] for photo in json.loads(source.read_text(encoding="utf-8")).values()]
    wanted += landing_sources(LANDING.read_text(encoding="utf-8"))
    wanted += venue_sources(Path(args.app).expanduser())
    wanted = sorted(set(wanted))
    wanted_set = set(wanted)

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    new = 0
    for count, src in enumerate(wanted, 1):
        entry = manifest.get(src)
        if entry and (PHOTO_DIR / entry["file"]).exists():
            continue
        data = download(session, src)
        if data is None:
            continue
        name = file_name(src)
        try:
            width, height = to_webp(data, PHOTO_DIR / name)
        except OSError as error:   # not an image Pillow can read
            print(f"  skipped ({error}): {src}")
            continue
        manifest[src] = {"file": name, "width": width, "height": height}
        new += 1
        if new % 100 == 0:
            print(f"  {new} downloaded ({count}/{len(wanted)})")
            MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")

    # Forget photos no page uses any more
    manifest = {src: entry for src, entry in manifest.items() if src in wanted_set}
    used = {entry["file"] for entry in manifest.values()}
    for old in PHOTO_DIR.glob("*.webp"):
        if old.name not in used:
            old.unlink()
    MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True), encoding="utf-8")
    update_landing(manifest)

    size = sum((PHOTO_DIR / name).stat().st_size for name in used)
    print(f"{len(manifest)} of {len(wanted)} photos stored locally ({new} new), "
          f"{size / 1_000_000:.1f} MB in {PHOTO_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
