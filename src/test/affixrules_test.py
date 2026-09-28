"""Tests for src/affixrules.py (Phase 2, DESIGN_2026-09-27-affix-rule-selection.md §4)."""
from src.affixes import RULE, SUFFIX, Candidate, Carrier, CarrierResult, Slot, WordRecord
from src.affixrules import (
    Rule, buildCandidateRule, candidateKey, childrenIndex, descendantsOf, exclusionCountOf,
    proxyScore, ruleScoreFromResults)

_idx = [0]


def rec(ortho, base, lemme=None, freq=10.0):
    _idx[0] += 1
    lemme = lemme or ortho
    return WordRecord(
        idx=_idx[0], ortho=ortho, lemme=lemme, gramCat="NOM", frequency=freq,
        phonoSylls=tuple("x" * len(base)), orthoSylls=tuple(ortho[i:i + 1] for i in range(len(base))),
        base=tuple(base), extra=(), isLemmaForm=(ortho == lemme))


class TestDescendants:
    def test_walks_the_whole_subtree_via_grownFromKey(self):
        root = Candidate(SUFFIX, 2, "li.te", "lité")
        child = Candidate(SUFFIX, 3, "i.li.te", "·ilité", grownFromKey=candidateKey(root))
        grandchild = Candidate(SUFFIX, 4, "a.i.li.te", "·alité", grownFromKey=candidateKey(child))
        unrelated = Candidate(SUFFIX, 2, "x.y", "xy")
        pool = {candidateKey(c): c for c in (root, child, grandchild, unrelated)}
        idx = childrenIndex(pool)
        descs = descendantsOf(root, idx)
        assert {candidateKey(d) for d in descs} == {candidateKey(child), candidateKey(grandchild)}

    def test_a_non_root_node_can_also_be_a_root(self):
        # DESIGN §4.4: "every pool node is a potential root" -- descendantsOf works from any node.
        root = Candidate(SUFFIX, 2, "li.te", "lité")
        child = Candidate(SUFFIX, 3, "i.li.te", "·ilité", grownFromKey=candidateKey(root))
        grandchild = Candidate(SUFFIX, 4, "a.i.li.te", "·alité", grownFromKey=candidateKey(child))
        pool = {candidateKey(c): c for c in (root, child, grandchild)}
        idx = childrenIndex(pool)
        assert [candidateKey(d) for d in descendantsOf(child, idx)] == [candidateKey(grandchild)]


class TestD5LongestFormWins:
    def test_word_matching_two_forms_is_cut_at_the_longest(self):
        # `disponibilité`-style word: a carrier of both the k=2 root and the k=3 grown form.
        w = rec("xxxbilité", [(1,), (2,), (3,), (4,), (5,)])
        rootCarrier = Carrier(w, 3, 2, "xxxb")     # matches the shorter "-ité"-style form
        childCarrier = Carrier(w, 2, 3, "xxx")     # matches the longer "-bilité"-style form
        root = Candidate(SUFFIX, 2, "i.te", "ité", carriers=[rootCarrier])
        child = Candidate(SUFFIX, 3, "bi.i.te", "·bilité", carriers=[childCarrier],
                           grownFromKey=candidateKey(root))
        from src.affixes import poolCarriers
        pooled = poolCarriers([root, child])
        assert len(pooled) == 1
        assert pooled[0].span == 3      # the longer form wins, never a shorter cut mid-form


class TestProxyScoreAndRuleBuilding:
    def _rootAndChild(self):
        carriers = [Carrier(rec(f"w{i}bilité", [(1,), (2,), (3,), (4,)]), 2, 2, f"w{i}b")
                    for i in range(6)]
        root = Candidate(SUFFIX, 2, "li.te", "lité", carriers=carriers)
        childCarriers = [Carrier(c.rec, 1, 3, "stem") for c in carriers]
        child = Candidate(SUFFIX, 3, "i.li.te", "·ilité", carriers=childCarriers,
                           grownFromKey=candidateKey(root))
        return root, child

    def test_adding_a_beneficial_descendant_raises_the_score(self):
        root, child = self._rootAndChild()
        pool = {candidateKey(c): c for c in (root, child)}
        idx = childrenIndex(pool)
        withoutChild = proxyScore(SUFFIX, [root])
        withChild = proxyScore(SUFFIX, [root, child])
        assert withChild > withoutChild

    def test_buildCandidateRule_adds_the_form_and_stops(self):
        root, child = self._rootAndChild()
        pool = {candidateKey(c): c for c in (root, child)}
        idx = childrenIndex(pool)
        rule = buildCandidateRule(root, idx)
        assert child in rule.forms and root in rule.forms
        assert rule.score == proxyScore(SUFFIX, rule.forms)

    def test_exclusion_count_sums_over_all_forms(self):
        a = Candidate(SUFFIX, 2, "a", "a", slots=(Slot("onset", "i", ("m", "s")),))
        b = Candidate(SUFFIX, 3, "b", "b", slots=(Slot("any", "", ("x",)),), grownFromKey=candidateKey(a))
        assert exclusionCountOf([a, b]) == 3


class TestRuleScore:
    def test_word_exceptions_only_count_collision_reasons(self):
        w1 = rec("w1", [(1,), (2,)])
        w2 = rec("w2", [(3,), (4,)])
        w3 = rec("w3", [(5,), (6,)])
        good = CarrierResult(Carrier(w1, 0, 1, "s"), gain=2, reason=None)
        collided = CarrierResult(Carrier(w2, 0, 1, "s"), gain=0, reason="lostDistinction")
        # keyOverlap/illegalChord are physical, not collisions -- must NOT count as exceptions.
        physical = CarrierResult(Carrier(w3, 0, 1, "s"), gain=0, reason="keyOverlap")
        score, benefit, excCount, excFreq, top = ruleScoreFromResults([good, collided, physical], 0, 1)
        assert excCount == 1 and top == ["w2"]
        assert benefit == 2 * w1.frequency
        assert excFreq == w2.frequency

    def test_form_and_exclusion_costs_subtract(self):
        from src.affixrules import EXCLUSION_COST, FORM_COST
        w1 = rec("w1", [(1,), (2,)])
        good = CarrierResult(Carrier(w1, 0, 1, "s"), gain=2, reason=None)
        score, *_ = ruleScoreFromResults([good], exclusionCount=3, numForms=2)
        assert score == 2 * w1.frequency - EXCLUSION_COST * 3 - FORM_COST * 1
