"""Tests for the decisions file (src/affixdecisions.py, affix_decisions.json) and their use in src/affixes.py / affixrules.py."""
import json
import re

import pytest

import src.affixes as A
import src.affixrules as R
from src.affixdecisions import (
    APART, FUSED, SINGLE, AnchorDecision, Decisions, DecisionsError, ScopeForm, loadDecisions, saveDecisions)
from src.affixes import PREFIX, SUFFIX, Candidate, Carrier, CarrierResult, WordRecord

_idx = [5000]


def _word(orthoSylls, phonoSylls, freq=10.0):
    _idx[0] += 1
    ortho = "".join(orthoSylls)
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=ortho, gramCat="NOM", frequency=freq, phonoSylls=tuple(phonoSylls),
        orthoSylls=tuple(orthoSylls), base=tuple((i + 1,) for i in range(len(orthoSylls))), extra=(), isLemmaForm=True)


def _anchor(pos, ortho, phono, carriers):
    return Candidate(pos, 1, phono, ortho, carriers=carriers, isAnchor=True)


def _decisions(pos, ortho, phono, forms):
    return Decisions([AnchorDecision(pos, ortho, phono, FUSED if "|" in ortho else SINGLE, list(forms))])


class TestDecisionsFile:
    def test_the_committed_file_holds_the_thirty_decided_anchors(self):
        d = loadDecisions()
        decided = [e for e in d.entries.values() if e.verdict != APART]
        assert len(decided) == 39                                  # the 30 rules' anchors + the approved fusions
        assert sum(1 for e in d.entries.values() if e.verdict == APART) == 8
        assert d.growthForms(PREFIX, "re|reh", "R°") == []          # no growth
        assert d.growthForms(PREFIX, "nonexistent", "x") is None    # no decision
        assert d.growthForms(SUFFIX, "man|ment", "m@") is None or d.fusionVerdict(SUFFIX, "man|ment", "m@") == APART

    def test_a_fused_merge_without_growth_inherits_its_parts_growth_on_their_own_spellings(self):
        from src.affixdecisions import ScopeForm
        import re
        form = ScopeForm("RE", None, re.compile("RE"), None)
        d = Decisions([
            AnchorDecision(PREFIX, "a", "a", SINGLE, [form]),
            AnchorDecision(PREFIX, "a|ha", "a", FUSED, None),
            AnchorDecision(PREFIX, "b|hb", "b", FUSED, None)])
        (inherited,) = d.growthForms(PREFIX, "a|ha", "a")
        assert inherited.anchors == frozenset({"a"}) and inherited.label == "RE"
        assert d.growthForms(PREFIX, "b|hb", "b") is None       # no part has growth: still undecided

    def test_round_trip_and_atomic_save(self, tmp_path):
        d = loadDecisions()
        path = str(tmp_path / "d.json")
        saveDecisions(d, path)
        again = loadDecisions(path)
        assert again.toJson() == d.toJson()
        assert not (tmp_path / "d.json.tmp").exists()

    def test_validation_errors(self):
        form = ScopeForm("x").toJson()
        good = {"position": SUFFIX, "spellings": "ab", "phono": "a", "verdict": "-", "growth": [form]}
        Decisions.fromJson({"format": 1, "anchors": [good]})
        for bad in ({**good, "growth": [{**form, "sound": "["}]},          # bad regex
                    {**good, "verdict": "fused"},                         # single spelling, merge verdict
                    {**good, "spellings": "a|b"},                          # merge, single verdict
                    {**good, "spellings": "a|b", "verdict": "apart"},      # apart merge with growth
                    {**good, "position": "middle"}):
            with pytest.raises(DecisionsError):
                Decisions.fromJson({"format": 1, "anchors": [bad]})
        with pytest.raises(DecisionsError):                                # duplicate key
            Decisions.fromJson({"format": 1, "anchors": [good, good]})
        with pytest.raises(DecisionsError):
            Decisions.fromJson({"format": 2, "anchors": []})

    def test_a_form_needs_every_condition(self):
        f = ScopeForm("x", anchors=frozenset({"di"}), sound=re.compile("[fs]i"), spelling=re.compile("fi|si"))
        assert f.matches("di", "fi", "fi")
        assert not f.matches("dis", "fi", "fi")       # anchor spelling
        assert not f.matches("di", "fi", "ki")        # sound
        assert not f.matches("di", "ti", "si")        # spelling

    def test_decided_patterns(self):
        d = loadDecisions()
        (en,) = d.growthForms(PREFIX, "am|an|ant|em|en|ench|enh|ham|han|hen", "@")
        assert en.matches("en", "fan", "f@") and en.matches("en", "gran", "gR@")
        assert not en.matches("en", "ta", "ta") and not en.matches("en", "ment", "@")   # needs C{1,2} before @
        assert not en.matches("em", "fan", "f@")                                          # growth stays on `en`
        (ten,) = d.growthForms(SUFFIX, "té", "te")
        assert ten.matches("té", "li", "li") and not ten.matches("té", "bi", "bi") and not ten.matches("té", "vi", "vi")
        liser, sez = d.growthForms(SUFFIX, "ser|sée|zer|zé", "ze")
        assert liser.matches("ser", "ba", "li") and sez.matches("sez", "cu", "ky") and not sez.matches("ser", "cu", "ky")

    def test_fused_forms_stay_on_the_approved_spelling(self):
        d = loadDecisions()
        (tion,) = d.growthForms(SUFFIX, "ccion|cion|cyon|sion|ssion|tion|tions", "sj§")
        assert tion.matches("tion", "ta", "ta") and tion.matches("tions", "ta", "ta")
        assert not tion.matches("ssion", "pa", "pa")          # passion: not on the added spelling
        (der,) = d.growthForms(SUFFIX, "der|dé|dée", "de")
        assert all(der.matches(a, "x", "gaR") for a in ("dez", "der", "dé")) and not der.matches("dée", "x", "gaR")

    def test_verdicts(self):
        d = loadDecisions()
        assert d.fusionVerdict(PREFIX, "am|an|ant|em|en|ench|enh|ham|han|hen", "@") == FUSED
        assert d.fusionVerdict(PREFIX, "re|reh", "R°") == FUSED       # one of the 30, kept fused (grandfathered)
        # a refused fusion, and a merge nobody judged: both behave as apart; only the second is undecided
        assert d.fusionVerdict(SUFFIX, "xx|yy", "z") == APART and not d.isDecidedMerge(SUFFIX, "xx|yy", "z")
        refused = [e for e in d.entries.values() if e.verdict == APART]
        assert refused and all(d.isDecidedMerge(*e.key) for e in refused)


class TestScopedGrowth:
    def test_suffix_form_takes_the_matching_neighbour_and_keeps_a_stem(self):
        form = ScopeForm("li", sound=re.compile("li"))
        decisions = _decisions(SUFFIX, "ser", "ze", [form])
        ws = [_word(("ab", "li", "ser"), ("ab", "li", "ze")), _word(("ab", "ca", "ser"), ("ab", "ka", "ze")),
              _word(("li", "ser"), ("li", "ze"))]          # no stem left once li joins the anchor
        anchor = _anchor(SUFFIX, "ser", "ze", [Carrier(w, len(w.orthoSylls) - 1, 1, "x") for w in ws])
        (child,) = A.growScopedForms(anchor, decisions)
        assert child.isScoped and child.k == 2 and child.ortho == "·[li]ser"
        assert [c.rec.ortho for c in child.carriers] == ["abliser"]
        (c,) = child.carriers
        assert (c.start, c.span) == (1, 2)

    def test_prefix_form_and_first_form_wins(self):
        f1 = ScopeForm("man", spelling=re.compile("man"))
        f2 = ScopeForm("m", sound=re.compile("m.*"))
        decisions = _decisions(PREFIX, "de", "d°", [f1, f2])
        ws = [_word(("de", "man", "der"), ("d°", "m@", "de")), _word(("de", "ma", "ri"), ("d°", "ma", "Ri")),
              _word(("de", "ta", "ri"), ("d°", "ta", "Ri"))]
        anchor = _anchor(PREFIX, "de", "d°", [Carrier(w, 0, 1, "x") for w in ws])
        anchor.isAnchor = True
        kids = A.growScopedForms(anchor, decisions)
        assert [k.ortho for k in kids] == ["de[man]·", "de[m]·"]
        assert [c.rec.ortho for c in kids[0].carriers] == ["demander"]
        assert [c.rec.ortho for c in kids[1].carriers] == ["demari"]      # `demander` is not taken twice

    def test_a_no_growth_anchor_has_no_forms_and_its_rule_is_the_anchor_alone(self):
        decisions = _decisions(SUFFIX, "ter", "te", [])
        ws = [_word((s, "ba", "ter"), (s, "ba", "te")) for s in ("ab", "cd", "ef", "gh", "ij", "kl")]
        anchor = _anchor(SUFFIX, "ter", "te", [Carrier(w, 2, 1, "x") for w in ws])
        anchor.hasDecision = True
        assert A.growScopedForms(anchor, decisions) == []
        rule = R.buildCandidateRule(anchor, R.childrenIndex({R.candidateKey(anchor): anchor}))
        assert rule.forms == [anchor]


class TestFallback:
    def _rule(self):
        w1, w2 = _word(("ab", "li", "ser"), ("ab", "li", "ze")), _word(("cd", "li", "ser"), ("cd", "li", "ze"))
        anchor = _anchor(SUFFIX, "ser", "ze", [Carrier(w, 2, 1, "x") for w in (w1, w2)])
        grown = Candidate(SUFFIX, 2, "li.ze", "·[li]ser", carriers=[Carrier(w, 1, 2, "x") for w in (w1, w2)],
                          isScoped=True, grownFromKey=A._candKey(anchor))
        return R.Rule(SUFFIX, anchor, [anchor, grown]), w1, w2

    def test_a_failed_grown_carrier_reverts_to_the_anchor(self, monkeypatch):
        rule, w1, w2 = self._rule()
        calls = []

        def fakeSim(groups, ctx, boundaryRisk=True):
            (_b, carriers), = groups
            calls.append([c.span for c in carriers])
            return [[CarrierResult(c, gain=0 if c.rec.idx == w1.idx and c.span == 2 else 1) for c in carriers]]

        monkeypatch.setattr(R, "simulate", fakeSim)
        carriers = R.poolCarriers(rule.forms)
        assert sorted(c.span for c in carriers) == [2, 2]
        fixed, n = R.resolveFallbacks(rule, (1,), carriers, None)
        assert n == 1
        assert {c.rec.idx: (c.span, c.member) for c in fixed} == {w1.idx: (1, 0), w2.idx: (2, 1)}
        assert R.ruleExclusions(rule) == 0          # fallbacks are recorded by chooseRuleKeypress
        rule.fallbacks = 1
        assert R.ruleExclusions(rule) == 1

    def test_a_rule_without_scoped_forms_is_not_simulated(self, monkeypatch):
        w = _word(("ab", "ser"), ("ab", "ze"))
        anchor = _anchor(SUFFIX, "ser", "ze", [Carrier(w, 1, 1, "x")])
        rule = R.Rule(SUFFIX, anchor, [anchor])

        def boom(*a, **k):
            raise AssertionError("must not simulate")

        monkeypatch.setattr(R, "simulate", boom)
        carriers = anchor.carriers
        assert R.resolveFallbacks(rule, (1,), carriers, None) == (carriers, 0)
