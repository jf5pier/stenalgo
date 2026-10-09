"""Tests for src/diffsignature.py: the table of docs/specs/lexicon-decisions.md section 7, alignment and grouping."""
import pytest

from src.diffsignature import (L1, L2, L3, L4, LEVELS, AlignmentError, ClassKey, CounterIndex, Edit, RowDiff, anchorEdits, buildRowDiff,
                               dropConventions, editScript, nearestReference, proposeGroups, realEdits, signatureAt)


def sig(ours: str, ref: str, syll: str, orthosyll: str, level: str = L1) -> str | None:
    row = buildRowDiff("w", ours, [ref], syll, orthosyll, "c", "w")
    return None if row is None else signatureAt(row, level)


def testSpecTable() -> None:
    assert sig("osija", "osila", "o|s_i|j_a", "o|sc_i|ll_a") == "j→l @ ll [medial]"
    # criions: the missing j is a silent-unit insertion; grapheme of the 4th unit is `i`
    assert sig("kRij§", "kRijj§", "k_R_ij_#|§", "c_r_i_i|ons") == "∅→j @ i [medial]"
    assert sig("kloni", "klOni", "k_l_o|n_i", "c_l_o|n_i") is None
    assert sig("kloni", "kl2ni", "k_l_o|n_i", "c_l_o|n_i") == "o→2 @ o [medial]"
    # constructed so the units align: d-é | l-ai-e | nt (the second E is the silent-looking 5th unit)
    assert sig("delEE", "deleE", "d_e|l_E_#|E", "d_é|l_ai_e|nt") == "E→e @ ai [medial]"
    assert sig("kRe°Rj§", "kReRj§", "", "") is None


def testEditScriptDeterministic() -> None:
    assert editScript("kRij§", "kRijj§") == [Edit("ins", "", "j", 3)]
    assert editScript("abc", "abc") == []
    assert editScript("abc", "axc") == [Edit("sub", "b", "x", 1)]
    assert editScript("abc", "ac") == [Edit("del", "b", "", 1)]
    assert editScript("ac", "abc") == [Edit("ins", "", "b", 1)]
    assert editScript("a", "ab") == [Edit("ins", "", "b", 1)]
    assert editScript("", "") == []


def testConventionsDropped() -> None:
    assert dropConventions(editScript("kloni", "klOni")) == []
    assert dropConventions(editScript("kRe°Rj§", "kReRj§")) == []
    assert dropConventions(editScript("kReRj§", "kRe°Rj§")) == []
    assert realEdits("kEni", "kOni") == [Edit("sub", "E", "O", 1)]


def testNearestReference() -> None:
    assert nearestReference("abc", ["abd", "abc"]) == "abc"
    assert nearestReference("abc", ["zbc", "abd"]) == "abd"          # tie: lexicographic
    assert nearestReference("klo", ["klx", "klO"]) == "klO"          # a convention beats a real difference
    with pytest.raises(ValueError):
        nearestReference("a", [])


def testAnchoringAndMerge() -> None:
    edits = [Edit("sub", "i", "a", 2), Edit("del", "j", "", 3)]       # both on the unit `ij`: merged
    a = anchorEdits(edits, "kRij§", "k_R_ij_#|§", "c_r_i_i|ons")
    assert len(a) == 1 and a[0].edit == Edit("sub", "ij", "a", 2) and a[0].grapheme == "i" and a[0].position == "medial"
    # initial / final positions; an insertion at index 0 anchors on the first unit
    first = anchorEdits([Edit("sub", "k", "g", 0)], "ka", "k_a", "c_a")
    assert first[0].position == "initial"
    last = anchorEdits([Edit("sub", "a", "e", 1)], "ka", "k_a", "c_a")
    assert last[0].position == "final"
    zero = anchorEdits([Edit("ins", "", "s", 0)], "ka", "k_a", "c_a")
    assert zero[0].unitIndex == 0 and zero[0].edit.ours == ""


def testAlignmentErrors() -> None:
    with pytest.raises(AlignmentError):
        anchorEdits([Edit("sub", "a", "e", 0)], "ka", "k_a_b", "c_a")
    with pytest.raises(AlignmentError):
        anchorEdits([Edit("sub", "a", "e", 1)], "ka", "k_a", "c_a_b")


def mismatch(ortho: str, lemma: str, cls: ClassKey) -> RowDiff:
    row = buildRowDiff(ortho, "osija", ["osila"], "o|s_i|j_a", "o|sc_i|ll_a", cls, lemma)
    assert row is not None
    return row


def matchedIndex(n: int) -> CounterIndex:
    idx = CounterIndex()
    for k in range(n):
        idx.addMatchedRow("fija", "f_i|j_a", "f_i|ll_a", ("other", "ind:pre:3s"), f"fille{k}", f"fille{k}")
    return idx


def testSignatureLevels() -> None:
    row = mismatch("oscille", "osciller", ("p:er", "ind:pre:1s"))
    assert signatureAt(row, L1) == "j→l @ ll [medial]"
    assert signatureAt(row, L2) == "j→l @ ll [medial] | p:er"
    assert signatureAt(row, L3) == "j→l @ ll [medial] | p:er ind:pre:1s"
    assert signatureAt(row, L4) == "j→l @ ll [medial] | p:er ind:pre:1s | osciller"
    assert LEVELS == (L1, L2, L3, L4)
    with pytest.raises(ValueError):
        signatureAt(row, "L5")


def testGroupsAndCounters() -> None:
    rows = [mismatch(f"oscille{k}", f"osciller{k}", ("p:er", f"ind:pre:{k + 1}s")) for k in range(3)]
    rows.append(mismatch("tille", "tiller", ("q:er", "ind:pre:2s")))     # alone in its family: falls to L4 = typo
    groups = proposeGroups(rows, matchedIndex(10))
    byLevel = {g.level: g for g in groups}
    assert set(byLevel) == {L2, L4}
    assert byLevel[L2].slots == 3 and byLevel[L2].counter == 0 and not byLevel[L2].typo
    assert not byLevel[L2].heterogeneous
    assert byLevel[L2].signature == "j→l @ ll [medial] | p:er"
    assert byLevel[L2].rec.startswith("rec: accept")
    assert byLevel[L4].typo and byLevel[L4].slots == 1 and byLevel[L4].counter == 0 and not byLevel[L4].heterogeneous
    assert byLevel[L4].rec == "rec: typo (single row)"
    assert sum(g.slots for g in groups) == len(rows)                   # each row in exactly one group
    assert [c["level"] for c in byLevel[L2].children] == [L3] * 3      # chain L2 -> L3 -> L4
    assert [c["level"] for c in byLevel[L2].children[0]["children"]] == [L4]
    assert len(byLevel[L2].sidecarEntry()["members"]) == 3
    # without counter-examples, the coarsest level qualifies for the three rows of one family and the L1 group (4) is taken
    assert [g.level for g in proposeGroups(rows, CounterIndex())] == [L1]


def testEssayerLikeFamilyCollapsesToOneL2Group() -> None:
    slots = [f"{m}:{t}:{p}{n}" for m in ("ind", "sub") for t in ("pre", "imp") for p in "123" for n in "sp"]
    rows = [mismatch(f"essai{k}", "essayer", ("p:ayer", slot)) for k, slot in enumerate(slots)]
    groups = proposeGroups(rows, matchedIndex(10))
    assert len(groups) == 1
    (g,) = groups
    assert g.level == L2 and g.slots == len(slots) and not g.heterogeneous and g.signature.endswith("| p:ayer")


def testHeterogeneousGroup() -> None:
    # three families, ten matching rows elsewhere: L1 has precision 3/13; no family reaches 3 slots, so the L1 group is
    # proposed as the coarsest level with >= 3 slots, flagged heterogeneous
    rows = [mismatch(f"x{k}", f"y{k}", (f"c{k}", "ind:pre:1s")) for k in range(3)]
    groups = proposeGroups(rows, matchedIndex(10))
    assert len(groups) == 1
    (g,) = groups
    assert g.level == L1 and g.slots == 3 and g.counter == 10 and g.heterogeneous and not g.typo
    assert g.rec.startswith("rec: review (heterogeneous, precision 0.23")
    assert g.sidecarEntry()["heterogeneous"] is True
    assert all(c["level"] == L2 and not c["heterogeneous"] for c in g.children)


def testHomogeneousBeatsHeterogeneous() -> None:
    # five rows of L1; three share a family with no counter-example at L2: they form the homogeneous L2 group and the
    # two others fall to L4 singletons, not into the larger heterogeneous L1 group
    rows = [mismatch(f"a{k}", f"la{k}", ("fam", f"ind:pre:{k + 1}s")) for k in range(3)]
    rows += [mismatch(f"b{k}", f"lb{k}", (f"other{k}", "ind:pre:1s")) for k in range(2)]
    groups = proposeGroups(rows, matchedIndex(10))
    assert sorted((g.level, g.slots) for g in groups) == [(L2, 3), (L4, 1), (L4, 1)]
    assert sum(g.slots for g in groups) == 5


def testL1WhenNoCounters() -> None:
    rows = [mismatch(f"x{k}", f"y{k}", (f"c{k}", "ind:pre:1s")) for k in range(4)]
    (g,) = proposeGroups(rows, matchedIndex(0))
    assert g.level == L1 and g.slots == 4 and g.precision == 1.0 and not g.heterogeneous
    assert g.children and g.children[0]["level"] == L2


def testCounterIndexLevels() -> None:
    idx = CounterIndex()
    idx.addMatchedRow("fija", "f_i|j_a", "f_i|ll_a", ("A", "s1"), "L1x")
    idx.addMatchedRow("fija", "f_i|j_a", "f_i|ll_a", ("A", "s2"), "L2x")
    idx.addMatchedRow("fija", "f_i|j_a", "f_i|ll_a", ("B", "s1"), "L3x")
    idx.addMatchedRow("kRij§", "k_R_ij_#|§", "c_r_i_i|ons", ("A", "s1"), "L1x")
    key = [("ll", "medial", "j")]
    assert idx.count(key, ("A", "s1"), "L1x", L1) == 3
    assert idx.count(key, ("A", "s1"), "L1x", L2) == 2                  # same family: the slot is ignored
    assert idx.count(key, ("A", "s1"), "L1x", L3) == 1                  # same family and slot
    assert idx.count(key, ("A", "s1"), "other", L4) == 0 and idx.count(key, ("A", "s1"), "L1x", L4) == 1
    assert idx.count([("i", "medial", "j")], ("A", "s1"), "L1x", L1) == 1       # j inside the unit `ij`
    assert idx.count([("ll", "medial", "j"), ("f", "initial", "f")], ("A", "s1"), "L1x", L1) == 3
    assert idx.count([("ll", "medial", "j"), ("f", "initial", "f")], ("A", "s1"), "L1x", L2) == 2
    assert idx.count([("ll", "medial", "j"), ("zz", "initial", "f")], ("A", "s1"), "L1x", L1) == 0
    idx.add("ll", "medial", "j", ("A", "s1"), "L1x")
    assert idx.count(key, ("A", "s1"), "L1x", L1) == 4 and len(idx) == 5
