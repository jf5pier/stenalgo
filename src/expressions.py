"""
Composition algebra for expression abbreviation rules — Phase 1 of
PLAN_2026-10-01-abbreviations-algorithm.md (whole-expression briefs and
attach keypresses: "il est", "il y a" -> one stroke; "de la + mot",
"ne + verbe + pas" as constant extra keys merged into a host stroke).

THE REWRITE SEMANTICS (spec; constraint set 3.5.5 of
PLAN_2026-10-01-abbreviations-complexity.md)

Vocabulary: a token is one word-unit in the scratch/build_expr_candidates.py
sense — an elision particle glued to its host ("n'", "l'") is its own unit.
Every token carries its longform Strokes. Rules come in two kinds:

- AttachRule: a contiguous particle expression ("de la", "n'", "pas") plus a
  constant keypress kappa (tuple of key ids, */# variant-selector keys
  included — they compose as ordinary keys). PREFIX rules sit before their
  host, SUFFIX rules after it.
- BriefRule: a contiguous expression replaced by fixed stroke(s) beta
  (usually one; Q8 allows multi-stroke betas).

Composition of a token stream, attach-first (Q1: attach beats brief when both
cover the tokens):

1. ATTACH MATCHING — longest-match-first, left-to-right, over the token
   stream: the longest attach expression starting at each position consumes
   its tokens (an attach rule of either position may match; position only
   decides the merge direction). Consumed tokens never overlap. Expression
   ties break on expression text then position ("prefix" before "suffix"),
   never on declaration order.
   Exception: a prefix rule matching at the very end of the stream (no token
   after it) yields to the suffix rule of the same expression when one exists
   and a token precedes it, so a host can receive it (voir le).
2. BRIEF MATCHING — longest-match-first over the RESIDUAL stream (attach
   tokens are transparent), so "il n'y a pas" = [il, n', y, a, pas] still
   matches the brief ("il", "y", "a") with the "n'" attach sitting INSIDE the
   brief's span. Unmatched residual tokens stay plain words.
3. MERGES — a PREFIX attach merges kappa into the content segment holding
   the first residual token at or after its span's end (its "next" segment:
   the host word, or a brief even when the attach sits inside that brief's
   span — kappa lands on the brief's FIRST stroke); a SUFFIX attach merges
   into the segment holding the last residual token before its span's start
   (the host's or brief's LAST stroke). Same tuple arithmetic as `withMarks`
   / `composeReservedKeyStrokes` (src/ambiguitychecker.py). A single-stroke
   segment (a brief) takes prefix and suffix unions into the one chord.
   Application order is fixed — prefix attaches in stream order, then suffix
   attaches — so the normal form is unique (confluence: every merge is a
   set-union at a fixed stroke index).
   The reserved mark keys (`*` 10 / `#` 15 — the Q2 variant selectors) are
   TRANSPARENT to both merge checks: overlap and chord legality run on the
   syllabic keys only. They are dedicated physical keys outside the syllabic
   banks (the structural-disjointness argument of
   `composeReservedKeyStrokes`), so `SimContext.isLegal` — whose bank costs
   know only syllabic keys — would reject every selector-bearing union; and
   a selector coinciding with a mark already on the host stroke is a
   canonical-collision question for the audit phase, not a felt-chord
   question. (`_newBase` never sees this: affix keypresses exclude the
   reserved keys, and its carriers' base strokes carry none.)
4. FAILURE LADDER per attach (the `_newBase` RULE ladder, src/affixes.py):
   key overlap with the neighbour stroke (`attachKeysOverlap`) or an illegal
   union chord (`SimContext.isLegal`) falls back to a STANDALONE stroke
   sorted(kappa) replacing the particle segment at its position (saving
   span-1); a standalone is itself impossible when the particle spanned one
   stroke (spanOne) or the standalone stroke is an existing single-stroke
   outline (standaloneTrap), and a merge with no neighbour stroke at all
   (noNeighbour, e.g. a trailing particle) never falls back — all three keep
   the particle's longform (EXCEPTION, saving 0, counted against the 5%
   exception gate by the selection phase).

CLUSTER MERGE: consecutive attaches that all ended noNeighbour (no host word
after/before them, e.g. a bare "qu' il") compose with each other: a group of two
or more becomes ONE stroke, the union of the keypresses, when they share no
syllabic key, the union chord is legal and it is not an existing single-stroke
outline (first member STANDALONE / "attachCluster", the others MERGED).

Outline assembly walks the stream in token order; an attach that falls
inside a brief's residual span (standalone or exception strokes only — a
merged one contributes nothing) emits AFTER that brief's strokes, since the
brief has collapsed its whole span to beta. Deterministic either way.

Rule families (Q2) are metadata here: variants of one family ("du / de la /
de l' / des") are separate AttachRules whose keypresses differ only by */#
selector keys, so their composed outlines differ exactly there. A circumfix
(Q3, open) is expressible as its decomposition — a PREFIX and a SUFFIX
attach (of one family or two); whether selection prefers one shared
keypress or a pair is a Phase 2 experiment, not an algebra decision.

Collision-freedom against the 190k live outlines is NOT checked here — it
is the selection/audit phase's hard constraint (`_feasible` pattern); this
module only reports `boundaryRisk` (a multi-stroke brief splittable into
existing outlines, `hasBoundaryRisk`) for the report.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass, field

from src.affixes import PREFIX, SUFFIX, SimContext, hasBoundaryRisk
from src.ambiguitychecker import HASH_KEY, STAR_KEY
from src.elision import elisionAgrees
from src.keyboard import Stroke, Strokes, canonicalizeStrokes
from src.keyconflicts import KeyConflicts

__all__ = [
    "AttachRule", "BriefRule", "Rules", "Token", "Composition", "Segment",
    "Failure", "composeOutline", "composeOutlineTraced", "conflictsOf",
]

MERGED = "merged"          # attach outcome: kappa vanished into the host stroke
STANDALONE = "standalone"  # attach outcome: constant stroke replaces the particle
KEPT = "kept"              # word/brief outcome: outline used as-is
EXCEPTION = "exception"    # attach outcome: longform kept, saving 0 (ladder bottom)

RESERVED_MARK_KEYS = (STAR_KEY, HASH_KEY)  # the */# variant selectors (Q2)


# How many syllabic keys an attach keypress may share with its host stroke
# (the union hides a shared key). 0 = strict: every merge is exactly
# invertible (host = stroke minus keypress), what a decoding Plover
# plugin needs. 1 = the max-1-key overlap study, see
# NOTES_2026-10-03-attach-overlap-and-plover-decoder.md. Deliberately NOT
# src.affixes.ruleKeysOverlap: main's affix layer ships explicit entries and
# decides its own mode (refuse only on a full overlap); the expression layer
# must not inherit that default when the branches merge.
EXPR_MAX_SHARED_KEYS = 0


def attachKeysOverlap(neighbour: Stroke, keys: Stroke,
                      maxShared: int | None = None,
                      conflicts: KeyConflicts | None = None) -> bool:
    """True when `keys` cannot merge into `neighbour`: more than `maxShared`
    keys are shared (default `EXPR_MAX_SHARED_KEYS`). Callers pass syllabic
    keys only; the */# selectors are transparent. With `conflicts`, a key
    also collides with the diagonal partner of a neighbour key (a pinky
    cannot press a diagonal pair: `src/keyconflicts.py`), which makes the
    test legality-aware."""
    limit = EXPR_MAX_SHARED_KEYS if maxShared is None else maxShared
    if conflicts is not None:
        return conflicts.conflictCount(neighbour, keys) > limit
    return len(set(neighbour) & set(keys)) > limit


def conflictsOf(ctx: SimContext) -> KeyConflicts:
    """The key-conflict model of the context's layout (derived once, cached on the context)."""
    cached = getattr(ctx, "_keyConflicts", None)
    if cached is None:
        cached = KeyConflicts.fromStarboard(ctx.starboard)
        ctx._keyConflicts = cached          # type: ignore[attr-defined]
    return cached


def _syllabic(keys: Stroke) -> Stroke:
    """The syllabic-bank keys of a stroke — everything but the reserved mark
    keys, which both merge checks treat as transparent (spec step 3)."""
    return tuple(k for k in keys if k not in RESERVED_MARK_KEYS)


@dataclass(frozen=True)
class AttachRule:
    expression: tuple[str, ...]       # particle word-units, contiguous
    position: str                     # src.affixes.PREFIX or SUFFIX
    keypress: tuple[int, ...]         # kappa; */# selector keys included
    family: str = ""                  # Q2 learnable unit; variants share it
    elision: str = ""                 # "base" | "elided": one chord for the pair, host decides (src/elision.py)

    def __post_init__(self) -> None:
        if not self.expression:
            raise ValueError("attach rule needs a non-empty expression")
        if self.position not in (PREFIX, SUFFIX):
            raise ValueError(f"attach rule position must be {PREFIX!r} or {SUFFIX!r}")
        if not self.keypress:
            raise ValueError("attach rule needs a non-empty keypress")


@dataclass(frozen=True)
class BriefRule:
    expression: tuple[str, ...]
    strokes: Strokes                  # beta; usually one stroke (Q8 allows more)
    family: str = ""

    def __post_init__(self) -> None:
        if not self.expression:
            raise ValueError("brief rule needs a non-empty expression")
        if not self.strokes:
            raise ValueError("brief rule needs at least one stroke")


@dataclass(frozen=True)
class Rules:
    briefs: tuple[BriefRule, ...] = ()
    attaches: tuple[AttachRule, ...] = ()
    # Ordered pairs (first expression, second expression) of adjacent attaches
    # that may NOT both attach: the union of two attach keypresses is
    # commutative, so `ce que` and `que ce` would write the same chord. The
    # second particle of a banned pair is left as a content token (the first
    # attaches onto its longform stroke). See `orderBan` in src/expressionrules.py.
    orderBan: frozenset[tuple[tuple[str, ...], tuple[str, ...]]] = frozenset()

    def __post_init__(self) -> None:
        for rule in self.briefs + self.attaches:
            if not all(isinstance(unit, str) and unit for unit in rule.expression):
                raise ValueError("rule expressions are non-empty word-unit strings")


@dataclass(frozen=True)
class Token:
    unit: str                         # word-unit surface ("n'", "est", "de")
    strokes: Strokes                  # longform outline


@dataclass(frozen=True)
class Failure:
    reason: str                       # "emptyStream" | "tokenWithoutStrokes"
    detail: str = ""


@dataclass(frozen=True)
class Segment:
    """One composed piece of the stream, in order: a word, a brief, or an
    attach particle. `strokes` is its contribution to the final outline
    (empty for a merged attach); `span` is the attach's token range."""
    units: tuple[str, ...]
    kind: str                         # "word" | "brief" | "attach"
    outcome: str                      # MERGED | STANDALONE | KEPT | EXCEPTION
    strokes: Strokes
    reason: str | None = None         # ladder reason for STANDALONE/EXCEPTION
    rule: AttachRule | BriefRule | None = None
    span: tuple[int, int] = (-1, -1)  # attach tokens [start, end)


@dataclass(frozen=True)
class Composition:
    strokes: Strokes | None           # canonical outline; None only on Failure
    segments: tuple[Segment, ...] = field(default_factory=tuple)
    saving: int = 0                   # longform strokes minus final strokes
    exceptions: int = 0               # attach segments that kept their longform
    boundaryRisk: bool = False        # some multi-stroke brief splits into outlines


@dataclass(frozen=True)
class StreamPlan:
    """The segmented stream: ordered entries plus the token-index geometry
    merge targeting needs."""
    entries: tuple[tuple, ...]        # ("attach", rule, span) | ("content", tokens, brief)
    residual: tuple[int, ...]         # sorted indices of non-attach tokens
    contentPosOf: dict[int, int]      # residual token index -> content position


def planStream(rules: Rules, tokens: list[Token]) -> StreamPlan:
    # Step 1: longest-match-first attach consumption.
    table = sorted(((rule.expression, rule) for rule in rules.attaches),
                   key=lambda item: (-len(item[0]), item[0], item[1].position))
    marks: dict[int, tuple[int, AttachRule]] = {}
    i = 0
    lastEnd, lastExpression = -1, ()      # the previous mark, for the order ban
    while i < len(tokens):
        for expression, rule in table:
            end = i + len(expression)
            if end <= len(tokens) and tuple(t.unit for t in tokens[i:end]) == expression:
                if lastEnd == i and (lastExpression, expression) in rules.orderBan:
                    continue
                # a prefix rule with no token after it (a trailing particle) yields to
                # the suffix rule of the same expression, which has a host before it
                if rule.position == PREFIX and end == len(tokens) and i > 0:
                    twin = next((r for e, r in table if e == expression
                                 and r.position == SUFFIX), None)
                    if twin is not None:
                        rule = twin
                marks[i] = (end, rule)
                lastEnd, lastExpression = end, rule.expression
                i = end
                break
        else:
            i += 1
    covered = {k for start, (end, _) in marks.items() for k in range(start, end)}
    residual = tuple(i for i in range(len(tokens)) if i not in covered)

    # Step 2: longest-match-first brief matching over the residual stream.
    briefs = sorted(rules.briefs, key=lambda r: (-len(r.expression), r.expression))
    content: list[tuple[int, list[int], BriefRule | None]] = []  # (first, residual span, brief)
    j = 0
    while j < len(residual):
        matched: BriefRule | None = None
        for brief in briefs:
            n = len(brief.expression)
            if j + n <= len(residual) and \
                    tuple(tokens[k].unit for k in residual[j:j + n]) == brief.expression:
                matched = brief
                break
        n = len(matched.expression) if matched else 1
        content.append((residual[j], list(residual[j:j + n]), matched))
        j += n

    contentPosOf: dict[int, int] = {}
    for position, (_, span, _) in enumerate(content):
        for k in span:
            contentPosOf[k] = position

    # Assembly: attach marks and content runs partition the stream; order by
    # first token index. An attach starting inside a brief's residual span
    # sorts after that brief (its start exceeds the brief's first index).
    # Entry shapes: ("attach", rule, (start, end)) | ("content", tokens, brief).
    ordered: list[tuple[int, str, object, object]] = sorted(
        [(start, "attach", rule, (start, end)) for start, (end, rule) in marks.items()]
        + [(span[0], "content", tuple(tokens[k] for k in span), brief)
           for _, span, brief in content],
        key=lambda entry: entry[0])
    entries = tuple((kind, payload, extra) for _, kind, payload, extra in ordered)
    return StreamPlan(entries, residual, contentPosOf)


def composeOutlineTraced(rules: Rules, tokens: tuple[Token, ...],
                         ctx: SimContext) -> Composition:
    """The full composition (spec in the module docstring): the outline plus
    the per-segment trace Phase 3's simulation feeds on."""
    tokenList = list(tokens)
    if not tokenList or any(not t.strokes for t in tokenList):
        return Composition(None)

    plan = planStream(rules, tokenList)
    conflicts = conflictsOf(ctx)

    # Content-segment outlines: briefs use beta, words their longform.
    outlines = [entry[2].strokes if entry[2] is not None else entry[1][0].strokes
                for entry in plan.entries if entry[0] == "content"]

    # Merge targets by token-index adjacency (spec step 3).
    def mergeTarget(span: tuple[int, int], position: str) -> int | None:
        start, end = span
        if position == PREFIX:
            i = bisect_left(plan.residual, end)
            return plan.contentPosOf.get(plan.residual[i]) if i < len(plan.residual) else None
        i = bisect_left(plan.residual, start) - 1
        return plan.contentPosOf.get(plan.residual[i]) if i >= 0 else None

    # Merges: fixed order — prefix attaches in stream order, then suffix
    # attaches — unions at the first/last stroke of the target content
    # segment; confluence by construction (set-unions at fixed indices).
    results: dict[int, tuple[str, str | None]] = {}  # entry index -> (outcome, reason)
    for position in (PREFIX, SUFFIX):
        for index, (kind, rule, span) in enumerate(plan.entries):
            if kind != "attach" or rule.position != position:
                continue
            particleStrokes = tuple(s for t in tokenList[span[0]:span[1]] for s in t.strokes)
            spanStrokes = len(particleStrokes)
            target = mergeTarget(span, position)
            if target is None:
                results[index] = (EXCEPTION, "noNeighbour")
                continue
            if rule.elision and span[1] < len(tokenList) \
                    and not elisionAgrees(rule.elision, tokenList[span[1]].unit):
                # elision pair: the chord is shared by the base and the elided form and the
                # decoder reads the word written right after the particle (the next token, which
                # may itself be an attach particle: `ce n' est`), so a disagreement cannot merge
                results[index] = (EXCEPTION, "elision")
                continue
            neighbourIndex = 0 if position == PREFIX else len(outlines[target]) - 1
            neighbour = outlines[target][neighbourIndex]
            if attachKeysOverlap(_syllabic(neighbour), _syllabic(rule.keypress),
                                 conflicts=conflicts):
                reason = "keyOverlap"
            else:
                union = tuple(sorted(set(neighbour) | set(rule.keypress)))
                if not ctx.isLegal(_syllabic(union)):
                    reason = "illegalChord"
                else:
                    outlines[target] = (outlines[target][:neighbourIndex] + (union,)
                                        + outlines[target][neighbourIndex + 1:])
                    results[index] = (MERGED, None)
                    continue
            # Ladder: standalone stroke, else the longform stays (exception).
            standalone = tuple(sorted(rule.keypress))
            if spanStrokes < 2:
                results[index] = (EXCEPTION, "spanOne")
            elif standalone in ctx.singleStrokeOutlines:
                results[index] = (EXCEPTION, "standaloneTrap")
            else:
                results[index] = (STANDALONE, reason)

    # Hostless adjacent attaches (qu' + il with nothing after them) compose
    # with each other: a run of consecutive noNeighbour attaches is greedily
    # grouped, a group of two or more becomes ONE stroke, the union of its
    # keypresses, when no syllabic key is shared (attachKeysOverlap), the
    # union chord is legal, and it is not an existing single-stroke outline.
    clusterStroke: dict[int, Stroke] = {}   # entry index -> the group's stroke (its first attach)

    def flushCluster(group: list[int]) -> None:
        if len(group) < 2:
            return
        union = tuple(sorted({k for i in group for k in plan.entries[i][1].keypress}))
        if union in ctx.singleStrokeOutlines:
            return
        clusterStroke[group[0]] = union
        results[group[0]] = (STANDALONE, "attachCluster")
        for i in group[1:]:
            results[i] = (MERGED, "attachCluster")

    group: list[int] = []
    union_: set[int] = set()
    for index, (kind, rule, span) in enumerate(plan.entries):
        if kind == "attach" and results[index] == (EXCEPTION, "noNeighbour"):
            keys = _syllabic(rule.keypress)
            if group and (attachKeysOverlap(tuple(union_), keys, conflicts=conflicts)
                          or not ctx.isLegal(_syllabic(tuple(sorted(union_ | set(rule.keypress)))))):
                flushCluster(group)
                group, union_ = [], set()
            group.append(index)
            union_ |= set(rule.keypress)
        else:
            flushCluster(group)
            group, union_ = [], set()
    flushCluster(group)

    # Final outline + trace, walking the entries in token order.
    final: list[Stroke] = []
    segments: list[Segment] = []
    exceptions = 0
    outlineIter = iter(outlines)
    for index, (kind, payload, extra) in enumerate(plan.entries):
        if kind == "attach":
            rule, span = payload, extra
            outcome, attachReason = results[index]
            units = tuple(t.unit for t in tokenList[span[0]:span[1]])
            keptStrokes = tuple(s for t in tokenList[span[0]:span[1]] for s in t.strokes)
            if outcome == MERGED:
                segments.append(Segment(units, "attach", MERGED, (), None, rule,
                                        (span[0], span[1])))
            elif outcome == STANDALONE:
                stroke = clusterStroke.get(index) or tuple(sorted(rule.keypress))
                final.append(stroke)
                segments.append(Segment(units, "attach", STANDALONE,
                                        (stroke,), attachReason, rule,
                                        (span[0], span[1])))
            else:
                final.extend(keptStrokes)
                exceptions += 1
                segments.append(Segment(units, "attach", EXCEPTION,
                                        keptStrokes, attachReason, rule,
                                        (span[0], span[1])))
        else:
            segTokens, brief = payload, extra
            strokes = next(outlineIter)
            final.extend(strokes)
            if brief is not None:
                segments.append(Segment(tuple(t.unit for t in segTokens), "brief",
                                        KEPT, strokes, None, brief))
            else:
                segments.append(Segment((segTokens[0].unit,), "word",
                                        KEPT, strokes, None, None))

    longformStrokes = sum(len(t.strokes) for t in tokenList)
    outline = tuple(final)
    boundaryRisk = any(hasBoundaryRisk(seg.strokes, ctx.finalOutlines)
                       for seg in segments
                       if seg.kind == "brief" and len(seg.strokes) > 1)
    return Composition(canonicalizeStrokes(outline), tuple(segments),
                       longformStrokes - len(outline), exceptions, boundaryRisk)


def composeOutline(rules: Rules, tokens: tuple[Token, ...], ctx: SimContext) -> Strokes | Failure:
    """The plan's Phase 1 entry point: the canonical composed outline, or a
    Failure when the stream cannot compose at all (empty stream, token
    without strokes). A particle exception is NOT a failure — it keeps the
    longform (gain 0)."""
    composition = composeOutlineTraced(rules, tokens, ctx)
    if composition.strokes is None:
        return Failure("emptyStream" if not tokens else "tokenWithoutStrokes")
    return composition.strokes
