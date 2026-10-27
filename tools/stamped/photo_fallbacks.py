"""Free photos for landmarks the app's Wikipedia lookup found nothing for (fetch_photos.py --fill).

Two sources, both openly licensed:
1. Wikimedia Commons, searched by location: files tagged within GEO_RADIUS metres of the landmark.
2. Openverse (openverse.org), which searches openly licensed images on Flickr, museums and more.

Only CC0, public domain, CC BY and CC BY-SA are kept, never NonCommercial or NoDerivs, and every
photo keeps its author, license and source page for the credit line. To avoid showing a
neighbouring building, a photo's title (or its Openverse tags) must name the landmark: a distinctive
word from its name, or, for generic names like "Main Library", every word of the name plus a
position within NEAR_METRES. Each photo is marked with `via` so it can be reviewed.
"""
import html
import re
import unicodedata

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"
GEO_RADIUS = 200      # metres around the landmark to search Commons
NEAR_METRES = 60      # how close a photo must be when the landmark's name is generic
MIN_WIDTH = 800
FREE = re.compile(r"^(CC0|CC BY(-SA)?( [0-9.]+)?|Public domain|PD.*)$", re.I)
OPENVERSE_LICENSES = {"cc0": "CC0", "pdm": "Public domain", "by": "CC BY", "by-sa": "CC BY-SA"}
# Not a picture of the building itself: drawings, details, statues, or a view looking away from it
NOT_A_PHOTO = re.compile(r"\b(map|plan|logo|diagram|seal|flag|coat of arms|sign|plaque|floor ?plan|interior|inside|"
                         r"statue|bust|clapper|bells?|totem|door|doorway|window|detail|carving|from|looking|visto|vista|vue|depuis|desde|"
                         r"dance|show|concert|festival|parade|coin|dinar|guard|fountain|construction)\b"
                         r"|\.(svg|pdf|tiff?|gif|webm|ogv)$", re.I)
# Files checked by eye and turned down: the wrong building, a detail, or mostly people
REJECTED = {
    "File:Durham - Elvet Bridge from Kingsgate footbridge - geograph.org.uk - 7292262.jpg",  # shows Elvet Bridge
    "File:Queens Campus of Rutgers University 2026e.jpg",               # a chapel, not Old Queens
    "File:Wall-Mounted Bell Clapper, Burton Tower (Ann Arbor, MI).jpg",  # a detail
    "File:John R. Park Building - front door - 25 August 2012.JPG",       # a detail
    "File:Museum of Anthropology (7960614552).jpg",                       # totem poles, not the building
}
# Landmarks whose nearby photos turned out to be something else when checked by eye (views from the
# landmark, exhibits inside it, signs, details, or a different building with a shared word)
NO_FALLBACK = {
    "campus_durham_kingsgate_bridge", "campus_ubc_museum_of_anthropology",
    "auh_qasr_al_hosn", "bcn_walden7", "br_japan_house", "buf_statler_city", "charles-bridge",
    "cph_round_tower", "cpq-torre-do-castelo", "doha-museum-of-islamic-art", "for-dragao-do-mar",
    "for-estoril", "glbl_apple_sanlitun", "hk_m_plus", "mil_bosco", "msp-07", "paris-fondation-lv",
    "pit-05", "rec-paco-alfandega", "sha_china_art",
}
REJECTED_PREFIXES = ("File:Queens Campus of Rutgers University",   # general views of the campus, not Old Queens
                     "File:The Provost's House from the mouth of Suffolk Street",)   # a crowd fills the frame

GENERIC = {
    "the", "and", "of", "at", "de", "la", "le", "of", "for", "hall", "building", "buildings", "house",
    "center", "centre", "tower", "museum", "library", "main", "old", "new", "university", "college",
    "school", "campus", "state", "church", "chapel", "park", "garden", "gardens", "stadium", "arena",
    "station", "bridge", "square", "street", "avenue", "palace", "theatre", "theater", "national",
    "memorial", "monument", "gate", "plaza", "court", "temple", "cathedral", "basilica", "art", "arts",
    "science", "sciences", "student", "students", "events", "facility", "international", "city",
}


def fold(text):
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower()


def words(text):
    return re.findall(r"[a-z0-9]+", fold(text))


def name_matches(name, text, near, place=""):
    """True when `text` (a file title or tags) names this landmark. Words from the place's own name
    (the city or country) don't count, so "Seoul Train Station" can't match "N Seoul Tower"."""
    found = set(words(text))
    place_words = set(words(place))
    distinctive = [w for w in words(name) if w not in GENERIC and w not in place_words and len(w) >= 3]
    if distinctive:
        return all(w in found for w in distinctive)
    return near and all(w in found for w in words(name))


def strip_tags(text):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def commons_nearby(client, landmark, place=""):
    """The best free Commons photo tagged near the landmark that names it, or None."""
    status, body = client.get_json(COMMONS_API, {
        "action": "query", "format": "json", "formatversion": "2", "list": "geosearch",
        "gscoord": f"{landmark.latitude}|{landmark.longitude}", "gsradius": str(GEO_RADIUS),
        "gsnamespace": "6", "gslimit": "50",
    })
    if status != 200 or not body:
        return None
    candidates = [g for g in body.get("query", {}).get("geosearch", [])
                  if not NOT_A_PHOTO.search(g["title"])
                  and g["title"] not in REJECTED and not g["title"].startswith(REJECTED_PREFIXES)
                  and name_matches(landmark.name, g["title"], g.get("dist", 9999) <= NEAR_METRES, place)]
    candidates.sort(key=lambda g: g.get("dist", 9999))
    if not candidates:
        return None
    status, body = client.get_json(COMMONS_API, {
        "action": "query", "format": "json", "formatversion": "2",
        "titles": "|".join(g["title"] for g in candidates[:10]),
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": "800",
        "iiextmetadatafilter": "Artist|LicenseShortName|LicenseUrl",
    })
    if status != 200 or not body:
        return None
    pages = {p["title"]: p for p in body.get("query", {}).get("pages", [])}
    for g in candidates[:10]:
        info = (pages.get(g["title"], {}).get("imageinfo") or [None])[0]
        if not info or (info.get("width") or 0) < MIN_WIDTH:
            continue
        meta = info.get("extmetadata", {})
        license_name = strip_tags(meta.get("LicenseShortName", {}).get("value"))
        if not FREE.match(license_name):
            continue
        return {
            "src": info.get("thumburl") or info["url"],
            "width": info.get("thumbwidth") or info["width"],
            "height": info.get("thumbheight") or info["height"],
            "page": info.get("descriptionurl"),
            "author": (strip_tags(meta.get("Artist", {}).get("value")) or "Unknown author")[:120],
            "license": license_name,
            "licenseUrl": meta.get("LicenseUrl", {}).get("value"),
            "site": "Wikimedia Commons",
            "via": f"commons-nearby {round(g.get('dist', 0))} m",
        }
    return None


def openverse(client, landmark, place):
    """The first free Openverse image whose title or tags name both the landmark and its place."""
    status, body = client.get_json(OPENVERSE_API, {
        "q": f"{landmark.name} {place}", "license": ",".join(OPENVERSE_LICENSES),
        "category": "photograph", "page_size": "20", "mature": "false",
    })
    if status != 200 or not body:
        return None
    place_words = [w for w in words(place) if w not in GENERIC and len(w) >= 3]
    for item in body.get("results", []):
        text = " ".join([item.get("title") or ""] + [t.get("name", "") for t in item.get("tags") or []])
        if NOT_A_PHOTO.search(item.get("title") or ""):
            continue
        if not name_matches(landmark.name, text, near=False, place=place):
            continue
        if place_words and not any(w in set(words(text)) for w in place_words):
            continue   # e.g. an "Old Main" somewhere else
        if (item.get("width") or 0) < MIN_WIDTH or item.get("license") not in OPENVERSE_LICENSES:
            continue
        version = item.get("license_version")
        license_name = OPENVERSE_LICENSES[item["license"]] + (f" {version}" if version and item["license"] in ("by", "by-sa") else "")
        return {
            "src": item["url"],
            "width": item["width"],
            "height": item["height"],
            "page": item.get("foreign_landing_url") or item.get("url"),
            "author": (item.get("creator") or "Unknown author")[:120],
            "license": license_name,
            "licenseUrl": item.get("license_url"),
            "site": (item.get("source") or item.get("provider") or "Openverse").replace("_", " ").title(),
            "via": "openverse",
        }
    return None


def fill(client, landmarks, photos, skipped, places=None):
    """`places` maps a city to its country, so neither name counts as a match."""
    added = 0
    use_openverse = True   # switched off after its first timeout; it's been unreliable
    missing = [l for l in landmarks if l.id not in photos and l.id not in skipped and l.id not in NO_FALLBACK]
    for i, landmark in enumerate(missing, 1):
        photo = None
        try:
            place = f"{landmark.city} {(places or {}).get(landmark.city, ('',))[0]}"
            photo = commons_nearby(client, landmark, place)
        except Exception as error:   # a slow or failing source is skipped, not fatal
            print(f"  Commons failed for {landmark.name}: {type(error).__name__}")
        if not photo and use_openverse:
            try:
                photo = openverse(client, landmark, place)
            except Exception as error:
                use_openverse = False
                print(f"  Openverse failed ({type(error).__name__}); skipping it for the rest of this run")
        if photo:
            photos[landmark.id] = photo
            added += 1
        if i % 50 == 0:
            print(f"  {i}/{len(missing)} fallbacks tried, {added} found")
    client.save()
    return added
