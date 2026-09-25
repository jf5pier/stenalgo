import gzip

import pytest

from util.ngram_data import (
    WINDOWS,
    _scanShard,
    _initWorker,
    loadLexiconWords,
    parseV2Line,
    parseV3Line,
    scanShards,
    stripPosSuffix,
    windowSums,
)


class TestStripPosSuffix:
    def test_strips_uppercase_tag(self):
        assert stripPosSuffix("beluga_NOUN") == "beluga"

    def test_keeps_word_without_tag(self):
        assert stripPosSuffix("beluga") == "beluga"

    def test_keeps_french_word_containing_underscore(self):
        # "_x" is not an ASCII uppercase tag: nothing is stripped.
        assert stripPosSuffix("sans_x") == "sans_x"

    def test_keeps_tag_with_lowercase(self):
        assert stripPosSuffix("word_noun") == "word_noun"


class TestParseV3Line:
    def test_packed_years(self):
        parsed = parseV3Line("1.183_DET\t1773,1,1 2019,3,3\n")
        assert parsed == ("1.183", [(1773, 1), (2019, 3)])

    def test_strips_pos_and_keeps_accents(self):
        parsed = parseV3Line("béluga_NOUN\t2015,7,5 2016,2,2\n")
        assert parsed == ("béluga", [(2015, 7), (2016, 2)])

    def test_junk_line_returns_none(self):
        assert parseV3Line("no-tabs-here\n") is None

    def test_empty_counts_returns_none(self):
        assert parseV3Line("word_NOUN\t\n") is None


class TestParseV2Line:
    def test_per_year_line(self):
        assert parseV2Line("zieuter\t2008\t24\t16\n") == ("zieuter", [(2008, 24)])

    def test_short_line_returns_none(self):
        assert parseV2Line("zieuter\t2008\n") is None


def testWindowSums():
    entries = [(1989, 5), (1995, 10), (2005, 4), (2012, 7), (2019, 2)]
    assert windowSums(entries) == (28, 10, 4, 9)


def writeShard(path, lines):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.writelines(lines)


class TestScanShards:
    def test_lexicon_match_case_folded_across_shards(self, tmp_path):
        writeShard(tmp_path / "a.gz", [
            "Beluga_NOUN\t2015,10,10 1980,3,3\n",
            "beluga_NOUN\t2016,4,4\n",
            "unrelated_NOUN\t2015,900,900\n",
        ])
        writeShard(tmp_path / "b.gz", [
            "BELUGA_NOUN\t2010,1,1\n",
            "béluga_NOUN\t2012,50,40 1998,6,5\n",
        ])
        counts = scanShards(tmp_path.glob("*.gz"),
                            words={"beluga", "béluga"})
        # All case variants fold into one row; decades split the years.
        assert counts["beluga"] == (18, 0, 0, 15)
        assert counts["béluga"] == (56, 6, 0, 50)
        # Not in the match set: never kept, however frequent.
        assert "unrelated" not in counts

    def test_min_recent_keeps_high_frequency_outsiders_only(self, tmp_path):
        writeShard(tmp_path / "a.gz", [
            "néologisme_NOUN\t2015,9000,1 1990,1,1\n",
            "rare_NOUN\t2015,3,3\n",
        ])
        counts = scanShards(tmp_path.glob("*.gz"), words=set(), minRecent=5000)
        assert "néologisme" in counts
        assert "rare" not in counts

    def test_excluded_words_skipped(self, tmp_path):
        writeShard(tmp_path / "a.gz", ["vetoed_NOUN\t2015,9000,1\n"])
        counts = scanShards(tmp_path.glob("*.gz"), words=set(),
                            excluded={"vetoed"}, minRecent=1)
        assert counts == {}


class TestLoadLexiconWords:
    def test_orthos_and_lemmes_lowercased(self, tmp_path):
        mixte = tmp_path / "LexiqueMixte.tsv"
        mixte.write_text(
            "ortho\tphon\tlemme\n"
            "Boîte\tbwat\tboîte\n"
            "trimbalait\ttR5bal\ttrimballer\n",
            encoding="utf-8")
        assert loadLexiconWords([str(mixte)],
                                reformTsv=str(tmp_path / "absent.tsv")) == {
            "boîte", "trimbalait", "trimballer"}

    def test_reform_spellings_included_even_if_absent_from_lexicons(
            self, tmp_path):
        # S1's rewrites erase the old spelling from LexiqueMixte.tsv; its
        # Ngram evidence must still be collected.
        reform = tmp_path / "reform1990.tsv"
        reform.write_text(
            "# comment\n"
            "oldSpelling\tnewSpelling\tisException\n"
            "événement\tévènement\tFalse\n"
            "fût\tfut\tTrue\n",
            encoding="utf-8")
        words = loadLexiconWords([str(tmp_path / "absent.tsv")],
                                 reformTsv=str(reform))
        assert words == {"événement", "évènement", "fût", "fut"}

    def test_missing_files_skipped(self, tmp_path):
        assert loadLexiconWords([str(tmp_path / "absent.tsv")],
                                reformTsv=str(tmp_path / "absent2.tsv")) == set()


def testInitWorkerGlobalsIsolated(tmp_path):
    # _scanShard driven directly through the worker protocol, as the
    # single-process path of scanShards does.
    writeShard(tmp_path / "a.gz", ["mot_NOUN\t2015,2,1\n"])
    _initWorker({"mot"}, set(), 0)
    assert _scanShard(str(tmp_path / "a.gz")) == {"mot": (2, 0, 0, 2)}


def testWindowsCoverThreeDecades():
    assert [name for name, _f, _l in WINDOWS] == [
        "count1990_1999", "count2000_2009", "count2010_2019"]
