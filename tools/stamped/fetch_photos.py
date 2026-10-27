#!/usr/bin/env python3
"""Find a freely licensed photo, with its credit, for every Stamped! city landmark.

    python3 tools/stamped/fetch_photos.py [--app ~/Documents/Stamped-A-City-Passport]

Uses the app's own Wikipedia lookup (tools/photo-audit/wiki.py in the app repo, which
mirrors WikimediaService.swift) so the site shows the same photo as the app. Then keeps
only photos that are on Wikimedia Commons under a free license (public domain or Creative
Commons), and records the author, license and file page for the credit line.

Writes stamped-cities/photos.json, which build_city_pages.py reads. With --campuses it looks up
the campus buildings instead and writes stamped-colleges/photos.json for build_campus_pages.py.
Needs `requests`.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "stamped-cities" / "photos.json"
CAMPUS_OUT = ROOT / "stamped-colleges" / "photos.json"
CACHE = ROOT / "tools" / "stamped" / ".cache" / "wiki_http_cache.json"   # git-ignored
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
THUMB_WIDTH = 800
FREE = re.compile(r"^(CC0|CC BY(-SA)? [0-9.]+|CC BY(-SA)?|Public domain|PD.*)", re.I)


def strip_tags(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def commons_file(url):
    """File name for a Commons upload URL, e.g. ".../commons/thumb/a/ab/X.jpg/800px-X.jpg" -> "X.jpg"."""
    if "/wikipedia/commons/" not in url:
        return None   # Hosted on English Wikipedia only, which usually means a non-free image
    path = url.split("?", 1)[0].split("/wikipedia/commons/", 1)[1].split("/")
    name = path[3] if path[0] == "thumb" else path[-1]
    return unquote(name)


def campus_title_overrides(app):
    """The `campusTitleOverrides` table in CampusList.swift (building id -> exact Wikipedia title).
    The app checks it after `titleOverrides`; wiki.swift_title_overrides() only reads the first."""
    source = (app / "Stamped! A City Passport" / "Models" / "CampusList.swift").read_text(encoding="utf-8")
    block = re.search(r"campusTitleOverrides: \[String: String\] = \[(.*?)\n    \]", source, re.DOTALL)
    if block is None:
        return {}
    pairs = re.findall(r'^\s*"((?:[^"\\]|\\.)*)":\s*"((?:[^"\\]|\\.)*)",', block.group(1), re.MULTILINE)
    return {key.replace('\\"', '"'): value.replace('\\"', '"') for key, value in pairs}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default=str(Path.home() / "Documents/Stamped-A-City-Passport"))
    parser.add_argument("--campuses", action="store_true", help="look up campus buildings instead of city landmarks")
    parser.add_argument("--fill", action="store_true", help="for landmarks still without a photo, search Commons nearby and Openverse (photo_fallbacks.py)")
    args = parser.parse_args()
    out = CAMPUS_OUT if args.campuses else OUT
    sys.path.insert(0, str(Path(args.app).expanduser() / "tools" / "photo-audit"))
    import wiki            # the app's lookup
    import audit           # the app's ok / far_away / logo checks

    wiki.CACHE_FILE = CACHE   # keep the HTTP cache in this repo, not the app's
    client = wiki.WikiClient()
    overrides = wiki.swift_title_overrides()
    overrides.update(campus_title_overrides(Path(args.app).expanduser()))
    logos = wiki.swift_logo_patterns()
    skipped = wiki.swift_skip_wikipedia()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from build_city_pages import PLACES
    landmarks = [l for l in wiki.load_landmarks() if (l.city not in PLACES) == args.campuses]

    # 1. The photo the app shows, kept only when the app's audit calls it "ok"
    files = {}
    for i, landmark in enumerate(landmarks, 1):
        if landmark.id in skipped:
            continue
        result = wiki.app_photo(client, landmark.name, overrides.get(landmark.id), logos)
        category, distance = audit.categorize(landmark, result)
        # Stricter than the app: the article must have coordinates within 2 km, so a
        # same-named building elsewhere (e.g. Christiansborg in Copenhagen vs Accra) is dropped
        confirmed = category == "ok" and distance is not None and result.photo_url
        name = commons_file(result.photo_url) if confirmed else None
        if name:
            files[landmark.id] = name
        if i % 100 == 0:
            print(f"  {i}/{len(landmarks)} looked up")
    client.save()

    # 2. License, author and a resized copy for each Commons file, 50 files per request
    info = {}
    names = sorted(set(files.values()))
    for start in range(0, len(names), 50):
        batch = names[start:start + 50]
        params = {
            "action": "query", "format": "json", "formatversion": "2",
            "titles": "|".join("File:" + n for n in batch),
            "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": str(THUMB_WIDTH),
            "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl|Credit",
        }
        status, body = client.get_json(COMMONS_API, params)
        if status != 200 or not body:
            continue
        for page in body.get("query", {}).get("pages", []):
            ii = (page.get("imageinfo") or [None])[0]
            if not ii:
                continue
            meta = ii.get("extmetadata", {})
            license_name = strip_tags(meta.get("LicenseShortName", {}).get("value"))
            if not FREE.match(license_name):
                continue
            artist = strip_tags(meta.get("Artist", {}).get("value")) or "Unknown author"
            info[page["title"].removeprefix("File:").replace("_", " ")] = {
                "src": ii.get("thumburl") or ii["url"],
                "width": ii.get("thumbwidth") or ii.get("width"),
                "height": ii.get("thumbheight") or ii.get("height"),
                "page": ii.get("descriptionurl"),
                "author": artist[:120],
                "license": license_name,
                "licenseUrl": meta.get("LicenseUrl", {}).get("value"),
            }
    client.save()

    photos = {}
    for landmark_id, name in files.items():
        entry = info.get(name.replace("_", " "))
        if entry:
            photos[landmark_id] = entry
    if args.fill:
        from photo_fallbacks import fill
        added = fill(client, landmarks, photos, set(), PLACES)
        print(f"{added} more from Commons (nearby) and Openverse")

    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(photos, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"{len(photos)} of {len(landmarks)} landmarks have a free photo -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
