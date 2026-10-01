"""Tests for util/build_affix_rules.py (S9a): per-rule cache, signatures, pending items, store. No pickles of the repo."""
import pytest

import src.affixrules as R
from src.affixdecisions import AnchorDecision, Decisions, ScopeForm
from src.affixes import PREFIX, SUFFIX, Candidate, Carrier, CarrierResult, WordRecord
from util import build_affix_rules as S

_idx = [10000]


def _rec(ortho, freq=100.0, n=3):
    _idx[0] += 1
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=ortho, gramCat="NOM", frequency=freq, phonoSylls=tuple("x" * n),
        orthoSylls=tuple(ortho[i:i + 1] for i in range(n)), base=tuple((_idx[0], 900 + i) for i in range(n)),
        extra=(), isLemmaForm=True)


def _anchor(ortho, phono, n=8, pos=SUFFIX, hasDecision=True):
    ws = [_rec(f"{ortho}{i}") for i in range(n)]
    start = 2 if pos == SUFFIX else 0
    return Candidate(pos, 1, phono, ortho, carriers=[Carrier(w, start, 1, "s") for w in ws], isAnchor=True,
                     hasDecision=hasDecision)


def _pool(*anchors):
    return {R.candidateKey(a): a for a in anchors}


def _decisions(*anchors, verdict="-", **kw):
    return Decisions([AnchorDecision(a.position, a.ortho, a.phono, verdict, **kw) for a in anchors])


@pytest.fixture
def fakeEval(monkeypatch):
    """chooseRuleKeypress without a keyboard: every carrier gains its span; one distinct key per evaluation."""
    calls: list[str] = []

    def fake(rule, pk, ctx, keypresses):
        calls.append(rule.root.ortho)
        rule.exactDone, rule.keys = True, (ord(rule.root.ortho[0]),)
        rule.results = [CarrierResult(c, gain=c.span) for c in R.poolCarriers(rule.forms)]
        rule.score, rule.strokeFreqSaved, *_ = R.ruleScoreFromResults(rule.results, 0, len(rule.forms))
        rule.alternatives = [(rule.score, rule.keys)]

    monkeypatch.setattr(R, "chooseRuleKeypress", fake)
    return calls


def _three():
    return [_anchor("aa", "A"), _anchor("bb", "B", 6), _anchor("cc", "C", 4)]


class TestSignature:
    def _sig(self, anchor, decisions):
        return S.ruleSignature(R.buildCandidateRule(anchor, R.childrenIndex(_pool(anchor))), decisions)

    def test_a_verdict_a_growth_form_or_a_carrier_changes_the_signature(self):
        a = _anchor("aa", "A")
        base = self._sig(a, _decisions(a))
        assert self._sig(a, _decisions(a)) == base
        assert self._sig(a, _decisions(a, growth=[ScopeForm("x")])) != base
        assert self._sig(a, Decisions()) != base                      # undecided
        a.carriers = a.carriers[:-1]
        assert self._sig(a, _decisions(a)) != base                    # a carrier moved

    def test_an_unrelated_rule_keeps_its_signature(self):
        a, b = _anchor("aa", "A"), _anchor("bb", "B")
        before = self._sig(b, _decisions(a, b))
        assert self._sig(b, _decisions(a, b).withEntry(AnchorDecision(a.position, a.ortho, a.phono, "-", [ScopeForm("y")]))) == before


class TestEvaluationCache:
    def test_compact_and_restore_round_trip(self, fakeEval):
        a = _anchor("aa", "A")
        pool = _pool(a)
        rule = R.buildCandidateRule(a, R.childrenIndex(pool))
        R.chooseRuleKeypress(rule, None, None, [])
        rule.results[0].reason, rule.results[0].partners = "x", [1, 2]
        fresh = R.buildCandidateRule(a, R.childrenIndex(pool))
        S.restoreEvaluation(fresh, S.compactEvaluation(rule))
        assert fresh.exactDone and fresh.keys == rule.keys and fresh.score == rule.score
        assert [(r.carrier, r.gain, r.reason, r.partners, r.newBase) for r in fresh.results] == \
               [(r.carrier, r.gain, r.reason, r.partners, r.newBase) for r in rule.results]

    def test_second_run_evaluates_nothing_and_selects_the_same(self, fakeEval):
        anchors = _three()
        pool, dec = _pool(*anchors), _decisions(*anchors)
        first = S.selectAndBind(pool, dec, None, None, [])
        n = len(fakeEval)
        assert n >= 3 and first.evaluatedNow == n
        again = S.selectAndBind(pool, dec, None, None, [], first.evaluations)
        assert len(fakeEval) == n and again.evaluatedNow == 0
        assert [(b.rule.root.ortho, b.keys) for b in again.bound] == [(b.rule.root.ortho, b.keys) for b in first.bound]

    def test_a_changed_verdict_reevaluates_only_that_rule_and_equals_a_full_recompute(self, fakeEval):
        anchors = _three()
        pool, dec = _pool(*anchors), _decisions(*anchors)
        first = S.selectAndBind(pool, dec, None, None, [])
        fakeEval.clear()
        changed = dec.withEntry(AnchorDecision(SUFFIX, "bb", "B", "-", [ScopeForm("never")]))
        partial = S.selectAndBind(pool, changed, None, None, [], first.evaluations)
        assert fakeEval == ["bb"] and partial.evaluatedNow == 1
        fakeEval.clear()
        full = S.selectAndBind(pool, changed, None, None, [])
        assert sorted(fakeEval) == ["aa", "bb", "cc"]
        key = lambda o: [(b.rule.root.ortho, b.rule.score, [r.gain for r in b.rule.results]) for b in o.bound]  # noqa: E731
        assert key(partial) == key(full) and partial.result.curve == full.result.curve


class TestPending:
    def test_undecided_growth_and_fusion_of_a_selected_rule_are_pending(self, fakeEval):
        a, b = _anchor("aa", "A"), _anchor("bb", "B", hasDecision=False)
        merged = Candidate(SUFFIX, 1, "A", "aa|az", isAnchor=True, mergeParts=[R.candidateKey(a)])
        pool = {**_pool(a, b), R.candidateKey(merged): merged}
        decided = Decisions([AnchorDecision(SUFFIX, "aa", "A", "-"), AnchorDecision(SUFFIX, "aa|ab", "A", "fused")])
        out = S.selectAndBind(pool, decided, None, None, [])
        kinds = [(p.kind, p.spellings) for p in out.pending]
        assert ("growth", "bb") in kinds and ("fusion", "aa|az") in kinds
        (fusion,) = [p for p in out.pending if p.kind == "fusion"]
        assert "closest decided merge `aa|ab`" in fusion.detail

    def test_nothing_pending_when_everything_is_decided(self, fakeEval):
        anchors = _three()
        out = S.selectAndBind(_pool(*anchors), _decisions(*anchors), None, None, [])
        assert out.pending == []

    def test_closest_decided_needs_the_same_sound(self):
        d = Decisions([AnchorDecision(SUFFIX, "aa|ab", "A", "fused")])
        assert S.closestDecided(d, SUFFIX, "aa|az", "B") is None
        assert S.closestDecided(d, PREFIX, "aa|az", "A") is None
        assert S.closestDecided(d, SUFFIX, "aa|az", "A") == "aa|ab"


class TestStore:
    def test_store_round_trip_is_atomic_and_unknown_versions_are_ignored(self, tmp_path):
        path = str(tmp_path / "s.pickle")
        assert S.loadStore(path) is None
        S.saveStore(path, {"version": S.STORE_VERSION, "x": 1})
        assert S.loadStore(path)["x"] == 1 and not (tmp_path / "s.pickle.tmp").exists()
        S.saveStore(path, {"version": 99})
        assert S.loadStore(path) is None

    def test_fingerprint_mismatch_warns_never_raises(self):
        w = S.fingerprintWarnings({"a": "1", "b": "2"}, {"a": "1", "b": "3", "c": "4"})
        assert w == ["b changed since the affix selection was made"]

    def test_outputs_are_written_atomically(self, tmp_path):
        S.writeOutputs([{"rank": 1}], "# r\n", str(tmp_path / "r.json"), str(tmp_path / "r.md"))
        assert (tmp_path / "r.json").read_text() == '[\n {\n  "rank": 1\n }\n]'
        assert (tmp_path / "r.md").read_text() == "# r\n" and not list(tmp_path.glob("*.tmp"))
