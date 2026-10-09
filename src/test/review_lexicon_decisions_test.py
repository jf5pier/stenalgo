"""Tests for util/review_lexicon_decisions.py: scripted answers through the injected input and output."""
from pathlib import Path
from typing import Any

from src.lexicondecisions import (ACCEPT, PENDING, REJECT, Decision, Decisions, groupIdFor, loadDecisions,
                                  loadExamplesSidecar, minedDecision, saveDecisions, writeExamplesSidecar)
from util import review_lexicon_decisions as V


def group(sig: str, slots: int, kind: str = "mixte_rule", level: str = "L1") -> Decision:
    return minedDecision(kind, level, sig, slots, 1, [f"{sig}:a>b"], "rec: accept")


A, B, C = group("aa", 30), group("bb", 20), group("cc", 10, kind="synth_rule")
CHILDREN = [
    {"level": "L2", "signature": "bb | k1", "slots": 12, "counter": 0, "examples": ["u:a>b"],
     "members": [{"ortho": "u", "ours": "a", "ref": "b", "refSource": "wikt", "syllCV": "x", "orthosyllCV": "y"}],
     "counters": [], "children": []},
    {"level": "L2", "signature": "bb | k2", "slots": 8, "counter": 0, "examples": ["v:a>b"], "members": [], "counters": [],
     "children": []},
]
EXAMPLES: dict[str, dict[str, Any]] = {
    B.groupId: {"members": [{"ortho": "m", "ours": "o", "ref": "r", "refSource": "wikt", "syllCV": "s", "orthosyllCV": "t"}],
                "counters": [{"ortho": "c", "ours": "o", "ref": "o", "syllCV": "s", "orthosyllCV": "t"}], "children": CHILDREN}}


class Script:
    def __init__(self, answers: list[str]) -> None:
        self.answers = list(answers)
        self.prompts: list[str] = []
        self.out: list[str] = []

    def ask(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.answers.pop(0)

    def say(self, text: str) -> None:
        self.out.append(text)


def run(tmp_path: Path, answers: list[str], **kw: Any) -> tuple[Decisions, Script, str]:
    path = str(tmp_path / "d.tsv")
    saveDecisions(Decisions([A, B, C]), path)
    s = Script(answers)
    ex = str(tmp_path / "ex.json")
    writeExamplesSidecar(ex, dict(EXAMPLES))
    V.review(loadDecisions(path), path, loadExamplesSidecar(ex), ex, s.ask, s.say, today="2026-10-09", **kw)
    return loadDecisions(path), s, ex


def testYesNoSkipAndOrder(tmp_path: Path) -> None:
    out, s, _ = run(tmp_path, ["y fine", "n", "s"])
    a, b, c = (out.get(g.groupId) for g in (A, B, C))
    assert a is not None and (a.verdict, a.note, a.date) == (ACCEPT, "fine", "2026-10-09")
    assert b is not None and b.verdict == REJECT
    assert c is not None and c.verdict == PENDING
    shown = [line for line in s.out if "mixte_rule" in line or "synth_rule" in line]
    assert "aa" in shown[0] and "bb" in shown[1] and "cc" in shown[2]       # descending slots
    assert any("m  o  r(wikt)  s  t" in line for line in s.out)               # member row display
    assert any("counter-examples" in line for line in s.out)


def testQuitSavesPrevious(tmp_path: Path) -> None:
    out, _, _ = run(tmp_path, ["y", "q"])
    a, b = out.get(A.groupId), out.get(B.groupId)
    assert a is not None and a.verdict == ACCEPT and b is not None and b.verdict == PENDING


def testParam(tmp_path: Path) -> None:
    out, _, _ = run(tmp_path, ["p", "aim:er", "q"])
    a = out.get(A.groupId)
    assert a is not None and a.verdict == ACCEPT and a.param == "aim:er"


def testSplit(tmp_path: Path) -> None:
    # aa: d (no children known: asks again) -> n; bb: d -> children reviewed next (12 then 8): y, n; cc: s
    out, s, ex = run(tmp_path, ["d", "n", "d", "y", "n", "s"])
    b = out.get(B.groupId)
    assert b is not None and b.verdict == REJECT and b.note == "split: L2"
    k1, k2 = (out.get(groupIdFor("mixte_rule", "L2", f"bb | {k}")) for k in ("k1", "k2"))
    assert k1 is not None and k1.verdict == ACCEPT and k1.slots == 12
    assert k2 is not None and k2.verdict == REJECT
    assert any("no finer subgroups" in line for line in s.out)
    assert groupIdFor("mixte_rule", "L2", "bb | k1") in loadExamplesSidecar(ex)


def testFiltersAndList(tmp_path: Path) -> None:
    out, s, _ = run(tmp_path, ["y", "q"], kind="synth_rule")
    c = out.get(C.groupId)
    assert c is not None and c.verdict == ACCEPT and out.get(A.groupId) is not None and out.get(A.groupId).verdict == PENDING  # type: ignore[union-attr]
    path = str(tmp_path / "d.tsv")
    saveDecisions(Decisions([A, B, C]), path)
    lines: list[str] = []
    assert V.main(["--file", path, "--list", "--min-slots", "15", "--examples", str(tmp_path / "none.json")], say=lines.append) == 0
    assert len(lines) == 3 and lines[1].split("\t")[0] == A.groupId and lines[2].split("\t")[0] == B.groupId


def testMainInteractive(tmp_path: Path) -> None:
    path = str(tmp_path / "d.tsv")
    saveDecisions(Decisions([A]), path)
    answers = ["x", "y"]                                                  # an invalid letter is asked again
    assert V.main(["--file", path, "--examples", str(tmp_path / "none.json")], ask=lambda _p: answers.pop(0),
                  say=lambda _t: None) == 0
    got = loadDecisions(path).get(A.groupId)
    assert got is not None and got.verdict == ACCEPT


def testHeterogeneousShown() -> None:
    lines: list[str] = []
    V.show(A, {"members": [], "heterogeneous": True}, lines.append)
    assert any("HETEROGENEOUS" in line for line in lines)
    lines.clear()
    V.show(A, {"members": []}, lines.append)
    assert not any("HETEROGENEOUS" in line for line in lines)
