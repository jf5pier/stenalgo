"""
Brief Building (S9e): the word, stem and expression briefs (src/briefs.py is the generator).

  python -m util.build_briefs                     the pipeline mode: validates the pinned briefs of briefs.json, re-expands the word
                                                  families, exports; NEVER writes briefs.json. An invalid pin, a colliding family
                                                  outline or an unpinned subject is left out with a warning naming --rederive.
  python -m util.build_briefs --rederive [SUBJECT ...]
                                                  derives all the subjects of resources/briefs.tsv, or the named ones plus the unpinned
                                                  ones, rewrites briefs.json and prints old -> new chords (the only way a brief moves)
  python -m util.build_briefs --propose CANDIDATES.tsv [--top N] [--out PATH] [--pluvier-root ../Pluvier]
                                                  the study: a proposal for each candidate word (pluvier_shorter_words.tsv), written to
                                                  an untracked TSV, with the strokes per word of Pluvier / now / with the proposals

Prerequisites: both pickles (the disambiguated theory), starboard3h.json, plover_stenalgo_dictionary.json, affix_abbreviations.tsv,
resources/briefs.tsv (the subjects), resources/Lexique383.tsv, the expression inputs (scratch/expr-*).
Outputs: plover_stenalgo_brief_dictionary.json (steno -> spelling, the word briefs and their family outlines) and briefs.tsv
(spelling long short saved brief scope; the columns of affix_abbreviations.tsv, which theorycompare.loadAbbreviations reads).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import defaultdict

from src import theorycompare as tc  # noqa: E402
from src.affixes import SimContext  # noqa: E402
from src.briefs import (BriefGenerator, BriefInputs, Derived, Outline, PinnedBrief, Subject, expressionSubject,  # noqa: E402
                        wordSubject)
from src.expressionrules import HostIndex, PoolExpression, attachMergeChords  # noqa: E402
from src.expressions import conflictsOf  # noqa: E402
from src.keyboard import Starboard, canonicalizeStrokes  # noqa: E402
from util._briefpins import BRIEFS_JSON, LEXIQUE, loadPins, loadSubjects, writePins  # noqa: E402
from util._expressioninput import loadExpressionInputs  # noqa: E402
from util._reservedchords import reservedChords  # noqa: E402
from util._stenorender import renderFinalStrokesToRTFCRE  # noqa: E402
from util._theoryio import loadDisambiguatedTheory  # noqa: E402
from util.compare_theories import buttonKeyMap, parseStenalgoOutline, starboardStrokeCost  # noqa: E402

DICTIONARY = "plover_stenalgo_dictionary.json"
ABBREVIATIONS = "affix_abbreviations.tsv"
OUT_DICTIONARY = "plover_stenalgo_brief_dictionary.json"
OUT_TSV = "briefs.tsv"
LAYOUT = "starboard3h.json"


def quote(subject: str) -> str:
    return f'"{subject}"' if " " in subject else subject


class World:
    """The theory the briefs are made against, loaded once."""

    def __init__(self, pluvierRoot: str | None = None) -> None:
        board = Starboard.fromJSONFile(LAYOUT)
        assert board is not None
        self.board = board
        self.render = lambda outline: renderFinalStrokesToRTFCRE(board, outline)
        theory = loadDisambiguatedTheory(board)
        self.lexicon = tc.loadLexicon(LEXIQUE, "films")
        with open(DICTIONARY, encoding="utf-8") as handle:
            entries: dict[str, str] = json.load(handle)
        outlinesOf: dict[str, list[Outline]] = defaultdict(list)
        owner: dict[str, set[str]] = defaultdict(set)
        for text, word in entries.items():
            parsed = parseStenalgoOutline(text)
            assert parsed is not None
            outlinesOf[word.lower()].append(canonicalizeStrokes(parsed))
            owner[text].add(word.lower())
        self.abbreviations = tc.loadAbbreviations(ABBREVIATIONS) if os.path.exists(ABBREVIATIONS) else {}
        live: list[Outline] = []
        for word, texts in self.abbreviations.items():
            for text in texts:
                owner[text].add(word)
                parsed = parseStenalgoOutline(text)
                if parsed is not None:
                    live.append(canonicalizeStrokes(parsed))
        ctxE, rules, pool, _words, _units = loadExpressionInputs(theory, pinned=False)
        self.pool: dict[tuple[str, ...], PoolExpression] = {e.units: e for e in pool}
        weights: dict = defaultdict(float)
        for word, outs in outlinesOf.items():
            for outline in outs:
                weights[outline] += self.lexicon.freq.get(word, 0.0)
        mergeChords = attachMergeChords(rules.attaches, HostIndex(weights, conflicts=conflictsOf(ctxE)))
        ctx = SimContext(board, [])
        ctx.finalOutlines = {o for outs in outlinesOf.values() for o in outs}
        ctx.singleStrokeOutlines = {o[0] for o in ctx.finalOutlines if len(o) == 1}
        reserved = reservedChords(board, theory, briefs=False)
        self.outlinesOf = dict(outlinesOf)
        self.inputs = BriefInputs(board, ctx, self.render, self.lexicon, self.outlinesOf, dict(owner), reserved, mergeChords,
                                  live)
        self.sten: tc.TheoryView | None = None
        self.plu: tc.TheoryView | None = None
        self.common: set[str] | None = None
        if pluvierRoot is not None:
            from util.find_pluvier_shorter_words import LAYERS
            resources = os.path.join(pluvierRoot, "resources")
            self.sten = tc.withAbbreviations(tc.loadStenalgoTheory(DICTIONARY, parseStenalgoOutline), self.abbreviations)
            self.plu = tc.loadPluvierTheory([os.path.join(resources, n) for n in LAYERS], os.path.join(resources, "dup.json"))
            self.sten.choose(starboardStrokeCost(board))
            self.plu.choose(starboardStrokeCost(board, buttonKeyMap()))
            self.common = {w for w in self.lexicon.freq if w in self.sten.chosen and w in self.plu.chosen}
            self.inputs.common = self.common
            self.inputs.strokesNow = {w: self.sten.chosen[w].count("/") + 1 for w in self.sten.chosen}

    def subject(self, name: str, scope: str) -> Subject | None:
        """The subject of a row of resources/briefs.tsv, None when the theory lacks it."""
        if " " not in name and scope != "expression" and name in self.outlinesOf:
            return wordSubject(name, scope, self.outlinesOf, self.lexicon)
        expression = self.pool.get(tuple(name.split()))
        if expression is None:
            return None
        return expressionSubject(expression.units, (t.strokes for t in expression.tokens), self.lexicon, expression.freq)


def exportFiles(world: World, generator: BriefGenerator, accepted: list[Derived]) -> int:
    """plover_stenalgo_brief_dictionary.json and briefs.tsv from the word briefs."""
    dictionary: dict[str, str] = {}
    rows: list[dict[str, str | int]] = []
    for derived in accepted:
        if derived.subject.kind != "word":
            continue
        for form, old, new in generator.pairs(derived):
            dictionary[world.render(new)] = form
            rows.append({"spelling": form, "long": world.render(old), "short": world.render(new), "saved": len(old) - len(new),
                         "brief": world.render((derived.chord,)), "scope": derived.subject.scope})
    with open(OUT_DICTIONARY, "w", encoding="utf-8") as handle:
        json.dump(dict(sorted(dictionary.items())), handle, ensure_ascii=False, indent=0)
        handle.write("\n")
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, ["spelling", "long", "short", "saved", "brief", "scope"], delimiter="\t",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(dictionary)


def strokesLine(world: World, generator: BriefGenerator) -> str | None:
    """Frequency-weighted strokes per word over the words both theories cover (Lexique383 films): Pluvier, now, with the briefs."""
    if world.sten is None or world.plu is None or world.common is None:
        return None
    freq, common = world.lexicon.freq, world.common
    now = tc.strokesPerWord(world.sten, freq, common)
    after = tc.weightedMean({w: float(generator.strokesNow[w]) for w in common}, freq, common)
    pluvier = tc.strokesPerWord(world.plu, freq, common)
    return f"strokes/word (common words, films): Pluvier {pluvier:.4f}; Stenalgo now {now:.4f}; with the briefs {after:.4f}"


def runPipeline(world: World) -> int:
    pins = {pin.subject: pin for pin in loadPins(world.board)}
    generator = BriefGenerator(world.inputs)
    subjects = loadSubjects()
    accepted: list[Derived] = []
    for name, scope in subjects:
        pin = pins.get(name)
        if pin is None:
            print(f"warning: {name}: no pinned brief (python -m util.build_briefs --rederive {quote(name)})")
            continue
        subject = world.subject(name, scope)
        if subject is None:
            print(f"warning: {name}: not in the theory (python -m util.build_briefs --rederive {quote(name)})")
            continue
        derived, why = generator.check(pin, subject)
        if derived is None:
            print(f"warning: {name}: pin excluded, {why} (python -m util.build_briefs --rederive {quote(name)})")
            continue
        accepted.append(derived)
    for name in sorted(set(pins) - {n for n, _ in subjects}):
        print(f"warning: {name}: pinned but not listed in resources/briefs.tsv, left out")
    count = exportFiles(world, generator, accepted)
    print(f"briefs: {len(accepted)} of {len(subjects)} subjects valid "
          f"({sum(d.subject.kind == 'word' for d in accepted)} words, {sum(d.subject.kind == 'expression' for d in accepted)} "
          f"expressions); {count} outlines -> {OUT_DICTIONARY}, {OUT_TSV}")
    return 0


def runRederive(world: World, names: list[str]) -> int:
    old = {pin.subject: pin for pin in loadPins(world.board)}
    subjects = loadSubjects()
    unknown = set(names) - {n for n, _ in subjects}
    if unknown:
        print(f"error: not in resources/briefs.tsv: {sorted(unknown)}", file=sys.stderr)
        return 1
    generator = BriefGenerator(world.inputs)
    accepted: list[Derived] = []
    newPins: list[PinnedBrief] = []
    for name, scope in subjects:
        subject = world.subject(name, scope)
        if subject is None:
            print(f"warning: {name}: not in the theory, no brief")
            continue
        derived: Derived | None = None
        if names and name not in names and name in old:
            derived, why = generator.check(old[name], subject)
            if derived is None:
                print(f"warning: {name}: old pin invalid, {why}; rederive it by name")
        elif generator.coveredBy.get(name, name) != name:
            print(f"{name}: covered by the family brief of {generator.coveredBy[name]}")
        else:
            derived = generator.derive(subject)
            if derived is None:
                print(f"warning: {name}: no brief found")
            else:
                before = world.render((old[name].chord,)) if name in old else "-"
                print(f"{name}: {before} -> {world.render((derived.chord,))}  /{derived.reading}/ shared {derived.shared}, "
                      f"foreign {derived.foreign}, cost {derived.cost}")
        if derived is not None:
            accepted.append(derived)
            newPins.append(derived.pin())
    writePins(world.board, newPins)
    count = exportFiles(world, generator, accepted)
    print(f"{len(newPins)} briefs -> {BRIEFS_JSON}; {count} outlines -> {OUT_DICTIONARY}, {OUT_TSV}")
    line = strokesLine(world, generator)
    if line:
        print(line)
    return 0


def runPropose(world: World, candidates: str, top: int, out: str) -> int:
    generator = BriefGenerator(world.inputs)
    with open(candidates, encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))[:top]
    proposals: list[dict[str, str]] = []
    for row in rows:
        word = row["word"]
        if generator.coveredBy.get(word, word) != word:
            proposals.append({**row, "status": f"covered by {generator.coveredBy[word]}"})
            continue
        subject = world.subject(word, "family")
        derived = generator.derive(subject) if subject is not None else None
        if derived is None:
            proposals.append({**row, "status": "no brief found"})
            continue
        proposals.append({**row, "status": "proposed", "derivation": f"/{derived.reading}/ shared {derived.shared}, "
                          f"foreign {derived.foreign}, cost {derived.cost}", "brief": world.render((derived.chord,)),
                          "stem": world.render(derived.stem()), "risk": str(derived.risk),
                          "forms": "; ".join(f"{form} {world.render(min(outs, key=lambda o: (len(o), o)))}"
                                             for form, outs in derived.news.items())})
    columns = ["rank", "word", "frequency", "pluvier", "stenalgo", "status", "derivation", "brief", "stem", "risk", "forms"]
    with open(out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, columns, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(proposals)
    print(f"-> {out}: {sum(p['status'] == 'proposed' for p in proposals)} proposed of {len(rows)}")
    line = strokesLine(world, generator)
    if line:
        print(line)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--rederive", nargs="*", metavar="SUBJECT", default=None,
                        help="derive all subjects, or the named ones and the unpinned ones, and rewrite briefs.json")
    parser.add_argument("--propose", metavar="CANDIDATES.tsv", help="the study: proposals for the candidate words")
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--out", default="word_briefs_proposal.tsv")
    parser.add_argument("--pluvier-root", default=None, help="a Pluvier clone: prices the saving on the words both theories cover")
    args = parser.parse_args()
    world = World(args.pluvier_root)
    if args.propose:
        return runPropose(world, args.propose, args.top, args.out)
    if args.rederive is not None:
        return runRederive(world, args.rederive)
    return runPipeline(world)


if __name__ == "__main__":
    sys.exit(main())
