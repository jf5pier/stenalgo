"""Tests for the decided growth scopes (src/affixscopes.py) and their use in src/affixes.py / affixrules.py."""
import re

import src.affixes as A
import src.affixrules as R
from src.affixes import PREFIX, SUFFIX, Candidate, Carrier, CarrierResult, WordRecord
from src.affixscopes import APPROVED_FUSIONS, SCOPES, ScopeForm, fusionVerdict, scopeFormsOf

_idx = [5000]


def _word(orthoSylls, phonoSylls, freq=10.0):
    _idx[0] += 1
    ortho = "".join(orthoSylls)
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=ortho, gramCat="NOM", frequency=freq, phonoSylls=tuple(phonoSylls),
        orthoSylls=tuple(orthoSylls), base=tuple((i + 1,) for i in range(len(orthoSylls))), extra=(), isLemmaForm=True)


def _anchor(pos, ortho, phono, carriers):
    return Candidate(pos, 1, phono, ortho, carriers=carriers, isAnchor=True)


class TestScopeTable:
    def test_all_thirty_decided_anchors_are_listed_with_distinct_keys(self):
        assert len(SCOPES) == 30
        assert len(APPROVED_FUSIONS) == 4
        assert not set(SCOPES) & set(APPROVED_FUSIONS)
        assert scopeFormsOf(PREFIX, "re|reh", "R°") == []          # no growth
        assert scopeFormsOf(PREFIX, "nonexistent", "x") is None    # no decision

    def test_a_form_needs_every_condition(self):
        f = ScopeForm("x", anchors=frozenset({"di"}), sound=re.compile("[fs]i"), spelling=re.compile("fi|si"))
        assert f.matches("di", "fi", "fi")
        assert not f.matches("dis", "fi", "fi")       # anchor spelling
        assert not f.matches("di", "fi", "ki")        # sound
        assert not f.matches("di", "ti", "si")        # spelling

    def test_decided_patterns(self):
        (en,) = scopeFormsOf(PREFIX, "en", "@")
        assert en.matches("en", "fan", "f@") and en.matches("en", "gran", "gR@")
        assert not en.matches("en", "ta", "ta") and not en.matches("en", "ment", "@")   # needs C{1,2} before @
        (ten,) = scopeFormsOf(SUFFIX, "té", "te")
        assert ten.matches("té", "li", "li") and not ten.matches("té", "bi", "bi") and not ten.matches("té", "vi", "vi")
        liser, sez = scopeFormsOf(SUFFIX, "ser|sée|zer|zé", "ze")
        assert liser.matches("ser", "ba", "li") and sez.matches("sez", "cu", "ky") and not sez.matches("ser", "cu", "ky")


class TestScopedGrowth:
    def test_suffix_form_takes_the_matching_neighbour_and_keeps_a_stem(self, monkeypatch):
        form = ScopeForm("li", sound=re.compile("li"))
        monkeypatch.setattr("src.affixscopes.SCOPES", {(SUFFIX, "ser", "ze"): [form]})
        ws = [_word(("ab", "li", "ser"), ("ab", "li", "ze")), _word(("ab", "ca", "ser"), ("ab", "ka", "ze")),
              _word(("li", "ser"), ("li", "ze"))]          # no stem left once li joins the anchor
        anchor = _anchor(SUFFIX, "ser", "ze", [Carrier(w, len(w.orthoSylls) - 1, 1, "x") for w in ws])
        (child,) = A.growScopedForms(anchor)
        assert child.isScoped and child.k == 2 and child.ortho == "·[li]ser"
        assert [c.rec.ortho for c in child.carriers] == ["abliser"]
        (c,) = child.carriers
        assert (c.start, c.span) == (1, 2)

    def test_prefix_form_and_first_form_wins(self, monkeypatch):
        f1 = ScopeForm("man", spelling=re.compile("man"))
        f2 = ScopeForm("m", sound=re.compile("m.*"))
        monkeypatch.setattr("src.affixscopes.SCOPES", {(PREFIX, "de", "d°"): [f1, f2]})
        ws = [_word(("de", "man", "der"), ("d°", "m@", "de")), _word(("de", "ma", "ri"), ("d°", "ma", "Ri")),
              _word(("de", "ta", "ri"), ("d°", "ta", "Ri"))]
        anchor = _anchor(PREFIX, "de", "d°", [Carrier(w, 0, 1, "x") for w in ws])
        anchor.isAnchor = True
        kids = A.growScopedForms(anchor)
        assert [k.ortho for k in kids] == ["de[man]·", "de[m]·"]
        assert [c.rec.ortho for c in kids[0].carriers] == ["demander"]
        assert [c.rec.ortho for c in kids[1].carriers] == ["demari"]      # `demander` is not taken twice

    def test_scoped_anchor_skips_the_lattice_and_no_growth_anchor_has_no_children(self, monkeypatch):
        monkeypatch.setattr("src.affixscopes.SCOPES", {(SUFFIX, "ter", "te"): []})
        ws = [_word((s, "ba", "ter"), (s, "ba", "te")) for s in ("ab", "cd", "ef", "gh", "ij", "kl")]
        anchor = _anchor(SUFFIX, "ter", "te", [Carrier(w, 2, 1, "x") for w in ws])
        pool = A.growAffixesLattice({(SUFFIX, 1, "te", "ter"): anchor})
        assert list(pool) == [(SUFFIX, 1, "te", "ter")]


class TestFallback:
    def _rule(self, monkeypatch):
        w1, w2 = _word(("ab", "li", "ser"), ("ab", "li", "ze")), _word(("cd", "li", "ser"), ("cd", "li", "ze"))
        anchor = _anchor(SUFFIX, "ser", "ze", [Carrier(w, 2, 1, "x") for w in (w1, w2)])
        grown = Candidate(SUFFIX, 2, "li.ze", "·[li]ser", carriers=[Carrier(w, 1, 2, "x") for w in (w1, w2)],
                          isScoped=True, grownFromKey=A._candKey(anchor))
        monkeypatch.setattr("src.affixscopes.SCOPES", {(SUFFIX, "ser", "ze"): [ScopeForm("li")]})
        return R.Rule(SUFFIX, anchor, [anchor, grown]), w1, w2

    def test_a_failed_grown_carrier_reverts_to_the_anchor(self, monkeypatch):
        rule, w1, w2 = self._rule(monkeypatch)
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


class TestFusions:
    def test_verdicts(self):
        en = (PREFIX, "am|an|ant|em|en|ench|enh|ham|han|hen", "@")
        assert fusionVerdict(en, [(PREFIX, "en", "@"), (PREFIX, "em", "@")]) == "fused"
        # a merged anchor containing a decided anchor, not approved: its parts stay apart
        assert fusionVerdict((SUFFIX, "man|ment", "m@"), [(SUFFIX, "ment", "m@"), (SUFFIX, "man", "m@")]) == "apart"
        # one of the 30 decided anchors that is itself a merge
        assert fusionVerdict((PREFIX, "re|reh", "R°"), [(PREFIX, "re", "R°")]) == "fused"
        assert fusionVerdict((SUFFIX, "xx|yy", "z"), [(SUFFIX, "xx", "z")]) is None

    def test_fused_forms_stay_on_the_approved_spelling(self):
        (tion,) = scopeFormsOf(SUFFIX, "ccion|cion|cyon|sion|ssion|tion|tions", "sj§")
        assert tion.matches("tion", "ta", "ta") and tion.matches("tions", "ta", "ta")
        assert not tion.matches("ssion", "pa", "pa")          # passion: not on the added spelling
        (der,) = scopeFormsOf(SUFFIX, "der", "de")
        assert all(der.matches(a, "x", "gaR") for a in ("dez", "der", "dé")) and not der.matches("dée", "x", "gaR")
