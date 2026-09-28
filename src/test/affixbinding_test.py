"""Tests for src/affixbinding.py."""
from src.affixes import MERGED, PREFIX, SUFFIX, Binding, Candidate, Carrier, SimContext, WordRecord, buildFamily
from src.affixbinding import (
    PhonemeKeys, Option, SubgroupChoice, assignGreedy, familySalience, orphanMembers, simScore,
    subgroupOption)
from src.affixes import FamilyMetrics
from src.keyboard import Starboard


def _sb():
    sb = Starboard.fromJSONFile("starboard3h.json")
    assert sb is not None
    return sb


def _rec(idx, ortho, base):
    return WordRecord(idx=idx, ortho=ortho, lemme=ortho, gramCat="NOM", frequency=10.0,
                      phonoSylls=("x",) * len(base), orthoSylls=("x",) * len(base), base=tuple(base),
                      extra=(), isLemmaForm=True)


class TestSim:
    def test_prefers_natural_bank(self):
        sb = _sb()
        pk = PhonemeKeys(sb)
        w = {"k": 1.0}
        onset = simScore(frozenset({2}), w, pk, PREFIX)   # k onset = key 2
        coda = simScore(frozenset({18}), w, pk, PREFIX)   # k coda = key 18
        assert onset > coda > 0
        assert simScore(frozenset({18}), w, pk, SUFFIX) > simScore(frozenset({2}), w, pk, SUFFIX)


class TestSubgroups:
    def test_shared_core_distinct_discriminators(self):
        sb = _sb()
        pk = PhonemeKeys(sb)
        ctx = SimContext(sb, [])
        members = []
        for i, o in enumerate(["logie", "logique", "logiste"]):
            c = Candidate(SUFFIX, 2, "lOZi", o, stemFreq={"bio": 10.0})
            c.carriers = [Carrier(_rec(10 * i + 1, "bio" + o, [(7,), (8,), (9,)]), 2, 1, "bio")]
            members.append(c)
        fam = buildFamily("S001", members)
        assert len(fam.stemSubgroups) == 3
        opt = subgroupOption(fam, (23,), pk, ctx, [k for k in range(16, 26)], fam.stemSubgroups)
        assert opt is not None
        keys = [s.binding.keys for s in opt.subgroups]
        assert all(23 in k for k in keys)
        discriminators = [tuple(x for x in k if x != 23) for k in keys]
        assert len(set(discriminators)) == 3


class TestOrphanMembers:
    def test_flags_unrelated_rider_not_the_related_members(self):
        # tion/ssion are close in spelling; cier shares almost nothing with either -- it should
        # be the only orphan (the -cier/-ion false-merge pattern).
        tion = Candidate(SUFFIX, 1, "sjo", "tion")
        ssion = Candidate(SUFFIX, 2, "sjo", "ssion")
        cien = Candidate(SUFFIX, 2, "sj5", "cien")
        cier = Candidate(SUFFIX, 1, "kaR", "cier")
        fa = buildFamily("S001", [tion, ssion])
        fb = buildFamily("S002", [cien, cier])
        orphans = orphanMembers(fa, fb)
        assert "cier" in orphans

    def test_no_orphans_when_every_member_has_a_close_partner(self):
        a1 = Candidate(SUFFIX, 1, "sjo", "tion")
        a2 = Candidate(SUFFIX, 1, "sjo", "ssion")
        b1 = Candidate(SUFFIX, 1, "sjo", "sion")
        b2 = Candidate(SUFFIX, 1, "sjo", "xion")
        fa = buildFamily("S001", [a1, a2])
        fb = buildFamily("S002", [b1, b2])
        assert orphanMembers(fa, fb) == []


class TestAssign:
    def test_no_two_families_share_position_and_keypress(self):
        sb = _sb()
        ctx = SimContext(sb, [])
        fams, options = [], {}
        for n in range(3):
            c = Candidate(PREFIX, 1, "x", f"a{n}")
            c.carriers = [Carrier(_rec(n + 1, f"a{n}bc", [(2,), (3,), (7,)]), 0, 1, "bc")]
            f = buildFamily(f"P00{n}", [c])
            fams.append(f)
            opts = []
            for keys in ((5,), (5,), (6,)):   # every family prefers key 5, then 6
                o = Option([SubgroupChoice([0], Binding(PREFIX, MERGED, keys), 0.9)],
                           FamilyMetrics(strokeFreqSaved=10.0 - n), 0.9, 0.0, [])
                opts.append(o)
            options[f.familyId] = opts[:1] + [opts[2]] if n else opts[:1] + [opts[2]]
        assigned, _unbound = assignGreedy(fams, options, ctx)
        sigs = [sig for a in assigned for sig in a.option.signature()]
        assert len(sigs) == len(set(sigs))
