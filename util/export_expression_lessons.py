"""
Theory Export (S8)-style trainer branch for the expression abbreviation layer: the `expressions` lesson track of the
steno trainer. One lesson per rule family (a particle and its elision twin share a chord, so they share a lesson), then
lessons on phrases that combine several abbreviations in one outline, then four lessons on the forced briefs.

Run: python -m util.export_expression_lessons
Requires the inputs of util.export_expression_data (both pickles, starboard3h.json and the committed expression files of
scratch/: expr-rules-final.json, expr-briefs.tsv, expr_candidates.tsv). Nothing is composed from the plugin's data file.
Output: steno-trainer/public/data/expression-lessons.json
    {"rules": [{"rank", "kind", "position", "units", "keys", "keyNames", "family", "label"[, "steno"]}, ...],
     "lessons": [<lesson>, ...]}
A lesson has exactly the `lessons.json` lesson schema (docs/specs/lessons.md); its words are `practice-words.json` records
whose `steno`/`strokes` are the COMPOSED outline plus an `alternates` list of the other accepted outlines (the plain
word-by-word outline and the partial compositions, as {steno, strokes}) and `ruleRanks`, the ranks of the rules the
composition fires. See docs/specs/expression-lessons.md.

The other trainer data files are not touched: the expression layer is optional, like the affix one.
"""
from __future__ import annotations

import csv
import itertools
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from src.affixes import SimContext
from src.expressionmodel import PREFIX
from src.expressions import MERGED, STANDALONE, AttachRule, BriefRule, Composition, Rules, composeOutlineTraced
from src.expressionrules import PoolExpression
from src.keyboard import Starboard, Strokes, canonicalizeStrokes
from util._expressioninput import CANDIDATES, loadExpressionInputs
from util.export_expression_data import writtenText
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_affix_lessons import _savedText, groupKeyNames
from util.export_lessons import RECORD_FIELDS, numberInFrench

KEYBOARD_JSON = "starboard3h.json"
OUTPUT_PATH = "steno-trainer/public/data/expression-lessons.json"

TRACK = "expressions"
RULE_KIND = "expression"
WORDS_PER_LESSON = 20
MIN_FAMILY_ITEMS = 10          # a family with fewer one-piece phrases is topped up with multi-piece ones
FAMILIES_PER_SECTION = 10
MAX_ALTERNATES = 8             # accepted outlines besides the composed one: the longform always, partial compositions fill the rest
TWO_PIECE_LESSONS = 2          # composed lessons: two-piece phrases fill up to this many lessons, then one for three pieces or more
BRIEFS_PER_LESSON = 10
BRIEF_LESSONS = 4

SECTION_COMPOSED = "Les phrases composées"
SECTION_BRIEFS = "Les mots et les expressions abrégés"


@dataclass(frozen=True)
class Composed:
    """A pool phrase and what the composer makes of it."""
    expr: PoolExpression
    comp: Composition
    fired: tuple[AttachRule | BriefRule, ...]     # the rules that shortened it (merged or standalone attaches, briefs)
    longform: Strokes


def firedRules(comp: Composition) -> tuple[AttachRule | BriefRule, ...]:
    """The rules whose abbreviation is in the outline, in stream order, without repeats."""
    out: list[AttachRule | BriefRule] = []
    for seg in comp.segments:
        rule = seg.rule
        if seg.kind == "brief" and isinstance(rule, BriefRule) and rule not in out:
            out.append(rule)
        elif seg.kind == "attach" and isinstance(rule, AttachRule) and seg.outcome in (MERGED, STANDALONE) \
                and rule not in out:
            out.append(rule)
    return tuple(out)


def composeAll(rules: Rules, pool: Sequence[PoolExpression], ctx: SimContext) -> list[Composed]:
    """Every pool phrase that the rules shorten, in the total order (-frequency, units)."""
    out = []
    for expr in sorted(pool, key=lambda e: (-e.freq, e.units)):
        comp = composeOutlineTraced(rules, expr.tokens, ctx)
        if comp.strokes is None or comp.saving < 1:
            continue
        longform = canonicalizeStrokes(tuple(s for t in expr.tokens for s in t.strokes))
        out.append(Composed(expr, comp, firedRules(comp), longform))
    return out


def partialOutlines(rules: Rules, item: Composed, ctx: SimContext) -> list[Strokes]:
    """Outlines of the phrase with only some of its fired rules applied (neither the full composition nor the
    longform), the most applied rules first, no duplicates."""
    found: dict[Strokes, int] = {}
    fired = item.fired
    for size in range(len(fired) - 1, 0, -1):
        for subset in itertools.combinations(fired, size):
            partial = Rules(briefs=tuple(r for r in subset if isinstance(r, BriefRule)),
                            attaches=tuple(r for r in subset if isinstance(r, AttachRule)), orderBan=rules.orderBan)
            outline = composeOutlineTraced(partial, item.expr.tokens, ctx).strokes
            if outline is not None and outline != item.comp.strokes and outline != item.longform \
                    and outline not in found:
                found[outline] = size
    return sorted(found, key=lambda o: (-found[o], o))


# --- rules -------------------------------------------------------------------------------------------------------

def _particles(rule: AttachRule) -> str:
    return " ".join(rule.expression)


def _twin(rule: AttachRule, attaches: Sequence[AttachRule]) -> AttachRule | None:
    """The other half of an elision pair: same family and chord, the other form."""
    for other in attaches:
        if other is not rule and other.family == rule.family and other.keypress == rule.keypress \
                and other.position == rule.position and other.elision and other.elision != rule.elision:
            return other
    return None


def attachLabel(rule: AttachRule, attaches: Sequence[AttachRule]) -> str:
    twin = _twin(rule, attaches)
    where = "au mot suivant" if rule.position == PREFIX else "au mot précédent"
    names = f"« {_particles(rule)} »" + (f" ou « {_particles(twin)} »" if twin else "")
    return f"{names} : se joint {where}"


def briefLabel(rule: BriefRule) -> str:
    return f"abréviation de « {' '.join(rule.expression)} »"


def familyScores(rules: Rules, composed: Sequence[Composed]) -> dict[str, float]:
    """Frequency-weighted saving of the phrases each family's rules take part in (a family counts once per phrase)."""
    scores: dict[str, float] = {r.family: 0.0 for r in rules.attaches}
    for item in composed:
        for family in {r.family for r in item.fired if isinstance(r, AttachRule)}:
            scores[family] += item.expr.freq * item.comp.saving
    return scores


def rankRules(rules: Rules, composed: Sequence[Composed]) -> tuple[list[str], list[AttachRule], list[BriefRule]]:
    """Families by descending score (then name); attach rules by family rank, base form before elided form, then
    units; briefs by descending frequency of their phrase, then units. Ranks are the 1-based positions in the list
    attaches + briefs."""
    scores = familyScores(rules, composed)
    families = sorted(scores, key=lambda f: (-scores[f], f))
    rankOf = {f: i for i, f in enumerate(families)}
    attaches = sorted(rules.attaches, key=lambda r: (rankOf[r.family], r.elision == "elided", r.expression))
    freqOf = {c.expr.units: c.expr.freq for c in composed}
    briefs = sorted(rules.briefs, key=lambda r: (-freqOf.get(r.expression, 0.0), r.expression))
    return families, attaches, briefs


# --- records and text ----------------------------------------------------------------------------------------------

def _strokesList(strokes: Strokes) -> list[list[int]]:
    return [sorted(stroke) for stroke in strokes]


def _outlineDoc(starboard: Starboard, outline: Strokes) -> dict[str, Any]:
    return {"steno": renderFinalStrokesToRTFCRE(starboard, outline), "strokes": _strokesList(outline)}


def wordRecord(item: Composed, rules: Rules, ctx: SimContext, starboard: Starboard, phonology: str, label: str,
               ranks: dict[AttachRule | BriefRule, int], primary: Strokes | None = None) -> dict[str, Any]:
    """`primary` overrides the composed outline as the hint (the brief lessons show the brief's own stroke)."""
    outline = primary or item.comp.strokes
    assert outline is not None
    values = {"ortho": writtenText(item.expr.units), "before": "", "after": "", "label": label,
              "phonology": phonology, "steno": renderFinalStrokesToRTFCRE(starboard, outline),
              "strokes": _strokesList(outline), "frequency": item.expr.freq}
    record: dict[str, Any] = {field: values[field] for field in RECORD_FIELDS}
    others: list[Strokes] = []
    if item.comp.strokes is not None and item.comp.strokes != outline:
        others.append(item.comp.strokes)
    others += [o for o in partialOutlines(rules, item, ctx) if o != outline]
    kept = others[:MAX_ALTERNATES - 1]
    if item.longform != outline and item.longform not in kept:
        kept.append(item.longform)          # the plain outline always stays accepted
    record["alternates"] = [_outlineDoc(starboard, o) for o in kept]
    record["ruleRanks"] = sorted({ranks[r] for r in item.fired})
    return record


def _example(item: Composed, starboard: Starboard, outline: Strokes | None = None) -> str:
    shown = outline or item.comp.strokes
    assert shown is not None
    return (f"« {writtenText(item.expr.units)} » : {renderFinalStrokesToRTFCRE(starboard, item.longform)} → "
            f"{renderFinalStrokesToRTFCRE(starboard, shown)}")


def _sectionTitle(index: int, count: int) -> str:
    """Families grouped by ten, titles spelled in words (the IPA toggle rewrites digits, spec §8)."""
    first = index // FAMILIES_PER_SECTION * FAMILIES_PER_SECTION
    last = min(first + FAMILIES_PER_SECTION, count)
    if first == 0:
        return f"Les {numberInFrench(last)} premières familles" if last > 1 else "La première famille"
    return f"Les familles {numberInFrench(first + 1)} à {numberInFrench(last)}"


def _familyLabel(family: str, attaches: Sequence[AttachRule]) -> str:
    texts: list[str] = []
    for r in attaches:
        if r.family == family:
            for text in (_particles(r),):
                if text not in texts:
                    texts.append(text)
    return " · ".join(f"« {t} »" for t in texts)


def ruleRanks(rules: Rules, pool: Sequence[PoolExpression], ctx: SimContext) -> dict[AttachRule | BriefRule, int]:
    """The rank of every rule in the lessons' `rules` list (shared with the expression sentences, whose records
    name the rules they use by these ranks)."""
    _families, attaches, briefs = rankRules(rules, composeAll(rules, pool, ctx))
    ordered: list[AttachRule | BriefRule] = [*attaches, *briefs]
    return {r: i + 1 for i, r in enumerate(ordered)}


def buildExpressionLessons(rules: Rules, pool: Sequence[PoolExpression], ctx: SimContext, starboard: Starboard,
                           phonologyByUnits: dict[tuple[str, ...], str] | None = None) -> dict[str, Any]:
    """Pure builder: the committed rule set and pool -> the `expression-lessons.json` document."""
    phonologyByUnits = phonologyByUnits or {}
    composed = composeAll(rules, pool, ctx)
    families, attaches, briefs = rankRules(rules, composed)
    ordered: list[AttachRule | BriefRule] = [*attaches, *briefs]
    ranks: dict[AttachRule | BriefRule, int] = {r: i + 1 for i, r in enumerate(ordered)}
    ruleDocs: list[dict[str, Any]] = []
    for r in attaches:
        keys = sorted(r.keypress)
        ruleDocs.append({"rank": ranks[r], "kind": "attach", "position": r.position, "units": list(r.expression),
                         "keys": keys, "keyNames": [starboard.keyDisplayName(k) for k in keys], "family": r.family,
                         "label": attachLabel(r, attaches)})
    for b in briefs:
        keys = sorted({k for stroke in b.strokes for k in stroke})
        ruleDocs.append({"rank": ranks[b], "kind": "brief", "position": "", "units": list(b.expression),
                         "keys": keys, "keyNames": [starboard.keyDisplayName(k) for k in keys], "family": "",
                         "label": briefLabel(b), "steno": renderFinalStrokesToRTFCRE(starboard, b.strokes)})
    lessons: list[dict[str, Any]] = []

    def emit(title: str, sectionTitle: str, newKeys: list[int], newChords: list[list[int]], rulesText: list[str],
             words: list[dict[str, Any]]) -> None:
        index = len(lessons) + 1
        lessons.append({
            "id": f"{TRACK}-{index:02d}", "track": TRACK, "index": index, "sectionTitle": sectionTitle,
            "title": title, "kind": TRACK, "newKeys": newKeys, "newChords": newChords,
            "rules": [{"kind": RULE_KIND, "text": t} for t in rulesText], "words": words})

    def record(item: Composed, label: str, primary: Strokes | None = None) -> dict[str, Any]:
        return wordRecord(item, rules, ctx, starboard, phonologyByUnits.get(item.expr.units, ""), label, ranks, primary)

    # 1. one lesson per rule family
    for position, family in enumerate(families):
        mine = [r for r in attaches if r.family == family]
        singles = [c for c in composed if len(c.fired) == 1 and c.fired[0] in mine]
        items = singles[:WORDS_PER_LESSON]
        if len(singles) < MIN_FAMILY_ITEMS:
            more = [c for c in composed if len(c.fired) >= 2 and any(r in mine for r in c.fired)]
            items = (singles + more)[:WORDS_PER_LESSON]
        if not items:
            continue
        chords = sorted({tuple(sorted(r.keypress)) for r in mine})
        names = "; ".join(f"{groupKeyNames([starboard.keyDisplayName(k) for k in chord])} pour "
                          + " ou ".join(dict.fromkeys(f"« {_particles(r)} »" for r in mine
                                                       if tuple(sorted(r.keypress)) == chord))
                          for chord in chords)
        where = "suivant" if mine[0].position == PREFIX else "précédent"
        intro = (f"Les touches pressées avec un mot ajoutent une particule : {names}. Elles se joignent à la frappe "
                 f"du mot {where}, ou forment une frappe à elles seules quand elles ne peuvent pas s'y joindre.")
        examples = "Par exemple : " + " ; ".join(_example(c, starboard) for c in items[:3]) + "."
        tail = ("Le contour long de chaque phrase reste valable, comme celui où une partie seulement des "
                "abréviations est faite.")
        n = len(lessons) + 1
        emit(f"Leçon {numberInFrench(n)} : {_familyLabel(family, mine)}", _sectionTitle(position, len(families)),
             sorted({k for r in mine for k in r.keypress}), [list(c) for c in chords if len(c) >= 2],
             [intro, examples, tail], [record(c, _savedText(c.comp.saving)) for c in items])

    # 2. phrases that combine several abbreviations
    multi = [c for c in composed if len(c.fired) >= 2]
    two = [c for c in multi if len(c.fired) == 2]
    threePlus = [c for c in multi if len(c.fired) >= 3]
    batches = [two[i * WORDS_PER_LESSON:(i + 1) * WORDS_PER_LESSON] for i in range(TWO_PIECE_LESSONS)]
    batches.append(threePlus[:WORDS_PER_LESSON])
    for i, batch in enumerate(b for b in batches if b):
        n = len(lessons) + 1
        intro = ("Ces phrases réunissent plusieurs abréviations dans un même contour : chaque particule se joint à "
                 "la frappe voisine, ou une abréviation d'expression absorbe les mots qui l'entourent.")
        examples = "Par exemple : " + " ; ".join(_example(c, starboard) for c in batch[:3]) + "."
        tail = "Chaque phrase s'écrit aussi mot à mot, ou avec une partie seulement de ses abréviations."
        emit(f"Leçon {numberInFrench(n)} : les phrases composées, partie {numberInFrench(i + 1)}", SECTION_COMPOSED,
             [], [], [intro, examples, tail],
             [record(c, f"{numberInFrench(len(c.fired))} abréviations · {_savedText(c.comp.saving)}") for c in batch])

    # 3. the forced briefs, most frequent first. Each is composed ALONE: the composer matches attach particles before
    # briefs, so with the whole rule set a phrase such as `avec` or `toutes les` is not abbreviated by its brief.
    poolByUnits = {e.units: e for e in pool}
    freqOf = {e.units: e.freq for e in pool}
    briefItems: list[tuple[BriefRule, Composed]] = []
    for b in sorted(briefs, key=lambda r: (-freqOf.get(r.expression, 0.0), r.expression)):
        expr = poolByUnits.get(b.expression)
        if expr is None:
            continue
        alone = composeOutlineTraced(Rules(briefs=(b,)), expr.tokens, ctx)
        longform = canonicalizeStrokes(tuple(s for t in expr.tokens for s in t.strokes))
        if alone.strokes is not None:
            briefItems.append((b, Composed(expr, alone, (b,), longform)))
    for i in range(BRIEF_LESSONS):
        briefBatch = briefItems[i * BRIEFS_PER_LESSON:(i + 1) * BRIEFS_PER_LESSON]
        if not briefBatch:
            continue
        n = len(lessons) + 1
        intro = ("Chaque abréviation de cette leçon remplace un mot ou une expression par une seule frappe, "
                 "à apprendre telle quelle.")
        examples = "Par exemple : " + " ; ".join(_example(c, starboard) for _, c in briefBatch[:3]) + "."
        tail = "Le contour mot à mot reste valable."
        emit(f"Leçon {numberInFrench(n)} : les abréviations, partie {numberInFrench(i + 1)}", SECTION_BRIEFS,
             [], [], [intro, examples, tail],
             [record(c, _savedText(c.comp.saving)) for _, c in briefBatch])
    return {"rules": ruleDocs, "lessons": lessons}


def loadPhonologies() -> dict[tuple[str, ...], str]:
    """Phonology of each pool phrase (its units' phonologies joined by dots) from the candidate file."""
    out: dict[tuple[str, ...], str] = {}
    with open(CANDIDATES, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            parts = [p.split("=", 1) for p in row["phonologies"].split(",") if p]
            out[tuple(p[0] for p in parts)] = ".".join(p[1] for p in parts if len(p) == 2)
    return out


def main() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    ctx, rules, pool, _words, _unitStrokes = loadExpressionInputs()
    document = buildExpressionLessons(rules, pool, ctx, starboard, loadPhonologies())
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(document, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}: {len(document['rules'])} rules, {len(document['lessons'])} lessons, "
          f"{sum(len(lesson['words']) for lesson in document['lessons'])} words.")


if __name__ == "__main__":
    main()
