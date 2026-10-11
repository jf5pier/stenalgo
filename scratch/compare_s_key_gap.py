"""
Hand-run diagnostic (2026-10-10): why Pluvier priced on the Starboard (Gemini key-to-key conversion) costs more than the Ireland
model (286.0 against 279.9 in the first report). Prices the SAME chosen Pluvier outlines under four variants of the Ireland model
and the shipped conversion; the whole gap is the Ireland `S` (one tall key) landing on the bottom Starboard pinky key 3, whose
zig-zag and gap shape terms are then charged. Findings: docs/PLUVIER_COMPARISON_2026-10-10.md.

Run from the repo root: python scratch/compare_s_key_gap.py
Needs starboard3h.json, resources/Lexique383.tsv and the Pluvier clone
at /home/jfsp/Steno/Pluvier.
"""
import sys, math
sys.path.insert(0,'/home/jfsp/Steno/stenalgo'); sys.path.insert(0,'/home/jfsp/Steno/stenalgo/plover_stenalgo')
from plover_stenalgo._generated_keys import GEMINI_PR_KEYMAP, KEYS
from util.export_plover_complements import convertStroke, starboardKeys
import src.theorycompare as tc
PLUVIER = '/home/jfsp/Steno/Pluvier/resources/'
# lowest priority first; the TAO briefs take an outline from the generated files (see docs/THEORY_COMPARISON.md)
PLUVIER_LAYERS = [PLUVIER + f for f in ('dicofr.json', 'dicofr-plural.json', 'verbs.json', 'tao_la_salle_simple.json')]
from src.irelandkeyboard import IrelandKeyboard, STARBOARD_ID, _shapeCost, _TABLE, _FW, parseChord
from src.keyboard import Starboard
board=Starboard.fromJSONFile('starboard3h.json'); bk=starboardKeys(KEYS,GEMINI_PR_KEYMAP)
lex=tc.loadLexicon('resources/Lexique383.tsv','films'); freq=lex.freq
plu=tc.loadPluvierTheory(PLUVIER_LAYERS, PLUVIER + 'dup.json')
cache={}
def conv(t):
    if t not in cache:
        c=convertStroke(t,bk); cache[t]=board.getChordCost(c[0]) if c else None
    return cache[t]
plu.choose(conv)
words=[w for w in plu.chosen if w in freq]
def model(keys, sBottom=False, starRule=True, sShape=False):
    ids={STARBOARD_ID[k] for k in keys}
    if sBottom and 2 in ids: ids.discard(2); ids.add(3)
    if '*' in keys:
        ids.discard(10)
        rb=any(16<=i<=17 for i in ids); lb=any(8<=i<=9 for i in ids)
        ids.add(15 if (starRule and rb and not lb) else 10)
    cost=0; nf=0
    for f in _TABLE.fingers:
        t=_TABLE[f]; combo=tuple(sorted(i for i in ids if (i,) in t))
        if not combo: continue
        nf+=1; cost+=t.get(combo,_FW.pinky4keys)
    lo=2 if sShape else 4
    on=tuple(sorted(i for i in ids if lo<=i<=9)); co=tuple(sorted(i for i in ids if 16<=i<=25))
    cost+=_shapeCost(on)+_shapeCost(co)
    return int(cost*0.85**nf)
def price(fn):
    out={}
    for w in words:
        cs=[]
        for s in plu.chosen[w].split('/'):
            k=parseChord(s)
            cs.append(None if k is None else fn(k))
        out[w]=None if any(c is None for c in cs) else sum(cs)
    return out
variants={
 'Ireland model (as shipped)': price(lambda k: model(k)),
 'S counted as bottom pinky key 3, in shape terms': price(lambda k: model(k,sBottom=True,sShape=True)),
 '* always on the left index': price(lambda k: model(k,starRule=False)),
 'both (S bottom+shape, * left)': price(lambda k: model(k,sBottom=True,sShape=True,starRule=False)),
}
conv_costs={}
for w in words:
    cs=[conv(s) for s in plu.chosen[w].split('/')]
    conv_costs[w]=None if any(c is None for c in cs) else sum(cs)
variants['Gemini conversion on Starboard (as shipped)']=conv_costs
ws=set(words)
both={w for w in words if all(v[w] is not None for v in variants.values())}
print('words',len(words),'priced in all variants',len(both),'freq share',round(sum(freq[w] for w in both)/sum(freq[w] for w in words),4))
for name,v in variants.items():
    m=math.fsum(v[w]*freq[w] for w in both)/math.fsum(freq[w] for w in both)
    print(f'{m:8.2f}  {name}')
