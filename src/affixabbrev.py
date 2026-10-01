"""Optional affix abbreviations: extra short outlines for words of a STABLE, finished theory.

The theory (base strokes, same-lemma feature strokes, star/hash marks) is complete without them and is never
changed here. Each of the 30 affix rules (`affix_rules.json`, written by `util.affix_scan`) names an anchor and a
keypress; a carrier word gets, in addition to its long outline, a shorter one in which the rule's keys replace the
affix syllable(s) (`src.affixes._newBase`). The long outline stays valid as a fallback for anyone who does not
remember the rules, and the abbreviations ship as a separate, optional dictionary.

Rules of the game:
- one abbreviation per word: the one saving the most strokes (a tie goes to the better-ranked rule);
- an abbreviation is added only if its outline collides with NO outline of the stable theory and with no better
  abbreviation of another spelling: it never needs a mark, so it cannot disturb the theory;
- a growth form that is not allowed falls back to the rule's anchor alone, then to no abbreviation.
"""
import json
from dataclasses import dataclass, field

from src.affixes import (
    Binding, Candidate, Carrier, RULE, SimContext, _newBase, canonicalizeStrokes, withMarks)
from src.affixrules import buildCandidateRule, childrenIndex
from src.keyboard import Strokes

RuleKey = tuple[str, int, str, str]


@dataclass(frozen=True)
class RuleSpec:
    rank: int
    position: str
    ortho: str
    phono: str
    keys: tuple[int, ...]


@dataclass(frozen=True)
class Abbreviation:
    ortho: str
    outline: Strokes          # the short outline (marks of the stable theory kept)
    longOutline: Strokes      # the word's primary outline in the stable theory
    saved: int                # strokes saved
    rank: int                 # rank of the rule in `affix_rules.json`
    anchor: str               # the rule's anchor (spelling)
    k: int                    # 1 = the anchor alone, 2 = a growth form
    frequency: float


@dataclass
class AbbreviationStats:
    carriers: int = 0
    abbreviated: int = 0
    noOption: int = 0            # every form fails (no merge, no gain, or collides with the stable theory)
    outranked: int = 0           # lost the shared outline to a more frequent spelling
    byRank: dict[int, int] = field(default_factory=dict)   # rank -> abbreviations in the dictionary


def loadRuleSpecs(path: str = "affix_rules.json") -> list[RuleSpec]:
    with open(path, encoding="utf-8") as f:
        return [RuleSpec(int(r["rank"]), r["position"], r["ortho"], r["phono"], tuple(r["keys"])) for r in json.load(f)]


def _options(forms: list[Candidate], root: Candidate) -> dict[int, list[Carrier]]:
    """idx -> the carriers a word may use under this rule, best form first: the growth form (span 2) if the
    word is in one, then the anchor alone."""
    options: dict[int, list[Carrier]] = {}
    for c in root.carriers:
        options[c.rec.idx] = [c]
    for fi, form in enumerate(forms[1:], 1):
        for c in form.carriers:
            options.setdefault(c.rec.idx, []).insert(0, c._replace(member=fi))
    return options


def buildAbbreviations(
    rules: list[RuleSpec], pool: dict[RuleKey, Candidate], ctx: SimContext, takenOutlines: set[Strokes],
    longOutline: dict[int, Strokes],
) -> tuple[list[Abbreviation], AbbreviationStats]:
    """`pool`: `affixes.buildCandidates` over the stable theory's records; `takenOutlines`: every canonical outline
    of the stable theory (all words, all readings); `longOutline`: rec.idx -> the word's primary final outline."""
    stats = AbbreviationStats()
    idx = childrenIndex(pool)
    chosen: dict[int, Abbreviation] = {}
    seen: set[int] = set()
    for rule in sorted(rules, key=lambda r: r.rank):
        root = pool.get((rule.position, 1, rule.phono, rule.ortho))
        if root is None:
            raise KeyError(f"affix rule {rule.rank} anchor {(rule.position, rule.phono, rule.ortho)} is not in the pool: "
                           "affix_rules.json is stale (rerun util.affix_scan, or the lexicon/layout changed)")
        forms = buildCandidateRule(root, idx).forms
        binding = Binding(rule.position, RULE, rule.keys)
        for wordIdx, options in _options(forms, root).items():
            seen.add(wordIdx)
            best: Abbreviation | None = None
            for carrier in options:
                newBase, _why, mergedSaving = _newBase(binding, carrier, ctx)
                if newBase is None:
                    continue
                saved = carrier.span if mergedSaving else carrier.span - 1
                rec = carrier.rec
                outline = canonicalizeStrokes(withMarks(newBase, rec.markKeys) + rec.extra)
                if saved <= 0 or outline in takenOutlines:
                    continue
                best = Abbreviation(rec.ortho, outline, longOutline[wordIdx], saved, rule.rank, root.ortho,
                                    carrier.span, rec.frequency)
                break               # options are ordered best form first
            if best is None:
                continue
            old = chosen.get(wordIdx)
            if old is None or best.saved > old.saved:
                chosen[wordIdx] = best
    stats.carriers = len(seen)
    stats.noOption = len(seen - chosen.keys())
    # one dictionary entry per outline: the most frequent spelling keeps it
    byOutline: dict[Strokes, list[Abbreviation]] = {}
    for a in chosen.values():
        byOutline.setdefault(a.outline, []).append(a)
    out: list[Abbreviation] = []
    for outline, group in byOutline.items():
        group.sort(key=lambda a: (-a.frequency, a.ortho, a.rank))
        winner = group[0]
        out.append(winner)
        stats.outranked += sum(1 for a in group[1:] if a.ortho != winner.ortho)
    out.sort(key=lambda a: (-a.frequency, a.ortho, a.outline))
    stats.abbreviated = len(out)
    for a in out:
        stats.byRank[a.rank] = stats.byRank.get(a.rank, 0) + 1
    return out, stats


def theoryOutlines(disambiguated: dict) -> set[Strokes]:  # type: ignore[type-arg]
    """Every canonical outline of the stable theory (all words, all readings)."""
    return {canonicalizeStrokes(s) for strokesList in disambiguated.values() for s in strokesList}
