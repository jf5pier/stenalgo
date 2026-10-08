"""
Plover complements for the Stenalgo French system: the punctuation and the cursor/editing commands the stock Plover
English and Lapwing dictionaries provide and the theory does not (docs/PLOVER_COMPLEMENTS.md). Only the rows of
`resources/outlineClassification.tsv` of kind `position` are converted here, KEY TO KEY: the meaning of those outlines
is the position of the keys (`TP-PL` = period), so each Ireland key is replaced by the Stenalgo key that sits on the
same Gemini PR button (`GEMINI_PR_KEYMAP`). The phonetic and mnemonic rows need another conversion and are left out.

* An Ireland `*` becomes the Stenalgo `*` key only. (It used to get a second spelling with `#`; those redundant twins were removed 2026-10-07 and `#` is kept for the numbers, see util/export_plover_numbers.py.)
* The Ireland number bar (`#` before a stroke) becomes the Stenalgo `#` key pressed with the stroke, and an Ireland `*` in
  such a stroke keeps the `*` as well. A number-bar row whose output equals its plain twin (Lapwing's `#TPH-R` and `STPH-R`) is
  redundant and skipped. Number-bar rows are converted before the others, so an explicit number-bar chord wins a clash.
* French spacing: the English metas `{:}` `{;}` `{?}` `{!}` attach with no space before and the quotes are straight,
  which is wrong for French. They are rewritten with a no-break space before `: ; ? !` and inside « » (`SPACE`).
* Phonetic aliases (`PHONETIC_ALIASES`): a second chord, spelled from the French name, for the glued comma (`v-l`), the glued hyphen and for the slash
  and backslash and for the glued comma, which Plover and Lapwing do not have (the period and the comma keep their Plover key-position chords).
* An outline that is not pressable (a finger's key combination that is not a legal keypress), equals a theory outline or is the first stroke of one is dropped and
  reported: it would shadow or hide a word.

A second punctuation dictionary is built for people coming from Pluvier (the TAO / LaSalle chords, `pluvier-tao` rows): the
key-position rows are converted key to key like the Plover ones, the phonetic rows are spelled from the French sounds with the
Stenalgo phoneme keys (`PLUVIER_PHONETIC`). It is shipped in the plugin and listed in `DEFAULT_DICTIONARIES` below the Plover
punctuation (Plover has no disabled-by-default entry, so both are on and Plover's chord wins a shared one); a Pluvier user
reorders or turns a set off in Plover's dictionary panel. Rows already served by another chord are reported as covered.

Run: python -m util.export_plover_complements
Requires starboard3h.json, resources/outlineClassification.tsv and plover_stenalgo_dictionary.json (collision check).
Outputs: plover_stenalgo_punctuation.json, plover_stenalgo_commands.json (outline -> Plover translation), copied into the
plugin package by `python -m util.export_plover_plugin`.
"""
from __future__ import annotations

import csv
import json
import sys
from itertools import product
from pathlib import Path
from typing import Any

from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE

KEYBOARD_JSON = "starboard3h.json"
CLASSIFICATION = "resources/outlineClassification.tsv"
THEORY = "plover_stenalgo_dictionary.json"
PUNCTUATION_OUT = "plover_stenalgo_punctuation.json"
PLUVIER_OUT = "plover_stenalgo_pluvier_punctuation.json"
COMMANDS_OUT = "plover_stenalgo_commands.json"
SOURCES = ("lapwing", "plover-english")        # a shared outline takes the first source's translation

SPACE = " "                               # the French space before `: ; ? !` and inside « »

LEFT, VOWELS, RIGHT = "STKPWHR", "AO*EU", "FRPBLGTSDZ"
# Ireland key -> Gemini PR button (`*` is split below); the Stenalgo key is the one `GEMINI_PR_KEYMAP` puts on it.
GEMINI: dict[str, str] = {"S": "S2-", "T": "T-", "K": "K-", "P": "P-", "W": "W-", "H": "H-", "R": "R-", "A": "A-", "O": "O-",
          "E": "-E", "U": "-U", "-F": "-F", "-R": "-R", "-P": "-P", "-B": "-B", "-L": "-L", "-G": "-G", "-T": "-T",
          "-S": "-S", "-D": "-D", "-Z": "-Z"}
STAR_BUTTONS = ("#1", "*4")                    # the Stenalgo `*` and `#` keys; an Ireland `*` is the Stenalgo `*` only (the `#` twins were dropped 2026-10-07: `#` is the number key)


def parseIreland(stroke: str) -> list[str] | None:
    """The Ireland keys of one stroke in steno order ("-F" for a right-hand F), None for text that is not a stroke. A
    leading `#` (number bar) is a key of its own, "#", first in the list."""
    if stroke.startswith("#"):
        rest = parseIreland(stroke[1:])
        return None if rest is None else ["#"] + rest
    if not stroke:
        return None
    i = 0
    left = ""
    while i < len(stroke) and stroke[i] in LEFT:
        left += stroke[i]
        i += 1
    vowels = ""
    while i < len(stroke) and stroke[i] in VOWELS:
        vowels += stroke[i]
        i += 1
    if i < len(stroke) and stroke[i] == "-":
        i += 1
    right = stroke[i:]
    if left != "".join(c for c in LEFT if c in left) or vowels != "".join(c for c in VOWELS if c in vowels) \
            or right != "".join(c for c in RIGHT if c in right) or len(set(left)) != len(left):
        return None
    return list(left) + list(vowels) + ["-" + c for c in right]


def starboardKeys(keys: tuple[str, ...], keymap: dict[str, str]) -> dict[str, int]:
    """Gemini PR button -> Stenalgo key index: `keys` is the system's KEYS in key-index order, `keymap` its
    GEMINI_PR_KEYMAP (key name -> button)."""
    return {button: keys.index(name) for name, button in keymap.items() if name in keys}


def convertStroke(stroke: str, buttonKey: dict[str, int], gemini: dict[str, str] = GEMINI) -> list[tuple[int, ...]] | None:
    """The Stenalgo key sets (one per spelling of an Ireland `*`) an Ireland stroke maps to; None when a key has no
    counterpart. `gemini` is the Ireland key -> Gemini PR button table (the number bar of Pluvier moves the top `S`, see
    util/export_plover_numbers.py)."""
    keys = parseIreland(stroke)
    if keys is None:
        return None
    fixed: list[int] = []
    star = False
    numberBar = keys[0] == "#"
    if numberBar:
        fixed.append(buttonKey[STAR_BUTTONS[1]])      # the Stenalgo `#` key
        keys = keys[1:]
    for key in keys:
        if key == "*":
            star = True
        elif gemini.get(key) in buttonKey:
            fixed.append(buttonKey[gemini[key]])
        else:
            return None
    if not star:
        return [tuple(sorted(fixed))]
    return [tuple(sorted(fixed + [buttonKey[STAR_BUTTONS[0]]]))] if STAR_BUTTONS[0] in buttonKey else []


def convertOutline(outline: str, buttonKey: dict[str, int], gemini: dict[str, str] = GEMINI
                   ) -> list[tuple[tuple[int, ...], ...]] | None:
    """Every Stenalgo outline (a tuple of key sets) of an Ireland outline, None when a stroke cannot be mapped."""
    perStroke = [convertStroke(s, buttonKey, gemini) for s in outline.split("/")]
    if any(p is None for p in perStroke):
        return None
    return [tuple(combo) for combo in product(*perStroke)]       # type: ignore[arg-type]


def pressable(starboard: Starboard, stroke: tuple[int, ...]) -> bool:
    """Whether one stroke can be pressed: on every finger the pressed keys are a legal keypress of that finger
    (`Starboard._possibleKeypress`). Unlike `SimContext.isLegal`, which judges word strokes and refuses any key outside
    the onset/nucleus/coda banks, this lets the reserved keys (`*`, `#`, `&`, `%`) join a chord: punctuation and
    commands may use them, the homophone marks of the theory are not in the way (the collision filter checks that)."""
    table = starboard._possibleKeypress
    pressed = set(stroke)
    for finger in table.fingers:
        fingerKeys = {key for combo in table[finger] for key in combo}
        mine = tuple(sorted(pressed & fingerKeys))
        if mine not in table[finger]:
            return False
        pressed -= fingerKeys
    return not pressed          # a key that no finger owns

# --- French spacing ------------------------------------------------------------------------------------------------

FRENCH = {
    "{:}": "{^" + SPACE + ":}", "{;}": "{^" + SPACE + ";}",
    "{?}": "{^" + SPACE + "?}{-|}", "{!}": "{^" + SPACE + "!}{-|}",
    '{~|"^}': "{~|«" + SPACE + "^}", '{^~|"}': "{^~|" + SPACE + "»}",
    "{~|'^}": "{~|\u201c^}", "{^~|'}": "{^~|\u201d}",      # the single quotes become the French inner quotes “ ”
}


def frenchTranslation(translation: str) -> str:
    """The French form of a Plover translation."""
    return FRENCH.get(translation, translation)


# --- phonetic aliases (Stenalgo's own, not converted from any Plover chord) ----------------------------------------------

# Chords spelled from the French name of the mark, from the layout's phoneme keys (onset p- v- t-, coda -t -l -d -k, the
# pair s+v = /b/ and m+t = /l/). They add a second chord to the glue marks the key-to-key conversion provides (`R-kd` for
# `{^}-{^}`...), so both stay writable. The period and the comma keep their key-position chords from Plover (`pm-kt`, `vt-dR`,
# 4 keys, and the glued period `m-k`): no phonetic alias for them (decided 2026-10-07); `v-l` is only the glued comma. The slash is also Pluvier's `BL-K`; the star
# key makes the backslash (`{^\\^}`: a backslash before `{` would escape the brace in a translation).
PHONETIC_ALIASES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("v-", "-l"), "{^},{^}"),                       # virgule: the glued comma (no Plover or Lapwing chord for it)
    (("t-", "-d"), "{^}-{^}"),                       # trait d'union
    (("s-", "v-", "m-", "t-", "-k"), "{^}/{^}"),     # barre oblique: bl-k
    (("s-", "v-", "m-", "t-", "*", "-k"), "{^\\^}"),   # backslash: bl*k
    (("v-", "t-", "@-", "-R", "-l"), '{~|"^}'),      # the straight guillemet ", opening: the French « chord (vt-Rl) plus the @ thumb
    (("v-", "w-", "@-", "-R", "-l"), '{^~|"}'),      # the straight guillemet ", closing: the French » chord (vw-Rl) plus the @ thumb
)


# The keys whose Plover chord is no position but an English word or a mnemonic (BackSpace PW-FP, Return R*R, Delete TK*EL), spelled
# from the French sound instead, in the commands file: backspace = /m t/ + /Z k/ (the docs/PLOVER_COMPLEMENTS.md survey, rows 30, 31,
# 35, 36), delete = "del" /d E l/; the `*` chord only. The free plain chord of Return is the glued newline.
COMMAND_ALIASES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("m-", "t-", "-j", "-k"), "{#BackSpace}"),
    (("m-", "t-", "*", "-j", "-k"), "{#BackSpace}"),
    (("w-", "*", "-s"), "{#Return}{^}"),
    (("w-", "-s"), "{^~|\n^}"),
    (("p-", "v-", "*", "-i", "-e", "-l"), "{#Delete}"),
)


def phoneticAliases(keys: tuple[str, ...], aliases: tuple[tuple[tuple[str, ...], str], ...] = PHONETIC_ALIASES
                    ) -> list[tuple[tuple[int, ...], str]]:
    """PHONETIC_ALIASES (or COMMAND_ALIASES) with the key names resolved to indices (`keys` is the system's KEYS)."""
    return [(tuple(sorted(keys.index(name) for name in names)), translation) for names, translation in aliases]


# --- Pluvier (TAO / LaSalle) --------------------------------------------------------------------------------------------

SOURCE_PLUVIER = "pluvier-tao"
# Plover translation of each key-position Pluvier outline (the TAO table writes plain characters; French spacing is applied after).
PLUVIER_POSITION: dict[str, str] = {
    "-RBGS": "{,}", "-FPLT": "{.}", "-FPLT/-FPLT": "{:}", "-FPLT/-RBGS": "{;}", "-FPLT/-FPLT/-FPLT": "{^...}",
    "STPH": "{?}", "STPH-FPLT": "{!}", "*P": "{^\n\n^}{-|}",
}
# Phonetic rows spelled with the Stenalgo phoneme keys: onset keys, nucleus keys, coda keys of each stroke, and the
# translation. trois points = /tR wa p/ (OEU = /wa/, Pluvier's 'wa' rule); dialogue = /d i j/ (the pair p+v is /d/);
# barre oblique = /b l/ + /k/ (the pairs s+v and m+t).
# Chords the theory already uses get a `*`: the guillemets /g i j/ (G + -LZ = /ij/) would
# be `ksij`, the first stroke of theory outlines; the apostrophe is Pluvier's STROFL = "strophe" /stRof/ (the dictionary maps
# STROFL to the word, so the -L is no sound), but `stResd` is the word strophe here; the dash is T-RS = /ti/ + /RE/ (`tieR` is
# "terre", `t*ieR` "taire", `tie#R` "ter": the `*` and the `#` together are free); parenthèse = p R z, the skeleton (-z = n+l);
# pourcent = p R n (pour cent), glued to the preceding word without a space.
APOSTROPHE = ("s-", "t-", "R-", "-e", "-s", "-d")
GUILLEMET = ("k-", "s-", "-i", "-j")
PLUVIER_PHONETIC: tuple[tuple[str, tuple[tuple[str, ...], ...], str], ...] = (
    ("TROEUP", (("t-", "R-", "w-", "a-", "-j", "-k"),), "{^...}"),
    ("TKEULZ", (("p-", "v-", "-i", "-j"),), "{^" + SPACE + ":}{~|\u00ab" + SPACE + "^}"),
    ("BL-K", (("s-", "v-", "m-", "t-", "-k"),), "{^}/{^}"),
    ("STROFL", ((*APOSTROPHE, "*"),), "{^'^}"),
    ("G-LZ", ((*GUILLEMET, "*"),), "{~|\u00ab" + SPACE + "^}"),
    ("G-LZ/G-LZ", ((*GUILLEMET, "*"),) * 2, "{^~|" + SPACE + "\u00bb}"),
    ("T-RS", (("t-", "-i", "-e", "-R", "*", "#"),), "-"),
    ("P-RZ", (("p-", "R-", "-n", "-l"),), "{(^}"),
    ("P-RZ/P-RZ", (("p-", "R-", "-n", "-l"),) * 2, "{^)}"),
    ("PR-PB", (("p-", "R-", "-n"),), "{^%}"),
)
# Pluvier's own glued comma and period, Tao.md Lesson 24 "-FRBGS removes the spaces before and after a comma": key to key from the Ireland chord, no
# classification row needed. The number lessons take them from the punctuation style, not from the number theory.
PLUVIER_GLUE: dict[str, str] = {"-FRBGS": "{^},{^}", "-RPBGS": "{^}.{^}"}
# Rows not given a chord of their own: they are served by one the Plover file already has.
PLUVIER_COVERED = {
    "OE": "trait d'union: `t-d` (phonetic alias, `{^}-{^}`) and `R-kd` (Plover's H-PB)",
    "PWHR-BG": "slash: `svmt-k` (BL-K, also in this file)",
}


def buildPluvier(rows: list[dict[str, str]], starboard: Starboard, buttonKey: dict[str, int], keys: tuple[str, ...],
                 theoryOutlines: set[str], theoryFirstStrokes: set[str]) -> dict[str, Any]:
    """The Pluvier punctuation dictionary: {"punctuation": {outline: translation}, "dropped": [...], "covered": [...]}."""
    result: dict[str, Any] = {"punctuation": {}, "dropped": [], "covered": []}

    def add(name: str, outline: tuple[tuple[int, ...], ...], translation: str) -> None:
        text = renderFinalStrokesToRTFCRE(starboard, outline)
        reason = ("not pressable" if not all(pressable(starboard, s) for s in outline) else
                  "equals a theory outline" if text in theoryOutlines else
                  "first stroke of a theory outline" if text.split("/")[0] in theoryFirstStrokes else
                  "already taken" if text in result["punctuation"] else "")
        if reason:
            result["dropped"].append((name, f"{text}: {reason}"))
        else:
            result["punctuation"][text] = translation

    for row in rows:
        if row["source"] == SOURCE_PLUVIER and row["kind"] == "position" and row["outline"] in PLUVIER_POSITION:
            outlines = convertOutline(row["outline"], buttonKey) or []
            translation = frenchTranslation(PLUVIER_POSITION[row["outline"]])
            for outline in outlines:
                add(row["outline"], outline, translation)
    for glueOutline, glueTranslation in PLUVIER_GLUE.items():
        for gluePress in convertOutline(glueOutline, buttonKey) or []:
            add(glueOutline, gluePress, glueTranslation)
    for name, strokes, translation in PLUVIER_PHONETIC:
        add(name, tuple(tuple(sorted(keys.index(k) for k in stroke)) for stroke in strokes), translation)
    result["covered"] = [(name, reason) for name, reason in PLUVIER_COVERED.items()]
    return result


def completePluvier(built: dict[str, Any], pluvier: dict[str, Any]) -> tuple[dict[str, str], list[tuple[str, str, str]]]:
    """The Pluvier file as a complete set: every punctuation chord and every command of the Plover-derived build (space, backspace,
    return, delete, cursor keys...) plus the Pluvier chords, which win a chord both define. Returns the entries and the
    overridden chords as (chord, Plover meaning, Pluvier meaning). Either file then offers the same symbols on its own."""
    merged = {**built["punctuation"], **built["commands"]}
    overridden = [(chord, merged[chord], meaning) for chord, meaning in pluvier["punctuation"].items()
                  if chord in merged and merged[chord] != meaning]
    merged.update(pluvier["punctuation"])
    return merged, overridden


# --- build -----------------------------------------------------------------------------------------------------------

def loadRows(path: str = CLASSIFICATION, sources: tuple[str, ...] = SOURCES) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter="\t") if r["kind"] == "position" and r["source"] in sources]


def build(rows: list[dict[str, str]], starboard: Starboard, buttonKey: dict[str, int],
          theoryOutlines: set[str], theoryFirstStrokes: set[str],
          aliases: list[tuple[tuple[int, ...], str]] | None = None,
          commandAliases: list[tuple[tuple[int, ...], str]] | None = None) -> dict[str, Any]:
    """Pure builder over the classification rows: {"punctuation": {outline: translation}, "commands": {...},
    "dropped": [(ireland outline, reason)]}."""
    result: dict[str, Any] = {"punctuation": {}, "commands": {}, "dropped": []}
    seen: set[str] = set()
    plainOutputs = {(r["source"], r["output"]) for r in rows if not r["outline"].startswith("#")}
    ordered = [r for source in SOURCES for r in rows if r["source"] == source]
    ordered.sort(key=lambda r: not r["outline"].startswith("#"))      # number-bar rows first (stable: sources keep their order)
    for row in ordered:
        if row["outline"] in seen:
            continue
        seen.add(row["outline"])
        if row["outline"].startswith("#") and (row["source"], row["output"]) in plainOutputs:
            result["dropped"].append((row["outline"], "redundant: a plain outline of the source has the same output"))
            continue
        translation = frenchTranslation(row["output"].replace("\\n", "\n"))
        outlines = convertOutline(row["outline"], buttonKey)
        if outlines is None:
            result["dropped"].append((row["outline"], "a key with no Stenalgo counterpart"))
            continue
        target = result["punctuation"] if row["note"].startswith("punctuation") else result["commands"]
        for outline in outlines:
            text = renderFinalStrokesToRTFCRE(starboard, outline)
            if not all(pressable(starboard, stroke) for stroke in outline):
                result["dropped"].append((row["outline"], f"{text}: not pressable"))
            elif text in theoryOutlines:
                result["dropped"].append((row["outline"], f"{text}: equals a theory outline"))
            elif text.split("/")[0] in theoryFirstStrokes:
                result["dropped"].append((row["outline"], f"{text}: first stroke of a theory outline"))
            elif text in result["punctuation"] or text in result["commands"]:
                result["dropped"].append((row["outline"], f"{text}: already taken by another entry"))
            else:
                target[text] = translation
    for target, group in ((result["punctuation"], aliases), (result["commands"], commandAliases)):
        for keys, translation in group or []:
            text = renderFinalStrokesToRTFCRE(starboard, (keys,))
            reason = ("not pressable" if not pressable(starboard, keys) else
                      "equals a theory outline" if text in theoryOutlines else
                      "first stroke of a theory outline" if text in theoryFirstStrokes else
                      "already taken by another entry" if text in result["punctuation"] or text in result["commands"] else "")
            if reason:
                result["dropped"].append((f"alias {text}", reason))
            else:
                target[text] = translation
    return result


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plover_stenalgo"))
    from plover_stenalgo._generated_keys import GEMINI_PR_KEYMAP, KEYS  # type: ignore[import-not-found]
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    with open(THEORY, encoding="utf-8") as f:
        theory = json.load(f)
    firstStrokes = {outline.split("/")[0] for outline in theory if "/" in outline}
    result = build(loadRows(), starboard, starboardKeys(KEYS, GEMINI_PR_KEYMAP), set(theory), firstStrokes,
                   phoneticAliases(KEYS), phoneticAliases(KEYS, COMMAND_ALIASES))
    buttonKey = starboardKeys(KEYS, GEMINI_PR_KEYMAP)
    pluvier = buildPluvier(loadRows(sources=(SOURCE_PLUVIER,)), starboard, buttonKey, KEYS, set(theory), firstStrokes)
    complete, overridden = completePluvier(result, pluvier)
    for document, path in ((result["punctuation"], PUNCTUATION_OUT), (result["commands"], COMMANDS_OUT),
                           (complete, PLUVIER_OUT)):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(document, f, ensure_ascii=False, indent=0, sort_keys=True)
            f.write("\n")
    print(f"Wrote {PUNCTUATION_OUT} ({len(result['punctuation'])}) and {COMMANDS_OUT} ({len(result['commands'])}); "
          f"dropped {len(result['dropped'])}:")
    for outline, reason in result["dropped"]:
        print(f"  {outline}: {reason}")
    print(f"Wrote {PLUVIER_OUT} ({len(complete)}: {len(pluvier['punctuation'])} Pluvier chords on top of the Plover punctuation "
          f"and commands; {len(overridden)} chords take the Pluvier meaning), dropped {len(pluvier['dropped'])}, covered {len(pluvier['covered'])}:")
    for chord, was, now in overridden:
        print(f"  overridden {chord}: Plover {was!r}, Pluvier {now!r}")
    for name, reason in pluvier["dropped"]:
        print(f"  dropped {name}: {reason}")
    for name, reason in pluvier["covered"]:
        print(f"  covered {name}: {reason}")


if __name__ == "__main__":
    main()
