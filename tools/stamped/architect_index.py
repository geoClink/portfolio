"""Group landmarks by architect the way the app does (ArchitectIndex.swift in the app repo).

The registry's `architect` field is free text ("I.M. Pei & Henry N. Cobb", "Darling and Pearson",
"Alphonse Venne / Dom Bellot"), and many joined names are ONE firm, so splitting is conservative:

1. A trailing note in brackets is dropped: "Cass Gilbert (Original)" groups with "Cass Gilbert".
2. " / " and ";" are split only when every side looks like a person's name, or is on its own
   the architect of another building in the app.
3. " & " and " and " are split only when every side looks like a person's name, so
   "Herzog & de Meuron" and "Darling and Pearson" stay whole.

Names are compared by a loose key (no case or accents, "and" = "&", "I. M." = "I.M."), and each
group is shown with the spelling most landmarks use. Keep this in step with the Swift file.
"""
import unicodedata

# Words that mark a firm or a vague credit rather than a person's name (rule 3)
NON_PERSON_WORDS = {
    "architects", "architect", "architecture", "architectural", "associates", "partners",
    "partnership", "design", "designs", "inc", "co", "company", "group", "team", "retail",
    "studio", "son", "sons", "bros", "office", "engineers", "others", "various", "traditional",
    "unknown", "original", "ancient", "medieval", "natural", "apple", "crew", "dynasty",
    "military", "concept", "et", "al", "builders", "craftsmen", "restoration", "renovation",
}
# First words of credits that describe no one in particular ("Traditional / Unknown", "Built by ...")
VAGUE_STARTS = {"traditional", "unknown", "various", "natural", "medieval",
                "original", "royal", "internal", "built", "local", "n/a"}


def strip_punctuation(word: str) -> str:
    """Trim punctuation from both ends, like Swift's trimmingCharacters(in: .punctuationCharacters)."""
    start, end = 0, len(word)
    while start < end and unicodedata.category(word[start]).startswith("P"):
        start += 1
    while end > start and unicodedata.category(word[end - 1]).startswith("P"):
        end -= 1
    return word[start:end]


def key(name: str) -> str:
    """The loose key two spellings of one name share."""
    decomposed = unicodedata.normalize("NFD", name.casefold())
    folded = "".join(char for char in decomposed if not unicodedata.combining(char))
    folded = folded.replace(" and ", " & ").replace(". ", ".")
    return " ".join(part for part in folded.split(" ") if part)


def known_architect(value) -> str | None:
    """The architect text, or None when it's empty or "Unknown" (Building.knownArchitect)."""
    trimmed = str(value or "").strip()
    return None if not trimmed or trimmed.lower() == "unknown" else trimmed


def is_linkable(name: str) -> bool:
    """False for names that describe no one in particular; those get no page."""
    words = name.split()
    if not words:
        return False
    return strip_punctuation(words[0]).lower() not in VAGUE_STARTS


def looks_like_person(side: str) -> bool:
    words = [word for word in side.split(" ") if word]
    if not 2 <= len(words) <= 5 or not words[0][0].isupper():
        return False
    if any(char in ",;/+" for char in side) or any(char.isnumeric() for char in side):
        return False
    if " and " in side or " & " in side:   # "Reed and Stem" is a pair or a firm, not one person
        return False
    return not any(strip_punctuation(word.lower()) in NON_PERSON_WORDS for word in words)


def removing_note(name: str) -> str:
    """"Cass Gilbert (Original)" -> "Cass Gilbert". Only a note at the very end is dropped."""
    if not name.endswith(")") or "(" not in name:
        return name
    trimmed = name[:name.rindex("(")].strip()
    return trimmed or name


def split(text: str, separators: list[str]) -> list[str]:
    marker = "\x1f"
    for separator in separators:
        text = text.replace(separator, marker)
    return [part.strip() for part in text.split(marker) if part.strip()]


def names(architect: str, standalone_keys: set[str] = frozenset()) -> list[str]:
    """The separate architect names in one registry `architect` string."""
    whole = removing_note(architect.strip())

    # Rule 2: parties joined by " / " or ";"
    parties = [whole]
    sides = [removing_note(side) for side in split(whole, [" / ", ";"])]
    if len(sides) > 1 and all(looks_like_person(side) or key(side) in standalone_keys for side in sides):
        parties = sides

    # Rule 3: partners joined by " & " or " and "
    found = []
    for party in parties:
        partners = split(party, [" & ", " and "])
        found.extend(partners if len(partners) > 1 and all(looks_like_person(p) for p in partners) else [party])

    # A name given twice in one string is still one name
    seen = set()
    result = []
    for name in found:
        if name and key(name) not in seen:
            seen.add(key(name))
            result.append(name)
    return result


class ArchitectIndex:
    """Every landmark grouped by architect key, across all cities and campuses.
    `registry` is BuildingRegistry.json: place -> landmarks. A landmark id found in
    two places counts once (the first place wins), as in the app."""

    def __init__(self, registry: dict):
        self.landmarks = {}        # key -> [(place, landmark)]
        self.display_names = {}    # key -> the spelling most landmarks use
        all_landmarks = []
        seen_ids = set()
        for place, items in registry.items():
            for landmark in items:
                if landmark["id"] not in seen_ids:
                    seen_ids.add(landmark["id"])
                    all_landmarks.append((place, landmark))

        self.standalone_keys = {key(removing_note(architect)) for _, landmark in all_landmarks
                                if (architect := known_architect(landmark.get("architect")))}

        spelling_counts = {}
        for place, landmark in all_landmarks:
            architect = known_architect(landmark.get("architect"))
            if not architect:
                continue
            for name in names(architect, self.standalone_keys):
                name_key = key(name)
                self.landmarks.setdefault(name_key, []).append((place, landmark))
                counts = spelling_counts.setdefault(name_key, {})
                counts[name] = counts.get(name, 0) + 1
        for name_key, counts in spelling_counts.items():
            # Most used first; alphabetical breaks a tie
            self.display_names[name_key] = min(counts, key=lambda spelling: (-counts[spelling], spelling))

    def names_of(self, landmark) -> list[str]:
        """The linkable architect names one landmark credits, in the order it names them."""
        architect = known_architect(landmark.get("architect"))
        if not architect:
            return []
        return [name for name in names(architect, self.standalone_keys) if is_linkable(name)]
