"""Why 1.24% of Pluvier's frequency is unpressable on the Starboard: which finger / combination fails, and what the chords are."""
import sys, collections
sys.path.insert(0, "plover_stenalgo")
from plover_stenalgo._generated_keys import GEMINI_PR_KEYMAP, KEYS
from util.export_plover_complements import convertStroke, parseIreland, starboardKeys
from src import theorycompare as tc
from src.keyboard import Starboard
from src.irelandkeyboard import IrelandKeyboard

P = "/home/jfsp/Steno/Pluvier/resources/"
board = Starboard.fromJSONFile("starboard3h.json"); bk = starboardKeys(KEYS, GEMINI_PR_KEYMAP); ire = IrelandKeyboard()
freq = tc.loadLexicon("resources/Lexique383.tsv", "films").freq
plu = tc.loadPluvierTheory([P + f for f in ("dicofr.json", "dicofr-plural.json", "verbs.json", "tao_la_salle_simple.json")], P + "dup.json")
cache = {}
def cost(t):
    if t not in cache:
        c = convertStroke(t, bk); cache[t] = board.getChordCost(c[0]) if c else None
    return cache[t]
plu.choose(cost)
covered = set(plu.outlines) & set(freq)
tot = tc.mass(freq, covered)
table = board._possibleKeypress
def why(t):
    if t == "": return "empty stroke (word 'ai' = '/-S')"
    if parseIreland(t) is None: return "malformed chord text (keys out of steno order)"
    c = convertStroke(t, bk)
    if not c: return "no counterpart"
    for f in table.fingers:
        combo = tuple(sorted(k for k in c[0] if (k,) in table[f]))
        if combo not in table[f]:
            names = []
            for k in combo:
                names.append({22: "-T", 23: "-S", 24: "-D", 25: "-Z", 2: "S", 3: "S'"}.get(k, str(k)))
            return f"{f}: {'+'.join(names)}"
    return "legal"
byWhy = collections.Counter(); byChord = collections.Counter(); words = 0; ex = collections.defaultdict(list)
for w in covered:
    outs = plu.chosen[w].split("/")
    bad = [s for s in outs if cost(s) is None]
    if bad:
        words += 1; reason = why(bad[0]); byWhy[reason] += freq[w]; byChord[bad[0]] += freq[w]
        if len(ex[reason]) < 4: ex[reason].append((w, plu.chosen[w]))
print("unpressable words", words, "share", sum(byWhy.values()) / tot)
for r, f in byWhy.most_common(): print(f"{f/tot:8.4%}  {r:30} e.g. {ex[r]}")
print("top chords", [(c, round(f / tot * 100, 3)) for c, f in byChord.most_common(15)])
# the same chords priced on Ireland
unp_ire = sum(freq[w] for w in covered if ire.getOutlineCost(plu.chosen[w]) is None)
print("unpriced on Ireland", unp_ire / tot)
print("--- empty-stroke examples")
n = 0
for w in sorted(covered, key=lambda w: -freq[w]):
    if any(s == "" for s in plu.chosen[w].split("/")):
        print(w, repr(plu.chosen[w]), plu.outlines[w][:4], round(freq[w])); n += 1
        if n >= 12: break
