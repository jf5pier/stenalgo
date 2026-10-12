from util.build_reading_shares import (
    buildTable,
    fitLuceWeights,
    labelCandidates,
    newClassCounts,
    rowClass,
    subtitleLabel,
    tokenizeSubtitle,
    udReading,
)

FAIS = frozenset({"imp:pre:2s", "ind:pre:1s", "ind:pre:2s"})
REGARDE = frozenset({"imp:pre:2s", "ind:pre:1s", "ind:pre:3s", "sub:pre:1s", "sub:pre:3s"})
FINIS = frozenset({"imp:pre:2s", "ind:pre:1s", "ind:pre:2s", "par:pas"})


def label(line: str, form: str) -> str | None:
    tokens = tokenizeSubtitle(line)
    return subtitleLabel(tokens, tokens.index(form))


class TestUdReading:
    def test_finite_moods(self) -> None:
        assert udReading("VERB", "Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin") == "ind:pre:1s"
        assert udReading("VERB", "Mood=Ind|Number=Plur|Person=3|Tense=Imp|VerbForm=Fin") == "ind:imp:3p"
        assert udReading("VERB", "Mood=Ind|Number=Sing|Person=3|Tense=Past|VerbForm=Fin") == "ind:pas:3s"
        assert udReading("AUX", "Mood=Ind|Number=Sing|Person=2|Tense=Fut|VerbForm=Fin") == "ind:fut:2s"
        assert udReading("VERB", "Mood=Sub|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin") == "sub:pre:3s"
        assert udReading("VERB", "Mood=Sub|Number=Sing|Person=3|Tense=Imp|VerbForm=Fin") == "sub:imp:3s"
        assert udReading("VERB", "Mood=Cnd|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin") == "cnd:pre:1s"
        assert udReading("VERB", "Mood=Imp|Number=Sing|Person=2|Tense=Pres|VerbForm=Fin") == "imp:pre:2s"

    def test_non_finite_and_nominal(self) -> None:
        assert udReading("VERB", "VerbForm=Inf") == "inf"
        assert udReading("VERB", "Gender=Masc|Number=Sing|Tense=Past|VerbForm=Part") == "par:pas"
        assert udReading("VERB", "Tense=Pres|VerbForm=Part") == "par:pre"
        assert udReading("NOUN", "Gender=Fem|Number=Plur") == "nom:fp"
        assert udReading("ADJ", "Gender=Masc|Number=Sing") == "nom:ms"

    def test_underspecified(self) -> None:
        assert udReading("VERB", "Mood=Ind|Tense=Pres|VerbForm=Fin") is None
        assert udReading("NOUN", "Number=Sing") is None
        assert udReading("NOUN", "_") is None
        assert udReading("DET", "Gender=Fem|Number=Sing") is None


class TestRowClass:
    def test_verb_readings_deduplicated(self) -> None:
        assert rowClass("VER", "", "", "imp:pre:2s;ind:pre:1s;ind:pre:1s;") == frozenset({"imp:pre:2s", "ind:pre:1s"})

    def test_nominal_cells(self) -> None:
        assert rowClass("NOM", "", "s", "") == frozenset({"nom:ms", "nom:fs"})
        assert rowClass("ADJ", "f", "p", "") == frozenset({"nom:fp"})

    def test_other_categories(self) -> None:
        assert rowClass("ADV", "", "", "") is None
        assert rowClass("VER", "", "", "") is None


class TestSubtitleHeuristic:
    def test_tokenizer(self) -> None:
        assert tokenizeSubtitle("-Je suis là. Dis-moi, a-t-il fini ?") == [
            "-", "je", "suis", "là", ".", "dis", "-moi", ",", "a", "-t-il", "fini", "?"]
        assert tokenizeSubtitle("J’ai") == ["j'", "ai"]

    def test_imperative(self) -> None:
        assert label("Regarde !", "regarde") == "imp"
        assert label("Dis-moi la vérité.", "dis") == "imp"
        assert label("Ne fais pas ça.", "fais") == "imp"
        assert label("Bon, regarde ça.", "regarde") == "imp"

    def test_subject_person(self) -> None:
        assert label("Je te dis que non.", "dis") == "1s"
        assert label("Tu ne le fais pas ?", "fais") == "2s"
        assert label("Que fais-tu ?", "fais") == "2s"
        assert label("Vous regardez la télé.", "regardez") == "2p"
        assert label("Le chat regarde.", "regarde") == "3"

    def test_coordination_keeps_the_subject(self) -> None:
        assert label("Il entre et regarde.", "regarde") == "3s"

    def test_participle_and_que(self) -> None:
        assert label("J'ai pas fini.", "fini") == "par"
        assert label("Il faut que je regarde.", "regarde") == "que:1s"

    def test_candidates(self) -> None:
        assert labelCandidates("imp", FAIS) == ["imp:pre:2s"]
        assert labelCandidates("1s", REGARDE) == ["ind:pre:1s"]
        assert labelCandidates("que:3", REGARDE) == ["ind:pre:3s", "sub:pre:3s"]
        assert labelCandidates("par", FINIS) == ["par:pas"]
        assert labelCandidates("3", FAIS) == []


class TestPooledModel:
    def test_luce_recovers_consistent_shares(self) -> None:
        counts = newClassCounts()
        counts[frozenset({"a", "b"})].update({"a": 300.0, "b": 100.0})
        counts[frozenset({"b", "c"})].update({"b": 200.0, "c": 200.0})
        weights = fitLuceWeights(counts, pseudoCount=0.0)
        assert abs(weights["a"] / weights["b"] - 3.0) < 0.01
        assert abs(weights["b"] / weights["c"] - 1.0) < 0.01

    def test_tiers_and_fallback(self) -> None:
        observed = newClassCounts()
        observed[frozenset({"a", "b"})].update({"a": 30.0, "b": 10.0})
        sparse = newClassCounts()
        sparse[frozenset({"a", "c"})].update({"a": 1.0})
        table = buildTable([frozenset({"a", "b"}), frozenset({"a", "c"})],
                           [("first", sparse), ("second", observed)], minTokens=20)
        rows = {(row.readingClass, row.reading): row for row in table}
        assert rows[("a;b", "a")].source == "second"
        assert abs(rows[("a;b", "a")].share - 0.75) < 1e-9
        assert rows[("a;c", "a")].source == "pooled"
        assert abs(rows[("a;c", "a")].share + rows[("a;c", "c")].share - 1.0) < 1e-9
