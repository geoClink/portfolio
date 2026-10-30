#!/usr/bin/env python3
"""Fetch the History card for every Stamped! school page: the founding year and a few sentences
from the university's English Wikipedia article, the same way the app does it
(CampusHistoryService.swift in the app repo).

    python3 tools/stamped/fetch_campus_history.py [--app ~/Documents/Stamped-A-City-Passport]

Writes stamped-colleges/history.json, which build_campus_pages.py reads. Uses only the standard
library. Wikipedia text stays in English, like in the app.
"""
import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "stamped-colleges" / "history.json"
HEADERS = {"User-Agent": "Stamped-site-builder/1.0 (https://georgeclinkscalesdev.com)"}

# Same as CampusHistoryTitles.swift: the article title where the campus's `wiki` isn't the
# university itself, and campuses whose Wikidata founding year would mislead
TITLE_OVERRIDES = {"sorbonne": "University of Paris"}
HIDE_FOUNDED_YEAR = {"sorbonne", "kuLeuven"}

# "U.S." and "St." end in a full stop but don't end a sentence
ABBREVIATIONS = re.compile(r"\b(U\.S|U\.K|St|Dr|Mr|Mrs|Ms|Jr|Sr|No|Inc|Co|Mt|Ft|e\.g|i\.e|ca|c)\.$")


def get_json(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def sentences(text):
    """Split at ". ", "! " or "? " unless the word before is an abbreviation."""
    out, current = [], ""
    for part in re.split(r"(?<=[.!?])\s+", text.strip()):
        current = f"{current} {part}".strip() if current else part
        if not ABBREVIATIONS.search(current):
            out.append(current)
            current = ""
    if current:
        out.append(current)
    return out


def history_text(extract, skipped=2, maximum=4):
    """The app's rule: the page header already shows the first two sentences, so History carries
    on from the third (up to four); a short article shows its opening instead."""
    all_sentences = sentences(extract)
    rest = all_sentences[skipped:]
    chosen = rest if len(rest) >= 2 else all_sentences
    return " ".join(chosen[:maximum])


def founded_year(item):
    """Wikidata P571: a preferred value wins, otherwise every value must agree on the year."""
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "wbgetclaims", "entity": item, "property": "P571", "format": "json"})
    statements = [s for s in get_json(url).get("claims", {}).get("P571", []) if s.get("rank") != "deprecated"]

    def year(statement):
        value = (statement.get("mainsnak", {}).get("datavalue") or {}).get("value") or {}
        if value.get("precision", 0) < 9:   # 9 = year; lower is a decade or century
            return None
        digits = value.get("time", "").lstrip("+").split("-")[0]
        return int(digits) if digits.isdigit() else None

    preferred = [y for y in (year(s) for s in statements if s.get("rank") == "preferred") if y]
    if len(preferred) == 1:
        return preferred[0]
    years = {y for y in (year(s) for s in statements) if y}
    return years.pop() if len(years) == 1 else None


def official_website(item):
    """The university's own site (Wikidata P856), kept only if it's https and answers now."""
    if not item:
        return None
    try:
        url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(
            {"action": "wbgetclaims", "entity": item, "property": "P856", "format": "json"})
        statements = [s for s in get_json(url).get("claims", {}).get("P856", []) if s.get("rank") != "deprecated"]
        statements.sort(key=lambda s: s.get("rank") != "preferred")   # a preferred value first
        for statement in statements:
            site = ((statement.get("mainsnak") or {}).get("datavalue") or {}).get("value", "")
            site = site.replace("http://", "https://", 1)
            if not site.startswith("https://"):
                continue
            request = urllib.request.Request(site, headers=HEADERS, method="HEAD")
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    if response.status < 400:
                        return site
            except urllib.error.HTTPError as error:
                if error.code in (403, 405):   # some sites refuse HEAD or robots but load in a browser
                    return site
            except Exception:
                continue
    except Exception:
        return None
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default=str(Path.home() / "Documents/Stamped-A-City-Passport"))
    app = Path(parser.parse_args().app).expanduser()
    campuses = [c for f in sorted((app / "tools" / "campus-data" / "campuses").glob("*.json"))
                for c in json.loads(f.read_text(encoding="utf-8"))]

    history = {}
    for campus in campuses:
        title = TITLE_OVERRIDES.get(campus["enumCase"]) or campus.get("wiki") or campus["name"]
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"))
        try:
            summary = get_json(url)
        except Exception as error:
            print(f"  skipped {campus['name']}: {error}")
            continue
        if summary.get("type") == "disambiguation" or not summary.get("extract"):
            continue
        text = history_text(summary["extract"])
        year = None
        if summary.get("wikibase_item") and campus["enumCase"] not in HIDE_FOUNDED_YEAR:
            try:
                year = founded_year(summary["wikibase_item"])
            except Exception:
                pass
        history[campus["name"]] = {
            "foundedYear": year,
            "summary": text,
            "url": (summary.get("content_urls") or {}).get("desktop", {}).get("page"),
            "website": official_website(summary.get("wikibase_item")),
        }
    OUT.write_text(json.dumps(history, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    with_year = sum(1 for h in history.values() if h["foundedYear"])
    print(f"wrote {OUT.relative_to(ROOT)}: {len(history)} of {len(campuses)} schools, {with_year} with a founding year")


if __name__ == "__main__":
    main()
