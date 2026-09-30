"""Regenerate every LexiqueMixte finite VER form from its infinitive; compare to the Mixte row."""
import sys, csv, collections, difflib
sys.path.insert(0,".")
import src.verbparadigm as vp
from util.completeVerbParadigms import loadTheoryAndKeyboard, VERBISTE_VERBS_PATH, EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH
theory,_=loadTheoryAndKeyboard()
vt=vp.loadVerbisteTemplates(VERBISTE_VERBS_PATH); ex=vp.loadVerbModelExceptions(EXCEPTIONS_PATH)
ct=vp.parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
tables=vp.deriveConjugationEndingTables(theory,vt,ex)
inf=vp.attestedInfinitiveWordByLemme(theory)
res=collections.Counter(); sig=collections.Counter(); sigex=collections.defaultdict(list)
for r in csv.DictReader(open("resources/LexiqueMixte.tsv"),delimiter="\t"):
  if r["cgram"]!="VER": continue
  tags=[t for t in r["infover"].split(";") if t]
  if "inf" in tags: continue
  tn=vp.getTrustedTemplate(r["lemme"],vt,ex); iw=inf.get(r["lemme"])
  if tn is None or iw is None or tn not in ct: continue
  for tag in tags:
    p=tag.split(":")
    if len(p)!=3: continue
    g=vp.generateMissingConjugatedForm(r["lemme"],ct[tn],iw,f"{p[0]}:{p[1]}",p[2],tables,minMatchRate=1.0)
    if g is None or g.ortho!=r["ortho"]: res["skipped"]+=1; continue
    k=tuple(a==b for a,b in [(g.phonology,r["phon"]),(g.rawSyllCV,r["syll_cv"]),(g.rawOrthosyllCV,r["orthosyll_cv"])])
    res[k]+=1
    if g.rawSyllCV!=r["syll_cv"]:
      sm=difflib.SequenceMatcher(a=g.rawSyllCV,b=r["syll_cv"],autojunk=False)
      d=tuple((g.rawSyllCV[i1:i2],r["syll_cv"][j1:j2]) for op,i1,i2,j1,j2 in sm.get_opcodes() if op!="equal")
      sig[d]+=1
      if len(sigex[d])<3: sigex[d].append((r["ortho"],tag,g.rawSyllCV,r["syll_cv"]))
    elif g.rawOrthosyllCV!=r["orthosyll_cv"]:
      d=("OSYLL",); sig[d]+=1
      if len(sigex[d])<6: sigex[d].append((r["ortho"],tag,g.rawOrthosyllCV,r["orthosyll_cv"]))
tot=sum(v for k,v in res.items() if k!="skipped")
print("(phon,syll,osyll) ok flags:"); 
for k,v in sorted(res.items(),key=str): print(f"{v:7d} {k}")
print("all ok:",res[(True,True,True)],"/",tot)
for d,n in sig.most_common(25): print(n,d,sigex[d])
