import pytest

from ..elicitation import (
    buildLemmaHomophoneGroups,
    enumerateOppositionSamples,
    featureCombinationsByOrtho,
    reportScale,
    wordFeatureCombinations,
)
from ..word import GramCat, Word


def _make_word(**overrides) -> Word:
    defaults = dict(
        ortho="chat", phonology="Sa", lemme="chat", gramCat=GramCat.NOM,
        orthoGramCat=[GramCat.NOM], gender="m", number="s", infoVerb=None,
        rawSyllCV="S_a", rawOrthosyllCV="ch_a_t", frequencyBook=1.0, frequencyFilm=2.0,
    )
    defaults.update(overrides)
    return Word(**defaults)


# ── wordFeatureCombinations ──────────────────────────────────────────────────

def test_finite_verb_combination_has_no_gender_number():
    word = _make_word(
        ortho="parle", lemme="parler", gramCat=GramCat.VER, gender="", number="",
        infoVerb="ind:pre:1s;",
    )
    assert wordFeatureCombinations(word) == [frozenset({"indicatif", "présent", "pers_1", "nbr_s"})]


def test_participle_combination_carries_gender_number_and_ver():
    word = _make_word(
        ortho="parlée", lemme="parler", gramCat=GramCat.VER, gender="f", number="s",
        infoVerb="par:pas;",
    )
    assert wordFeatureCombinations(word) == [frozenset({"participe", "passé", "VER", "f", "s"})]


def test_homograph_word_gender_number_not_leaked_into_finite_combination():
    """'fait' merges a participle combination (m:s) and a finite combination (ind pres 3s)
    on one Word (see Word.mergeInfoVerb); only the participle combination should carry m/s."""
    word = _make_word(
        ortho="fait", lemme="faire", gramCat=GramCat.VER, gender="m", number="s",
        infoVerb="ind:pre:3s;par:pas;",
    )
    combinations_ = wordFeatureCombinations(word)
    assert frozenset({"indicatif", "présent", "pers_3", "nbr_s"}) in combinations_
    assert frozenset({"participe", "passé", "VER", "m", "s"}) in combinations_


def test_non_verb_word_combination_is_just_gender_number():
    assert wordFeatureCombinations(_make_word()) == [frozenset({"m", "s"})]


def test_subjonctif_imparfait_combination_is_out_of_scope():
    word = _make_word(
        ortho="parlât", lemme="parler", gramCat=GramCat.VER, gender="", number="",
        infoVerb="sub:imp:3s;",
    )
    assert wordFeatureCombinations(word) == []


def test_subjonctif_imparfait_dropped_but_other_combinations_of_same_word_kept():
    """Synthetic homograph exercising the merge logic -- not a claim that any real
    French word carries exactly these two combinations on one spelling."""
    word = _make_word(
        ortho="parlat", lemme="parler", gramCat=GramCat.VER, gender="", number="",
        infoVerb="sub:imp:3s;ind:pas:3s;",
    )
    assert wordFeatureCombinations(word) == [frozenset({"indicatif", "passé", "pers_3", "nbr_s"})]


# ── lemma-homophone groups / enumeration ─────────────────────────────────────

@pytest.fixture
def parler_group() -> dict[str, list[Word]]:
    strokes = (("K1",),)
    parle = _make_word(ortho="parle", lemme="parler", gramCat=GramCat.VER, gender="", number="",
                        infoVerb="ind:pre:1s;ind:pre:3s;")
    parles = _make_word(ortho="parles", lemme="parler", gramCat=GramCat.VER, gender="", number="",
                         infoVerb="ind:pre:2s;")
    parlent = _make_word(ortho="parlent", lemme="parler", gramCat=GramCat.VER, gender="", number="",
                          infoVerb="ind:pre:3p;")
    return {strokes: [parle, parles, parlent]}


def test_buildLemmaHomophoneGroups_groups_by_lemme_within_a_stroke(parler_group):
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    assert len(homophoneGroups) == 1
    ((strokes, lemmeGramCat), words), = homophoneGroups.items()
    assert lemmeGramCat == "parler_VER"
    assert len(words) == 3


def test_enumerate_samples_covers_every_cross_spelling_combination_pair(parler_group):
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    samples = enumerateOppositionSamples(homophoneGroups)
    # parle has 2 combinations, parles 1, parlent 1 -> (2*1)+(2*1)+(1*1) = 5 cross-spelling pairs
    assert len(samples) == 5
    # combinations of the SAME spelling (parle's 2 combinations) never appear as a sample
    assert all(s.orthoA != s.orthoB for s in samples)


def test_reportScale_dedups_oppositions_and_finds_cooccurrence(parler_group):
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    report = reportScale(homophoneGroups)
    assert report.lemmaHomophoneGroupCount == 1
    assert report.maxCompoundSize == 4  # indicatif:présent:pers_3:nbr_p, the biggest combination here
    assert frozenset({"pers_3", "nbr_p"}) in report.coOccurrencePairs
    assert report.distinctOppositionCount > 0


def test_tie_opposition_flagged_when_two_spellings_share_a_combination():
    strokes = (("K1",),)
    fayote = _make_word(ortho="fayote", lemme="fayoter", gramCat=GramCat.VER, gender="", number="",
                         infoVerb="ind:pre:3s;")
    fayotte = _make_word(ortho="fayotte", lemme="fayoter", gramCat=GramCat.VER, gender="", number="",
                          infoVerb="ind:pre:3s;")
    homophoneGroups = buildLemmaHomophoneGroups({strokes: [fayote, fayotte]})
    report = reportScale(homophoneGroups)
    assert len(report.tieOppositions) == 1
    assert report.distinctOppositionCount == 0
