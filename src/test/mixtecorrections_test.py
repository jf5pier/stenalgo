from pathlib import Path

import pytest

from src.lexicondecisions import ACCEPT, PENDING, Decision, Decisions, groupIdFor
from src.mixterules import activeRules, applyRules
from src.mixtecorrections import (COLUMNS, MANUAL_CORRECTIONS_PATH, Correction, MixteCorrectionError, applyMixteCorrections,
                                  formatMixteCorrections, loadAllMixteCorrections, loadMixteCorrections)


def _row(ortho: str, infover: str = "ind:pre:1s;", phon: str = "osija") -> dict[str, str]:
    return {"ortho": ortho, "phon": phon, "lemme": "osiller", "cgram": "VER", "infover": infover, "syll_cv": "o|s_i|j_a",
            "orthosyll_cv": "o|sc_i|ll_a", "freqlivres": "1"}


def _fix(ortho: str = "osille", infover: str = "ind:pre:1s;") -> Correction:
    return Correction(ortho, "osiller", "VER", infover, "", "", "osila", "o|s_i|l_a", "o|sc_i|ll_a", "abc")


def test_apply_match() -> None:
    rows = [_row("a"), _row("osille"), _row("osille", "ind:pre:3s;")]
    out = applyMixteCorrections(rows, [_fix()])
    assert out[1]["phon"] == "osila" and out[1]["syll_cv"] == "o|s_i|l_a" and out[1]["freqlivres"] == "1"
    assert out[0] == rows[0] and out[2] == rows[2]
    assert rows[1]["phon"] == "osija"      # input untouched


def test_unmatched_raises_with_list() -> None:
    with pytest.raises(MixteCorrectionError, match="no output row for .*osille"):
        applyMixteCorrections([_row("a")], [_fix()])


def test_ambiguous_raises() -> None:
    with pytest.raises(MixteCorrectionError, match="2 output rows"):
        applyMixteCorrections([_row("osille"), _row("osille")], [_fix()])


def test_infover_is_matched_as_written() -> None:
    with pytest.raises(MixteCorrectionError):
        applyMixteCorrections([_row("osille", "ind:pre:1s")], [_fix()])


def test_no_op_when_empty() -> None:
    rows = [_row("a"), _row("b")]
    assert applyMixteCorrections(rows, []) == rows


def test_file_roundtrip_and_header_only(tmp_path: object) -> None:
    import pathlib
    path = pathlib.Path(str(tmp_path)) / "c.tsv"
    assert loadMixteCorrections(str(path)) == []                    # absent
    path.write_text(formatMixteCorrections([]), encoding="utf-8")
    assert loadMixteCorrections(str(path)) == []                    # header only
    fixes = [_fix("osille"), _fix("osilles")]
    path.write_text(formatMixteCorrections(fixes[::-1]), encoding="utf-8")
    assert loadMixteCorrections(str(path)) == fixes                 # sorted
    path.write_text(formatMixteCorrections(fixes) + "\t".join(["x"] * 3) + "\n", encoding="utf-8")
    with pytest.raises(MixteCorrectionError):
        loadMixteCorrections(str(path))
    path.write_text("\t".join(COLUMNS) + "\n" + "\t".join(_fix().fields()) + "\n" + "\t".join(_fix().fields()) + "\n",
                    encoding="utf-8")
    with pytest.raises(MixteCorrectionError, match="duplicate"):
        loadMixteCorrections(str(path))


def test_rules_registry_runs_only_accepted() -> None:
    def upper(row: dict[str, str]) -> dict[str, str]:
        return {**row, "phon": row["phon"].upper()}
    gid = groupIdFor("mixte_rule", "L1", "s")
    registry = {gid: upper}
    accepted = Decisions([Decision(gid, "mixte_rule", "L1", "s", ACCEPT)])
    pending = Decisions([Decision(gid, "mixte_rule", "L1", "s", PENDING)])
    assert activeRules(pending, registry) == [] and activeRules(Decisions(), registry) == []
    assert applyRules([_row("a")], activeRules(accepted, registry))[0]["phon"] == "OSIJA"
    assert activeRules(accepted) == []     # the shipped registry is empty


def test_load_all_rejects_a_key_in_two_files(tmp_path: Path) -> None:
    text = formatMixteCorrections([_fix()])
    a, b = tmp_path / "a.tsv", tmp_path / "b.tsv"
    a.write_text(text, encoding="utf-8")
    b.write_text(text, encoding="utf-8")
    assert loadAllMixteCorrections([str(a)]) == [_fix()]
    with pytest.raises(MixteCorrectionError, match="duplicate key"):
        loadAllMixteCorrections([str(a), str(b)])


def test_manual_corrections_file_loads_and_pairs_units() -> None:
    rows = loadMixteCorrections(MANUAL_CORRECTIONS_PATH)
    assert len(rows) == 74  # 30 stray-i + 15 dropped-schwa (rejeter, épousseter) + 29 arguer, décatie and loanword unit rebuilds
    for c in rows:
        assert len(c.syllCV.split("|")) == len(c.orthosyllCV.split("|"))
        assert all(len(a.split("_")) == len(b.split("_")) for a, b in zip(c.syllCV.split("|"), c.orthosyllCV.split("|")))
        assert c.syllCV.replace("_", "").replace("|", "").replace("#", "") == c.phon


def test_tag_corrections_replace_genre_and_number(tmp_path: Path) -> None:
    from src.mixtecorrections import TagCorrection, applyTagCorrections, loadTagCorrections
    path = tmp_path / "tags.tsv"
    path.write_text("ortho\tlemme\tcgram\tinfover\tgenre\tnombre\tnew_genre\tnew_nombre\treason\n"
                    "ioniennes\tionien\tADJ\t\tf\t\tf\tp\twhy\n", encoding="utf-8")
    loaded = loadTagCorrections(str(path))
    assert loaded == [TagCorrection("ioniennes", "ionien", "ADJ", "", "f", "", "f", "p", "why")]
    row = {"ortho": "ioniennes", "lemme": "ionien", "cgram": "ADJ", "infover": "", "genre": "f", "nombre": "", "phon": "x"}
    other = dict(row, ortho="ionienne", nombre="s")
    out = applyTagCorrections([other, row], loaded)
    assert out[1]["nombre"] == "p" and out[1]["phon"] == "x" and out[0] == other and row["nombre"] == ""
    with pytest.raises(MixteCorrectionError, match="no output row"):
        applyTagCorrections([other], loaded)


def test_committed_tag_corrections_load() -> None:
    from src.mixtecorrections import loadTagCorrections
    assert [c.ortho for c in loadTagCorrections()] == ["ioniennes"]


def test_lemma_corrections_replace_the_lemma(tmp_path: Path) -> None:
    from src.mixtecorrections import LemmaCorrection, applyLemmaCorrections, loadLemmaCorrections
    path = tmp_path / "lemmas.tsv"
    path.write_text("ortho\tcgram\tlemme\tnew_lemme\tgenre\tnombre\tinfover\treason\n"
                    "liseré\tVER\tliserer\tlisérer\tm\ts\tpar:pas;\twhy\n", encoding="utf-8")
    loaded = loadLemmaCorrections(str(path))
    assert loaded == [LemmaCorrection("liseré", "VER", "liserer", "lisérer", "m", "s", "par:pas;", "why")]
    row = {"ortho": "liseré", "lemme": "liserer", "cgram": "VER", "infover": "par:pas;", "genre": "m", "nombre": "s", "phon": "x"}
    other = dict(row, lemme="liseré", cgram="NOM", infover="")
    out = applyLemmaCorrections([other, row], loaded)
    assert out[1]["lemme"] == "lisérer" and out[1]["phon"] == "x" and out[0] == other and row["lemme"] == "liserer"
    with pytest.raises(MixteCorrectionError, match="no output row"):
        applyLemmaCorrections([other], loaded)
    with pytest.raises(MixteCorrectionError, match="2 output rows"):
        applyLemmaCorrections([row, dict(row)], loaded)


def test_lemma_corrections_reject_a_no_op_row(tmp_path: Path) -> None:
    from src.mixtecorrections import loadLemmaCorrections
    path = tmp_path / "lemmas.tsv"
    path.write_text("ortho\tcgram\tlemme\tnew_lemme\tgenre\tnombre\tinfover\treason\n"
                    "liseré\tVER\tliserer\tliserer\tm\ts\tpar:pas;\twhy\n", encoding="utf-8")
    with pytest.raises(MixteCorrectionError, match="must differ"):
        loadLemmaCorrections(str(path))


def test_committed_lemma_corrections_match_exactly_one_mixte_row() -> None:
    from src.mixtecorrections import applyLemmaCorrections, loadLemmaCorrections
    corrections = loadLemmaCorrections()
    assert [c.ortho for c in corrections] == ["liseré", "liserée"]
    mixte = Path("resources/LexiqueMixte.tsv")
    if not mixte.exists():
        pytest.skip("no LexiqueMixte.tsv")
    wanted = {c.key for c in corrections}
    rows = []
    for line in mixte.read_text(encoding="utf-8").splitlines()[1:]:
        cells = line.split("\t")
        row = {"ortho": cells[0], "lemme": cells[2], "cgram": cells[3], "genre": cells[5], "nombre": cells[6], "infover": cells[7]}
        if (row["ortho"], row["lemme"], row["cgram"], row["infover"], row["genre"], row["nombre"]) in wanted:
            rows.append(row)
    # Once the file has been rebuilt with the corrections the old keys are gone: accept either state.
    if rows:
        assert [r["lemme"] for r in applyLemmaCorrections(rows, corrections)] == ["lisérer", "lisérer"]
