"""Hand-run diagnostic: for each proposed PRP3 phonology override, the new outline and the spellings that already hold it."""
import sys
from util._theoryio import loadDictionary, loadPhoneticTheory
from src.keyboard import Starboard

ROWS = {"je": "Z", "te": "t", "se": "s", "le": "l", "ce": "s", "de": "d", "me": "m", "ne": "n", "que": "k"}

dictionary = loadDictionary()
theory = loadPhoneticTheory()
keyboard = Starboard.fromJSONFile("starboard3h.json")
assert keyboard is not None
names = dictionary.syllableCollection.syllable_names
owner = {}
for strokes, words in theory.items():
    for w in words:
        owner.setdefault(strokes, set()).add(w.ortho)
byOrtho = {}
for strokes, words in theory.items():
    for w in words:
        byOrtho.setdefault(w.ortho, set()).add(strokes)
for ortho, phono in ROWS.items():
    if phono not in names:
        print(f"{ortho}: syllable '{phono}' not in the syllable collection"); continue
    new = keyboard.getStrokeOfSyllableByPart(names[phono].phonemeNamesByPart())
    strokes = (new,)
    old = byOrtho.get(ortho)
    others = sorted(owner.get(strokes, set()) - {ortho})
    print(f"{ortho}: old {[keyboard.strokesToString(s) for s in old or []]} -> {keyboard.strokesToString(strokes)} ; holders: {others}")
