"""
app/scripts/clean_proverb_topics.py

Cleans and normalises topics from a Kazakh proverbs JSON dataset.
Always run from the project root:

    python -m app.scripts.clean_proverb_topics --topics data/raw/topics.json
    python -m app.scripts.clean_proverb_topics --topics data/raw/topics.json \
                                               --proverbs data/raw/proverbs.json \
                                               --topic-field topics \
                                               --min-count 5

Outputs (all written to data/):
    data/cleaned_topics.json   — cleaned topic index
    data/topic_mapping.json    — old_topic -> new_topic  (None = deleted)
    data/cleaned_proverbs.json — proverbs with updated tags  (only if --proverbs given)
"""

import json
import argparse
import re
from collections import defaultdict
from pathlib import Path

# Project root = two levels up from this file  (app/scripts/ -> app/ -> root)
ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "data"


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY 1: Foreign / non-Kazakh source labels
# These describe provenance, not theme. Deleted entirely.
# ─────────────────────────────────────────────────────────────────────────────
FOREIGN_KEYWORDS = [
    "мақалы",
    "нақылы",
    "мәтелі",
    "мақал-мәтелдері",
    "халқының мақал",
    "елінің мақал",
    "халқының нақыл",
    "даналығы",        # e.g. "Жапон даналығы", "Қытай даналығы"
]


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY 2: Semantic merges
# Format:  canonical -> [aliases that collapse into it]
# Specific animals (сиыр, жылқы, түйе, ит, қой, қыран …) stay distinct.
# ─────────────────────────────────────────────────────────────────────────────
MERGE_MAP: dict[str, list[str]] = {
    # Food
    "тамақ":            ["ас", "тағам"],

    # Animals (general)
    "жануар":           ["жан-жануар", "жан-жануарлар", "жануарлар"],
    "төрт түлік мал":   ["төрт түлік"],

    # Poverty / wealth
    "кедейлік":         ["кедей", "кедейшілік"],
    "байлық":           ["бай", "ырыс", "дәулет"],

    # Life / living
    "өмір":             ["тірлік", "тұрмыс"],

    # People
    "адам":             ["кісі"],
    "халық":            ["жұрт"],

    # Bravery / hero
    "батырлық":         ["батыр"],
    "ерлік":            ["ер"],

    # Laziness
    "жалқаулық":        ["жалқау", "еріншек", "еріншектік"],

    # Wisdom / knowledge
    "ақыл":             ["ақылды", "ақылсыз"],
    "білім":            ["білімді", "білімділік", "білімсіз", "біліктілік"],

    # Work
    "еңбек":            ["іс"],

    # Unity
    "ынтымақ":          ["бірлік"],

    # Relatives
    "туыс":             ["туысқан", "ағайындық", "туыстық"],

    # Homeland  (отан and туған жер are the same concept in proverbs)
    "отан":             ["туған жер"],

    # Family / home
    "отбасы":           ["үй"],

    # Friendship
    "достық":           ["дос"],

    # Health
    "денсаулық":        ["ауру"],

    # Education / upbringing
    "тәрбие":           ["өнеге"],
}


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY 3: Verbose labels  →  short canonical form
# ─────────────────────────────────────────────────────────────────────────────
VERBOSE_MAP: dict[str, str | None] = {
    # Animals
    "жануарлар туралы мақал":                   "жануар",
    "жануарлар туралы мақалдар":                "жануар",

    # Knowledge / speech
    "білім туралы мақал":                       "білім",
    "Жақсы сөз":                                "сөз",
    "Білімдіден шыққан сөз":                    "сөз",
    "Асыл сөз":                                 "сөз",
    "асыл сөз":                                 "сөз",
    "сөз өнері":                                "сөз",
    "тіл туралы":                               "тіл",
    "ана тілі":                                 "тіл",
    "ұстаз туралы нақыл сөздер":                "ұстаз",

    # Family / relatives
    '"Отбасы"туралы мақал-мәтелдер':            "отбасы",
    "ерлі-зайыптылар":                          "отбасы",
    "ағайын туралы мақал-мәтел":                "ағайын",
    "ағайін туралы мақал-мәтел":                "ағайын",
    "ағайын туыс":                              "ағайын",
    "туған-туыстар":                            "туыс",
    "туған-туыс туралы мақал-мәтел":            "туыс",
    "туыстық қатынастар":                       "туыс",
    "Туыстық қатынастар":                       "туыс",
    "туыс.отбасы":                              "туыс",
    "ата-ана":                                  "ата",
    "бала тәрбиесі":                            "тәрбие",
    "бала-шаға":                                "бала",
    "балалық":                                  "бала",
    "балалық шақ":                              "бала",

    # Homeland
    "туған жер туралы мақал–мәтелдер жинағы":  "отан",
    "Туған жер":                                "отан",
    "туған жер":                                "отан",

    # People / character
    "адам және оның қасиеттері":                "адам",
    "адамның қасиеттері":                       "адам",
    "адамгершілік.":                            "адамгершілік",

    # Hero / man
    "ер жігіт":                                 "жігіт",
    "жігіттік":                                 "жігіт",

    # Nature / seasons
    "жыл мезгілдері":                           "табиғат",
    "жыл мезгілдер":                            "табиғат",

    # Crafts / art
    "қол өнері":                                "өнер",
    "қол өнер":                                 "өнер",

    # Horse equipment -> horse
    "ер-тоқым":                                 "ат",
    "ер тоқым":                                 "ат",

    # Body
    "дене мүшелері":                            "дене",

    # Misc verbose
    "сан туралы мақал":                         "сан",
    "тарих туралы мақал":                       "тарих",
    "шегіртке туралы мақал":                    "шегіртке",
    "өтірік туралы мақал-мәтелдер":             "өтірік",
    "достық туралы мақал-мәтел":                "достық",
    "ана туралы":                               "ана",
    "ана сүті":                                 "ана",

    # Redundant Kazakh-label tags  (delete — everything in the dataset is Kazakh)
    "қазақ мәтелі":                             None,
    "қазақ мақалы":                             None,
    "Қазақ мақалы":                             None,

    # Misclassified foreign
    "Арабмақал-мәтелдері":                      None,
    "Араб мақал-мәтелдері":                     None,
}


# ─────────────────────────────────────────────────────────────────────────────
# CATEGORY 4: Absurd / off-topic / clearly malformed  →  delete or redirect
# ─────────────────────────────────────────────────────────────────────────────
ABSURD_DELETE: set[str] = {
    "интернет",                 # anachronistic
    "пулемет",                  # anachronistic
    "Абай Құнанбаев",           # author name, not a theme
    "Шерхан Мұртаза",           # author name
    "Құлатай батыр",            # specific named person
    "Хорасан",                  # geographic region used as tag
    # typos / nonsense
    "жігітт",
    "асуғу",
    "асыд",
    # malformed concatenations
    "бағалау \nИспан мақалы",
    "қу \nДжон Локк",
    "асығу. ер",
    "асығыс. іс",
    "аш.денсаулық",
    "аға.бала",
    "еркек.әйел",
    "ит.жануар",
    "кедей. ауа",
    "көз.көңіл",
    "мал.қоныс",
    "сыр.нұр",
    "тары.қарын",
    "туыс.отбасы",
    "қызыл.парсы мақалы",
    "ұры.ұрыс",
    "өсекші.ауыз",
}

ABSURD_REDIRECT: dict[str, str] = {
    "ерке бала":    "бала",
    "жастық шақ":   "жастық",
    "отыз жас":     "жас",
    "қырық жас":    "жас",
    "жеті ата":     "ата",
}


# ─────────────────────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────────────────────

def build_mapping(topics: list[dict]) -> dict[str, str | None]:
    """Return a dict of old_topic -> canonical (or None = delete)."""
    mapping: dict[str, str | None] = {}

    # 1. Foreign labels
    for t in topics:
        name = t["topic"]
        if any(kw in name for kw in FOREIGN_KEYWORDS):
            mapping[name] = None

    # 2. Semantic merges
    alias_to_canonical: dict[str, str] = {}
    for canonical, aliases in MERGE_MAP.items():
        for alias in aliases:
            alias_to_canonical[alias] = canonical
    for t in topics:
        name = t["topic"]
        if name in alias_to_canonical and name not in mapping:
            mapping[name] = alias_to_canonical[name]

    # 3. Verbose -> short
    for t in topics:
        name = t["topic"]
        if name in VERBOSE_MAP and name not in mapping:
            mapping[name] = VERBOSE_MAP[name]

    # 4. Absurd: delete or redirect
    for t in topics:
        name = t["topic"]
        if name not in mapping:
            if name in ABSURD_DELETE:
                mapping[name] = None
            elif name in ABSURD_REDIRECT:
                mapping[name] = ABSURD_REDIRECT[name]

    # 5. Case normalisation  (e.g. "Жапон мақалы" == "жапон мақалы")
    lower_first_seen: dict[str, str] = {}
    for t in topics:
        name = t["topic"]
        key = name.lower().strip()
        if key not in lower_first_seen:
            lower_first_seen[key] = name
    for t in topics:
        name = t["topic"]
        canonical_case = lower_first_seen[name.lower().strip()]
        if name != canonical_case and name not in mapping:
            mapping[name] = canonical_case

    return mapping


def _clean(name: str) -> str:
    """Strip whitespace noise and trailing punctuation from a topic string."""
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    name = name.rstrip(".")
    return name


def apply_mapping_to_topics(
    topics: list[dict],
    mapping: dict[str, str | None],
    min_count: int = 0,
) -> list[dict]:
    merged: dict[str, int] = defaultdict(int)
    for t in topics:
        name = t["topic"]
        canonical = mapping.get(name, name)
        if canonical is None:
            continue
        canonical = _clean(canonical)
        merged[canonical] += t["count"]

    result = [{"topic": k, "count": v} for k, v in merged.items()]
    if min_count > 0:
        result = [t for t in result if t["count"] >= min_count]
    result.sort(key=lambda x: -x["count"])
    return result


def apply_mapping_to_proverbs(
    proverbs: list[dict],
    mapping: dict[str, str | None],
    topic_field: str,
) -> list[dict]:
    cleaned = []
    for p in proverbs:
        p = dict(p)
        raw = p.get(topic_field)
        if raw is None:
            cleaned.append(p)
            continue

        if isinstance(raw, list):
            new_tags: list[str] = []
            for tag in raw:
                tag = _clean(tag)
                resolved = mapping.get(tag, tag)
                if resolved is not None:
                    resolved = _clean(resolved)
                    if resolved not in new_tags:
                        new_tags.append(resolved)
            p[topic_field] = new_tags
        elif isinstance(raw, str):
            tag = _clean(raw)
            resolved = mapping.get(tag, tag)
            p[topic_field] = _clean(resolved) if resolved else ""

        cleaned.append(p)
    return cleaned


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Clean Kazakh proverb topics")
    parser.add_argument(
        "--topics", required=True,
        help="Path to topics index JSON  (e.g. data/raw/topics.json)",
    )
    parser.add_argument(
        "--proverbs", default=None,
        help="Path to proverbs JSON to clean  (optional)",
    )
    parser.add_argument(
        "--topic-field", default="topics",
        help='Field name in each proverb object that holds topic tags  (default: "topics")',
    )
    parser.add_argument(
        "--min-count", type=int, default=0,
        help="Drop topics with count below this value after merging  (default: 0 = keep all)",
    )
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load topics ──────────────────────────────────────────────────────────
    topics_path = Path(args.topics)
    with topics_path.open(encoding="utf-8") as f:
        raw_data = json.load(f)
    topics: list[dict] = raw_data["topics"]
    print(f"Loaded {len(topics)} topics from '{topics_path}'")

    # ── Build mapping ────────────────────────────────────────────────────────
    mapping = build_mapping(topics)
    n_deleted = sum(1 for v in mapping.values() if v is None)
    n_merged  = sum(1 for k, v in mapping.items() if v is not None and k != v)
    print(f"  → {n_deleted} deleted,  {n_merged} merged/renamed")

    # ── Clean topic index ────────────────────────────────────────────────────
    cleaned_topics = apply_mapping_to_topics(topics, mapping, args.min_count)
    if args.min_count > 0:
        print(f"  → {args.min_count}+ count threshold applied")
    print(f"  → {len(cleaned_topics)} topics remaining")

    # ── Save cleaned_topics.json ─────────────────────────────────────────────
    out_topics_path = DATA_DIR / "cleaned_topics.json"
    with out_topics_path.open("w", encoding="utf-8") as f:
        json.dump(
            {"success": True, "total_topics": len(cleaned_topics), "topics": cleaned_topics},
            f, ensure_ascii=False, indent=2,
        )
    print(f"Saved: {out_topics_path.relative_to(ROOT)}")

    # ── Save topic_mapping.json ───────────────────────────────────────────────
    out_mapping_path = DATA_DIR / "topic_mapping.json"
    with out_mapping_path.open("w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_mapping_path.relative_to(ROOT)}")

    # ── Optionally clean proverbs ─────────────────────────────────────────────
    if args.proverbs:
        proverbs_path = Path(args.proverbs)
        with proverbs_path.open(encoding="utf-8") as f:
            proverbs_raw = json.load(f)

        if isinstance(proverbs_raw, list):
            proverbs_list = proverbs_raw
            wrap_key: str | None = None
        else:
            wrap_key = next(
                (k for k in ("proverbs", "data", "results", "items") if k in proverbs_raw),
                None,
            )
            if wrap_key is None:
                print("ERROR: cannot find proverbs list in JSON — expected a root list or a key in {proverbs, data, results, items}")
                return
            proverbs_list = proverbs_raw[wrap_key]

        print(f"\nLoaded {len(proverbs_list)} proverbs from '{proverbs_path}'")
        cleaned_proverbs = apply_mapping_to_proverbs(proverbs_list, mapping, args.topic_field)

        if wrap_key is None:
            out_proverbs = cleaned_proverbs
        else:
            out_proverbs = dict(proverbs_raw)
            out_proverbs[wrap_key] = cleaned_proverbs

        out_proverbs_path = DATA_DIR / "cleaned_proverbs.json"
        with out_proverbs_path.open("w", encoding="utf-8") as f:
            json.dump(out_proverbs, f, ensure_ascii=False, indent=2)
        print(f"Saved: {out_proverbs_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()