"""
Export a frequency-ordered word -> chord list for the `steno-trainer` web app to
drill from, keyed by orthography (not by steno string, the way
`util/export_plover_dictionary.py` is) -- the trainer only ever needs "what chord
for this word," never the reverse, so it dedupes on `ortho` instead of `steno`
when a word appears under more than one entry, keeping the highest-frequency one.

Uses `util._theoryio.loadFinalTheory` (theory 2: base strokes + Phase P's
same-lemma marks + the `*`/`#` lemma-homophone track), not the raw unmarked
theory 1 -- this is what actually disambiguates homophones like "a"/"as"/"à"
(same base phonology, different final chords once Phase P/the */# track are
applied). A word whose final chord still collides with another word's (the same
lemma+gramCat, or an intentionally-exempted pair -- 1990-reform doublets, or one
word >10x rarer than the other) is expected, not a bug in this exporter; the
most frequent variant is kept.

Each record also carries context words to show around it (`before`/`after`, never
typed -- see `formatContext`), and the word's X-SAMPA `phonology`, syllabified (see
`formatPhonology`); the trainer can show it in IPA instead (`Notation.elm`).

Emits both a display steno string and the raw key-index strokes, so the browser
never needs a steno-notation parser -- it just compares sets of key indices
against a decoded Gemini PR packet.

Each record also carries a human-readable French grammatical `label` (e.g.
"impératif présent, 2e pl.", "nom, f. pl."), so a drill can say WHICH reading a
chord is for. A self-homograph word (e.g. "calmez", see `loadFinalTheory`) gets
one record per independently-valid stroke, each labelled with only the
reading(s) that stroke is for -- taken from `resolved_press_sets.json`'s
"readings" field (`src.elicitation.serializeResolvedPressSets`), which is
parallel to that spelling's press-set alternates, and therefore to
`loadFinalTheory`'s per-word stroke list.

Run: python -m util.export_practice_words [--limit N]
Requires FirstTheory.pickle/Dictionary.pickle (`python dictionary.py` first),
keypress_groups.json (`python -m util.build_keypress_groups`) and
resolved_press_sets.json (`python -m src.elicitation`).
"""
import argparse
import json

from src.ambiguitychecker import _resolveEntryWord, buildWordsByOrthoLemme, buildWordToStrokes
from src.elicitation import wordFeatureCombinations
from src.keyboard import Starboard, Strokes
from src.word import GramCat, Word
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadFirstAndFinalTheory

KEYBOARD_JSON = "starboard3h.json"
RESOLVED_PRESS_SETS_PATH = "resolved_press_sets.json"
OUTPUT_PATH = "steno-trainer/public/data/practice-words.json"
DEFAULT_LIMIT = 10000

GRAMCAT_LABELS = {
    "ADJ": "adjectif", "ADJ:dem": "adjectif démonstratif", "ADJ:ind": "adjectif indéfini",
    "ADJ:int": "adjectif interrogatif", "ADJ:num": "adjectif numéral", "ADJ:pos": "adjectif possessif",
    "ADV": "adverbe", "ART:def": "article défini", "ART:ind": "article indéfini", "AUX": "auxiliaire",
    "CON": "conjonction", "LIA": "liaison", "NOM": "nom", "ONO": "onomatopée", "PRE": "préposition",
    "PRO:dem": "pronom démonstratif", "PRO:ind": "pronom indéfini", "PRO:int": "pronom interrogatif",
    "PRO:per": "pronom personnel", "PRO:pos": "pronom possessif", "PRO:rel": "pronom relatif",
    "VER": "verbe",
}
MOODS = ["infinitif", "indicatif", "impératif", "subjonctif", "conditionnel", "participe"]
TENSE_LABELS = {"présent": "présent", "passé": "passé", "imparfait": "imparfait", "future": "futur"}
PERSON_LABELS = {"pers_1": "1re", "pers_2": "2e", "pers_3": "3e"}
VERB_NUMBER_LABELS = {"nbr_s": "sg.", "nbr_p": "pl."}
GENDER_LABELS = {"m": "m.", "f": "f."}
NUMBER_LABELS = {"s": "sg.", "p": "pl."}

type Reading = frozenset[str]

# Context words shown around a drilled word (never typed), so a bare form reads as the
# reading its chord writes: "la maison", "je parle", "que tu viennes", "parle !".
PRONOUNS = {
    ("pers_1", "nbr_s"): "je", ("pers_2", "nbr_s"): "tu", ("pers_3", "nbr_s"): "il",
    ("pers_1", "nbr_p"): "nous", ("pers_2", "nbr_p"): "vous", ("pers_3", "nbr_p"): "ils",
}
# Which of a chord's readings to give context for when it writes several (e.g. "fais" =
# indicatif 1s/2s and impératif 2s): the plainest one.
CONTEXT_MOOD_PRIORITY = ["indicatif", "conditionnel", "subjonctif", "impératif"]
VOWEL_INITIALS = frozenset("aàâäeéèêëiîïoôöuùûüyœæ")
# Common h-aspiré lemmas: no elision before them ("le haricot", "je hais"). Every other
# h-initial word is treated as h muet ("l'homme", "j'habite").
H_ASPIRE_LEMMAS = frozenset({
    "hache", "hacher", "haie", "haillon", "haine", "haïr", "hall", "halle", "halte", "hamac",
    "hameau", "hamster", "hanche", "handicap", "hangar", "hanter", "harceler", "hardi",
    "hareng", "haricot", "harnais", "harpe", "hasard", "hâte", "hâter", "hausse", "hausser",
    "haut", "hauteur", "hennir", "hérisser", "hérisson", "hernie", "héros", "hêtre", "heurter",
    "hibou", "hiérarchie", "hisser", "hockey", "homard", "honte", "honteux", "hoquet", "hors",
    "hotte", "housse", "hublot", "huer", "huit", "huitième", "hurlement", "hurler", "hutte",
})


def _readingHeadAndDetail(gramCat: GramCat, reading: Reading) -> tuple[str, str]:
    """One reading (a `src.elicitation` feature combination) split into its
    "what" (mood + tense, or the part of speech) and its person/gender/number detail,
    so several readings sharing a head can be written once: "indicatif présent, 1re sg. / 3e sg."."""
    mood = next((m for m in MOODS if m in reading), None)
    if mood is not None:
        head = " ".join([mood] + [label for tense, label in TENSE_LABELS.items() if tense in reading])
    else:
        head = GRAMCAT_LABELS.get(gramCat.name, gramCat.name)
    detail = " ".join(
        [PERSON_LABELS[a] for a in PERSON_LABELS if a in reading]
        + [VERB_NUMBER_LABELS[a] for a in VERB_NUMBER_LABELS if a in reading]
        + [GENDER_LABELS[a] for a in GENDER_LABELS if a in reading]
        + [NUMBER_LABELS[a] for a in NUMBER_LABELS if a in reading]
    )
    return head, detail


def formatReadingsLabel(gramCat: GramCat, readings: list[Reading]) -> str:
    """Human-readable French label for the reading(s) one stroke writes, e.g.
    "impératif présent, 2e pl.", "participe passé, f. pl.", "nom, m. sg."."""
    if not readings:
        return GRAMCAT_LABELS.get(gramCat.name, gramCat.name)
    detailsByHead: dict[str, list[str]] = {}
    for reading in readings:
        head, detail = _readingHeadAndDetail(gramCat, reading)
        details = detailsByHead.setdefault(head, [])
        if detail and detail not in details:
            details.append(detail)
    return " · ".join(
        f"{head}, {' / '.join(details)}" if details else head for head, details in detailsByHead.items()
    )


def _elides(word: Word) -> bool:
    first = word.ortho[:1].lower()
    return first in VOWEL_INITIALS or (first == "h" and word.lemme not in H_ASPIRE_LEMMAS)


def formatContext(word: Word, readings: list[Reading]) -> tuple[str, str]:
    """The context word(s) to show before and after `word` for the reading its chord
    writes: an article for a noun/adjective ("le"/"la"/"l'"/"les"), a subject pronoun
    for a conjugated verb ("je"/"j'", "que tu", "qu'ils"), "!" after an impératif.
    ("", "") when nothing fits (infinitif, participe, other categories)."""
    if word.gramCat in (GramCat.NOM, GramCat.ADJ):
        reading = readings[0] if readings else frozenset()
        if "p" in reading:
            return "les", ""
        if "s" in reading and _elides(word):
            return "l'", ""
        if "s" in reading and "m" in reading:
            return "le", ""
        if "s" in reading and "f" in reading:
            return "la", ""
        return "", ""
    if word.gramCat not in (GramCat.VER, GramCat.AUX):
        return "", ""

    conjugated = [r for r in readings if any(mood in r for mood in CONTEXT_MOOD_PRIORITY)]
    if not conjugated:
        return "", ""
    reading = min(conjugated, key=lambda r: next(i for i, m in enumerate(CONTEXT_MOOD_PRIORITY) if m in r))
    if "impératif" in reading:
        return "", "!"
    pronoun = next((p for (person, number), p in PRONOUNS.items() if person in reading and number in reading), None)
    if pronoun is None:
        return "", ""
    if pronoun == "je" and _elides(word):
        pronoun = "j'"
    if "subjonctif" in reading:
        return ("qu'" + pronoun if pronoun.startswith("i") else "que " + pronoun), ""
    return pronoun, ""


def formatPhonology(word: Word) -> str:
    """The word's X-SAMPA pronunciation, syllables dot-separated the way the steno
    splits them into strokes (`Word.syllCV`, after its steno-encoding syllable-break
    fixes), e.g. "kal.me". "#" is `syllCV`'s empty-slot placeholder, not a phoneme."""
    return ".".join("".join(part for part in syllable if part != "#") for syllable in word.syllCV)


def buildReadingsByWord(
    resolvedGroups: list[dict], theory: dict[Strokes, list[Word]],
) -> dict[Word, list[list[Reading]]]:
    """Every word covered by `resolved_press_sets.json` -> its readings per press-set
    alternate (parallel to its `loadFinalTheory` stroke list), matched to the real `Word`
    the same way the Phase P pipeline does (`_resolveEntryWord`)."""
    wordToStrokes = buildWordToStrokes(theory)
    wordsByOrthoLemme = buildWordsByOrthoLemme(theory)
    readingsByWord: dict[Word, list[list[Reading]]] = {}
    for entry in resolvedGroups:
        for ortho, readingsPerAlternate in entry.get("readings", {}).items():
            word = _resolveEntryWord(entry, ortho, wordToStrokes, wordsByOrthoLemme)
            if word is not None:
                readingsByWord[word] = [
                    [frozenset(reading) for reading in readings] for readings in readingsPerAlternate
                ]
    return readingsByWord


def chordsWithReadings(
    word: Word, strokesList: list[Strokes], readingsByWord: dict[Word, list[list[Reading]]],
) -> tuple[list[tuple[Strokes, list[Reading]]], bool]:
    """Each of `word`'s final strokes paired with the reading(s) it writes, and whether
    `buildReadingsByWord`'s readings lined up with the strokes. A word that isn't a
    same-lemma homophone (or is misaligned) writes every one of its readings with every
    stroke."""
    readingsPerStroke = readingsByWord.get(word)
    aligned = readingsPerStroke is None or len(readingsPerStroke) == len(strokesList)
    if readingsPerStroke is None or not aligned:
        readingsPerStroke = [wordFeatureCombinations(word)] * len(strokesList)
    return list(zip(strokesList, readingsPerStroke)), aligned


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                         help="Keep only the N most frequent words (default %(default)s).")
    args = parser.parse_args()

    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; run dictionary.py once first to generate it.")

    theory, finalTheory = loadFirstAndFinalTheory(starboard)
    with open(RESOLVED_PRESS_SETS_PATH, encoding="utf-8") as f:
        readingsByWord = buildReadingsByWord(json.load(f), theory)

    # Keyed by (ortho, steno), not ortho alone: a self-homograph's alternate strokes, and
    # two different words sharing a spelling but not a chord ("est" = être / nom), are
    # each their own drill item now that every item says which reading it's for.
    byOrthoSteno: dict[tuple[str, str], dict] = {}
    misalignedWords = 0
    for word, strokesList in finalTheory.items():
        chords, aligned = chordsWithReadings(word, strokesList, readingsByWord)
        misalignedWords += not aligned
        for strokes, readings in chords:
            steno = renderFinalStrokesToRTFCRE(starboard, strokes)
            label = formatReadingsLabel(word.gramCat, readings)
            existing = byOrthoSteno.get((word.ortho, steno))
            if existing is not None:
                # Same spelling AND same chord from two Words (an exempted homograph pair):
                # one drill item, labelled with both.
                if label not in existing["label"].split(" · "):
                    existing["label"] += f" · {label}"
                # Keep the plainer context: any over none, a subject pronoun over "!".
                before, after = formatContext(word, readings)
                if (before or after) and (existing["after"] == "!" or not (existing["before"] or existing["after"])) \
                        and after != "!":
                    existing["before"], existing["after"] = before, after
                existing["frequency"] = max(existing["frequency"], round(word.frequency, 3))
                continue
            before, after = formatContext(word, readings)
            byOrthoSteno[(word.ortho, steno)] = {
                "ortho": word.ortho, "before": before, "after": after,
                "label": label, "phonology": formatPhonology(word), "steno": steno,
                "strokes": [sorted(set(stroke)) for stroke in strokes],
                "frequency": round(word.frequency, 3),
            }

    records = sorted(byOrthoSteno.values(), key=lambda r: (-r["frequency"], r["ortho"], r["steno"]))
    records = records[:args.limit]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)

    print(f"Wrote {OUTPUT_PATH}: {len(records)} drill items"
          f" ({misalignedWords} words whose resolved readings didn't line up with their strokes"
          f" -- labelled with all of the word's readings instead).")

if __name__ == "__main__":
    main()
