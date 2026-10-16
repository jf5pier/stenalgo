"""
Export short practice sentences for the `steno-trainer` web app's sentence mode:
each sentence's words resolved to the one chord that writes the reading used in
context, concatenated in sentence order.

The sentence text is not generated from the lexicon: `util/candidate_sentences.jsonl`
was authored once by a cheap LLM subagent, one JSON object per line, each token
annotated `[form, lemma, gramCat, infoVerb tag, gender, number]` in Lexique383's own
conventions (e.g. `["ai", "avoir", "AUX", "ind:pre:1s", "", ""]`). The annotation is
what makes context-dependent chords resolvable at all -- "sais" is `-k` after "je" but
`-d` after "tu", "ai" has a different chord as an auxiliary than as a main verb -- and
this script is the gate that keeps the LLM's mistakes out: a sentence is rejected
unless every token resolves to exactly one chord. Rejection reasons:

- a token isn't in the dictionary at all (after the elision/inversion fallbacks
  below), or its tag is a subjonctif/passé simple (out of scope for practice);
- a verb's tag matches none of that spelling's readings;
- the annotation still leaves several different chords (can't tell which is meant);
- the resolved (word, chord) isn't one of `practice-words.json`'s drill items -- the
  sentence vocabulary is exactly the word drill's, so run `export_practice_words` first;
- the tokens don't spell out the sentence text (a tokenization slip).

Lexicon quirks the lookup papers over: Lexique383 has "l'"/"d'"/"n'"/"s'" but files
"j'"/"c'"/"qu'" as "j"/"c"/"qu", and has no hyphenated inversions ("-tu", "-ce") --
those are looked up as the bare pronoun.

Run: python -m util.export_practice_sentences [--candidates PATH]
Requires the same inputs as `util.export_practice_words`, plus its output.
"""
from typing import Any
import argparse
import json
from dataclasses import dataclass, field

from src.keyboard import Starboard, Strokes
from src.word import Word
from util._outlines import ShortForms, taggedOutlines
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadPhoneticAndDisambiguatedTheory
from util.export_practice_words import (
    KEYBOARD_JSON, OUTPUT_PATH as PRACTICE_WORDS_PATH, RESOLVED_PRESS_SETS_PATH, Reading,
    buildReadingsByWord, chordsWithAlternates, formatPhonology, formatReadingsLabel,
)

CANDIDATES_PATH = "util/candidate_sentences.jsonl"
OUTPUT_PATH = "steno-trainer/public/data/practice-sentences.json"
OUT_OF_SCOPE_TAG_PREFIXES = ("sub:", "ind:pas")
FINAL_PUNCTUATION = ".?!"


@dataclass(frozen=True)
class Chord:
    """`strokes`/`steno`: the theory's primary outline (what the expression layer composes on); `hint`: the outline
    the drill shows (the long one, MKD25) and `alternates` the other accepted ones (MKD24, `util._outlines`)."""
    word: Word
    strokes: Strokes
    steno: str
    readings: list[Reading]
    hint: dict[str, Any] = field(default_factory=dict)
    alternates: list[dict[str, Any]] = field(default_factory=list)


class Rejected(Exception):
    pass


def _lookupForms(form: str) -> list[str]:
    bare = form.lower().lstrip("-")
    return [bare, bare[:-1]] if bare.endswith("'") else [bare]


def _narrow(chords: list[Chord], keep) -> list[Chord]:  # type: ignore[no-untyped-def]
    """A soft filter: applied only when it leaves something, since the lexicon's own
    lemma/category conventions don't always match the annotation's ("l'" is its own
    lemma in Lexique383)."""
    kept = [chord for chord in chords if keep(chord)]
    return kept or chords


def resolveToken(token: list[str], chordsByOrtho: dict[str, list[Chord]]) -> tuple[Chord, list[Reading]]:
    """The one chord (and the reading(s) of it meant here) that `token` writes."""
    form, lemma, gramCat, tag, gender, number = token
    if tag.startswith(OUT_OF_SCOPE_TAG_PREFIXES):
        raise Rejected(f"{form!r}: out-of-scope tense {tag}")
    chords = next((chordsByOrtho[f] for f in _lookupForms(form) if f in chordsByOrtho), None)
    if chords is None:
        raise Rejected(f"{form!r}: not in the dictionary")

    chords = _narrow(chords, lambda c: c.word.lemme == lemma)
    chords = _narrow(chords, lambda c: c.word.gramCat.name == gramCat)
    genderNumber = {atom for atom in (gender, number) if atom}
    if tag:
        required = set(Word.splitInfoVerb(None, tag))  # type: ignore[arg-type]
        chords = [c for c in chords if any(required <= reading for reading in c.readings)]
        if not chords:
            raise Rejected(f"{form!r}: no reading matches {tag}")
        chords = _narrow(chords, lambda c: any(required | genderNumber <= r for r in c.readings))
    else:
        required = set()
        chords = _narrow(chords, lambda c: any(genderNumber <= r for r in c.readings))

    stenos = sorted({chord.steno for chord in chords})
    if len(stenos) > 1:
        raise Rejected(f"{form!r} ({lemma} {gramCat} {tag}): still ambiguous between {stenos}")
    chord = max(chords, key=lambda c: c.word.frequency)
    meant = [r for r in chord.readings if required | genderNumber <= r] or chord.readings
    return chord, meant


def _spellOut(tokens: list[list[str]]) -> str:
    """The sentence as its tokens write it: no space after an elision, none before a
    hyphenated inversion."""
    text = ""
    for form, *_ in tokens:
        if text and not text.endswith("'") and not form.startswith("-"):
            text += " "
        text += form
    return text


def buildSentence(candidate: dict[str, Any], chordsByOrtho: dict[str, list[Chord]],
                  drillItems: set[tuple[str, str]]) -> dict[str, Any]:
    text: str = candidate["text"].strip()
    tokens: list[list[str]] = candidate["tokens"]
    body = text.rstrip(FINAL_PUNCTUATION).strip()
    if _spellOut(tokens).lower() != body.lower():
        raise Rejected(f"tokens spell {_spellOut(tokens)!r}")

    words = []
    for token in tokens:
        chord, meant = resolveToken(token, chordsByOrtho)
        if (chord.word.ortho, chord.steno) not in drillItems:
            raise Rejected(f"{token[0]!r} ({chord.steno}): not a drilled word")
        words.append((token[0], chord, meant))

    def segment(form: str, chord: Chord, meant: list[Reading]) -> dict[str, Any]:
        hint = chord.hint or {"steno": chord.steno, "strokes": [sorted(set(s)) for s in chord.strokes]}
        record = {"text": form, "label": formatReadingsLabel(chord.word.gramCat, meant),
                  "steno": hint["steno"], "strokeCount": len(hint["strokes"])}
        if chord.alternates:
            record["alternates"] = chord.alternates   # MKD24: the word may be written with any of them
        return record

    segments = [segment(form, chord, meant) for form, chord, meant in words]
    return {
        "text": text,
        "phonology": " ".join(formatPhonology(chord.word) for _, chord, _ in words),
        "steno": " ".join(s["steno"] for s in segments),
        "strokes": [stroke for _, chord, _ in words
                    for stroke in (chord.hint["strokes"] if chord.hint else [sorted(set(s)) for s in chord.strokes])],
        "words": segments,
    }


def loadChordsByOrtho(starboard: Starboard) -> tuple[dict[str, list[Chord]], set[tuple[str, str]]]:
    """Every chord of the disambiguated theory by spelling, and the (ortho, steno) pairs of `practice-words.json`:
    what `buildSentence` resolves tokens against. Shared with `util.export_expression_sentences`."""
    theory, disambiguatedTheory, wordToStrokes, wordsByOrthoLemme = loadPhoneticAndDisambiguatedTheory(starboard)
    with open(RESOLVED_PRESS_SETS_PATH, encoding="utf-8") as f:
        readingsByWord = buildReadingsByWord(json.load(f), theory,
                                             wordToStrokes=wordToStrokes, wordsByOrthoLemme=wordsByOrthoLemme)
    with open(PRACTICE_WORDS_PATH, encoding="utf-8") as f:
        # Every outline a drill item accepts: the hint (long) one and its alternates (merged, abbreviated).
        drillItems = {(item["ortho"], steno) for item in json.load(f)
                      for steno in [item["steno"]] + [a["steno"] for a in item.get("alternates", [])]}

    affix = ShortForms(starboard)
    chordsByOrtho: dict[str, list[Chord]] = {}
    for word, strokesList in disambiguatedTheory.items():
        chords, _aligned = chordsWithAlternates(word, strokesList, readingsByWord)
        for strokes, readings, longs in chords:
            hint, alternates = taggedOutlines(starboard, strokes, longs, affix)
            chordsByOrtho.setdefault(word.ortho, []).append(
                Chord(word, strokes, renderFinalStrokesToRTFCRE(starboard, strokes), readings, hint, alternates))
    return chordsByOrtho, drillItems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default=CANDIDATES_PATH)
    parser.add_argument("--verbose", action="store_true", help="Print every rejection.")
    args = parser.parse_args()

    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    chordsByOrtho, drillItems = loadChordsByOrtho(starboard)

    with open(args.candidates, encoding="utf-8") as f:
        candidates = [json.loads(line) for line in f if line.strip()]

    sentences: list[dict[str, Any]] = []
    seen: set[str] = set()
    rejections: list[tuple[str, str]] = []
    for candidate in candidates:
        if candidate["text"] in seen:
            continue
        seen.add(candidate["text"])
        try:
            sentences.append(buildSentence(candidate, chordsByOrtho, drillItems))
        except Rejected as reason:
            rejections.append((candidate["text"], str(reason)))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(sentences, f, ensure_ascii=False, indent=1)

    if args.verbose:
        for text, why in rejections:
            print(f"  rejected {text!r}: {why}")
    print(f"Wrote {OUTPUT_PATH}: {len(sentences)} sentences"
          f" ({len(rejections)} of {len(seen)} distinct candidates rejected).")


if __name__ == "__main__":
    main()
