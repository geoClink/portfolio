#!/usr/bin/env python3
"""Write the data for the architecture quiz on each city guide and school page.

    python3 tools/stamped/build_quiz_data.py [--app ~/Documents/Stamped-A-City-Passport]

The app builds its 10-question quiz from each place's landmarks (QuizView/QuizView-ViewModel.swift
and Components/QuizLogic.swift). This script saves the same facts the app asks about, one small
file per place, next to the pages:

    stamped-cities/quiz/<slug>.json      one per city guide
    stamped-colleges/quiz/<slug>.json    one per school page

stamped-cities/quiz.js turns them into questions in the browser, with the app's rules, so each
round is different. The quiz section itself is added to the pages by quiz_search.py.
Re-run after the app's data changes, like the page builders.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_city_pages import OUT as CITIES_OUT, PLACES, known, slug
from build_campus_pages import OUT as COLLEGES_OUT


def known_text(value) -> str:
    """The value, or "" when the app treats it as unknown (the app never asks about those)."""
    text = str(value or "").strip()
    return text if known(text) else ""


def quiz_landmark(landmark: dict, photo: dict | None) -> dict:
    """Only the facts the quiz uses. year 0 and stories 0 mean "not known", as in the app."""
    item = {
        "id": landmark["id"],
        "name": landmark["name"],
        "architect": known_text(landmark.get("architect")),
        "style": known_text(landmark.get("buildingStyle")),
        "year": landmark["yearBuilt"] if isinstance(landmark.get("yearBuilt"), int) else 0,
        "stories": landmark["numberOfStories"] if isinstance(landmark.get("numberOfStories"), int) else 0,
    }
    # Photo questions ("Which building is this?") need a photo and its credit line
    if photo:
        item["photo"] = {key: photo[key] for key in
                         ("src", "width", "height", "author", "license", "licenseUrl", "page", "site") if key in photo}
    return item


def write_place(folder: Path, place: str, landmarks: list[dict], photos: dict) -> None:
    data = {"place": place, "landmarks": [quiz_landmark(item, photos.get(item["id"])) for item in landmarks]}
    path = folder / "quiz" / f"{slug(place)}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", default=str(Path.home() / "Documents/Stamped-A-City-Passport"))
    args = parser.parse_args()
    app = Path(args.app).expanduser()
    registry = load_json(app / "Stamped! A City Passport" / "Resources" / "BuildingRegistry.json")
    campuses = [campus["name"] for file in sorted((app / "tools" / "campus-data" / "campuses").glob("*.json"))
                for campus in json.loads(file.read_text(encoding="utf-8"))]

    # Only places that have a page (a city the city builder doesn't know yet has none)
    cities = [city for city in registry if city in PLACES and (CITIES_OUT / f"{slug(city)}.html").exists()]
    schools = [name for name in campuses if name in registry and (COLLEGES_OUT / f"{slug(name)}.html").exists()]

    for folder, places in ((CITIES_OUT, cities), (COLLEGES_OUT, schools)):
        (folder / "quiz").mkdir(exist_ok=True)
        photos = load_json(folder / "photos.json")
        for place in places:
            write_place(folder, place, registry[place], photos)
    print(f"wrote quiz data for {len(cities)} cities and {len(schools)} schools")


if __name__ == "__main__":
    main()
