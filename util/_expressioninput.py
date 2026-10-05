"""
Inputs of the expression abbreviation layer's decoder side, shared by `util/export_expression_data.py` and the
`scratch/` audits (which re-import them): the elision particles and the token -> theory resolution that built the
pool, and `loadExpressionInputs`, which rebuilds the rule set, the pool and the theory indexes from the committed
files (`scratch/expr-rules-final.json`, `scratch/expr-briefs.tsv`, `scratch/expr_candidates.tsv`).
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from src.affixes import SimContext
from src.expressionrules import ExprRule, PoolExpression, orderBan
from src.expressions import BriefRule, Rules, Token
from src.keyboard import Starboard, canonicalizeStrokes
from src.word import Word
from util._theoryio import loadDisambiguatedTheory

REPO = Path(__file__).resolve().parent.parent
CANDIDATES = REPO / "scratch" / "expr_candidates.tsv"
RULES_JSON = REPO / "scratch" / "expr-rules-final.json"
BRIEFS_TSV = REPO / "scratch" / "expr-briefs.tsv"

# Left parts of elision particles: `X'` gluing onto a host word.
PARTICLES = {"l", "c", "d", "n", "s", "j", "m", "t", "qu", "jusqu", "lorsqu",
             "quelqu", "puisqu", "quoiqu", "presqu", "entr"}

# Elision particles whose fragment is not a theory word fall back to these.
FULL_FORMS = {"c": "ce", "j": "je", "qu": "que", "quelqu": "quelque",
              "quoiqu": "quoique", "presqu": "presque", "entr": "entre"}


def pickWord(words: list[Word]) -> Word:
    """Primary Word of an orthography: the most frequent (self-homographs
    keep several strokes under one Word; different-lemma homographs differ)."""
    return max(words, key=lambda w: w.frequency)


def resolveToken(token: str, byOrtho: dict[str, list[Word]]) -> list[tuple[str, Word | None]]:
    """Token -> [(unit display, Word or None)], trying whole token, hyphen
    split, then elision split (fragment, bare, full form -- in that order)."""
    if token in byOrtho:
        return [(token, pickWord(byOrtho[token]))]
    # The lexicons spell the œ ligature "oe" (oeil, oeuvre).
    oe = token.replace("œ", "oe").replace("æ", "ae")
    if oe != token and oe in byOrtho:
        return [(token, pickWord(byOrtho[oe]))]
    if "-" in token:
        out: list[tuple[str, Word | None]] = []
        for part in token.split("-"):
            if not part:
                continue
            out.extend(resolveToken(part, byOrtho))
        return out
    if "'" in token:
        left, _, host = token.partition("'")
        if left in PARTICLES and host:
            particle = None
            for cand in (left + "'", left, FULL_FORMS.get(left)):
                if cand and cand in byOrtho:
                    particle = (cand, pickWord(byOrtho[cand]))
                    break
            resolved: list[tuple[str, Word | None]] = [(left + "'", particle[1] if particle else None)]
            return resolved + resolveToken(host, byOrtho)
        if left in PARTICLES and not host:
            # a BARE fragment unit ("c'", "qu'" — unlike n'/l'/d'/s' these are
            # not theory words): fall back to its full form (ce/que/je...)
            for cand in (left + "'", left, FULL_FORMS.get(left)):
                if cand and cand in byOrtho:
                    return [(token, pickWord(byOrtho[cand]))]
    return [(token, None)]


def resolveTerm(term: str, byOrtho: dict[str, list[Word]]) -> list[tuple[str, Word | None]]:
    """Whole expression -> units: whitespace tokens, then per-token rules."""
    out: list[tuple[str, Word | None]] = []
    for token in term.split():
        out.extend(resolveToken(token, byOrtho))
    return out


def loadExpressionInputs():
    """The committed rule set (`scratch/expr-rules-final.json`, `expr-briefs.tsv`), the pool (`expr_candidates.tsv`)
    and the theory indexes the composer, decoder and exporters need: (SimContext, Rules, pool, outline -> surfaces,
    unit -> longform stroke count)."""
    starboard = Starboard.fromJSONFile("starboard3h.json")
    assert starboard is not None
    theory = loadDisambiguatedTheory(starboard)
    byOrtho: dict = {}
    for w in theory:
        byOrtho.setdefault(w.ortho, []).append(w)
    ctx = SimContext(starboard, [])
    ctx.finalOutlines = {canonicalizeStrokes(s) for alts in theory.values() for s in alts}
    ctx.singleStrokeOutlines = {o[0] for o in ctx.finalOutlines if len(o) == 1}
    pool: list[PoolExpression] = []
    with open(CANDIDATES, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            row = dict(zip(header, line.rstrip("\n").split("\t")))
            units = [p.split("=")[0] for p in row["phonologies"].split(",") if p]
            pairs = [resolveTerm(u, byOrtho) for u in units]
            if any(any(w is None for _, w in p) for p in pairs):
                continue
            tokens = []
            for u, p in zip(units, pairs):
                word = p[0][1]
                assert word is not None
                tokens.append(Token(u, theory[word][0]))
            pool.append(PoolExpression(tuple(units), float(row["freq"]), tuple(tokens)))
    data = json.load(open(RULES_JSON, encoding="utf-8"))
    selected = [ExprRule(kind=r["kind"], units=tuple(r["units"]), position=r["position"],
                         family=r["family"], freq=r["freq"], keys=tuple(r["keys"]) or None,
                         beta=tuple(tuple(s) for s in r["beta"]) or None,
                         elision=r.get("elision", ""), elisionBase=tuple(r.get("elisionBase", ())))
                for r in data["rules"]]
    forced = []
    with open(BRIEFS_TSV, encoding="utf-8") as fh:
        fh.readline()
        for line in fh:
            f = line.rstrip("\n").split("\t")
            forced.append((tuple(f[0].split()), tuple(int(k) for k in f[3].split(","))))
    attachRules = [r for r in selected if r.kind == "attach" and r.keys]
    briefRules = [r for r in selected if r.kind == "brief" and r.beta]
    rules = Rules(attaches=tuple(r.toAttach() for r in attachRules),
                  briefs=tuple(r.toBrief() for r in briefRules)
                  + tuple(BriefRule(u, (s,)) for u, s in forced),
                  orderBan=orderBan(selected, pool))
    words: dict = defaultdict(set)
    unitStrokes: dict = {}
    for w, alts in theory.items():
        for s in alts:
            words[canonicalizeStrokes(s)].add(w.ortho)
        unitStrokes[w.ortho] = max(unitStrokes.get(w.ortho, 0), len(alts[0]))
    return ctx, rules, pool, words, unitStrokes
