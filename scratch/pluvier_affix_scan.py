"""
Pluvier/TAO prefix-suffix shortcut scan (TODO.md, "Pluvier-style TAO prefix/suffix shortcut scan").

MEASUREMENT ONLY -- nothing here is wired into the theory.

For each TAO rule that emits a whole prefix/suffix from one special keystroke (rule list from
https://github.com/Vermoot/Pluvier/blob/main/TAO_rules.md, transcribed in RULES below), measure
the payoff in OUR lexicon under the current Plover dictionary strokes (disambiguated theory,
first stroke sequence of each Word).

Model: stroke i of a Word is its i-th orthographic syllable (`orthosyllCV`); strokes beyond the
syllable count are trailing marks (plural/conjugation suffix strokes) and are never touched. A
shortcut replaces the syllable strokes the affix spans by ONE stroke, assumed conflict-free.
  strict gain = (syllables fully inside the affix's letter span) - 1, if >= 2 such syllables
  loose gain  = (syllables overlapping the affix's letter span) - 1  (upper bound: a boundary
                syllable only partly covered is assumed absorbed by the replacement stroke)
A suffix rule also matches when a plural "s" follows the affix (the "s" is then a mark stroke).

Run from the repo root: PYTHONPATH=. env/bin/python scratch/pluvier_affix_scan.py
Output: scratch/pluvier-affix-shortcuts.tsv (descending strict payoff).
"""
import re
from collections import defaultdict

from src.keyboard import Starboard
from util._theoryio import loadDisambiguatedTheory

OUTPUT = "scratch/pluvier-affix-shortcuts.tsv"
FAMILY_OUTPUT = "scratch/pluvier-affix-families.tsv"
V = "[aeiouyàâäéèêëîïôöùûü]"
C = "[^aeiouyàâäéèêëîïôöùûü]"

# (chord, position, [(affix, restRegex-or-None)], lesson, note)
S, P = "suffix", "prefix"
RULES: list[tuple[str, str, list[tuple[str, str | None]], int, str]] = [
    ("AER", S, [("ier", None)], 13, "financier voilier caissier"),
    ("A*ER", S, [("ière", None)], 13, "financière théière"),
    ("A*EM", S, [("ième", None)], 12, "huitième seizième"),
    ("-BLG", S, [("quel", None), ("quelle", None)], 13, "laquelle lequel séquelle"),
    ("-RP", S, [("peur", None)], 13, "trappeur torpeur"),
    ("-RL", S, [("leur", None)], 13, "voleur malheur"),
    ("*N", S, [("on", None)], 14, "Caron melon"),
    ("*S", S, [("ste", None)], 14, "piste poste liste"),
    ("*T", S, [("ette", None)], 17, "words in -ette"),
    ("*EB", S, [("ène", None)], 19, ""),
    ("W*E", S, [("ué", None), ("oué", None)], 19, ""),
    ("W*EL", S, [("uel", None)], 19, ""),
    ("*EL", S, [("el", None)], 21, ""),
    ("*RT/RT", S, [("teur", None)], 21, ""),
    ("*RTS/RTS", S, [("trice", None)], 21, ""),
    ("O*IB", S, [("oine", None)], 22, ""),
    ("AEN", S, [("ien", None)], 22, ""),
    ("A*EN", S, [("ien", None)], 22, "orthographic variant"),
    ("AEB", S, [("ienne", None)], 22, ""),
    ("AOUB", S, [("ouine", None)], 22, ""),
    ("-GZ", S, [("sion", None), ("zon", None), ("zion", None), ("cienne", None), ("tionne", None), ("zionne", None)], 22, "sion/zon/zion/cienne"),
    ("-NS", S, [("ance", None), ("ence", None)], 26, "IPA ɑ̃s"),
    ("-ND", S, [("ande", None)], 26, ""),
    ("-KT", S, [("cte", None)], 26, ""),
    ("-GS", S, [("ssion", None), ("tion", None), ("cial", None), ("tial", None), ("ciel", None), ("tiel", None), ("cien", None)], 29, ""),
    ("-BGS", S, [("cation", None)], 29, "X"),
    ("-FT", S, [("vité", None), ("cité", None)], 31, ""),
    ("-RD", S, [("deur", None)], 31, ""),
    ("-RG", S, [("gueur", None)], 31, ""),
    ("-RN", S, [("neur", None)], 31, ""),
    ("AO*R", S, [("eur", None)], 31, ""),
    ("*IFL", S, [("if", None)], 32, ""),
    ("*IF", S, [("ive", None)], 32, ""),
    ("-PBGS", S, [("ntion", None), ("nction", None)], 33, ""),
    ("*BGS", S, [("ction", None)], 33, ""),
    ("IGZ", S, [("ition", None), ("itionne", None)], 33, ""),
    ("-TS", S, [("tre", None), ("taire", None), ("ture", None)], 33, ""),
    ("A*IR", S, [("aire", None)], 33, ""),
    ("EBS", S, [("éner", None)], 33, ""),
    ("-RGS", S, [("rtion", None), ("ration", None)], 33, ""),
    ("-PLT", S, [("ment", None)], 41, "mɑ̃"),
    ("-FPLT", S, [("vement", None)], 41, ""),
    ("-TD", S, [("tude", None)], 37, ""),
    ("*L", S, [("elle", None)], 38, ""),
    ("-RB", S, [("cis", None), ("ci", None), ("rbe", None), ("rne", None)], 38, ""),
    ("SRAGS", S, [("ciation", None)], 44, ""),
    ("ITD", S, [("ité", None)], 45, ""),
    ("-LT", S, [("ilité", None)], 45, ""),
    ("-BT", S, [("bité", None)], 45, ""),
    ("-BLT", S, [("bilité", None)], 45, ""),
    ("-RL", S, [("ral", None)], 46, "(same chord as -RL leur)"),
    ("-BL", S, [("bal", None), ("ble", None)], 46, ""),
    ("-RBL", S, [("rbal", None), ("rible", None)], 46, ""),
    ("-RT", S, [("rité", None)], 46, ""),
    ("-FRS", S, [("voir", None)], 47, ""),
    ("-GT", S, [("th", None)], 48, ""),
    ("LO*EG", S, [("logue", None)], 49, ""),
    ("LO*IG", S, [("logie", None)], 49, ""),
    ("LO*IS", S, [("logiste", None)], 49, ""),
    ("LO*IK", S, [("logique", None)], 49, ""),
    ("-LGS", S, [("lation", None)], 49, ""),
    ("-LZ", S, [("ille", None), ("lise", None)], 50, "ille / lise"),
    ("-RLZ", S, [("reille", None), ("ralise", None)], 50, "reille / ralise"),
    ("-BLZ", S, [("bilise", None)], 56, ""),
    ("-NL", S, [("nal", None)], 51, ""),
    ("O*EX", S, [("aux", None)], 51, "plurals in aux"),
    ("ST*E", S, [("sité", None)], 51, ""),
    ("-PGS", S, [("ption", None)], 52, ""),
    ("EG", S, [("igé", None)], 56, ""),
    ("*EG", S, [("iger", None)], 56, ""),
    ("-SZ", S, [("ce", None)], 58, "homonym distinguisher"),
    ("-FK", S, [("sque", None)], 60, ""),
    ("HO*N", S, [("gnon", None)], 60, ""),
    ("-FL", S, [("val", None), ("vail", None), ("vel", None)], 40, ""),
    ("-FR", S, [("fre", None), ("vre", None)], 43, ""),
    ("-FRB", S, [("fer", None), ("vaire", None), ("erve", None)], 43, ""),
    # Prefixes
    ("KOEN", P, [("con", None)], 26, ""),
    ("KOENS", P, [("cons", None)], 39, ""),
    ("STPH-", P, [("conn", None), ("ins", f"^{V}"), ("ens", f"^{V}")], 39, "conn / ins,ens + vowel"),
    ("STK", P, [("dés", f"^{V}"), ("déc", f"^{V}")], 27, "followed by a vowel"),
    ("DAOEZ", P, [("dés", f"^{C}")], 47, "not followed by a vowel"),
    ("STK-", P, [("dé", None)], 56, ""),
    ("K*", P, [("com", None)], 28, ""),
    ("KM-", P, [("comm", None)], 28, ""),
    ("SPW", P, [("ent", None), ("int", None), ("end", None), ("ind", None)], 30, ""),
    ("SP-R", P, [("super", None)], 30, ""),
    ("MULT", P, [("multi", None)], 30, ""),
    ("INTS", P, [("inter", None)], 30, ""),
    ("TRANS", P, [("trans", None)], 43, ""),
    ("AIBGS", P, [("ex", None)], 54, ""),
    ("-BGS", P, [("ex", f"^{C}")], 54, "ex + consonant (chord shared with the cation suffix)"),
    ("KP-", P, [("exce", None), ("exci", None)], 54, ""),
    ("KPW-", P, [(a, None) for a in ("amp", "amb", "emp", "emb", "imp", "imb", "omp", "omb", "ump", "umb")], 57, "vowel + mp/mb"),
    ("TPH-", P, [("in", f"^{V}")], 59, "in + vowel"),
    ("WH-", P, [("fin", None), ("fen", None)], 51, ""),
    ("TH-", P, [("ten", None), ("tén", None)], 53, ""),
    ("VH-", P, [("ven", None), ("vén", None)], 53, ""),
    ("KR-/KL-", P, [("corr", None), ("coll", None)], 40, "co + rr/ll"),
    ("R-", P, [("re", None)], 13, "re- prefix"),
]


# Family of each affix, by (position, affix). Anything unlisted falls into "<position> other".
FAMILIES: dict[str, list[str]] = {
    "suffix -ité (ité rité ilité bilité bité vité cité sité)": ["ité", "rité", "ilité", "bilité", "bité", "vité", "cité", "sité"],
    "suffix -tion (tion ssion sion ration cation lation ciation ction ntion ition ption rtion ...)": [
        "tion", "ssion", "sion", "zion", "zon", "cien", "cial", "tial", "ciel", "tiel", "cienne", "tionne", "zionne",
        "ration", "rtion", "cation", "lation", "ciation", "ction", "nction", "ntion", "ition", "itionne", "ption"],
    "suffix -logie (logie logique logiste logue)": ["logie", "logique", "logiste", "logue"],
    "suffix -ment (ment vement)": ["ment", "vement"],
    "suffix -ier/-ien (ier ière ien ienne ième)": ["ier", "ière", "ien", "ienne", "ième"],
    "suffix -eur (teur trice deur gueur neur eur peur leur)": ["teur", "trice", "deur", "gueur", "neur", "eur", "peur", "leur"],
    "suffix verb -ise/-iger (lise bilise ralise igé iger éner)": ["lise", "bilise", "ralise", "igé", "iger", "éner"],
    "suffix -al/-el/-ble (ral bal ble rbal rible nal val vail vel el elle uel ette)": [
        "ral", "bal", "ble", "rbal", "rible", "nal", "val", "vail", "vel", "el", "elle", "uel", "ette"],
    "suffix -if/-ive": ["if", "ive"],
    "suffix -ance/-ande/-cte": ["ance", "ence", "ande", "cte"],
    "suffix consonant clusters (tre taire ture fre vre fer vaire erve ste sque ce th ille reille gnon cis ci rbe rne)": [
        "tre", "taire", "ture", "fre", "vre", "fer", "vaire", "erve", "ste", "sque", "ce", "th", "ille", "reille",
        "gnon", "cis", "ci", "rbe", "rne"],
    "suffix vowel/glide endings (on ène aire aux tude oine ouine ué oué quel)": [
        "on", "ène", "aire", "aux", "tude", "oine", "ouine", "ué", "oué", "quel", "quelle"],
    "prefix con-/com- (con cons conn com comm coll corr)": ["con", "cons", "conn", "com", "comm", "coll", "corr"],
    "prefix dé- (dé dés déc)": ["dé", "dés", "déc"],
    "prefix vowel+m+b/p (amp amb emp emb imp imb omp omb ump umb)": [
        "amp", "amb", "emp", "emb", "imp", "imb", "omp", "omb", "ump", "umb"],
    "prefix nasal+consonant (ent end int ind in ins ens)": ["ent", "end", "int", "ind", "in", "ins", "ens"],
    "prefix consonant+en (fin fen ten tén ven vén)": ["fin", "fen", "ten", "tén", "ven", "vén"],
    "prefix ex- (ex exce exci)": ["ex", "exce", "exci"],
    "prefix Latin (inter super multi trans re)": ["inter", "super", "multi", "trans", "re"],
}
FAMILY_OF: dict[tuple[str, str], str] = {}
for _fam, _affixes in FAMILIES.items():
    for _a in _affixes:
        FAMILY_OF[(_fam.split()[0], _a)] = _fam


def spans(letterGroups: list[list[str]], ortho: str) -> list[tuple[int, int]] | None:
    out, pos = [], 0
    for grp in letterGroups:
        n = sum(len(x) for x in grp)
        out.append((pos, pos + n))
        pos += n
    return out if pos == len(ortho) and "".join("".join(g) for g in letterGroups) == ortho else None


def main() -> None:
    starboard = Starboard.fromJSONFile("starboard3h.json")
    assert starboard is not None
    theory = loadDisambiguatedTheory(starboard)

    words = []  # (ortho, freq, nStrokes, syllable spans, nSyll)
    skipped = 0
    for w, strokesList in theory.items():
        sp = spans(w.orthosyllCV, w.ortho)
        if sp is None:
            skipped += 1
            continue
        words.append((w.ortho, w.frequency, len(strokesList[0]), sp))
    print(f"{len(words)} words scanned, {skipped} skipped (ortho/syllable letter mismatch)")

    def gains(ortho: str, sp: list[tuple[int, int]], a: int, b: int) -> tuple[int, int]:
        full = sum(1 for s, e in sp if s >= a and e <= b)
        over = sum(1 for s, e in sp if s < b and e > a)
        return (full - 1 if full >= 2 else 0), (over - 1 if over >= 2 else 0)

    rows = []
    famWords: dict[str, dict[int, tuple[float, int, int]]] = defaultdict(dict)  # word index -> (freq, gs, gl)
    famMembers: dict[str, list[tuple[float, str]]] = defaultdict(list)
    for chord, pos, affixes, lesson, note in RULES:
        for affix, rest in affixes:
            nMatch = freqMatch = 0
            nStrict = nLoose = 0
            fStrict = fLoose = 0.0
            sStrict = sLoose = 0.0
            examples: list[tuple[float, str]] = []
            # aggregate by ortho so a word with several grammatical entries counts once per entry
            fam = FAMILY_OF.get((pos, affix), pos + " other")
            for wi, (ortho, freq, nStrokes, sp) in enumerate(words):
                if ortho == affix:
                    continue
                spanSp, end = sp, len(ortho)
                if pos == P:
                    if not ortho.startswith(affix):
                        continue
                    a, b = 0, len(affix)
                    if rest and not re.match(rest, ortho[b:]):
                        continue
                else:
                    tail = ortho
                    if ortho.endswith(affix):
                        a, b = len(ortho) - len(affix), len(ortho)
                    elif ortho.endswith(affix + "s") and not affix.endswith("s"):
                        a, b = len(ortho) - len(affix) - 1, len(ortho) - 1
                        # the plural "s" is a mark stroke, not part of the last syllable
                        spanSp = sp[:-1] + [(sp[-1][0], sp[-1][1] - 1)]
                    else:
                        continue
                    if rest and not re.search(rest, tail):
                        continue
                nMatch += 1
                freqMatch += freq
                gs, gl = gains(ortho, spanSp, a, b)
                old = famWords[fam].get(wi, (freq, 0, 0))
                famWords[fam][wi] = (freq, max(gs, old[1]), max(gl, old[2]))
                if gs > 0:
                    nStrict += 1
                    fStrict += freq
                    sStrict += freq * gs
                    examples.append((freq, ortho))
                if gl > 0:
                    nLoose += 1
                    fLoose += freq
                    sLoose += freq * gl
            examples.sort(reverse=True)
            famMembers[fam].append((fStrict, f"{chord} {affix}"))
            rows.append((chord, pos, affix + (f" (rest {rest})" if rest else ""), lesson, note,
                         nMatch, freqMatch, nStrict, fStrict, sStrict, nLoose, fLoose, sLoose,
                         " ".join(o for _, o in examples[:6])))

    rows.sort(key=lambda r: (-r[8], -r[11]))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("rank\tchord\tposition\taffix\tlesson\tnote\tmatched_words\tmatched_freq\t"
                "strict_words\tstrict_freq\tstrict_freq_x_strokes_saved\t"
                "loose_words\tloose_freq\tloose_freq_x_strokes_saved\ttop_strict_examples\n")
        for i, r in enumerate(rows, 1):
            f.write(f"{i}\t{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\t{r[5]}\t{r[6]:.1f}\t{r[7]}\t{r[8]:.1f}\t"
                    f"{r[9]:.1f}\t{r[10]}\t{r[11]:.1f}\t{r[12]:.1f}\t{r[13]}\n")
    famRows = []
    for fam, d in famWords.items():
        strict = [(f, g) for f, g, _ in d.values() if g > 0]
        loose = [(f, g) for f, _, g in d.values() if g > 0]
        members = sorted(famMembers[fam], reverse=True)
        famRows.append((fam, len(strict), sum(f for f, _ in strict), sum(f * g for f, g in strict),
                        len(loose), sum(f for f, _ in loose), sum(f * g for f, g in loose),
                        " ".join(m for _, m in members)))
    famRows.sort(key=lambda r: (-r[2], -r[5]))
    with open(FAMILY_OUTPUT, "w", encoding="utf-8") as f:
        f.write("rank\tfamily\tstrict_words\tstrict_freq\tstrict_freq_x_strokes_saved\t"
                "loose_words\tloose_freq\tloose_freq_x_strokes_saved\tmembers (chord affix) by strict freq\n")
        for i, r in enumerate(famRows, 1):
            f.write(f"{i}\t{r[0]}\t{r[1]}\t{r[2]:.1f}\t{r[3]:.1f}\t{r[4]}\t{r[5]:.1f}\t{r[6]:.1f}\t{r[7]}\n")
    print(f"wrote {OUTPUT}: {len(rows)} (chord, affix) rows")


if __name__ == "__main__":
    main()
