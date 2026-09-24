"""
Export a real Plover JSON dictionary (steno string -> French word) from
the disambiguated theory (base strokes + the same-lemma marks of Discriminating-Feature Stroke
Realization (Realization Phase) + the star/hash marks of Different-Lemma or
Grammatical-Category Disambiguation (S7) -- see `util._theoryio.loadDisambiguatedTheory`), rendered via
`util._stenorender.renderFinalStrokesToRTFCRE` (Stenalgo's own key names,
matching `plover_stenalgo`'s system plugin) instead of the phoneme-letter
rendering `writePhoneticTheory`/`phonetic_theory.tsv` uses.

Until 2026-09-21 this only used the phonetic theory (`PhoneticTheory.pickle`), so homophones
the marking pipeline is specifically built to distinguish (e.g. "a"/"as"/"à")
collided onto the same steno string in the real dictionary. Any collision
remaining now is either an intentional exemption (homograph, 1990-reform
doublet, one word >10x rarer than the other) or a real gap in the marking
pipeline, not something this exporter can fix -- the most frequent word of
each colliding group is kept; the rest are reported, same as `writePhoneticTheory`'s
existing ambiguity reporting.

Run: python -m util.export_plover_dictionary
Requires PhoneticTheory.pickle/Dictionary.pickle (`python -m util.build_phonetic_theory` first),
keypress_groups.json (`python -m util.build_keypress_groups`) and
resolved_press_sets.json (`python -m src.elicitation`).
"""
import json
from collections import defaultdict

from src.keyboard import Starboard
from src.word import Word
from util._stenorender import renderFinalStrokesToRTFCRE
from util._theoryio import loadDisambiguatedTheory

KEYBOARD_JSON = "starboard3h.json"
OUTPUT_PATH = "plover_stenalgo_dictionary.json"


def main() -> None:
    starboard = Starboard.fromJSONFile(KEYBOARD_JSON)
    if starboard is None:
        raise RuntimeError(f"{KEYBOARD_JSON} not found; it is a committed input -- run from the repo root.")

    disambiguatedTheory = loadDisambiguatedTheory(starboard)

    stenoToWords: dict[str, list[Word]] = defaultdict(list)
    for word, strokesList in disambiguatedTheory.items():
        for strokes in strokesList:
            steno = renderFinalStrokesToRTFCRE(starboard, strokes)
            # A self-homograph word's own several strokes (see loadDisambiguatedTheory) should
            # always render distinct steno strings -- guard against counting the same
            # word twice under one steno as a spurious 1-word "collision" if they ever
            # coincide.
            if word not in stenoToWords[steno]:
                stenoToWords[steno].append(word)

    stenoDict: dict[str, str] = {}
    collisions: list[tuple[str, list[str]]] = []
    for steno, words in stenoToWords.items():
        chosen = max(words, key=lambda w: w.frequency)
        stenoDict[steno] = chosen.ortho
        if len(words) > 1:
            collisions.append((steno, sorted({w.ortho for w in words})))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(stenoDict, f, ensure_ascii=False, indent=1, sort_keys=True)

    print(f"Wrote {OUTPUT_PATH}: {len(stenoDict)} strokes"
          f" ({len(collisions)} same-steno collisions -- expected for homograph/exempted"
          f" pairs, not a regression).")
    for steno, orthos in sorted(collisions, key=lambda c: -len(c[1]))[:10]:
        print(f"  {steno!r}: {orthos} -> kept {stenoDict[steno]!r}")


if __name__ == "__main__":
    main()
