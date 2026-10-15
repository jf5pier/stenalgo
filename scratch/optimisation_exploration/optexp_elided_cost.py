import json,re,collections,sys
sys.path.insert(0,'.')
from src.keyboard import Starboard
from util.compare_theories import starboardStrokeCost
b=Starboard.fromJSONFile('starboard3h.json'); cost=starboardStrokeCost(b)
d=json.load(open('plover_stenalgo_dictionary.json'))
t=open('opensubtitles-fr/sample.txt',encoding='utf8').read().lower().replace('’',"'")
c=collections.Counter(re.findall(r"[a-zàâçéèêëîïôûùüÿœ]+'?",t)); N=sum(c.values())
base={"je":"vt@a","de":"pv@a","le":"mt@a","ne":"mR@a","se":"s*@a","me":"m*@a","que":"k@a","te":"t@a","ce":"s@a"}
el={"j'":"vt-","d'":"pv-","l'":"mt-","n'":"mR-","s'":"s-","m'":"m*","qu'":"k-","t'":"t-","c'":None}
pairs=[("je","j'","vt"),("de","d'","pv"),("le","l'","mt"),("ne","n'","mR"),("se","s'","s"),("me","m'","m"),("que","qu'","k"),("te","t'","t"),("ce","c'","s")]
print("star alone",cost("*"),"k@a",cost("k@a"),"k",cost("k-"))
tot={}
print("pair  fB fE  | cur: B E | A: E=B+*  | B: B=bare E=bare+*")
for bw,ew,cs in pairs:
    fb,fe=c[bw],c[ew]
    cb=cost(base[bw]); ce=cost(el[ew]) if el[ew] else None
    bare=cost(cs+"-") if cs[-1] not in "*" else cost(cs)
    bs=base[bw]; Ae=cost(bs.replace("@","*@",1)) if "*" not in bs else None
    Be=cost(cs+"*") 
    print(bw,ew,fb,fe,"|",cb,ce,"|",Ae,"|",bare,Be, d.get(cs+"-"), d.get(cs+"*"), d.get(bs.replace("@","*@",1)))
