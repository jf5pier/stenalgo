from util.export_affix_abbreviations import buildIndex, buildRuleIndex, foldIntoDefinitionChords


def test_index_lists_every_distinct_short_outline_of_a_long_one_in_row_order():
    rows = [
        {"spelling": "arrête", "long": "a/Riet", "short": "Rwiejt"},
        {"spelling": "arrête", "long": "a/Riet/-k", "short": "Rwiejt/-k"},
        {"spelling": "arrête", "long": "a/Riet", "short": "other"},
        {"spelling": "arrête", "long": "a/Riet", "short": "Rwiejt"},
        {"spelling": "amour", "long": "a/m@eR", "short": "mw@ejR"},
    ]
    assert buildIndex(rows) == {"arrête": {"a/Riet": ["Rwiejt", "other"], "a/Riet/-k": ["Rwiejt/-k"]},
                                "amour": {"a/m@eR": ["mw@ejR"]}}


def test_rule_index_lists_the_distinct_ranks_of_a_spelling_ascending():
    rows = [
        {"spelling": "arrête", "rank": "3"},
        {"spelling": "arrête", "rank": "1"},
        {"spelling": "arrête", "rank": "3"},
        {"spelling": "amour", "rank": "2"},
    ]
    assert buildRuleIndex(rows) == {"arrête": [1, 3], "amour": [2]}


def test_a_short_of_an_unmerged_long_outline_joins_the_definitions_chord_with_the_same_strokes():
    index = {"étais": {"e/tied": ["*e#dt"], "e/tie/-d": ["*e#t/-d"], "x/y": ["xy"]}}
    chords = {"étais": ["e/tied", "e/tiek"]}
    assert foldIntoDefinitionChords(index, chords) == {"étais": {"e/tied": ["*e#dt", "*e#t/-d"], "x/y": ["xy"]}}
