"""
The most frequent words that Pluvier types in fewer strokes than Stenalgo, each with the reason Pluvier is shorter: a
dedicated brief, an identifiable Pluvier affix rule, the generator's syllable compression, or plain phonetic writing.

Run: python -m util.find_pluvier_shorter_words --pluvier-root PLUVIER [--top 100] [--out pluvier_shorter_words.tsv]
         [--stenalgo-dict plover_stenalgo_dictionary.json] [--stenalgo-layout starboard3h.json]
         [--stenalgo-abbreviations affix_abbreviations.tsv --stenalgo-abbreviations briefs.tsv] [--lexicon resources/Lexique383.tsv] [--freq films|livres]
PLUVIER is a Pluvier clone: its four dictionary layers (resources/dicofr.json, dicofr-plural.json, verbs.json,
tao_la_salle_simple.json, lowest priority first, as in util/compare_theories.py) and dup.json, plus src/steno.py and
TAO_rules.md, read for the affix rules. No pickle is read.
Output: the TSV (default pluvier_shorter_words.tsv in the repo root, untracked), and a count per kind on stdout.

Both short forms are the ones of the theory comparison (docs/THEORY_COMPARISON.md): Stenalgo's dictionary plus its affix
abbreviations, Pluvier's briefest outline; each word's outline is the cheapest (fewest strokes, then Starboard cost). Only the
words both theories cover are ranked, by Lexique383 frequency.

The `kind` of a Pluvier outline, first match wins:
- `brief`: a dedicated brief, the outline of the hand-written TAO layer (tao_la_salle_simple.json) that none of the generator
  layers (dicofr.json, dicofr-plural.json, verbs.json) gives the word.
- `affix`: a generated outline that uses an affix rule (`rule` names it; below).
- `compressed`: a generated outline with no identified rule but fewer strokes than spoken syllables (Lexique383 `syll` of
  the most frequent row): the generator's own syllable merging.
- `phonetic`: a generated outline with no identified rule and at least one stroke per syllable: Pluvier only writes the
  syllables, Stenalgo spends more strokes.
`rule` is filled for a brief too when it uses an affix rule (`comment` `KPHA`, `comm-` = `KPH`). A rule is used when the word
has its spelling (for a sound rule, its final phonemes) and the outline its chord, as its own last (first) stroke or ending
(starting) a fused one. Rules: the `OrthoSuffix`/`OrthoPrefix` tables of Pluvier's src/steno.py, its sound tables
`SUFFIXES`/`REAL_SUFFIXES` (matched on the `syll` without its hyphens; a one-phoneme entry only when its chord is right-hand
only, `e` = `-D`, `j` = `-LZ`: the others, `§` = `OPB`, only write a vowel), the verb endings of its
`ortho_add_alone_keys_on_verb` (VERB_ENDINGS below, transcribed; only for a spelling Lexique383 lists as a verb or auxiliary
form) and the "Keys `X` designate ... ending in "y"" lines of TAO_rules.md.
`layer` is the Pluvier file the outline comes from (a later layer wins an outline, as in the comparison).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
from dataclasses import dataclass

from src import theorycompare as tc
from src.keyboard import Starboard
from util.compare_theories import buttonKeyMap, loadAbbreviationFiles, parseStenalgoOutline, starboardStrokeCost

TAO_LAYER = "tao_la_salle_simple.json"
LAYERS = ("dicofr.json", "dicofr-plural.json", "verbs.json", TAO_LAYER)

# Pluvier src/steno.py `ortho_add_alone_keys_on_verb`: spelling ending -> chord (a `/` = its own stroke)
VERB_ENDINGS = (("é", "/-D"), ("ée", "ED"), ("és", "/*ES"), ("ez", "/*EZ"), ("rez", "/R*EZ"), ("iez", "AEZ"),
                ("iez", "/A*E"), ("ons", "OPB"), ("ons", "/*PB"), ("erons", "ROPB"), ("ont", "OPBT"), ("iont", "AOPB"),
                ("ais", "/-S"), ("ais", "/AEUS"), ("ai", "/-S"), ("ai", "/AEU"), ("ait", "/-S"), ("rait", "-RS"),
                ("rais", "RAEUS"), ("raient", "RAEUPBT"), ("aient", "/AEUPBT"), ("ent", "/-PBT"), ("it", "/EUT"),
                ("ant", "/-G"), ("er", "-R"), ("a", "/*Z"))


@dataclass(frozen=True)
class AffixRule:
    spelling: str           # letters, or X-SAMPA phonemes for a sound rule
    chord: str              # the stroke text, `-` kept for a right-hand-only chord
    prefix: bool
    source: str
    sound: bool = False
    verbOnly: bool = False

    def label(self) -> str:
        affix = f"/{self.spelling}/" if self.sound else self.spelling
        return f"{'' if self.prefix else '-'}{affix}{'-' if self.prefix else ''} = {self.chord} ({self.source})"


def ruleChords(text: str) -> list[str]:
    """The chord alternatives of a Pluvier rule (`-/BGS`, `KOEPB/|KOPB`, `ITD|T`) as stroke texts."""
    return [chord for chord in (alternative.replace("/", "") for alternative in text.split("|")) if chord and chord != "-"]


def tableBlock(source: str, name: str) -> str:
    """The text of the `NAME = { ... }` dict literal of Pluvier's src/steno.py."""
    found = re.search(r"(?<!\w)" + name + r" = \{", source)
    if found is None:
        raise SystemExit(f"no {name} table in Pluvier's src/steno.py")
    start = found.start()
    return source[start:source.index("\n        }", start)]


def loadAffixRules(pluvierRoot: str) -> list[AffixRule]:
    rules: list[AffixRule] = []
    with open(os.path.join(pluvierRoot, "src", "steno.py"), encoding="utf-8") as handle:
        steno = handle.read()
    pattern = re.compile(r"""^\s*['"]([^'"]+)['"]\s*:\s*Ortho(Suffix|Prefix)\(\s*['"][^'"]*['"]\s*,\s*['"]([^'"]*)['"]""", re.M)
    for spelling, kind, chords in pattern.findall(steno):
        for chord in ruleChords(chords):
            rules.append(AffixRule(spelling, chord, kind == "Prefix", "steno.py"))
    soundPattern = re.compile(r"""^\s*['"]([^'"]+)['"]\s*:\s*['"]([^'"]+)['"]""", re.M)
    for table in ("REAL_SUFFIXES", "SUFFIXES"):
        for sounds, chords in soundPattern.findall(tableBlock(steno, table)):
            for chord in ruleChords(chords):
                if len(sounds) > 1 or chord.startswith("-"):
                    rules.append(AffixRule(sounds, chord, False, f"steno.py {table}", sound=True))
    for spelling, chords in VERB_ENDINGS:
        for chord in ruleChords(chords):
            rules.append(AffixRule(spelling, chord, False, "verb ending", verbOnly=True))
    with open(os.path.join(pluvierRoot, "TAO_rules.md"), encoding="utf-8") as handle:
        tao = handle.read()
    taoPattern = re.compile(r'(?:Keys|key|chord|Chord)s?\s+`([^`]+)`[^\n]*?(?:ending in|suffix|ending of words in|ending)\s*'
                            r'(?:of words in\s*)?"([^"]+)"')
    for chord, spelling in taoPattern.findall(tao):
        rules.append(AffixRule(spelling, chord, False, "TAO_rules.md"))
    # spelling rules before sound rules, the longest affix first: `-ation` explains a word better than `-on`
    return sorted(rules, key=lambda r: (r.sound, -len(r.spelling), r.prefix, r.spelling, r.chord))


def stripDash(chord: str) -> str:
    return chord[1:] if chord.startswith("-") else chord


def matchRule(word: str, phon: str, outline: str, rules: list[AffixRule], isVerb: bool) -> AffixRule | None:
    """The first rule whose affix the word has (`phon` for a sound rule) and whose chord its outline starts (prefix) or
    ends (suffix) with, as a whole stroke or inside a fused one; a verb-only rule needs `isVerb`."""
    strokes = outline.split("/")
    for rule in rules:
        if rule.verbOnly and not isVerb:
            continue
        text = phon if rule.sound else word
        chord = stripDash(rule.chord)
        if rule.prefix:
            if text.startswith(rule.spelling) and text != rule.spelling and strokes[0].startswith(chord):
                return rule
        elif text.endswith(rule.spelling) and text != rule.spelling and strokes[-1].endswith(chord):
            return rule
    return None


def outlineLayers(pluvierRoot: str) -> tuple[dict[tuple[str, str], str], set[tuple[str, str]]]:
    """(outline, word) -> the highest-priority layer that maps the outline to the word, and the (outline, word) pairs of the
    generator layers (every layer but the TAO briefs)."""
    origin: dict[tuple[str, str], str] = {}
    generated: set[tuple[str, str]] = set()
    for name in LAYERS:
        with open(os.path.join(pluvierRoot, "resources", name), encoding="utf-8") as handle:
            for outline, word in json.load(handle).items():
                origin[(outline, word.lower())] = name
                if name != TAO_LAYER:
                    generated.add((outline, word.lower()))
    return origin, generated


def syllables(syll: str) -> int:
    return len([part for part in syll.split("-") if part]) if syll else 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1] if __doc__ else None)
    parser.add_argument("--pluvier-root", required=True)
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--out", default="pluvier_shorter_words.tsv")
    parser.add_argument("--stenalgo-dict", default="plover_stenalgo_dictionary.json")
    parser.add_argument("--stenalgo-layout", default="starboard3h.json")
    parser.add_argument("--stenalgo-abbreviations", action="append", default=None,
                        help="repeat the option (default: affix_abbreviations.tsv and briefs.tsv)")
    parser.add_argument("--lexicon", default="resources/Lexique383.tsv")
    parser.add_argument("--freq", choices=("films", "livres"), default="films")
    args = parser.parse_args(argv)

    board = Starboard.fromJSONFile(args.stenalgo_layout)
    if board is None:
        raise SystemExit(f"cannot read the layout {args.stenalgo_layout}")
    lexicon = tc.loadLexicon(args.lexicon, args.freq)
    resources = os.path.join(args.pluvier_root, "resources")
    sten = tc.withAbbreviations(tc.loadStenalgoTheory(args.stenalgo_dict, parseStenalgoOutline),
                                loadAbbreviationFiles(args.stenalgo_abbreviations or [p for p in ("affix_abbreviations.tsv", "briefs.tsv")
                                                                                      if os.path.exists(p)]))
    plu = tc.loadPluvierTheory([os.path.join(resources, name) for name in LAYERS], os.path.join(resources, "dup.json"))
    stenCost, pluCost = starboardStrokeCost(board), starboardStrokeCost(board, buttonKeyMap())
    sten.choose(stenCost)
    plu.choose(pluCost)
    rules = loadAffixRules(args.pluvier_root)
    origin, generated = outlineLayers(args.pluvier_root)
    verbForms = set().union(*lexicon.tenseForms.values())

    def strokes(outline: str) -> int:
        return outline.count("/") + 1

    shorter = [w for w in lexicon.freq if w in sten.chosen and w in plu.chosen
               and strokes(plu.chosen[w]) < strokes(sten.chosen[w])]
    shorter.sort(key=lambda w: (-lexicon.freq[w], w))
    counts: dict[str, int] = {}
    with open(args.out, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["rank", "word", "frequency", "syllables", "pluvier", "pluvierStrokes", "pluvierLayer",
                         "stenalgo", "stenalgoStrokes", "kind", "rule"])
        for rank, word in enumerate(shorter[:args.top], 1):
            outline = plu.chosen[word]
            syll = lexicon.syll.get(word, "")
            rule = matchRule(word, syll.replace("-", ""), outline, rules, word in verbForms)
            count = syllables(syll)
            if (outline, word) not in generated:
                kind = "brief"
            else:
                kind = "affix" if rule else ("compressed" if strokes(outline) < count else "phonetic")
            counts[kind] = counts.get(kind, 0) + 1
            writer.writerow([rank, word, f"{lexicon.freq[word]:.2f}", count, outline, strokes(outline),
                             origin.get((outline, word), ""), sten.chosen[word], strokes(sten.chosen[word]), kind,
                             rule.label() if rule else ""])
    print(f"{len(shorter)} words covered by both are shorter in Pluvier; the top {min(args.top, len(shorter))} -> {args.out}")
    print(", ".join(f"{kind} {n}" for kind, n in sorted(counts.items())))


if __name__ == "__main__":
    main()
