"""Real-Plover check of the dictionary plugin: feeds every pool outline through plover.translation.Translator
with [plugin dictionary, stock JSON dictionary] and compares the text with the expression.
Run with the Windows Plover python (WSL paths via wslpath -w):
  python.exe -X utf8 plover_translator_sim.py PLUGIN_DIR EXPRESSIONS.stenalgo plover_stenalgo_dictionary.json POOL.json
POOL.json: [{"strokes": [[key ids]...], "units": [...], "freq": f}] from scratch/decode_roundtrip.loadAll + composeOutlineTraced."""
import sys, json
sys.path.insert(0, sys.argv[1])
from plover.steno import Stroke
import plover.system as system
from plover_stenalgo._generated_keys import KEYS, IMPLICIT_HYPHEN_KEYS
Stroke.setup(KEYS, IMPLICIT_HYPHEN_KEYS, None, {}, False, "*")
system.SUFFIX_KEYS = ()
from plover.translation import Translator
from plover.steno_dictionary import StenoDictionaryCollection
from plover.dictionary.json_dict import JsonDictionary
from plover_stenalgo.dictionary import StenalgoExpressionDictionary
ours = StenalgoExpressionDictionary.load(sys.argv[2])
stock = JsonDictionary.load(sys.argv[3])
pool = json.load(open(sys.argv[4], encoding="utf-8"))

def run(entries, dicts):
    tr = Translator()
    tr.set_dictionary(StenoDictionaryCollection(dicts))
    cur = []
    def cb(undo, do, prev):
        for _ in undo: cur.pop()
        cur.extend(do)
    tr.add_listener(cb)
    for ids in entries:
        tr.translate(Stroke.from_keys([KEYS[i] for i in ids]))
    out = []
    for t in cur:
        out.append(t.english if t.english is not None else "<%s>" % "/".join(t.rtfcre))
    text = ""
    for w in out:
        if w.endswith("{^}"):
            text += (" " if text else "") + w[:-3]; glue = True; continue
        text += w if (text.endswith("'") or text.endswith("\0")) else (" " + w if text else w)
    return text.replace("'\0", "'")

def norm(units):
    s = ""
    for u in units:
        s += u if (s.endswith("'") or not s) else " " + u
    return s

ok = bad = 0; okf = badf = 0.0; shown = 0
for e in pool:
    got = run(e["strokes"], [ours, stock])
    want = norm(e["units"])
    if got.replace("{^}", "") == want:
        ok += 1; okf += e["freq"]
    else:
        bad += 1; badf += e["freq"]
        if shown < 25:
            shown += 1; print("%.2e  want %-28r got %r" % (e["freq"], want, got))
print("match %d (%.1f%% of mass), differ %d (%.1f%%)" % (ok, 100*okf/(okf+badf), bad, 100*badf/(okf+badf)))
