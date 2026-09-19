import pytest

from ..elicitation import (
    AnsweredOpposition,
    buildAnswersByOpposition,
    buildFrequencyByGroupOrtho,
    buildLemmaHomophoneGroups,
    enumerateOppositionSamples,
    featureCombinationsByOrtho,
    reportScale,
    resolveGroupPressSets,
    serializeResolvedPressSets,
    validateElicitation,
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


# ── E5: buildAnswersByOpposition / validateElicitation ───────────────────────

def test_buildAnswersByOpposition_merges_consistent_answers():
    combinationA = frozenset({"pers_2"})
    combinationB = frozenset({"pers_3"})
    # The same opposition (A vs B) recurring across two different lexemes with the same
    # answer is expected and fine -- E4's "the answer propagates ... across all lexemes".
    answers = [
        AnsweredOpposition(combinationA, frozenset({"pers_2"}), combinationB, frozenset()),
        AnsweredOpposition(combinationA, frozenset({"pers_2"}), combinationB, frozenset()),
    ]
    answersByOpposition, duplicates = buildAnswersByOpposition(answers)
    key = frozenset({combinationA, combinationB})
    assert answersByOpposition[key] == {combinationA: frozenset({"pers_2"}), combinationB: frozenset()}
    assert duplicates == []


def test_buildAnswersByOpposition_allows_same_combination_different_press_against_different_partners():
    """A single reading legitimately needs a different press depending on which OTHER
    reading it is opposed to -- this must NOT be flagged, unlike a real duplicate
    (same exact pair, disagreeing answers)."""
    combinationA = frozenset({"pers_2"})
    combinationB = frozenset({"pers_3"})
    combinationC = frozenset({"pers_1"})
    answers = [
        AnsweredOpposition(combinationA, frozenset({"pers_2"}), combinationB, frozenset()),
        AnsweredOpposition(combinationA, frozenset(), combinationC, frozenset({"pers_1"})),
    ]
    answersByOpposition, duplicates = buildAnswersByOpposition(answers)
    assert answersByOpposition[frozenset({combinationA, combinationB})][combinationA] == frozenset({"pers_2"})
    assert answersByOpposition[frozenset({combinationA, combinationC})][combinationA] == frozenset()
    assert duplicates == []


def test_buildAnswersByOpposition_flags_duplicate_disagreeing_answers():
    combinationA = frozenset({"pers_2"})
    combinationB = frozenset({"pers_3"})
    key = frozenset({combinationA, combinationB})
    answers = [
        AnsweredOpposition(combinationA, frozenset({"pers_2"}), combinationB, frozenset()),
        # The EXACT same pair, answered differently the second time.
        AnsweredOpposition(combinationA, frozenset(), combinationB, frozenset({"pers_3"})),
    ]
    answersByOpposition, duplicates = buildAnswersByOpposition(answers)
    assert key not in answersByOpposition
    assert duplicates == [key]


def _opposition_answers(parler_group) -> dict:
    """The 5 pairwise oppositions the parler_group fixture actually needs (see
    test_enumerate_samples_covers_every_cross_spelling_combination_pair), each answered
    consistently: parle needs `pers_1`, parles needs `pers_2`, parlent needs `nbr_p`."""
    pers1 = frozenset({"indicatif", "présent", "pers_1", "nbr_s"})
    pers3s = frozenset({"indicatif", "présent", "pers_3", "nbr_s"})
    pers2 = frozenset({"indicatif", "présent", "pers_2", "nbr_s"})
    pers3p = frozenset({"indicatif", "présent", "pers_3", "nbr_p"})
    return {
        frozenset({pers1, pers3p}): {pers1: frozenset({"pers_1"}), pers3p: frozenset({"nbr_p"})},
        frozenset({pers3s, pers3p}): {pers3s: frozenset(), pers3p: frozenset({"nbr_p"})},
        frozenset({pers1, pers2}): {pers1: frozenset({"pers_1"}), pers2: frozenset({"pers_2"})},
        frozenset({pers3s, pers2}): {pers3s: frozenset(), pers2: frozenset({"pers_2"})},
        frozenset({pers3p, pers2}): {pers3p: frozenset({"nbr_p"}), pers2: frozenset({"pers_2"})},
    }


def test_validateElicitation_finds_no_conflict_when_press_sets_are_distinct(parler_group):
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    conflicts, unresolved = validateElicitation(homophoneGroups, _opposition_answers(parler_group))
    assert conflicts == []
    assert unresolved == []


def test_validateElicitation_flags_two_spellings_sharing_a_press_set(parler_group):
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    answers = _opposition_answers(parler_group)
    pers1 = frozenset({"indicatif", "présent", "pers_1", "nbr_s"})
    pers2 = frozenset({"indicatif", "présent", "pers_2", "nbr_s"})
    pers3p = frozenset({"indicatif", "présent", "pers_3", "nbr_p"})
    # Change every answer touching pers1 so it ends up implying {"pers_2"} -- the same
    # press-set parles already implies -- a real conflict.
    answers[frozenset({pers1, pers3p})][pers1] = frozenset({"pers_2"})
    answers[frozenset({pers1, pers2})][pers1] = frozenset({"pers_2"})
    conflicts, unresolved = validateElicitation(homophoneGroups, answers)
    assert unresolved == []
    assert len(conflicts) == 1
    assert conflicts[0].pressSet == frozenset({"pers_2"})
    assert set(conflicts[0].orthos) == {"parle", "parles"}


def test_validateElicitation_skips_group_with_an_unresolved_opposition(parler_group):
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    answers = _opposition_answers(parler_group)
    pers3p = frozenset({"indicatif", "présent", "pers_3", "nbr_p"})
    pers2 = frozenset({"indicatif", "présent", "pers_2", "nbr_s"})
    missingKey = frozenset({pers3p, pers2})
    del answers[missingKey]
    conflicts, unresolved = validateElicitation(homophoneGroups, answers)
    assert conflicts == []
    assert unresolved == [missingKey]


# ── E6: resolveGroupPressSets / serializeResolvedPressSets ───────────────────

def test_resolveGroupPressSets_matches_validateElicitations_own_resolution(parler_group):
    """resolveGroupPressSets is the factored-out step validateElicitation itself uses --
    its output must be exactly what validateElicitation checked for conflicts against."""
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    pressSetsByGroup, unresolved = resolveGroupPressSets(homophoneGroups, _opposition_answers(parler_group))
    assert unresolved == []
    ((_key, pressSetByOrtho),) = pressSetsByGroup.items()
    assert pressSetByOrtho == {
        "parle": frozenset({"pers_1"}),
        "parles": frozenset({"pers_2"}),
        "parlent": frozenset({"nbr_p"}),
    }


def test_serializeResolvedPressSets_is_json_ready(parler_group):
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    pressSetsByGroup, _ = resolveGroupPressSets(homophoneGroups, _opposition_answers(parler_group))
    serialized = serializeResolvedPressSets(pressSetsByGroup)
    assert len(serialized) == 1
    entry = serialized[0]
    assert entry["lemmeGramCat"] == "parler_VER"
    assert entry["strokes"] == [["K1"]]
    assert entry["pressSets"] == {"parle": ["pers_1"], "parles": ["pers_2"], "parlent": ["nbr_p"]}
    assert entry["frequencies"] == {"parle": 0.0, "parles": 0.0, "parlent": 0.0}  # no frequencies passed
    import json
    json.dumps(serialized)  # must not raise -- the whole point of serializing


def test_buildFrequencyByGroupOrtho_reads_each_spellings_corpus_frequency(parler_group):
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    frequencyByGroupOrtho = buildFrequencyByGroupOrtho(homophoneGroups)
    ((key, freqByOrtho),) = frequencyByGroupOrtho.items()
    # _make_word's default frequencyFilm=2.0 -> Word.frequency, shared by all three spellings here
    assert freqByOrtho == {"parle": 2.0, "parles": 2.0, "parlent": 2.0}


def test_buildFrequencyByGroupOrtho_zeroes_out_frequent_words(parler_group):
    # "parle" is a brief candidate (top-200 word) -- typed as a whole-word shortcut, not
    # via its phonemic keypresses, so it must not count toward keypress usage load.
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    frequencyByGroupOrtho = buildFrequencyByGroupOrtho(homophoneGroups, frozenset({"parle"}))
    ((key, freqByOrtho),) = frequencyByGroupOrtho.items()
    assert freqByOrtho == {"parle": 0.0, "parles": 2.0, "parlent": 2.0}


def test_serializeResolvedPressSets_carries_frequency_when_given(parler_group):
    homophoneGroups = buildLemmaHomophoneGroups(parler_group)
    pressSetsByGroup, _ = resolveGroupPressSets(homophoneGroups, _opposition_answers(parler_group))
    frequencyByGroupOrtho = buildFrequencyByGroupOrtho(homophoneGroups)
    serialized = serializeResolvedPressSets(pressSetsByGroup, frequencyByGroupOrtho)
    entry = serialized[0]
    assert entry["frequencies"] == {"parle": 2.0, "parles": 2.0, "parlent": 2.0}
