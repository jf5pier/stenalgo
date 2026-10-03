"""
Theory Export (S8)-style trainer branch for the affix layer (Affix Abbreviation Building, S9c): the `affixes` lesson
track of the steno trainer, one lesson per affix rule plus one on the marked routes of verbs.

Run: python -m util.export_affix_lessons
Requires the same inputs as util.export_affix_dictionary (both pickles, starboard3h.json, affix_rules.json).
Output: steno-trainer/public/data/affix-lessons.json
    {"rules": [{"rank", "position", "ortho", "phono", "keys", "keyNames", "label"}, ...],
     "lessons": [<lesson>, ...]}
A lesson has exactly the `lessons.json` lesson schema (docs/specs/lessons.md); its words are `practice-words.json`
records whose `steno`/`strokes` are the SHORT outline plus an `alternates` list holding the long outline as {steno, strokes}
(the drill accepts either). See docs/specs/affix-lessons.md.

The five other trainer data files are not touched: this exporter runs after S9b, S9 being an optional layer.
"""
import json
import os
from typing import Iterable

from src.affixabbrev import Abbreviation, RuleSpec, loadRuleSpecs
from src.keyboard import Starboard, Strokes
from util._affixio import loadAbbreviations
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_lessons import RECORD_FIELDS, numberInFrench

KEYBOARD_JSON = "starboard3h.json"
RULES_JSON = "affix_rules.json"
OUTPUT_PATH = "steno-trainer/public/data/affix-lessons.json"

TRACK = "affixes"
SECTION_TITLE_BASE = "Affixes"
WORDS_PER_LESSON = 20
RULES_PER_SECTION = 10
MAX_SPELLING_VARIANTS = 3
VERB_CATEGORY = "VER"   # str(GramCat.VER) == "VER"? checked in `isVerb`
RULE_KIND = "affix"


def isVerb(gramCat: str) -> bool:
    return gramCat.split(".")[-1].upper().startswith("VER")


def _spellings(ortho: str) -> list[str]:
    """`ortho` of a rule is `a|b|c` (spelling variants) or `a+b` (a family): every spelling, in order, no duplicates."""
    out: list[str] = []
    for part in ortho.replace("+", "|").split("|"):
        if part and part not in out:
            out.append(part)
    return out


def ruleLabel(rule: RuleSpec) -> str:
    spellings = _spellings(rule.ortho)

    def dashed(s: str) -> str:
        return s + "-" if rule.position == "prefix" else "-" + s
    kind = "préfixe" if rule.position == "prefix" else "suffixe"
    label = f"{kind} « {dashed(spellings[0])} »"
    others = spellings[1:1 + MAX_SPELLING_VARIANTS]
    if others:
        label += " (aussi " + ", ".join(dashed(s) for s in others) + ")"
    return label


def _strokesList(strokes: Strokes) -> list[list[int]]:
    return [sorted(stroke) for stroke in strokes]


def _savedText(saved: int) -> str:
    return "économise un trait" if saved == 1 else f"économise {numberInFrench(saved)} traits"


def _wordRecord(a: Abbreviation, starboard: Starboard, phonology: str, label: str) -> dict:
    short = renderFinalStrokesToRTFCRE(starboard, a.outline)
    values = {"ortho": a.ortho, "before": "", "after": "", "label": label, "phonology": phonology,
              "steno": short, "strokes": _strokesList(a.outline), "frequency": a.frequency}
    record = {field: values[field] for field in RECORD_FIELDS}
    record["alternates"] = [{"steno": renderFinalStrokesToRTFCRE(starboard, a.longOutline),
                            "strokes": _strokesList(a.longOutline)}]
    return record


def _example(a: Abbreviation, starboard: Starboard) -> str:
    return (f"« {a.ortho} » : {renderFinalStrokesToRTFCRE(starboard, a.longOutline)} → "
            f"{renderFinalStrokesToRTFCRE(starboard, a.outline)}")


def _top(abbreviations: Iterable[Abbreviation], limit: int = WORDS_PER_LESSON) -> list[Abbreviation]:
    return sorted(abbreviations, key=lambda a: (-a.frequency, a.ortho, a.outline))[:limit]


def _sectionTitle(ruleIndex: int, nRules: int) -> str:
    """Rules grouped by ten, titles spelled in words (the IPA toggle rewrites digits, spec §8)."""
    first = ruleIndex // RULES_PER_SECTION * RULES_PER_SECTION
    last = min(first + RULES_PER_SECTION, nRules)
    if first == 0:
        return f"Les {numberInFrench(last)} premières règles" if last > 1 else "La première règle"
    return f"Les règles {numberInFrench(first + 1)} à {numberInFrench(last)}"


def buildAffixLessons(
    rules: list[RuleSpec], abbreviations: list[Abbreviation], starboard: Starboard,
    phonologyByIdx: dict[int, str],
) -> dict:
    """Pure builder: rule specs + the abbreviations of `buildAbbreviations` -> the `affix-lessons.json` document."""
    rules = sorted(rules, key=lambda r: r.rank)
    ruleDocs = []
    for r in rules:
        keys = sorted(r.keys)
        ruleDocs.append({"rank": r.rank, "position": r.position, "ortho": r.ortho, "phono": r.phono, "keys": keys,
                         "keyNames": [starboard.keyDisplayName(k) for k in keys], "label": ruleLabel(r)})
    lessons: list[dict] = []

    def emit(title: str, sectionTitle: str, newKeys: list[int], rulesText: list[str], words: list[dict]) -> None:
        index = len(lessons) + 1
        lessons.append({
            "id": f"{TRACK}-{index:02d}", "track": TRACK, "index": index, "sectionTitle": sectionTitle,
            "title": title, "kind": TRACK, "newKeys": newKeys,
            "newChords": [newKeys] if len(newKeys) >= 2 else [],
            "rules": [{"kind": RULE_KIND, "text": t} for t in rulesText], "words": words})

    for i, (r, doc) in enumerate(zip(rules, ruleDocs)):
        carriers = _top(a for a in abbreviations if a.rank == r.rank and a.route == 0)
        if not carriers:
            continue
        what = "préfixe" if r.position == "prefix" else "suffixe"
        names = ", ".join(doc["keyNames"])
        n = len(lessons) + 1
        intro = (f"Les touches {names} pressées ensemble remplacent le {what} {doc['label'].split(' ', 1)[1]} : "
                 f"elles se joignent à la frappe de la syllabe voisine, ou forment une frappe à elles seules "
                 f"quand elles ne peuvent pas s'y joindre.")
        examples = "Exemples : " + " ; ".join(_example(a, starboard) for a in carriers[:3]) + "."
        saved = max(a.saved for a in carriers)
        tail = ("Chaque mot s'écrit aussi avec son contour long, qui reste valable : "
                "le contour court " + _savedText(saved).replace("économise", "économise au plus") + ".")
        words = [_wordRecord(a, starboard, phonologyByIdx.get(a.wordIdx, ""),
                             f"{what} {doc['label'].split(' ', 1)[1]} · {_savedText(a.saved)}") for a in carriers]
        emit(f"Leçon {numberInFrench(n)} : {doc['label']}", _sectionTitle(i, len(rules)), doc["keys"],
             [intro, examples, tail], words)

    verbs = _top(a for a in abbreviations if a.route >= 1 and isVerb(a.gramCat))
    if verbs:
        n = len(lessons) + 1
        intro = ("Une forme conjuguée garde sa marque de conjugaison (voir la légende des marques) : "
                 "l'abréviation raccourcit la base du verbe, puis reprend la marque et les frappes qui la suivent.")
        examples = "Exemples : " + " ; ".join(_example(a, starboard) for a in verbs[:3]) + "."
        words = [_wordRecord(a, starboard, phonologyByIdx.get(a.wordIdx, ""),
                             f"forme conjuguée · {_savedText(a.saved)}") for a in verbs]
        emit(f"Leçon {numberInFrench(n)} : les formes conjuguées", "Formes conjuguées", [], [intro, examples], words)
    return {"rules": ruleDocs, "lessons": lessons}


def main() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    if not os.path.exists(RULES_JSON):
        raise RuntimeError(f"{RULES_JSON} not found: run `python -m util.build_affix_rules` first.")
    loaded = loadAbbreviations(starboard, RULES_JSON, verbose=False)
    phonologyByIdx = {r.idx: ".".join(r.phonoSylls) for r in loaded.records}
    document = buildAffixLessons(loadRuleSpecs(RULES_JSON), loaded.abbreviations, starboard, phonologyByIdx)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}: {len(document['rules'])} rules, {len(document['lessons'])} lessons, "
          f"{sum(len(l['words']) for l in document['lessons'])} words.")


if __name__ == "__main__":
    main()
