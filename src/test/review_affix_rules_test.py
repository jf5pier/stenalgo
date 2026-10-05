"""Tests for util/review_affix_rules.py: scripted answers, a fake proposer, the decisions file saved after every answer."""
import src.affixproposals as P
from src.affixdecisions import APART, FUSED, SINGLE, AnchorDecision, Decisions, ScopeForm, loadDecisions
from util import review_affix_rules as V
from util.build_affix_rules import Pending

GROWTH = Pending("growth", "prefix", "aa", "A", "no growth verdict")
FUSION = Pending("fusion", "suffix", "bb|bc", "B", "parts bb, bc")


def _entry(source, position, spellings, phono):
    """The stored decision, which the test expects to exist (`source`: a decisions file path or a Decisions)."""
    found = (loadDecisions(source) if isinstance(source, str) else source).get(position, spellings, phono)
    assert found is not None
    return found


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
    queue, ans = list(proposals), list(answers)
    log: list[str] = []

    def proposer(item, dec):
        return queue.pop(0) if queue else None

    out = V.review(items, decisions, proposer, path, ask=lambda _p: ans.pop(0), say=log.append, today="2026-10-01")
    assert not ans, f"unused answers {ans}"
    return out, path, log


def test_accepting_a_growth_stores_the_forms_note_and_numbers_and_offers_an_extension(tmp_path):
    first = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    ext = _proposal("growth", "ma|ti", net=40.0, forms=[ScopeForm("ma|ti")])
    out, path, log = _run([GROWTH], [first, ext, None], ["y", "a note", "n", ""], tmp_path)
    e = _entry(path, "prefix", "aa", "A")
    assert [f.label for f in e.growth] == ["ma"]                      # the extension was refused, the form kept
    assert e.refused == ["ma|ti"] and e.date == "2026-10-01"
    assert any("helps 10 words" in line for line in log)


def test_refusing_a_growth_never_stores_the_refused_forms(tmp_path):
    p = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    out, path, _ = _run([GROWTH], [p, None], ["n", "", "n"], tmp_path)    # refuse; then "record no growth?" -> no
    e = _entry(path, "prefix", "aa", "A")
    assert e.growth is None and e.refused == ["ma"]


def test_no_proposal_then_yes_records_no_growth(tmp_path):
    out, path, _ = _run([GROWTH], [None], ["y"], tmp_path)
    e = _entry(path, "prefix", "aa", "A")
    assert e.growth == [] and e.verdict == SINGLE


def test_fusion_accept_and_refuse(tmp_path):
    acc = _proposal("fusion", "fuse bb|bc", forms=[ScopeForm("x")], spellings="bb|bc")
    out, path, _ = _run([FUSION], [acc], ["y", "ok"], tmp_path)
    assert _entry(path, "suffix", "bb|bc", "B").verdict == FUSED
    ref = _proposal("fusion", "fuse bb|bc", forms=[], spellings="bb|bc")
    out, path, _ = _run([FUSION], [ref], ["n", "no"], tmp_path)
    e = _entry(path, "suffix", "bb|bc", "B")
    assert e.verdict == APART and e.growth == [] and e.note == "no"


def test_skip_writes_nothing_and_quit_stops(tmp_path):
    p1 = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    out, path, _ = _run([GROWTH, FUSION], [p1], ["s"], tmp_path)
    assert loadDecisions(path).entries == {}
    p2 = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    out, path, _ = _run([GROWTH, FUSION], [p2], ["q"], tmp_path)
    assert loadDecisions(path).entries == {}


def test_the_file_is_saved_after_every_answer(tmp_path, monkeypatch):
    saved: list[int] = []
    real = V.saveDecisions

    def recordingSave(d, p):
        saved.append(len(d.entries))
        real(d, p)

    monkeypatch.setattr(V, "saveDecisions", recordingSave)
    first = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    _run([GROWTH], [first, None], ["y", ""], tmp_path)
    assert len(saved) >= 1


def test_an_invalid_answer_is_asked_again(tmp_path):
    p = _proposal("growth", "ma", forms=[ScopeForm("ma")])
    out, path, _ = _run([GROWTH], [p], ["x", "", "s"], tmp_path)
    assert loadDecisions(path).entries == {}


def _groupProposal():
    p = _proposal("growth", "R[e]", forms=[ScopeForm("R[e]")])
    p.rows = [P.Row("aa + /RE/", 10, 100.0, 10, 200.0), P.Row("aa + /R@/", 5, 50.0, 5, 90.0),
              P.Row("aa + /Re/", 3, 1.0, 3, 1.0, fallbacks=1)]
    p.groups = {"aa + /RE/": ("aa", "RE"), "aa + /R@/": ("aa", "R@"), "aa + /Re/": ("aa", "Re")}
    return p


def test_growth_asks_one_line_per_group_and_saves_only_the_accepted_ones(tmp_path):
    out, path, log = _run([GROWTH], [_groupProposal(), None], ["y", "y", "n", ""], tmp_path)
    e = _entry(path, "prefix", "aa", "A")
    assert e.growth is not None
    assert [f.sound is not None and f.sound.pattern for f in e.growth] == ["R@|RE"]
    assert e.refused == ["aa + /Re/"] and e.numbers["acceptedGroups"] == ["aa + /RE/", "aa + /R@/"]


def test_refused_groups_leave_growth_undecided_and_skip_stops_without_writing(tmp_path):
    out, path, _ = _run([GROWTH], [_groupProposal(), None], ["n", "n", "n", "", "n"], tmp_path)
    e = _entry(path, "prefix", "aa", "A")
    assert e.growth is None and len(e.refused) == 3
    out, path, _ = _run([GROWTH], [_groupProposal()], ["y", "s"], tmp_path)
    assert loadDecisions(path).entries == {}


def test_merged_anchor_spellings_with_the_same_sounds_share_a_form():
    from src.affixes import Candidate
    root = Candidate("prefix", 1, "A", "aa|ab")
    forms = P.formsForGroups(root, [("aa", "RE"), ("ab", "RE"), ("aa", "R@")])
    assert [(sorted(f.anchors or ()), f.sound and f.sound.pattern) for f in forms] == [(["aa"], "R@|RE"), (["ab"], "RE")]
    same = P.formsForGroups(root, [("aa", "RE"), ("ab", "RE")])
    assert len(same) == 1 and sorted(same[0].anchors or ()) == ["aa", "ab"]


def _fusionProposal(accept):
    base = _proposal("fusion", "fuse a|b|c", forms=[], spellings="bb|bc|bd")
    base.rows = [P.Row("bc", 5, 50.0, 5, 50.0), P.Row("bd", 3, 5.0, 3, 5.0)]
    base.groups = {"bc": ("bc", ""), "bd": ("bd", "")}
    base.baseSpellings = ["bb"]
    sub = _proposal("fusion", "fuse bb|bc", forms=[], spellings="bb|bc")
    base.evaluateSubset = lambda accepted: sub if accepted == accept else base
    return base, sub


def test_fusion_asks_one_line_per_added_spelling_and_saves_the_confirmed_sub_merge(tmp_path):
    base, sub = _fusionProposal(["bc"])
    out, path, log = _run([FUSION], [base], ["y", "n", "", "y"], tmp_path)
    d = loadDecisions(path)
    assert _entry(d, "suffix", "bb|bc", "B").verdict == FUSED                    # the chosen sub-merge
    full = _entry(d, "suffix", "bb|bc|bd", "B")
    assert full.verdict == APART and full.refused == ["bd"]                  # the greedy full merge is settled


def test_fusion_sub_merge_declined_writes_nothing_and_none_accepted_keeps_it_apart(tmp_path):
    base, sub = _fusionProposal(["bc"])
    out, path, _ = _run([FUSION], [base], ["y", "n", "", "n"], tmp_path)
    assert loadDecisions(path).entries == {}
    base, sub = _fusionProposal(["bc"])
    out, path, _ = _run([FUSION], [base], ["n", "n", ""], tmp_path)
    e = _entry(path, "suffix", "bb|bc|bd", "B")
    assert e.verdict == APART and e.refused == ["bc", "bd"]
