"""
Theory Export (S8)-style trainer branch for the expression abbreviation layer: the practice sentences written with the
abbreviations. The same candidate sentences and token resolution as `util.export_practice_sentences`, but the sentence's
tokens go through the expression composer, so particles join their neighbours and briefs replace their phrases.

Run: python -m util.export_expression_sentences
Requires the inputs of `util.export_practice_sentences` (its output `practice-words.json` included) and of
`util.export_expression_lessons`.
Output: steno-trainer/public/data/expression-sentences.json, a list of sentence records of the `practice-sentences.json`
schema (`text`, `phonology`, `steno`, `strokes`, `words`) plus `alternates` (the plain word-by-word outline of the
whole sentence, as {steno, strokes}) and `ruleRanks` (the ranks, in `expression-lessons.json`, of the rules the outline
uses). Only the sentences that at least one abbreviation shortens are kept. `practice-sentences.json` is not touched.
See docs/specs/expression-lessons.md for the word segmentation of an abbreviated sentence.
"""
from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from typing import Any

from src.affixes import SimContext
from src.expressions import EXCEPTION, MERGED, STANDALONE, AttachRule, BriefRule, Composition, Rules, Token, \
    composeOutlineTraced
from src.expressionrules import PoolExpression
from src.keyboard import Starboard, Strokes, canonicalizeStrokes
from util._expressioninput import loadExpressionInputs
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_expression_lessons import firedRules, ruleRanks
from util.export_practice_sentences import (CANDIDATES_PATH, FINAL_PUNCTUATION, Chord, Rejected, _spellOut,
                                            loadChordsByOrtho, resolveToken)
from util.export_practice_words import KEYBOARD_JSON, formatPhonology, formatReadingsLabel

OUTPUT_PATH = "steno-trainer/public/data/expression-sentences.json"


def wordStrokeCounts(comp: Composition, tokens: Sequence[Token]) -> list[int]:
    """How many strokes of the composed outline each token owns (the `strokeCount` of the sentence's words).

    A word keeps its own strokes (a merged particle changes the stroke's keys, not the count). A merged attach owns
    none. A standalone attach, and a brief, put their strokes on the FIRST token of the unit group they replace; the
    other tokens of the group own none. An attach that fell to an exception keeps each token's longform strokes.
    Raises ValueError when the counts do not add up to the composed outline."""
    counts = [0] * len(tokens)
    index = 0
    for seg in comp.segments:
        if seg.kind == "attach":
            start, end = seg.span
            if start != index:
                raise ValueError(f"segment starts at token {start}, expected {index}")
            if seg.outcome == EXCEPTION:
                for i in range(start, end):
                    counts[i] = len(tokens[i].strokes)
            elif seg.outcome == STANDALONE:
                counts[start] = len(seg.strokes)
            index = end
        else:
            counts[index] = len(seg.strokes)
            index += len(seg.units)
    if index != len(tokens) or sum(counts) != len(comp.strokes or ()):
        raise ValueError("segment stroke counts do not add up to the composed outline")
    return counts


def buildExpressionSentence(candidate: dict[str, Any], chordsByOrtho: dict[str, list[Chord]],
                            drillItems: set[tuple[str, str]], rules: Rules, ctx: SimContext, starboard: Starboard,
                            ranks: dict[AttachRule | BriefRule, int]) -> dict[str, Any]:
    """The abbreviated record of one candidate sentence; `Rejected` when a token does not resolve (the reasons of
    `util.export_practice_sentences`) or no abbreviation shortens the sentence."""
    text: str = candidate["text"].strip()
    tokens: list[list[str]] = candidate["tokens"]
    if _spellOut(tokens).lower() != text.rstrip(FINAL_PUNCTUATION).strip().lower():
        raise Rejected(f"tokens spell {_spellOut(tokens)!r}")
    words = []
    for token in tokens:
        chord, meant = resolveToken(token, chordsByOrtho)
        if (chord.word.ortho, chord.steno) not in drillItems:
            raise Rejected(f"{token[0]!r} ({chord.steno}): not a drilled word")
        words.append((token[0], chord, meant))

    units = tuple(Token(form.lower().lstrip("-"), chord.strokes) for form, chord, _ in words)
    comp = composeOutlineTraced(rules, units, ctx)
    if comp.strokes is None or comp.saving < 1:
        raise Rejected("no abbreviation shortens it")
    try:
        counts = wordStrokeCounts(comp, units)
    except ValueError as reason:
        raise Rejected(str(reason)) from reason
    longform: Strokes = canonicalizeStrokes(tuple(s for _, chord, _ in words for s in chord.strokes))

    segments: list[dict[str, Any]] = []
    taken = 0
    for (form, chord, meant), count in zip(words, counts):
        part: Strokes = comp.strokes[taken:taken + count]
        taken += count
        segments.append({"text": form, "label": formatReadingsLabel(chord.word.gramCat, meant),
                         "steno": renderFinalStrokesToRTFCRE(starboard, part) if part else "", "strokeCount": count})
    return {
        "text": text,
        "phonology": " ".join(formatPhonology(chord.word) for _, chord, _ in words),
        "steno": " ".join(seg["steno"] for seg in segments if seg["steno"]),
        "strokes": [sorted(set(stroke)) for stroke in comp.strokes],
        "words": segments,
        "alternates": [{"steno": renderFinalStrokesToRTFCRE(starboard, longform),
                        "strokes": [sorted(set(stroke)) for stroke in longform]}],
        "ruleRanks": sorted({ranks[r] for r in firedRules(comp)}),
    }


def buildExpressionSentences(candidates: Sequence[dict[str, Any]], chordsByOrtho: dict[str, list[Chord]],
                             drillItems: set[tuple[str, str]], rules: Rules, pool: Sequence[PoolExpression],
                             ctx: SimContext, starboard: Starboard) -> tuple[list[dict[str, Any]], int]:
    """Pure builder: (the sentences, the number of distinct candidates rejected)."""
    ranks = ruleRanks(rules, pool, ctx)
    sentences: list[dict[str, Any]] = []
    seen: set[str] = set()
    rejected = 0
    for candidate in candidates:
        if candidate["text"] in seen:
            continue
        seen.add(candidate["text"])
        try:
            sentences.append(buildExpressionSentence(candidate, chordsByOrtho, drillItems, rules, ctx, starboard, ranks))
        except Rejected:
            rejected += 1
    return sentences, rejected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default=CANDIDATES_PATH)
    args = parser.parse_args()
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    chordsByOrtho, drillItems = loadChordsByOrtho(starboard)
    ctx, rules, pool, _words, _unitStrokes = loadExpressionInputs()
    with open(args.candidates, encoding="utf-8") as f:
        candidates = [json.loads(line) for line in f if line.strip()]
    sentences, rejected = buildExpressionSentences(candidates, chordsByOrtho, drillItems, rules, pool, ctx, starboard)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sentences, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"Wrote {OUTPUT_PATH}: {len(sentences)} sentences ({rejected} of {len(candidates)} candidates left out).")


if __name__ == "__main__":
    main()
