import sys, json
sys.path.insert(0, "/home/jfsp/Steno/stenalgo-briefs")
from scratch.build_expr_candidates import resolveTerm
from src.affixes import SimContext
from src.expressions import AttachRule, Rules, Token, composeOutlineTraced, _syllabic
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
att = tuple(AttachRule(tuple(r["units"]), r["position"], tuple(r["keys"]), r["family"]) for r in fin if r["kind"]=="attach")
R = lambda s: renderFinalStrokesToRTFCRE(sb, s)
for units in [("qu'","il"),("qu'","elle"),("qu'","on"),("que","je"),("que","nous")]:
    toks = tuple(tok(u) for u in units)
    t = composeOutlineTraced(Rules(attaches=att), toks, ctx)
    print(" ".join(units), "longform:", [R(x.strokes) for x in toks], "->", R(t.strokes), "saving", t.saving)
    for sg in t.segments:
        print("   ", sg.kind, sg.units, sg.outcome, sg.reason, R(sg.strokes) if sg.strokes else "")
    for r in att:
        if r.expression == units[:1] and r.position == "prefix":
            h = toks[1].strokes[0]
            u = tuple(sorted(set(h) | set(r.keypress)))
            print("    host stroke", h, "attach keys", r.keypress, "union", u,
                  "overlap", sorted(set(_syllabic(h)) & set(_syllabic(r.keypress))),
                  "legal", ctx.isLegal(_syllabic(u)))
print("---- in context")
from src.expressions import BriefRule
briefs = {("qu'","il"): ((4,),), ("que","je"): ((2,5,7,11,12),)}
for units in [("qu'","il","est"),("qu'","il","a"),("que","je","suis"),("que","je","sais")]:
    toks = tuple(tok(u) for u in units)
    base = composeOutlineTraced(Rules(attaches=att), toks, ctx)
    br = tuple(BriefRule(k, v) for k, v in briefs.items())
    withB = composeOutlineTraced(Rules(attaches=att, briefs=br), toks, ctx)
    print(" ".join(units), "longform", sum(len(t.strokes) for t in toks), "| attaches:", R(base.strokes), "saving", base.saving,
          [(sg.kind, sg.units, sg.outcome, sg.reason) for sg in base.segments], "| with brief:", R(withB.strokes), "saving", withB.saving)
