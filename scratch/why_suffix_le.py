"""Why do the suffix `le` / `les` rules save 0? Compose host-then-pronoun pairs
(voir le, prend les) with the final rules and print the segment outcomes.
Run: PYTHONPATH=. env/bin/python scratch/why_suffix_le.py"""
import sys, json
sys.path.insert(0, "/home/jfsp/Steno/stenalgo-briefs")
from scratch.build_expr_candidates import resolveTerm
from src.affixes import SimContext
from src.expressions import AttachRule, Rules, Token, composeOutlineTraced
from src.keyboard import Starboard, canonicalizeStrokes
from util._theoryio import loadDisambiguatedTheory
from util._stenorender import renderFinalStrokesToRTFCRE
sb = Starboard.fromJSONFile("starboard3h.json")
theory = loadDisambiguatedTheory(sb)
byOrtho = {}
for w in theory: byOrtho.setdefault(w.ortho, []).append(w)
ctx = SimContext(sb, [])
ctx.finalOutlines = {canonicalizeStrokes(s) for a in theory.values() for s in a}
ctx.singleStrokeOutlines = {o[0] for o in ctx.finalOutlines if len(o) == 1}
def tok(u):
    pairs = resolveTerm(u, byOrtho); return Token(u, theory[pairs[0][1]][0])
fin = json.load(open("scratch/expr-rules-final.json"))["rules"]
att = tuple(AttachRule(tuple(r["units"]), r["position"], tuple(r["keys"]), r["family"]) for r in fin if r["kind"] == "attach")
R = lambda s: renderFinalStrokesToRTFCRE(sb, s)
for units in [("voir", "le"), ("prend", "les"), ("voir", "le", "chat"), ("le", "chat")]:
    try:
        toks = tuple(tok(u) for u in units)
    except Exception as e:
        print(units, "unresolved", e); continue
    t = composeOutlineTraced(Rules(attaches=att), toks, ctx)
    print(" ".join(units), "->", R(t.strokes), "saving", t.saving)
    for sg in t.segments:
        print("   ", sg.kind, sg.units, sg.outcome, sg.reason, getattr(sg.rule, "position", ""))
