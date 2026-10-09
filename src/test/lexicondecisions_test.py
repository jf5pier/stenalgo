"""Tests for src/lexicondecisions.py."""
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from src.lexicondecisions import (ACCEPT, PENDING, REJECT, Decision, Decisions, DecisionsError, groupIdFor,
                                  loadDecisions, loadExamplesSidecar, mergeMined, minedDecision, saveDecisions,
                                  writeExamplesSidecar)


def mined(sig: str, slots: int = 5, note: str = "rec: accept", kind: str = "mixte_rule", level: str = "L2") -> Decision:
    return minedDecision(kind, level, sig, slots, 1, ["a:x>y", "b:x>y"], note)


def testGroupIdStable() -> None:
    gid = groupIdFor("mixte_rule", "L1", "j→l @ ll [medial]")
    assert gid == groupIdFor("mixte_rule", "L1", "j→l @ ll [medial]") and len(gid) == 10
    assert gid != groupIdFor("mixte_rule", "L2", "j→l @ ll [medial]")
    assert gid != groupIdFor("mixte_typo", "L1", "j→l @ ll [medial]")
    int(gid, 16)


def testRoundTripAndOrder(tmp_path: Path) -> None:
    p = str(tmp_path / "d.tsv")
    ds = Decisions([mined("zz"), mined("aa"), replace(mined("mm"), verdict=ACCEPT, param="aim:er", date="2026-10-08",
                                                         note="ok\tnote")])
    saveDecisions(ds, p)
    first = Path(p).read_bytes()
    back = loadDecisions(p)
    assert [d.groupId for d in back.all()] == sorted(d.groupId for d in ds.all())
    saveDecisions(back, p)
    assert Path(p).read_bytes() == first                              # deterministic
    mm = back.get(groupIdFor("mixte_rule", "L2", "mm"))
    assert mm is not None and mm.param == "aim:er" and mm.examples == ("a:x>y", "b:x>y") and mm.note == "ok note"
    assert first.decode().startswith("# ")


def testLoadErrors(tmp_path: Path) -> None:
    p = tmp_path / "d.tsv"
    p.write_text("a\tb\n")
    with pytest.raises(DecisionsError):
        loadDecisions(str(p))
    d = mined("x")
    saveDecisions(Decisions([d]), str(p))
    p.write_text(p.read_text().replace("pending", "maybe"))
    with pytest.raises(DecisionsError):
        loadDecisions(str(p))
    with pytest.raises(DecisionsError):
        Decisions([d, d])
    with pytest.raises(DecisionsError):
        replace(d, signature="other").validate()                        # id no longer matches


def testImmutable() -> None:
    ds = Decisions([mined("a")])
    ds2 = ds.withEntry(mined("b"))
    assert len(ds) == 1 and len(ds2) == 2
    with pytest.raises(TypeError):
        ds.entries["x"] = mined("c")  # type: ignore[index]
    assert ds2.pending("mixte_rule") and not ds2.accepted()
    assert ds2.pending("template") == []


def testMergeNeverTouchesVerdicts() -> None:
    decided = replace(mined("a"), verdict=ACCEPT, param="p", date="2026-10-08", note="mine")
    rejected = replace(mined("b"), verdict=REJECT, date="2026-10-08")
    pend = mined("c", note="rec: review (old)")
    userNote = replace(mined("d"), note="my note")
    ds = Decisions([decided, rejected, pend, userNote])
    refreshed = [mined(s, slots=9, note="rec: accept (new)") for s in ("a", "c", "d")]
    refreshed[0] = replace(refreshed[0], verdict=REJECT, param="zzz", date="1999-01-01")
    out = mergeMined(ds, refreshed + [mined("e", slots=2)])
    a = out.get(decided.groupId)
    assert a is not None and (a.verdict, a.param, a.date, a.note, a.slots, a.counter) == (ACCEPT, "p", "2026-10-08", "mine", 9, 1)
    c = out.get(pend.groupId)
    assert c is not None and c.note == "rec: accept (new)" and c.verdict == PENDING and c.slots == 9
    d = out.get(userNote.groupId)
    assert d is not None and d.note == "my note"
    e = out.get(groupIdFor("mixte_rule", "L2", "e"))
    assert e is not None and e.verdict == PENDING and e.slots == 2 and e.date == ""
    b = out.get(rejected.groupId)
    assert b is not None and b.note.endswith(" [stale]") and b.verdict == REJECT       # decided and not found


def testStaleOnceAndCleared() -> None:
    decided = replace(mined("a"), verdict=ACCEPT, note="n")
    first = mergeMined(Decisions([decided]), [])
    twice = mergeMined(first, [])
    got = twice.get(decided.groupId)
    assert got is not None and got.note == "n [stale]"
    back = mergeMined(twice, [mined("a")]).get(decided.groupId)
    assert back is not None and back.note == "n"
    pending = mined("p")
    kept = mergeMined(Decisions([pending]), []).get(pending.groupId)
    assert kept == pending                                              # a pending group is never dropped or flagged


def testMergeDeterministic() -> None:
    ds = Decisions([mined("a")])
    rows = [mined("z"), mined("y"), mined("a", slots=7)]
    one = mergeMined(ds, rows).all()
    two = mergeMined(ds, list(reversed(rows))).all()
    assert one == two


def testSidecar(tmp_path: Path) -> None:
    p = str(tmp_path / "s.json")
    assert loadExamplesSidecar(p) == {}
    data: dict[str, dict[str, Any]] = {"b": {"members": [{"ortho": "x"}], "counters": [], "children": []}, "a": {"members": []}}
    writeExamplesSidecar(p, data)
    assert loadExamplesSidecar(p) == data
    assert Path(p).read_text().index('"a"') < Path(p).read_text().index('"b"')
