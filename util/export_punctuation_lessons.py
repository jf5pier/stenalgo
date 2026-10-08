"""
Punctuation and Command Lessons (S10d): the trainer's `ponctuation` and `commandes` lesson tracks, for the two chord styles
of the Plover dictionary plugin (Plover English / Lapwing derived, and Pluvier / TAO derived), plus the entries listing of the
Definitions page.

Run: python -m util.export_punctuation_lessons
Requires plover_stenalgo_punctuation.json, plover_stenalgo_commands.json, plover_stenalgo_pluvier_punctuation.json,
(`util.export_plover_complements`), starboard3h.json, steno-trainer/public/data/practice-words.json
(`util.export_practice_words`), resources/punctuationLessons.json (the families and the punctuation entries, authored) and
util/punctuation_examples.jsonl (the drill examples, authored: word spellings and `@slug` symbols).
Output: steno-trainer/public/data/punctuation-lessons.json
    {"tracks": [{"id", "title", "description"}, ...],
     "lessons": {"plover": [<lesson>, ...], "pluvier": [<lesson>, ...]},
     "entries": {"plover": [<entry>, ...], "pluvier": [<entry>, ...]}}
A lesson has the `lessons.json` lesson schema; its words are drill items: a phrase mixing words and marks (`Il dit : « Merci »`,
with one segment per token, the paired marks always together) for the punctuation, the bare command chord for the commands
(commands are never executed by the trainer, only the strokes are compared). Both styles have the same lesson ids. An entry is
{"name", "glyph", "family", "primary", "chords", "output", "keywords"}: every chord of the meaning, the `*`/`#` twins included, which the lessons
leave out (the Definitions page lists them).
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from src.keyboard import Starboard
from util._stenorender import renderFinalStrokesToRTFCRE
from util.export_lessons import numberInFrench

KEYBOARD_JSON = "starboard3h.json"
PLOVER_FILES = ("plover_stenalgo_punctuation.json", "plover_stenalgo_commands.json")
PLUVIER_FILE = "plover_stenalgo_pluvier_punctuation.json"
PRACTICE_WORDS = "steno-trainer/public/data/practice-words.json"
LESSON_DATA = "resources/punctuationLessons.json"
EXAMPLES = "util/punctuation_examples.jsonl"
OUTPUT_PATH = "steno-trainer/public/data/punctuation-lessons.json"

NBSP = " "
TRACKS = (
    {"id": "ponctuation", "title": "Ponctuation",
     "description": "Les signes de ponctuation et les signes collés, dans des phrases : un style de frappes au choix, Plover ou Pluvier."},
    {"id": "commandes", "title": "Commandes",
     "description": "Effacer, valider, se déplacer, sélectionner : les frappes de commande (elles ne sont pas exécutées ici), "
                    "dans le style Plover ou Pluvier."},
)
NO_EXECUTION = "Dans l'exercice, la commande n'est pas exécutée : seule la frappe est contrôlée."


# --- chords ---------------------------------------------------------------------------------------------------------------

def parseStroke(text: str, keys: tuple[str, ...]) -> tuple[int, ...]:
    """The key indices of one steno stroke written in the system's key order (`KEYS`), the way
    `renderFinalStrokesToRTFCRE` writes it. Keys are matched left to right, the `-` jumping to the first right-hand key."""
    firstRight = next(i for i, name in enumerate(keys) if name.startswith("-") and name not in ("-i", "-e"))
    pressed: list[int] = []
    pointer = 0
    for char in text:
        if char == "-":
            pointer = max(pointer, firstRight)
            continue
        if char == "#":
            pressed.append(keys.index("#"))
            continue
        index = next((i for i in range(pointer, len(keys)) if keys[i].strip("-") == char), None)
        if index is None:
            raise ValueError(f"cannot parse stroke {text!r} at {char!r}")
        pressed.append(index)
        pointer = index + 1
    return tuple(sorted(pressed))


def parseOutline(text: str, keys: tuple[str, ...]) -> tuple[tuple[int, ...], ...]:
    return tuple(parseStroke(stroke, keys) for stroke in text.split("/"))


def checkedOutline(text: str, keys: tuple[str, ...], starboard: Starboard) -> tuple[tuple[int, ...], ...]:
    outline = parseOutline(text, keys)
    if renderFinalStrokesToRTFCRE(starboard, outline) != text:
        raise ValueError(f"chord {text!r} does not round-trip ({renderFinalStrokesToRTFCRE(starboard, outline)!r})")
    return outline


def isMarked(chord: str) -> bool:
    return "*" in chord or "#" in chord


def chordOrder(chord: str, own: set[str]) -> tuple[bool, bool, int, int, str]:
    """The primary chord of a meaning first: the style's own chords, then the unmarked ones, then the shortest."""
    return (chord not in own, isMarked(chord), chord.count("/"), len(chord), chord)


# --- French typing simulation (the text of a drill item) ---------------------------------------------------------------

ATOM = re.compile(r"\{[^}]*\}|[^{]+")
ATTACH_LEFT_MARKS = {".", ",", ":", ";", "?", "!"}


def typeText(parts: list[str], capitalizeFirst: bool = True) -> str:
    """The text Plover types for a sequence of items: a plain word (no braces) or a translation. Just enough of Plover's
    formatting for the marks of the two sets: `{^...}` attaches to the previous word, `{...^}` to the next one, `{-|}` and the
    sentence marks capitalize the next word, `{#BackSpace}` erases a character, `{#Return}` is a newline."""
    return typePieces(parts, capitalizeFirst)[0]


def typePieces(parts: list[str], capitalizeFirst: bool = True) -> tuple[str, list[tuple[str, bool]]]:
    """`typeText` and, for each part, the text it adds and whether a space precedes it."""
    out = ""
    pieces: list[tuple[str, bool]] = []
    attachNext = True
    capital = capitalizeFirst
    previousGlue = False
    for part in parts:
        start = len(out)
        spaced: bool | None = None
        for atom in ATOM.findall(part):
            if atom.startswith("{#"):
                if "BackSpace" in atom:
                    out = out[:-1]
                elif atom.lower().startswith("{#return"):
                    out += "\n"
                    attachNext = True
                continue
            if atom == "{-|}":
                capital = True
                continue
            if atom == "{~|}":
                continue
            glue = atom.startswith("{&")
            if atom.startswith("{"):
                body = atom[1:-1]
                if glue:
                    text, attachLeft, attachRight = body[1:], previousGlue, False      # a glue sticks to the glue before it
                elif body in ATTACH_LEFT_MARKS:
                    text, attachLeft, attachRight = body, True, False
                    capital = capital or body in {".", "?", "!"}
                else:
                    attachLeft, attachRight = body.startswith("^"), body.endswith("^") and len(body) > 1
                    text = body.removeprefix("^").removesuffix("^").replace("~|", "")
                    if body in ("^", "^^"):
                        text, attachLeft, attachRight = "", True, True
                    if text.startswith("\\") and len(text) > 1:
                        text = text[1:]
            else:
                text, attachLeft, attachRight = atom, False, False
            if capital and text[:1].isalpha():
                text = text[0].upper() + text[1:]
                capital = False
            gap = bool(out) and not attachLeft and not attachNext
            if gap:
                out += " "
            if spaced is None and text:
                spaced = gap
            out += text
            previousGlue = glue
            attachNext = attachRight or text.endswith("\n")
        added = out[start:]
        space = bool(spaced) if spaced is not None else False
        pieces.append((added[1:] if added.startswith(" ") and space else added, space))
    return out, pieces


def glyphOf(translation: str) -> str:
    """The visible characters of one mark (what a segment shows)."""
    text = typeText([translation], capitalizeFirst=False)
    return text.replace(NBSP, "").strip() or "␣"


# --- commands --------------------------------------------------------------------------------------------------------------

KEY_NAMES = {"Left": "Flèche gauche", "Right": "Flèche droite", "Up": "Flèche haut", "Down": "Flèche bas",
             "Home": "Début", "End": "Fin", "Page_Up": "Page précédente", "Page_Down": "Page suivante",
             "Return": "Entrée", "Tab": "Tab", "BackSpace": "Retour arrière", "Delete": "Suppression"}
MODIFIERS = {"Control": "Ctrl", "Control_L": "Ctrl", "Shift": "Maj", "Alt_L": "Alt"}
COMMAND_SLUGS = {"BackSpace": "backspace", "Delete": "delete", "Return": "return"}
COMMAND_GLYPHS = {"backspace": "⌫", "delete": "⌦", "return": "↵"}


def parseKeyCombo(spec: str) -> tuple[list[str], str]:
    """`Control_L(Shift(Left))` -> (["Control_L", "Shift"], "Left")."""
    mods: list[str] = []
    while "(" in spec:
        head, _, rest = spec.partition("(")
        mods.append(head)
        spec = rest.removesuffix(")")
    return mods, spec


def commandInfo(translation: str) -> tuple[str, str, str, str]:
    """(family, name, slug, glyph) of a `{#...}` translation: a key combination, repeated 1 to 4 times."""
    combos = re.findall(r"\{#([^}]*)\}", translation)
    repeats = len(combos)
    mods, base = parseKeyCombo(combos[0])
    base = {"return": "Return"}.get(base, base)
    names = [MODIFIERS[m] for m in mods] + [KEY_NAMES[base]]
    name = "+".join(names) + (f" ×{repeats}" if repeats > 1 else "")
    slug = "_".join([COMMAND_SLUGS.get(base, base.lower())] + [m.lower() for m in mods] + ([f"x{repeats}"] if repeats > 1 else []))
    if translation.endswith("{~|}"):
        name += " (variante)"
        slug += "_variante"
    shifted = "Shift" in mods
    if base in ("BackSpace", "Delete", "Return", "Tab"):
        family = "edition"
    elif shifted:
        family = "selection"
    elif base in ("Left", "Right", "Up", "Down"):
        family = "mots" if mods else "fleches"
        if "Alt_L" in mods:
            family = "debut_fin"
    else:
        family = "debut_fin"
    return family, name, slug, COMMAND_GLYPHS.get(slug, name)


# --- entries -----------------------------------------------------------------------------------------------------------------

def loadChords(files: tuple[str, ...]) -> dict[str, str]:
    chords: dict[str, str] = {}
    for file in files:
        with open(file, encoding="utf-8") as fh:
            chords.update(json.load(fh))
    return chords


def commandSortKey(translation: str) -> tuple[int, list[str], int]:
    """A stable teaching order for commands: the key in KEY_NAMES order, then the modifiers, then the repeat count."""
    combos = re.findall(r"\{#([^}]*)\}", translation)
    mods, base = parseKeyCombo(combos[0])
    return list(KEY_NAMES).index({"return": "Return"}.get(base, base)), mods, len(combos)


def styleEntries(chords: dict[str, str], own: set[str], authored: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """The entries of one style, one per meaning: authored punctuation entries and parsed commands."""
    byTranslation: dict[str, list[str]] = defaultdict(list)
    for chord, translation in chords.items():
        byTranslation[translation].append(chord)
    entries: list[dict[str, Any]] = []
    sortKeys: list[tuple[Any, ...]] = []
    for translation, group in byTranslation.items():
        if translation in authored:
            a = authored[translation]
            info = {"slug": a["slug"], "name": a["name"], "family": a["family"], "glyph": a.get("glyph") or glyphOf(translation),
                    "keywords": a.get("keywords", [])}
            sortKeys.append((0, list(authored).index(translation), [], 0))
        elif translation.startswith("{#"):
            family, name, slug, glyph = commandInfo(translation)
            info = {"slug": slug, "name": name, "family": family, "glyph": glyph, "keywords": []}
            sortKeys.append((1, *commandSortKey(translation)))
        else:
            raise ValueError(f"no lesson entry for the translation {translation!r} ({group})")
        ordered = sorted(group, key=lambda c: chordOrder(c, own))
        # a style offers its own chords only: the other style's chords of a meaning are left out as soon as the style has one
        # of its own (a chord both sets share, like `[`, stays)
        offered = [c for c in ordered if c in own] or ordered
        entries.append({**info, "translation": translation, "primary": offered[0], "chords": offered,
                        "own": offered,
                        "output": typeText([translation], capitalizeFirst=False)})
    return [entry for _key, entry in sorted(zip(sortKeys, entries), key=lambda pair: pair[0])]


# --- lessons -----------------------------------------------------------------------------------------------------------------

def segmentOf(text: str, label: str, steno: str, strokeCount: int, spaceBefore: bool) -> dict[str, Any]:
    return {"text": text, "label": label, "steno": steno, "strokeCount": strokeCount, "spaceBefore": spaceBefore}


def phraseItem(tokens: list[str], bySlug: dict[str, dict[str, Any]], words: dict[str, dict[str, Any]],
               outlines: dict[str, tuple[tuple[int, ...], ...]], capitalizeFirst: bool = True) -> dict[str, Any] | None:
    """One drill item from an example, None when a mark of the example does not exist in this style. `capitalizeFirst` False: the
    spelling lessons show the letters as typed (a lower-case first letter stays one)."""
    parts: list[str] = []
    marks: list[dict[str, Any] | None] = []
    strokes: list[list[int]] = []
    stenos: list[str] = []
    phonology: list[str] = []
    for token in tokens:
        if token.startswith("@"):
            entry = bySlug.get(token[1:])
            if entry is None:
                return None
            parts.append(entry["translation"])
            marks.append(entry)
            outline = outlines[entry["primary"]]
            strokes += [list(s) for s in outline]
            stenos.append(entry["primary"])
            phonology.append("")
        else:
            word = words[token]
            parts.append(token)
            marks.append(None)
            strokes += [list(s) for s in word["strokes"]]
            stenos.append(word["steno"])
            phonology.append(word["phonology"])
    text, pieces = typePieces(parts, capitalizeFirst)
    segments = []
    for token, entry, (shown, spaced) in zip(tokens, marks, pieces):
        if entry is None:
            word = words[token]
            segments.append(segmentOf(shown, word["label"], word["steno"], len(word["strokes"]), spaced))
        else:
            invisible = entry["translation"].startswith("{#") or not shown.strip()      # a command, a space, a newline: show its glyph
            segments.append(segmentOf(entry["glyph"] if invisible else shown, entry["name"], entry["primary"],
                                      len(outlines[entry["primary"]]), True if invisible else spaced))
    return {"ortho": text, "before": "", "after": "", "label": "", "phonology": " ".join(phonology),
            "steno": " ".join(stenos), "strokes": strokes, "frequency": 0, "segments": segments}


def commandItem(entry: dict[str, Any], outlines: dict[str, tuple[tuple[int, ...], ...]]) -> dict[str, Any]:
    primary = outlines[entry["primary"]]
    alternates = [{"steno": c, "strokes": [list(s) for s in outlines[c]]} for c in entry["chords"][1:]]
    item: dict[str, Any] = {"ortho": entry["name"], "before": "", "after": "", "label": "commande (non exécutée)",
                            "phonology": "", "steno": entry["primary"], "strokes": [list(s) for s in primary], "frequency": 0}
    if alternates:
        item["alternates"] = alternates
    return item


def ruleLines(entries: list[dict[str, Any]], others: bool) -> list[str]:
    lines = []
    for entry in entries:
        # only the style's own other chords: the other style's chords belong to the other style (Definitions lists them all)
        extra = [c for c in entry["own"] if c != entry["primary"] and not isMarked(c)]
        also = f" ; aussi {', '.join(extra)}" if extra and others else ""
        lines.append(f"{entry['name'][0].upper() + entry['name'][1:]} ( {entry['glyph']} ) : {entry['primary']}{also}.")
    return lines


def buildStyle(entries: list[dict[str, Any]], families: list[dict[str, Any]], examples: list[dict[str, Any]],
               words: dict[str, dict[str, Any]], outlines: dict[str, tuple[tuple[int, ...], ...]]) -> list[dict[str, Any]]:
    bySlug = {e["slug"]: e for e in entries}
    lessons: list[dict[str, Any]] = []
    counters: dict[str, int] = defaultdict(int)
    for family in families:
        members = [e for e in entries if e["family"] == family["id"]]
        if not members:
            continue
        track = family["track"]
        counters[track] += 1
        index = counters[track]
        isCommand = track == "commandes"
        items = [phraseItem(ex["tokens"], bySlug, words, outlines)
                 for ex in examples if ex["lesson"] == family["id"]]
        drill = [i for i in items if i is not None]
        if isCommand:
            drill += [commandItem(e, outlines) for e in members]
        rules = [family["intro"], *ruleLines(members, others=True)]
        if isCommand:
            rules.append(NO_EXECUTION)
        chords = [list(s) for e in members for s in outlines[e["primary"]]]
        lessons.append({
            "id": f"{track}-{index:02d}", "track": track, "index": index, "sectionTitle": family["section"],
            "title": f"Leçon {numberInFrench(index)} : {family['title']}", "kind": track,
            "newKeys": [], "newChords": sorted({tuple(c) for c in chords if len(c) >= 2}),
            "rules": [{"kind": track, "text": t} for t in rules], "words": drill})
    for lesson in lessons:
        lesson["newChords"] = [list(c) for c in lesson["newChords"]]
    return lessons


def loadWords() -> dict[str, dict[str, Any]]:
    """The highest-frequency drill item of each spelling in practice-words.json (the chord a phrase uses for it)."""
    best: dict[str, dict[str, Any]] = {}
    with open(PRACTICE_WORDS, encoding="utf-8") as fh:
        for item in json.load(fh):
            if item["ortho"] not in best or item["frequency"] > best[item["ortho"]]["frequency"]:
                best[item["ortho"]] = item
    return best


def build(plover: dict[str, str], pluvier: dict[str, str], data: dict[str, Any], examples: list[dict[str, Any]],
          words: dict[str, dict[str, Any]], starboard: Starboard, keys: tuple[str, ...]) -> dict[str, Any]:
    authored = {e["translation"]: e for e in data["entries"]}
    families = data["families"]
    unknown = {ex["lesson"] for ex in examples} - {f["id"] for f in families}
    if unknown:
        raise ValueError(f"examples for unknown lessons: {sorted(unknown)}")
    for ex in examples:
        for token in ex["tokens"]:
            if not token.startswith("@") and token not in words:
                raise ValueError(f"the example word {token!r} is not in practice-words.json ({ex['tokens']})")
    ploverOwn = set(plover)
    pluvierOwn = {chord for chord, translation in pluvier.items() if plover.get(chord) != translation}
    sets = {"plover": (plover, ploverOwn), "pluvier": (pluvier, pluvierOwn)}
    lessons: dict[str, list[dict[str, Any]]] = {}
    entriesDoc: dict[str, list[dict[str, Any]]] = {}
    for style, (chords, own) in sets.items():
        entries = styleEntries(chords, own, authored)
        outlines = {chord: checkedOutline(chord, keys, starboard) for e in entries for chord in e["chords"]}
        lessons[style] = buildStyle(entries, families, examples, words, outlines)
        entriesDoc[style] = [{"name": e["name"], "glyph": e["glyph"], "family": e["family"], "primary": e["primary"],
                              "chords": e["chords"], "output": e["output"], "keywords": e["keywords"]} for e in entries]
    ids = {style: [lesson["id"] for lesson in value] for style, value in lessons.items()}
    if ids["plover"] != ids["pluvier"]:
        raise ValueError(f"the two styles have different lessons: {ids}")
    return {"tracks": list(TRACKS), "lessons": lessons, "entries": entriesDoc}


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "plover_stenalgo"))
    from plover_stenalgo._generated_keys import KEYS  # type: ignore[import-not-found]
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")
    with open(LESSON_DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    with open(EXAMPLES, encoding="utf-8") as fh:
        examples = [json.loads(line) for line in fh if line.strip()]
    document = build(loadChords(PLOVER_FILES), loadChords((PLUVIER_FILE,)), data, examples, loadWords(), starboard, KEYS)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(document, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    for style, lessons in document["lessons"].items():
        print(f"{style}: {len(lessons)} lessons, {sum(len(l['words']) for l in lessons)} drill items, "
              f"{len(document['entries'][style])} entries")


if __name__ == "__main__":
    main()
