"""
Theory Export (S8)-style trainer branch for the affix layer (Affix Abbreviation Building, S9c): the `affixes` lesson
track of the steno trainer, one lesson per affix rule plus one on the marked routes of verbs.

Run: python -m util.export_affix_lessons
Requires the same inputs as util.export_affix_dictionary (both pickles, starboard3h.json, affix_rules.json).
Output: steno-trainer/public/data/affix-lessons.json
    {"rules": [{"rank", "position", "ortho", "phono", "keys", "keyNames", "label"}, ...],
     "lessons": [<lesson>, ...]}
A lesson has exactly the `lessons.json` lesson schema (docs/specs/lessons.md); its words are `practice-words.json`
records whose `steno`/`strokes` are the SHORT outline plus an `alternates` list of the other accepted outlines as {steno, strokes}
(the drill accepts any) and the `rank` of its `rule`. See docs/specs/affix-lessons.md.

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


def groupKeyNames(names: list[str]) -> str:
    """Key names with each side's keys grouped: `-j -s -d` -> `-jsd`, `w- p- -j` -> `wp- + -j` (left-hand names end
    with `-`, right-hand ones start with it; any other name follows)."""
    left = [n for n in names if n.endswith("-")]
    right = [n for n in names if n.startswith("-") and not n.endswith("-")]
    other = [n for n in names if n not in left and n not in right]
    parts = ([("".join(n[:-1] for n in left) + "-")] if left else []) + \
            ([("-" + "".join(n[1:] for n in right))] if right else []) + other
    return " + ".join(parts)


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


def _wordRecord(group: list[Abbreviation], starboard: Starboard, phonology: str, label: str) -> dict:
    """`group`: the abbreviations of one spelling, best first. The first one's short outline is the primary one (the
    hint); every other outline (its long one, and both outlines of the others, i.e. the homographs) is an alternate."""
    a = group[0]
    short = renderFinalStrokesToRTFCRE(starboard, a.outline)
    values = {"ortho": a.ortho, "before": "", "after": "", "label": label, "phonology": phonology,
              "steno": short, "strokes": _strokesList(a.outline), "frequency": a.frequency}
    record = {field: values[field] for field in RECORD_FIELDS}
    seen = {a.outline}
    alternates = []
    for b in group:
        for outline in (b.longOutline, b.outline):
            if outline not in seen:
                seen.add(outline)
                alternates.append({"steno": renderFinalStrokesToRTFCRE(starboard, outline),
                                   "strokes": _strokesList(outline)})
    record["alternates"] = alternates
    record["rule"] = a.rank   # the affix rule that shortens it (the trainer shows only the rules touching the current word)
    return record


_MOODS = {"ind": "ind.", "sub": "subj.", "cnd": "cond.", "imp": "impér."}
_TENSES = {"pre": "prés.", "imp": "imparf.", "fut": "fut.", "pas": "passé"}
_PERSONS = {"1": "première", "2": "deuxième", "3": "troisième"}   # in words: the IPA toggle rewrites digits 1, 2
_NUMBERS = {"s": "sing.", "p": "plur."}


def conjugationText(infoVerb: str) -> str:
    """`ind:pre:1s;ind:pre:3s;imp:pre:2s` -> `ind. prés., première et troisième pers. sing. ; ...`.
    Spelled out in words, no digits (the trainer's IPA toggle rewrites digits)."""
    groups: dict[tuple[str, str], list[str]] = {}
    for item in infoVerb.split(";"):
        parts = item.split(":")
        if not item:
            continue
        if item == "inf":
            groups.setdefault(("inf.", ""), [])
        elif parts[0] == "par" and len(parts) == 2:
            groups.setdefault(("part. " + _TENSES.get(parts[1], parts[1]), ""), [])
        elif len(parts) == 3 and parts[0] in _MOODS and len(parts[2]) == 2:
            who = _PERSONS.get(parts[2][0], ""), _NUMBERS.get(parts[2][1], "")
            groups.setdefault((f"{_MOODS[parts[0]]} {_TENSES.get(parts[1], parts[1])},", who[1]), []).append(who[0])
        else:
            groups.setdefault((item, ""), [])
    texts = []
    for (name, number), persons in groups.items():
        if persons:
            texts.append(f"{name} {' et '.join(dict.fromkeys(persons))} pers. {number}")
        else:
            texts.append(name)
    return " ; ".join(texts)


def _example(a: Abbreviation, starboard: Starboard) -> str:
    return (f"« {a.ortho} » : {renderFinalStrokesToRTFCRE(starboard, a.longOutline)} → "
            f"{renderFinalStrokesToRTFCRE(starboard, a.outline)}")


def _top(abbreviations: Iterable[Abbreviation], limit: int = WORDS_PER_LESSON) -> list[Abbreviation]:
    return sorted(abbreviations, key=lambda a: (-a.frequency, a.ortho, a.outline))[:limit]


def _groupByOrtho(abbreviations: Iterable[Abbreviation], limit: int = WORDS_PER_LESSON) -> list[list[Abbreviation]]:
    """The `limit` most frequent spellings, each with all its abbreviations (homographs), best first."""
    byOrtho: dict[str, list[Abbreviation]] = {}
    for a in sorted(abbreviations, key=lambda a: (-a.frequency, a.ortho, a.outline)):
        byOrtho.setdefault(a.ortho, []).append(a)
    return list(byOrtho.values())[:limit]


def _sectionTitle(ruleIndex: int, nRules: int) -> str:
    """Rules grouped by ten, titles spelled in words (the IPA toggle rewrites digits, spec §8)."""
    first = ruleIndex // RULES_PER_SECTION * RULES_PER_SECTION
    last = min(first + RULES_PER_SECTION, nRules)
    if first == 0:
        return f"Les {numberInFrench(last)} premières règles" if last > 1 else "La première règle"
    return f"Les règles {numberInFrench(first + 1)} à {numberInFrench(last)}"


def buildAffixLessons(
    rules: list[RuleSpec], abbreviations: list[Abbreviation], starboard: Starboard,
    phonologyByIdx: dict[int, str], formByIdx: dict[int, str] | None = None,
) -> dict:
    """Pure builder: rule specs + the abbreviations of `buildAbbreviations` -> the `affix-lessons.json` document."""
    rules = sorted(rules, key=lambda r: r.rank)
    formByIdx = formByIdx or {}
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
        groups = _groupByOrtho(a for a in abbreviations if a.rank == r.rank and a.route == 0)
        if not groups:
            continue
        carriers = [g[0] for g in groups]
        what = "préfixe" if r.position == "prefix" else "suffixe"
        names = groupKeyNames(doc["keyNames"])
        n = len(lessons) + 1
        intro = (f"Les touches {names} pressées ensemble remplacent le {what} {doc['label'].split(' ', 1)[1]} : "
                 f"elles se joignent à la frappe de la syllabe voisine, ou forment une frappe à elles seules "
                 f"quand elles ne peuvent pas s'y joindre.")
        examples = "Exemples : " + " ; ".join(_example(a, starboard) for a in carriers[:3]) + "."
        saved = max(a.saved for a in carriers)
        tail = ("Chaque mot s'écrit aussi avec son contour long, qui reste valable : "
                "le contour court " + _savedText(saved).replace("économise", "économise au plus") + ".")
        words = [_wordRecord(g, starboard, phonologyByIdx.get(g[0].wordIdx, ""),
                             f"{what} {doc['label'].split(' ', 1)[1]} · {_savedText(g[0].saved)}") for g in groups]
        emit(f"Leçon {numberInFrench(n)} : {doc['label']}", _sectionTitle(i, len(rules)), doc["keys"],
             [intro, examples, tail], words)

    verbs = _top(a for a in abbreviations if a.route >= 1 and isVerb(a.gramCat))
    if verbs:
        n = len(lessons) + 1
        intro = ("Une forme conjuguée garde sa marque de conjugaison (voir la légende des marques) : "
                 "l'abréviation raccourcit la base du verbe, puis reprend la marque et les frappes qui la suivent.")
        examples = "Exemples : " + " ; ".join(_example(a, starboard) for a in verbs[:3]) + "."
        # one example per conjugated form / homograph (no dedupe by spelling); each accepts its short or long outline
        words = [_wordRecord([a], starboard, phonologyByIdx.get(a.wordIdx, ""),
                             " · ".join(t for t in (formByIdx.get(a.wordIdx, "forme conjuguée"),
                                                    _savedText(a.saved)) if t)) for a in verbs]
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
    formByIdx = {r.idx: f"{r.lemme} : {conjugationText(r.infoVerb)}" if r.infoVerb else r.lemme
                 for r in loaded.records}
    document = buildAffixLessons(loadRuleSpecs(RULES_JSON), loaded.abbreviations, starboard, phonologyByIdx, formByIdx)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}: {len(document['rules'])} rules, {len(document['lessons'])} lessons, "
          f"{sum(len(l['words']) for l in document['lessons'])} words.")


if __name__ == "__main__":
    main()
