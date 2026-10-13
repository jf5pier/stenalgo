"""
Compare the Stenalgo theory (Starboard layout) with the Pluvier French theory (Ireland layout) on one word universe.

Run: python -m util.compare_theories [--stenalgo-dict plover_stenalgo_dictionary.json] [--stenalgo-layout starboard3h.json]
         --pluvier-dict PATH/dicofr.json [--pluvier-dict PATH/more.json ...] [--pluvier-dup PATH/dup.json]
         [--stenalgo-abbreviations affix_abbreviations.tsv] [--lexicon resources/Lexique383.tsv]
         [--phoneme-keys resources/pluvierPhonemeKeys.tsv] [--freq films|livres] [--out DIR]
`--pluvier-dict` is repeated for the Pluvier files in priority order, LOWEST first (a later file takes an outline from an earlier one:
dicofr.json, dicofr-plural.json, verbs.json, then the tao_la_salle_simple.json briefs); `--pluvier-dup` is the generator's collision record.
Requires: the Stenalgo and Pluvier dictionaries, starboard3h.json, Lexique383.tsv, resources/pluvierPhonemeKeys.tsv. No pickle is read.
Output: DIR/theory_comparison.json and DIR/theory_comparison.md (default DIR = the repo root, untracked), and the table on
stdout. Two runs on the same inputs give byte-identical files.

Metrics (definitions and the choices made are in the docstring of `src/theorycompare.py`): word coverage, collisions on the
words both theories cover, frequency-weighted strokes per word, frequency-weighted chord cost (Stenalgo on Starboard, Pluvier
converted to Starboard keys, Pluvier on the Ireland model of `src/irelandkeyboard.py`), and the frequency-weighted share of
words whose phoneme order is not left to right in the outline. The CP-SAT score is not part of this tool; the report is a
dict of named metrics so one can be added.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from typing import Any, Callable

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plover_stenalgo"))

from plover_stenalgo._generated_keys import GEMINI_PR_KEYMAP, KEYS  # type: ignore[import-not-found]  # noqa: E402
from plover_stenalgo.stroke import parseStroke  # type: ignore[import-not-found]  # noqa: E402

from src import theorycompare as tc  # noqa: E402
from src.irelandkeyboard import KEYS as IRELAND_KEYS, IrelandKeyboard  # noqa: E402
from src.keyboard import Starboard  # noqa: E402
from util.export_plover_complements import convertStroke, starboardKeys  # noqa: E402


def md5(path: str) -> str:
    digest = hashlib.md5()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def gitCommit(path: str) -> str | None:
    """The commit of the clone holding `path` (read-only `git rev-parse`), None when it is not a clone."""
    try:
        done = subprocess.run(["git", "-C", os.path.dirname(os.path.abspath(path)), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True)
        return done.stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def parseStenalgoOutline(text: str) -> tuple[tuple[int, ...], ...] | None:
    strokes = tuple(parseStroke(s) for s in text.split("/"))
    if any(s is None for s in strokes):
        return None
    return strokes  # type: ignore[return-value]


def compare(args: argparse.Namespace) -> dict[str, Any]:
    board = Starboard.fromJSONFile(args.stenalgo_layout)
    if board is None:
        raise SystemExit(f"cannot read the layout {args.stenalgo_layout}")
    buttonKey = starboardKeys(KEYS, GEMINI_PR_KEYMAP)
    ireland = IrelandKeyboard()

    lexicon = tc.loadLexicon(args.lexicon, args.freq)
    freq = lexicon.freq
    sten = tc.loadStenalgoTheory(args.stenalgo_dict, parseStenalgoOutline)
    pluvierFiles = [args.pluvier_dict] if isinstance(args.pluvier_dict, str) else list(args.pluvier_dict)
    plu = tc.loadPluvierTheory(pluvierFiles, args.pluvier_dup)

    stenCache: dict[str, int | None] = {}
    pluCache: dict[str, int | None] = {}

    def stenStroke(text: str) -> int | None:
        if text not in stenCache:
            keys = parseStroke(text)
            stenCache[text] = None if keys is None else board.getChordCost(keys)
        return stenCache[text]

    def pluStroke(text: str) -> int | None:
        """A Pluvier chord converted key to key to the Starboard, priced there."""
        if text not in pluCache:
            converted = convertStroke(text, buttonKey)
            pluCache[text] = board.getChordCost(converted[0]) if converted else None
        return pluCache[text]

    tallSCache: dict[str, int | None] = {}

    def pluStrokeTallS(text: str) -> int | None:
        """The same conversion, but the Ireland `S` (one tall key) is pressed on whichever of the two Starboard pinky
        keys, 2 (top) or 3 (bottom), is cheaper: the Gemini mapping alone always uses the bottom one."""
        if text not in tallSCache:
            converted = convertStroke(text, buttonKey)
            if not converted:
                tallSCache[text] = None
            else:
                options = [converted[0]]
                if 3 in converted[0]:
                    options.append(tuple(sorted({2 if k == 3 else k for k in converted[0]})))
                priced = [c for c in (board.getChordCost(o) for o in options) if c is not None]
                tallSCache[text] = min(priced) if priced else None
        return tallSCache[text]

    sten.choose(stenStroke)
    plu.choose(pluStroke)
    # the short form: the same words with the affix abbreviations (S9b, `affix_abbreviations.tsv`) added to their outlines, each word
    # taking its cheapest (fewest strokes, then cost); None when the file is not given. Expression (phrase) abbreviations are word
    # sequences and have no per-word outline: not part of it.
    short: tc.TheoryView | None = None
    if args.stenalgo_abbreviations:
        short = tc.withAbbreviations(sten, tc.loadAbbreviations(args.stenalgo_abbreviations))
        short.choose(stenStroke)

    universe = set(freq)
    stenCovered, pluCovered = set(sten.outlines) & universe, set(plu.outlines) & universe
    common = stenCovered & pluCovered

    stenCosts = tc.outlineCosts(sten, stenStroke, stenCovered)
    pluOnStar = tc.outlineCosts(plu, pluStroke, pluCovered)
    pluOnIre = tc.outlineCosts(plu, lambda s: ireland.getStrokeCost(s), pluCovered)
    pluOnStarTallS = tc.outlineCosts(plu, pluStrokeTallS, pluCovered)
    # the cheapest one-key stroke of each keyboard stands for "a low-cost keypress" that disambiguates a collision
    extraOnStar = min(c for c in (board.getChordCost((k,)) for k in range(26)) if c is not None)
    extraOnIre = min(c for c in (ireland.getChordCost((k,)) for k in IRELAND_KEYS) if c is not None)

    # phoneme order
    encoder = tc.PluvierEncoder(args.phoneme_keys)
    stenViol: dict[str, int | None] = {}
    pluViol: dict[str, int | None] = {}
    pluMatch: dict[str, float] = {}
    for w in sorted(universe):
        syll = lexicon.syll[w]
        total: int | None = 0
        for syllable in syll.split("-"):
            groups = tc.starboardGroups(board, syllable)
            if groups is None or total is None:
                total = None
            else:
                total += tc.countViolations(groups)
        stenViol[w] = total
        encoded = encoder.encodeWord(syll)
        if encoded is None:
            pluViol[w] = None
        else:
            pluViol[w] = tc.pluvierViolations(encoded[0])
            if w in plu.outlines:
                pluMatch[w] = float(encoded[1] in plu.outlines[w])

    def resolved(words: set[str], rule: str) -> dict[str, Any]:
        """Strokes per word and complexity if every colliding word got one more, cheap, stroke."""
        markedSten = tc.markedForResolution(sten, freq, words & stenCovered, rule)
        markedPlu = tc.markedForResolution(plu, freq, words & pluCovered, rule)
        return {
            "markedWords": {"stenalgo": len(markedSten), "pluvier": len(markedPlu),
                            "pluvierFrequencyShare": tc.share(tc.mass(freq, markedPlu), tc.mass(freq, words & pluCovered))},
            "strokesPerWord": {"stenalgo": tc.strokesPerWordResolved(sten, freq, words & stenCovered, markedSten),
                               "pluvier": tc.strokesPerWordResolved(plu, freq, words & pluCovered, markedPlu)},
            "complexity": {
                "stenalgoOnStarboard": tc.complexity(tc.costsResolved(stenCosts, markedSten, extraOnStar), freq, words & stenCovered),
                "pluvierOnStarboard": tc.complexity(tc.costsResolved(pluOnStar, markedPlu, extraOnStar), freq, words & pluCovered),
                "pluvierOnStarboardTallS": tc.complexity(tc.costsResolved(pluOnStarTallS, markedPlu, extraOnStar), freq,
                                                         words & pluCovered),
                "pluvierOnIreland": tc.complexity(tc.costsResolved(pluOnIre, markedPlu, extraOnIre), freq, words & pluCovered),
            },
        }

    def longResolved(words: set[str], rule: str) -> dict[str, Any]:
        """Pluvier's long form with one more stroke on each word whose LONG outline is claimed by another word."""
        marked = tc.markedForResolution(pluLong, freq, words & pluCovered, rule)
        return {"markedWords": len(marked),
                "markedFrequencyShare": tc.share(tc.mass(freq, marked), tc.mass(freq, words & pluCovered)),
                "strokesPerWord": tc.strokesPerWordResolved(pluLong, freq, words & pluCovered, marked),
                "costOnStarboard": tc.complexity(tc.costsResolved(pluLongOnStar, marked, extraOnStar), freq, words & pluCovered),
                "costOnIreland": tc.complexity(tc.costsResolved(pluLongOnIre, marked, extraOnIre), freq, words & pluCovered)}

    def block(words: set[str]) -> dict[str, Any]:
        shortBlock: dict[str, Any] = {}
        if short is not None and shortCosts is not None:
            abbreviated = {w for w in words & stenCovered if short.chosen[w] != sten.chosen[w]}
            shortBlock = {"stenalgoShort": {
                "strokesPerWord": tc.strokesPerWord(short, freq, words & stenCovered),
                "complexity": tc.complexity(shortCosts, freq, words & stenCovered),
                "abbreviatedWords": len(abbreviated),
                "abbreviatedFrequencyShare": tc.share(tc.mass(freq, abbreviated), tc.mass(freq, words & stenCovered))}}
        multi = {w for w in words & pluCovered if len(plu.outlines[w]) > 1}
        differing = {w for w in multi if pluLong.chosen[w] != plu.chosen[w]}
        pluLongBlock = {
            "wordsWithSeveralOutlines": len(multi),
            "severalOutlinesFrequencyShare": tc.share(tc.mass(freq, multi), tc.mass(freq, words & pluCovered)),
            "wordsWithDifferentLongAndShort": len(differing),
            "differentFrequencyShare": tc.share(tc.mass(freq, differing), tc.mass(freq, words & pluCovered)),
            "strokesPerWord": tc.strokesPerWord(pluLong, freq, words & pluCovered),
            "withoutCollisions": {rule: longResolved(words, rule) for rule in ("winnerKeeps", "everyClaimant")},
            "complexity": {
                "pluvierOnStarboard": tc.complexity(pluLongOnStar, freq, words & pluCovered),
                "pluvierOnStarboardTallS": tc.complexity(pluLongOnStarTallS, freq, words & pluCovered),
                "pluvierOnIreland": tc.complexity(pluLongOnIre, freq, words & pluCovered)}}
        return {
            **shortBlock, "pluvierLong": pluLongBlock,
            "withoutCollisions": {"extraStrokeCost": {"starboard": extraOnStar, "ireland": extraOnIre},
                                  "winnerKeeps": resolved(words, "winnerKeeps"),
                                  "everyClaimant": resolved(words, "everyClaimant")},
            "strokesPerWord": {"stenalgo": tc.strokesPerWord(sten, freq, words & stenCovered),
                               "pluvier": tc.strokesPerWord(plu, freq, words & pluCovered)},
            "complexity": {
                "stenalgoOnStarboard": tc.complexity(stenCosts, freq, words & stenCovered),
                "pluvierOnStarboard": tc.complexity(pluOnStar, freq, words & pluCovered),
                "pluvierOnStarboardTallS": tc.complexity(pluOnStarTallS, freq, words & pluCovered),
                "pluvierOnIreland": tc.complexity(pluOnIre, freq, words & pluCovered),
                "pressableInBoth": tc.complexityBoth(stenCosts, pluOnStar, freq, words & stenCovered & pluCovered),
                "pluvierTallSVersusIreland": tc.complexityBoth(pluOnStarTallS, pluOnIre, freq, words & pluCovered),
            },
            "phonemeOrder": {"stenalgo": tc.orderViolations(stenViol, freq, words & stenCovered),
                             "pluvier": tc.orderViolations(pluViol, freq, words & pluCovered)},
        }

    pluLong = tc.longForm(plu, pluStroke)
    pluLongOnStar = tc.outlineCosts(pluLong, pluStroke, pluCovered)
    pluLongOnStarTallS = tc.outlineCosts(pluLong, pluStrokeTallS, pluCovered)
    pluLongOnIre = tc.outlineCosts(pluLong, lambda s: ireland.getStrokeCost(s), pluCovered)
    shortCosts = tc.outlineCosts(short, stenStroke, stenCovered) if short is not None else None
    pluOnly = pluCovered & universe
    lemmaReport = tc.lemmaCoverage(lexicon, sten, plu)
    tenseReport = tc.verbCoverageByTense(lexicon, sten, plu)
    return {
        "lemmaCoverage": lemmaReport,
        "verbCoverageByTense": tenseReport,
        "coverageByFeature": tc.coverageByFeature(lexicon, sten, plu),
        "inputs": {
            "stenalgoDict": {"path": args.stenalgo_dict, "md5": md5(args.stenalgo_dict)},
            "stenalgoLayout": {"path": args.stenalgo_layout, "md5": md5(args.stenalgo_layout)},
            "pluvierDicts": [{"path": path, "md5": md5(path), "commit": gitCommit(path)} for path in pluvierFiles],
            "pluvierDup": None if args.pluvier_dup is None else {"path": args.pluvier_dup, "md5": md5(args.pluvier_dup)},
            "lexicon": {"path": args.lexicon, "md5": md5(args.lexicon), "frequency": args.freq},
            "stenalgoAbbreviations": None if not args.stenalgo_abbreviations else
                {"path": args.stenalgo_abbreviations, "md5": md5(args.stenalgo_abbreviations)},
            "phonemeKeys": {"path": args.phoneme_keys, "md5": md5(args.phoneme_keys)},
        },
        "theories": {"stenalgo": sten.notes, "pluvier": {**plu.notes,
                     "apostropheForms": sum(1 for w in plu.outlines if "'" in w),
                     "oneLetterWords": sum(1 for w in plu.outlines if len(w) == 1),
                     "wordsOnlyInCollisionRecord": len(plu.lostWords)}},
        "coverage": tc.coverage(freq, sten, plu),
        "collisionsOnCommonWords": {"stenalgo": tc.collisions(sten, freq, common),
                                    "pluvier": tc.collisions(plu, freq, common)},
        "commonWords": block(common),
        "fullCoverage": block(universe),
        "pluvierEncodingMatchesDicofr": {
            "words": len(pluMatch),
            "share": tc.share(sum(pluMatch.values()), len(pluMatch)),
            "frequencyShare": tc.weightedMean(pluMatch, freq, pluOnly)},
    }


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100 * x:.2f}%"


def num(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.3f}"


TENSE_LABELS = {"ind:pre": "indicatif présent", "ind:imp": "indicatif imparfait", "ind:pas": "passé simple", "ind:fut": "futur simple",
                "cnd:pre": "conditionnel présent", "sub:pre": "subjonctif présent", "sub:imp": "subjonctif imparfait",
                "imp:pre": "impératif présent", "inf": "infinitif", "par:pre": "participe présent", "par:pas": "participe passé",
                "pers:1": "1st person", "pers:2": "2nd person", "pers:3": "3rd person",
                "nbr:s": "person singular", "nbr:p": "person plural",
                "genre:m": "masculine", "genre:f": "feminine", "nombre:s": "singular", "nombre:p": "plural"}
NOT_APPLICABLE, NO_SHORT_FORM = "—", "n/a"
Row = tuple[str, str, str]  # label, Stenalgo cell, Pluvier cell


def withShare(count: int, share: float | None) -> str:
    return f"{count} ({pct(share)})"


def table(rows: list[Row]) -> list[str]:
    return ["| metric | Stenalgo | Pluvier |", "|---|---|---|", *(f"| {label} | {sten} | {plu} |" for label, sten, plu in rows), ""]


def renderMarkdown(report: dict[str, Any]) -> str:
    cov, com = report["coverage"], report["commonWords"]
    col = report["collisionsOnCommonWords"]
    inputs = report["inputs"]
    ss = com.get("stenalgoShort")                  # None without --stenalgo-abbreviations
    pl = com["pluvierLong"]
    cx, plcx, wc = com["complexity"], pl["complexity"], com["withoutCollisions"]

    def short(getter: Callable[[dict[str, Any]], str]) -> str:
        return NO_SHORT_FORM if ss is None else getter(ss)

    lines = ["# Stenalgo (Starboard) vs Pluvier (Ireland)", "",
             f"Frequency: {inputs['lexicon']['frequency']}; Pluvier commit {inputs['pluvierDicts'][0]['commit']}; "
             f"Pluvier layers (lowest priority first): {', '.join(os.path.basename(d['path']) for d in inputs['pluvierDicts'])}.", ""]

    def section(title: str, text: str, rows: list[Row]) -> None:
        lines.extend([f"## {title}", "", text, "", *table(rows)])

    def covered(key: str) -> str:
        return withShare(cov[key]["spellings"], cov[key]["frequencyShare"])

    lines += ["## 1. Word coverage (Lexique383 spellings)", "",
              f"Of the {cov['universe']['spellings']} spellings of Lexique383, {covered('both')} are covered by both theories "
              f"and {covered('neither')} by neither; a higher share of the word frequency means more of what is typed is available.", ""]
    lines += table([("words covered", covered("stenalgo"), covered("pluvier")),
                    ("words covered by this theory only", covered("stenalgoOnly"), covered("pluvierOnly"))])

    lem = report["lemmaCoverage"]

    def lemmaRow(label: str, key: str) -> Row:
        return (label, withShare(lem["stenalgo"][key]["lemmas"], lem["stenalgo"][key]["frequencyShare"]),
                withShare(lem["pluvier"][key]["lemmas"], lem["pluvier"][key]["frequencyShare"]))

    section("2. Lemma coverage", f"A lemma is a lemme with its grammatical category ({lem['lemmas']} in all, weighted by lemma frequency): "
            "a lemma with some form covered can be typed in at least one form, one with all forms covered in every form.",
            [lemmaRow("some form covered", "someFormCovered"), lemmaRow("all forms covered", "allFormsCovered")])

    features = report["coverageByFeature"]

    def shareRange(count: int, split: float | None, whole: float | None) -> str:
        if split is None or whole is None or pct(split) == pct(whole):
            return withShare(count, whole)
        low, high = sorted((split, whole))
        return f"{count} ({100 * low:.2f}–{pct(high)})"

    def featureCells(cell: dict[str, Any]) -> str:
        return (f"{shareRange(cell['forms'], cell['frequencyShareSplit'], cell['frequencyShare'])} | "
                f"{shareRange(cell['colliding'], cell['collidingFrequencyShareSplit'], cell['collidingFrequencyShare'])}")

    lines += ["## 3. Coverage by mood, tense, person, gender and number", "",
              "The features the conjugation, gender and number keypress groups of Stenalgo discriminate. A row counts the "
              "Lexique383 forms carrying the feature: the tense and person rows the verb and auxiliary forms, the gender and "
              "number rows the forms of every category. A form weighs only the frequency of its Lexique rows carrying the "
              "feature; a verb row with several readings (`mange`: 1st and 3rd person, indicatif and subjonctif) gives a "
              "range, from an equal part of its frequency in each reading to the whole in each. Covered and colliding forms "
              "(whose outline also belongs to another word) are given with their share of the row's frequency; Stenalgo "
              "leaves out the subjonctif imparfait by design.", "",
              "| feature | forms | Stenalgo covered | Stenalgo colliding | Pluvier covered | Pluvier colliding |",
              "|---|---|---|---|---|---|",
              *(f"| {TENSE_LABELS.get(key, key)} | {f['forms']} | {featureCells(f['stenalgo'])} | {featureCells(f['pluvier'])} |"
                for key, f in features.items()), ""]

    common = f"words covered by both: {cov['both']['spellings']}"
    section(f"4. Collisions ({common})",
            "A word collides when its outline also belongs to another word; fewer colliding words means fewer ambiguities left to the typist.",
            [("words colliding (freq share)", withShare(col["stenalgo"]["wordsColliding"], col["stenalgo"]["frequencyShare"]),
              withShare(col["pluvier"]["wordsColliding"], col["pluvier"]["frequencyShare"])),
             ("collision groups", str(col["stenalgo"]["groups"]), str(col["pluvier"]["groups"])),
             ("words in groups fully common", str(col["stenalgo"]["wordsInGroupsFullyCommon"]), str(col["pluvier"]["wordsInGroupsFullyCommon"]))])

    both = cx["pressableInBoth"]
    abbreviated = short(lambda x: withShare(x["abbreviatedWords"], x["abbreviatedFrequencyShare"]))
    section(f"5. Strokes and cost ({common})",
            "The cost of a word is the sum of the chord costs of its outline, averaged over the word frequency (lower is easier), "
            "both keyboard models using the same units; the short form is what a typist types, the long form is the dictionary alone for "
            "Stenalgo and the longest outline for Pluvier.",
            [("strokes per word, short form", short(lambda x: num(x["strokesPerWord"])), num(com["strokesPerWord"]["pluvier"])),
             ("strokes per word, long form", num(com["strokesPerWord"]["stenalgo"]), num(pl["strokesPerWord"])),
             ("cost on its own keyboard, short form", short(lambda x: num(x["complexity"]["meanCost"])), num(cx["pluvierOnIreland"]["meanCost"])),
             ("cost on its own keyboard, long form", num(cx["stenalgoOnStarboard"]["meanCost"]), num(plcx["pluvierOnIreland"]["meanCost"])),
             ("cost, both on Starboard, short form", short(lambda x: num(x["complexity"]["meanCost"])), num(cx["pluvierOnStarboard"]["meanCost"])),
             ("cost, both on Starboard, long form", num(cx["stenalgoOnStarboard"]["meanCost"]), num(plcx["pluvierOnStarboard"]["meanCost"])),
             ("unpressable on Starboard (freq share)", pct(cx["stenalgoOnStarboard"]["unpricedFrequencyShare"]),
              pct(cx["pluvierOnStarboard"]["unpricedFrequencyShare"])),
             ("words whose short form differs from the long form", abbreviated,
              withShare(pl["wordsWithDifferentLongAndShort"], pl["differentFrequencyShare"])),
             ("words with several outlines", NOT_APPLICABLE, withShare(pl["wordsWithSeveralOutlines"], pl["severalOutlinesFrequencyShare"]))])
    tall, tallIre = cx["pluvierTallSVersusIreland"], cx["pluvierOnStarboardTallS"]
    lines += [
        f"On the {both['words']} words that can be pressed on Starboard with both theories, Stenalgo (long form) costs {num(both['meanA'])} "
        f"and Pluvier (short form) {num(both['meanB'])}.", "",
        f"With Ireland's `S` moved to the cheaper pinky key of Starboard, Pluvier on Starboard costs {num(tallIre['meanCost'])} (short form) "
        f"and {num(plcx['pluvierOnStarboardTallS']['meanCost'])} (long form); on the {tall['words']} words priced on both boards, "
        f"that variant costs {num(tall['meanA'])} on Starboard against {num(tall['meanB'])} on Ireland.", ""]

    extra = wc["extraStrokeCost"]
    lines += [f"### 5b. If every colliding word took one more stroke ({common})", "",
              f"The extra stroke is the cheapest single key (cost {extra['starboard']} on Starboard, {extra['ireland']} on Ireland); "
              "the first rule gives it only to the colliding words that lose the outline, the second to every word that claims it"
              + (", and Stenalgo, having no collision, is unchanged." if wc["everyClaimant"]["markedWords"]["stenalgo"] == 0 else "."), ""]
    for rule, title in (("winnerKeeps", "The most frequent claimant keeps the outline"), ("everyClaimant", "Every claimant takes the stroke")):
        r, pr = wc[rule], pl["withoutCollisions"][rule]
        noMark = r["markedWords"]["stenalgo"] == 0     # Stenalgo has no collision: its figures do not change
        sShort = (lambda f: short(f)) if noMark else (lambda f: NO_SHORT_FORM if ss is None else NOT_APPLICABLE)
        sMarked = withShare(0, 0.0) if noMark else NOT_APPLICABLE
        lines += [f"#### {title}", ""]
        lines += table([
            ("words given a stroke, short form", sMarked if ss is not None else NO_SHORT_FORM,
             withShare(r["markedWords"]["pluvier"], r["markedWords"]["pluvierFrequencyShare"])),
            ("words given a stroke, long form", sMarked,
             withShare(pr["markedWords"], pr["markedFrequencyShare"])),
            ("strokes per word, short form", sShort(lambda x: num(x["strokesPerWord"])), num(r["strokesPerWord"]["pluvier"])),
            ("strokes per word, long form", num(r["strokesPerWord"]["stenalgo"]), num(pr["strokesPerWord"])),
            ("cost on its own keyboard, short form", sShort(lambda x: num(x["complexity"]["meanCost"])),
             num(r["complexity"]["pluvierOnIreland"]["meanCost"])),
            ("cost on its own keyboard, long form", num(r["complexity"]["stenalgoOnStarboard"]["meanCost"]),
             num(pr["costOnIreland"]["meanCost"]))])

    po = com["phonemeOrder"]
    match = report["pluvierEncodingMatchesDicofr"]
    section(f"6. Phoneme order ({common})",
            "A violation is a phoneme pressed in an order other than the spoken one; the unencodable words are those whose phonemes "
            "the theory's keys cannot write at all.",
            [("words with a phoneme order violation", pct(po["stenalgo"]["shareWithViolation"]), pct(po["pluvier"]["shareWithViolation"])),
             ("mean violations per word", num(po["stenalgo"]["meanViolations"]), num(po["pluvier"]["meanViolations"])),
             ("unencodable words (freq share)", pct(po["stenalgo"]["unencodableFrequencyShare"]), pct(po["pluvier"]["unencodableFrequencyShare"]))])
    lines += [f"Pluvier table encoding equals one of the word's Pluvier outlines for {pct(match['share'])} of its words "
              f"({pct(match['frequencyShare'])} of frequency).", ""]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stenalgo-dict", default="plover_stenalgo_dictionary.json")
    parser.add_argument("--stenalgo-layout", default="starboard3h.json")
    parser.add_argument("--pluvier-dict", action="append", required=True, metavar="PATH",
                        help="a Pluvier outline -> word JSON file; repeat the option, LOWEST priority first (a later file "
                             "takes an outline from an earlier one; the TAO briefs go last)")
    parser.add_argument("--pluvier-dup", default=None,
                        help="the generator's collision record (dup.json: outline -> every word that claimed it), optional")
    parser.add_argument("--stenalgo-abbreviations", default=None, metavar="TSV",
                        help="affix_abbreviations.tsv (S9b): adds the Stenalgo SHORT form next to the long form (the dictionary alone)")
    parser.add_argument("--lexicon", default="resources/Lexique383.tsv")
    parser.add_argument("--phoneme-keys", default="resources/pluvierPhonemeKeys.tsv")
    parser.add_argument("--freq", choices=("films", "livres"), default="films")
    parser.add_argument("--out", default=".")
    args = parser.parse_args(argv)
    report = compare(args)
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "theory_comparison.json"), "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=1, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    text = renderMarkdown(report)
    with open(os.path.join(args.out, "theory_comparison.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)


if __name__ == "__main__":
    main()
