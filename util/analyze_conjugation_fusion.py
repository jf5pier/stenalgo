"""
Hand-run diagnostic: what if the conjugation disambiguation key were FUSED into the word's last
stroke (an attached suffix keypress) instead of being the extra coda stroke of the Realization Phase?

Each word needing one or more Grouping Phase keypress groups gets, hypothetically, its last base
stroke united with the chosen key(s) of its groups (`realization_report.json`), instead of a trailing
stroke. Every hypothetical outline is rendered and compared with every other word's. Per group
(a word needing several groups counts in each) and overall, a word is:

- clean: no other spelling lands on its outline;
- abbrev-only: no full-form conflict, but its outline is an affix-abbreviation outline of another word;
- same lemma+category / same lemma, other category / cross-lemma conflict: the closest conflicting word.
  A cross-lemma pair whose base strokes are already equal is an existing homophone (the star/hash
  marks' job today); otherwise it is NEW, created by the fusion;
- unpressable: the fused last stroke has no cost (`getStrokeCost` is None). This is often NOT the fusion's
  doing: the base coda is already unpressable (see `baseUnpressable`).

Star/hash marks are left out. "absorbed" counts words whose key is already in their last stroke (the stroke
does not change). Frequency is the film frequency.

Prerequisites: both pickles or DisambiguatedTheory.pickle, starboard3h.json, keypress_groups.json,
resolved_press_sets.json, realization_report.json, plover_stenalgo_affix_dictionary.json.
Outputs: docs/CONJUGATION_FUSION_STATS.md (OUT to choose). ~3 min.

Run: python -m util.analyze_conjugation_fusion [OUT]
"""
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from src.ambiguitychecker import (
    buildKeypressGroupExtraAlternates,
    buildKeypressGroupToWords,
    buildWordToGroups,
)
from src.keyboard import Starboard, Strokes
from src.word import Word
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadPhoneticAndDisambiguatedTheory

OUTPUT_PATH = "docs/CONJUGATION_FUSION_STATS.md"
CATEGORIES = ("clean", "abbrevOnly", "sameLemmaGC", "sameLemmaOtherCat", "crossLemmaNew",
              "crossLemmaHomophone", "unpressable")
CONFLICT_RANK = {"sameLemmaGC": 0, "sameLemmaOtherCat": 1, "crossLemma": 2}
EXAMPLES = 4


@dataclass
class Verdict:
    category: str
    partner: Word | None = None
    abbreviation: str | None = None


def _fuse(base: Strokes, keys: set[int]) -> Strokes:
    if not keys:
        return base
    return base[:-1] + (tuple(sorted(set(base[-1]) | keys)),)


def _conflictKind(word: Word, other: Word) -> str:
    if word.lemmeGramCat == other.lemmeGramCat:
        return "sameLemmaGC"
    return "sameLemmaOtherCat" if word.lemme == other.lemme else "crossLemma"


def _pct(part: float, whole: float) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "-"


def main() -> None:
    output = sys.argv[1] if len(sys.argv) > 1 else OUTPUT_PATH
    keyboard = Starboard.fromJSONFile("starboard3h.json")
    if keyboard is None:
        raise RuntimeError("starboard3h.json not found; run from the repo root.")
    _phonetic, disambiguated, wordToStrokes, wordsByOrthoLemme = loadPhoneticAndDisambiguatedTheory(keyboard)

    with open("realization_report.json", encoding="utf-8") as f:
        report: dict[str, Any] = json.load(f)["keypressGroups"]
    keysOf = {int(g): tuple(v["chosenKeys"]) for g, v in report.items()}
    with open("keypress_groups.json", encoding="utf-8") as f:
        markers = {int(g): frozenset(m) for g, m in json.load(f)["markersByKeypress"].items()}
    with open("resolved_press_sets.json", encoding="utf-8") as f:
        resolved = json.load(f)
    groupToWords = buildKeypressGroupToWords(resolved, markers, wordToStrokes, wordsByOrthoLemme)
    extraSets = buildKeypressGroupExtraAlternates(resolved, markers, wordToStrokes, wordsByOrthoLemme)
    wordToGroups = buildWordToGroups(groupToWords)
    with open("plover_stenalgo_affix_dictionary.json", encoding="utf-8") as f:
        affix: dict[str, str] = json.load(f)

    def render(strokes: Strokes) -> str:
        return renderFinalStrokesToRTFCRE(keyboard, strokes)

    def keysOfGroups(groups: frozenset[int] | set[int]) -> set[int]:
        return {k for g in groups for k in keysOf[g]}

    fused: dict[Word, str] = {}
    byOutline: dict[str, list[Word]] = defaultdict(list)
    unpressable: set[Word] = set()
    baseUnpressable: set[Word] = set()
    for word in disambiguated:
        base = wordToStrokes[word]
        keys = keysOfGroups(wordToGroups.get(word, frozenset()))
        stroke = _fuse(base, keys)
        if keyboard.getStrokeCost(base[-1], "coda") is None:
            baseUnpressable.add(word)
        if keys and keyboard.getStrokeCost(stroke[-1], "coda") is None:
            unpressable.add(word)
        fused[word] = render(stroke)
        byOutline[fused[word]].append(word)
        for groups in extraSets.get(word, ()):
            alternate = render(_fuse(base, keysOfGroups(groups)))
            if alternate != fused[word]:
                byOutline[alternate].append(word)

    def judge(word: Word) -> Verdict:
        if word in unpressable:
            return Verdict("unpressable")
        best: Word | None = None
        bestKind = ""
        for other in byOutline[fused[word]]:
            if other is word or other.ortho == word.ortho:
                continue
            kind = _conflictKind(word, other)
            if best is None or CONFLICT_RANK[kind] < CONFLICT_RANK[bestKind]:
                best, bestKind = other, kind
        if best is not None:
            if bestKind == "crossLemma":
                sameBase = render(wordToStrokes[word]) == render(wordToStrokes[best])
                return Verdict("crossLemmaHomophone" if sameBase else "crossLemmaNew", best)
            return Verdict(bestKind, best)
        abbreviation = affix.get(fused[word])
        if abbreviation and abbreviation != word.ortho:
            return Verdict("abbrevOnly", None, abbreviation)
        return Verdict("clean")

    verdicts = {word: judge(word) for word in disambiguated if word in wordToGroups}

    lines = [
        "# Conjugation key fused into the last stroke: conflict statistics",
        "",
        "Generated by `python -m util.analyze_conjugation_fusion` (see its docstring for the method).",
        "Question: if the 7 conjugation keypress groups were an attached suffix key (united with the word's last",
        "stroke) instead of the extra coda stroke, how many words would conflict? Star/hash marks left out;",
        "a word needing several groups counts in each. Freq = film frequency share.",
        "",
    ]

    def section(title: str, words: list[Word]) -> None:
        total = len(words)
        freq = sum(w.frequency for w in words)
        count: Counter[str] = Counter()
        mass: Counter[str] = Counter()
        examples: dict[str, list[Word]] = defaultdict(list)
        for word in words:
            category = verdicts[word].category
            count[category] += 1
            mass[category] += word.frequency  # type: ignore[assignment]
            examples[category].append(word)
        absorbed = sum(1 for w in words if fused[w] == render(wordToStrokes[w]))
        lines.extend([f"## {title}", "", f"{total} words, absorbed (stroke unchanged): {absorbed}", "",
                      "| Outcome | Words | Share | Freq |", "|---|---|---|---|"])
        for category in CATEGORIES:
            lines.append(f"| {category} | {count[category]} | {_pct(count[category], total)} "
                         f"| {_pct(mass[category], freq)} |")
        lines.append("")
        for category in CATEGORIES[1:6]:
            for word in sorted(examples[category], key=lambda w: -w.frequency)[:EXAMPLES]:
                verdict = verdicts[word]
                target = (f"abbreviation of `{verdict.abbreviation}`" if verdict.abbreviation
                          else f"`{verdict.partner.ortho}` ({verdict.partner.gramCat.name}, {verdict.partner.lemme})"
                          if verdict.partner else "")
                lines.append(f"- {category}: `{word.ortho}` [{fused[word]}] vs {target}")
        lines.append("")

    section("All words needing at least one group", list(verdicts))
    for group in sorted(keysOf, key=lambda g: -len(groupToWords.get(g, []))):
        section(f"Group {group}: {'+'.join(sorted(markers[group]))} (key {keysOf[group]})",
                [w for w in groupToWords.get(group, []) if w in verdicts])

    codas: Counter[tuple[int, ...]] = Counter()
    sample: dict[tuple[int, ...], list[str]] = defaultdict(list)
    for word in baseUnpressable:
        coda = tuple(sorted(k for k in wordToStrokes[word][-1] if k >= 16))
        codas[coda] += 1
        sample[coda].append(word.ortho)
    lines.extend(["## baseUnpressable", "",
                  f"{len(baseUnpressable)} words of the disambiguated theory whose BASE last stroke already has no cost "
                  "(independent of the fusion; see TODO.md, unpressable base codas).", "",
                  "| Coda keys | Words | Examples |", "|---|---|---|"])
    for coda, n in codas.most_common(12):
        lines.append(f"| {coda} | {n} | {', '.join(sample[coda][:5])} |")
    lines.append("")
    with open(output, "w", encoding="utf-8") as f:
        _ = f.write("\n".join(lines))
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
