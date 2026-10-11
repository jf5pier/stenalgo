"""
Hand-run diagnostic (2026-10-10): the top-N words by film frequency, Stenalgo against Pluvier, strokes per word.
Prints how many of the N words need fewer / the same / more strokes in Pluvier (or are covered by one theory only) and lists the
words where Pluvier is shorter, marking the Pluvier outlines that collide (`dup.json`). Findings: docs/PLUVIER_COMPARISON_2026-10-10.md.

Run from the repo root: python scratch/compare_top_words.py   (N = 200 and the Pluvier clone paths are in the code below)
Also lists the top-N words covered by one theory only (`only Pluvier`, `only Stenalgo`, the latter marked when the word is in dup.json).
Uses the same views and costs as `util/compare_theories.py` (src/theorycompare.py); needs plover_stenalgo_dictionary.json,
starboard3h.json, resources/Lexique383.tsv and the Pluvier clone at /home/jfsp/Steno/Pluvier. Pluvier = the four layers dicofr, plural, verbs, TAO briefs.
"""
import sys
sys.path.insert(0,'/home/jfsp/Steno/stenalgo'); sys.path.insert(0,'/home/jfsp/Steno/stenalgo/plover_stenalgo')
from plover_stenalgo._generated_keys import GEMINI_PR_KEYMAP, KEYS
from util.export_plover_complements import convertStroke, starboardKeys
from util.compare_theories import parseStenalgoOutline
from plover_stenalgo.stroke import parseStroke
import src.theorycompare as tc
PLUVIER = '/home/jfsp/Steno/Pluvier/resources/'
# lowest priority first; the TAO briefs take an outline from the generated files (see docs/THEORY_COMPARISON.md)
PLUVIER_LAYERS = [PLUVIER + f for f in ('dicofr.json', 'dicofr-plural.json', 'verbs.json', 'tao_la_salle_simple.json')]
from src.keyboard import Starboard
board=Starboard.fromJSONFile('starboard3h.json'); bk=starboardKeys(KEYS,GEMINI_PR_KEYMAP)
freq=tc.loadLexicon('resources/Lexique383.tsv','films').freq
sten=tc.loadStenalgoTheory('plover_stenalgo_dictionary.json',parseStenalgoOutline)
plu=tc.loadPluvierTheory(PLUVIER_LAYERS, PLUVIER + 'dup.json')
def sc(t):
    k=parseStroke(t); return None if k is None else board.getChordCost(k)
def pc(t):
    c=convertStroke(t,bk); return board.getChordCost(c[0]) if c else None
sten.choose(sc); plu.choose(pc)
top=sorted(freq,key=lambda w:(-freq[w],w))[:200]
rows=[]
cnt={'pluvier fewer':0,'equal':0,'stenalgo fewer':0,'only stenalgo':0,'only pluvier':0,'neither':0}
for r,w in enumerate(top,1):
    s=sten.chosen.get(w); p=plu.chosen.get(w)
    ns=len(s.split('/')) if s else None; np_=len(p.split('/')) if p else None
    if s is None and p is None: cnt['neither']+=1
    elif p is None: cnt['only stenalgo']+=1
    elif s is None: cnt['only pluvier']+=1
    elif np_<ns: cnt['pluvier fewer']+=1; rows.append((r,w,freq[w],s,ns,p,np_,p in plu.claimants))
    elif np_==ns: cnt['equal']+=1
    else: cnt['stenalgo fewer']+=1
print(cnt, 'total',sum(cnt.values()))
print('rank word freq | stenalgo (strokes) | pluvier (strokes) [collides in Pluvier?]')
for r,w,f,s,ns,p,np_,c in rows: print(f'{r:3d} {w:14s} {f:9.1f} | {s} ({ns}) | {p} ({np_}){" [COLLIDES]" if c else ""}')
cov=sum(freq[w] for w in top)
print('frequency mass of the pluvier-fewer words / top200:',round(sum(r[2] for r in rows)/cov,3))
print('--- only Pluvier:')
for r,w in enumerate(top,1):
    if w not in sten.chosen and w in plu.chosen: print(r,w,round(freq[w],1),plu.chosen[w],plu.outlines[w])
print('--- only Stenalgo (first 50):')
for r,w in enumerate(top,1):
    if w in sten.chosen and w not in plu.chosen: print(r,w,round(freq[w],1),sten.chosen[w], 'in dup record' if w in plu.lostWords else '')
