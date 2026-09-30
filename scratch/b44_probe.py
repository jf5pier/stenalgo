import json
from collections import defaultdict
from src.keyboard import Starboard
from util._theoryio import loadPhoneticAndDisambiguatedTheory
from src.ambiguitychecker import buildWordsByOrthoLemme, _resolveEntryWord
from util.export_plover_dictionary import renderFinalStrokesToRTFCRE

kb = Starboard.fromJSONFile("starboard3h.json")
phon, dis = loadPhoneticAndDisambiguatedTheory(kb)
wordToStrokes = {w: s for s, ws in phon.items() for w in ws}
byOL = buildWordsByOrthoLemme(phon)
plover = json.load(open("plover_stenalgo_dictionary.json"))
stenoToWords = defaultdict(list)
for w, sl in dis.items():
    for s in sl:
        stenoToWords[renderFinalStrokesToRTFCRE(kb, s)].append(w)
entries = json.load(open("resolved_press_sets.json"))
resolved = set()
for e in entries:
    for ortho in e["pressSets"]:
        w = _resolveEntryWord(e, ortho, wordToStrokes, byOL)
        if w is not None: resolved.add(w)
stats = defaultdict(int); examples = defaultdict(list)
for e in entries:
    for ortho, alts in e["pressSets"].items():
        cands = byOL.get((ortho, e["lemmeGramCat"]), [])
        if len(cands) < 2: continue
        chosen = _resolveEntryWord(e, ortho, wordToStrokes, byOL)
        stats["twin spellings"] += 1
        # every steno of the chosen Word outputs this spelling?
        chosenStenos = [renderFinalStrokesToRTFCRE(kb, s) for s in dis.get(chosen, [])]
        nAltOk = sum(plover.get(st) == ortho for st in chosenStenos)
        if nAltOk < len(alts): stats["chosen Word: some alternate stroke does not output the spelling"] += 1; examples["altlost"].append((ortho, len(alts), nAltOk))
        for tw in cands:
            if tw is chosen: continue
            if tw in resolved: stats["other Word resolved by its own entry"] += 1; continue
            stats["twin Words never resolved"] += 1
            if wordToStrokes.get(tw) != wordToStrokes.get(chosen): stats["  (different phonetic strokes: B2/B9 territory)"] += 1; continue
            stats["  SAME phonetic strokes (B1 proper)"] += 1
            examples["b1"].append((ortho, tw.infoVerb, tw.gender, tw.number, [renderFinalStrokesToRTFCRE(kb,x) for x in dis.get(tw,[])], chosen.infoVerb, chosenStenos))
            0 and examples["twin"].append((ortho, tw.gender, tw.number, tw.infoVerb, [renderFinalStrokesToRTFCRE(kb,x) for x in dis.get(tw,[])], chosenStenos))
            for s in dis.get(tw, []):
                st = renderFinalStrokesToRTFCRE(kb, s)
                others = {w.ortho for w in stenoToWords[st]} - {ortho}
                if st in chosenStenos: stats["twin on a chosen Word stroke (harmless)"] += 1
                elif not others: stats["twin alone on its stroke (extra route, harmless)"] += 1
                elif plover.get(st) == ortho:
                    lost = [o for o in others if o not in plover.values()]
                    stats["twin WINS a shared stroke"] += 1
                    if lost: stats["...and a spelling becomes unreachable"] += 1; examples["unreach"].append((ortho, st, lost))
                    else: examples["steal"].append((ortho, st, sorted(others)))
                else: stats["twin loses a shared stroke (harmless)"] += 1
for k, v in stats.items(): print(f"{v:6d}  {k}")
for k, v in examples.items(): print(k, len(v), v[:8])
print("--- altlost detail")
for e in entries:
    for ortho, alts in e["pressSets"].items():
        if ortho not in {x[0] for x in examples["altlost"]}: continue
        c = _resolveEntryWord(e, ortho, wordToStrokes, byOL)
        sts = [renderFinalStrokesToRTFCRE(kb, s) for s in dis.get(c, [])]
        print(ortho, alts, [(st, plover.get(st), sorted({w.ortho for w in stenoToWords[st]})) for st in sts])
print("--- lost feature strokes")
seen=set()
for e in entries:
    for ortho, alts in e["pressSets"].items():
        c = _resolveEntryWord(e, ortho, wordToStrokes, byOL)
        for s in dis.get(c, []):
            st = renderFinalStrokesToRTFCRE(kb, s)
            if plover.get(st) not in (None, ortho) and (ortho, st) not in seen:
                seen.add((ortho, st)); print(f"{ortho}({c.phonology},{c.lemmeGramCat}) {st} -> {plover[st]}")
