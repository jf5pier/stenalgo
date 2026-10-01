"""Tests for util/review_affix_rules.py: scripted answers, a fake proposer, the decisions file saved after every answer."""
import src.affixproposals as P
from src.affixdecisions import APART, FUSED, SINGLE, AnchorDecision, Decisions, ScopeForm, loadDecisions
from util import review_affix_rules as V
from util.build_affix_rules import Pending

GROWTH = Pending("growth", "prefix", "aa", "A", "no growth verdict")
FUSION = Pending("fusion", "suffix", "bb|bc", "B", "parts bb, bc")


def _proposal(kind, label, net=100.0, spellings=None, forms=None, verdict=SINGLE):
    item = GROWTH if kind == "growth" else FUSION
    entry = AnchorDecision(item.position, spellings or item.spellings, item.phono,
                           FUSED if kind == "fusion" else verdict, forms)
    return P.Proposal(kind, item.position, entry.spellings, item.phono, label, 10, 1000.0, 1, 5.0, 0, 0.0, net, entry)


def _run(items, proposals, answers, tmp_path, decisions=None):
    """proposals: a list consumed one per proposer call; answers: consumed by ask(); returns (decisions, say-log)."""
    path = str(tmp_path / "d.json")
    decisions = decisions or Decisions()
    from src.affixdecisions import saveDecisions
    saveDecisions(decisions, path)
    queue, ans, log = list(proposals), list(answers), []

    def proposer(item, dec):
        return queue.pop(0) if queue else None

    out = V.review(items, decisions, proposer, path, ask=lambda _p: ans.pop(0), say=log.append, today="2026-10-01")
    assert not ans, f"unused answers {ans}"
    return out, path, log


def test_accepting_a_growth_stores_the_forms_note_and_numbers_and_offers_an_extension(tmp_path):
    first = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    ext = _proposal("growth", "ma|ti", net=40.0, forms=[ScopeForm("ma|ti")])
    out, path, log = _run([GROWTH], [first, ext, None], ["y", "a note", "n", ""], tmp_path)
    e = loadDecisions(path).get("prefix", "aa", "A")
    assert [f.label for f in e.growth] == ["ma"]                      # the extension was refused, the form kept
    assert e.refused == ["ma|ti"] and e.date == "2026-10-01"
    assert any("helps 10 words" in line for line in log)


def test_refusing_a_growth_never_stores_the_refused_forms(tmp_path):
    p = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    out, path, _ = _run([GROWTH], [p, None], ["n", "", "n"], tmp_path)    # refuse; then "record no growth?" -> no
    e = loadDecisions(path).get("prefix", "aa", "A")
    assert e.growth is None and e.refused == ["ma"]


def test_no_proposal_then_yes_records_no_growth(tmp_path):
    out, path, _ = _run([GROWTH], [None], ["y"], tmp_path)
    e = loadDecisions(path).get("prefix", "aa", "A")
    assert e.growth == [] and e.verdict == SINGLE


def test_fusion_accept_and_refuse(tmp_path):
    acc = _proposal("fusion", "fuse bb|bc", forms=[ScopeForm("x")], spellings="bb|bc")
    out, path, _ = _run([FUSION], [acc], ["y", "ok"], tmp_path)
    assert loadDecisions(path).get("suffix", "bb|bc", "B").verdict == FUSED
    ref = _proposal("fusion", "fuse bb|bc", forms=[], spellings="bb|bc")
    out, path, _ = _run([FUSION], [ref], ["n", "no"], tmp_path)
    e = loadDecisions(path).get("suffix", "bb|bc", "B")
    assert e.verdict == APART and e.growth == [] and e.note == "no"


def test_skip_writes_nothing_and_quit_stops(tmp_path):
    p1 = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    out, path, _ = _run([GROWTH, FUSION], [p1], ["s"], tmp_path)
    assert loadDecisions(path).entries == {}
    p2 = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    out, path, _ = _run([GROWTH, FUSION], [p2], ["q"], tmp_path)
    assert loadDecisions(path).entries == {}


def test_the_file_is_saved_after_every_answer(tmp_path, monkeypatch):
    saved = []
    real = V.saveDecisions
    monkeypatch.setattr(V, "saveDecisions", lambda d, p: (saved.append(len(d.entries)), real(d, p)))
    first = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    _run([GROWTH], [first, None], ["y", ""], tmp_path)
    assert len(saved) >= 1


def test_an_invalid_answer_is_asked_again(tmp_path):
    p = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    out, path, _ = _run([GROWTH], [p], ["x", "", "s"], tmp_path)
    assert loadDecisions(path).entries == {}
