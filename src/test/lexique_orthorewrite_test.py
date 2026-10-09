from lexique import applyOrthoRewrite, computeSingleEditRule, orthoRewriteOccurrence


def _rewrite(old: str, new: str, ortho: str, orthosyll: str) -> str:
    rule = computeSingleEditRule(old, new)
    occurrence = orthoRewriteOccurrence(ortho, rule)
    assert occurrence is not None
    return applyOrthoRewrite(orthosyll, rule, occurrence)


def test_deletionInsideMultiLetterUnitKeepsBoundaries() -> None:
    assert _rewrite("interpeller", "interpeler", "interpella", "in|t_e_r|p_e|ll_a") == "in|t_e_r|p_e|l_a"


def test_deletionOfWholeUnitDropsOneSeparator() -> None:
    assert _rewrite("quincaillier", "quincailler", "quincaillier", "qu_in|c_a|ill_i_er") == "qu_in|c_a|ill_er"


def test_deletionInFlatOrtho() -> None:
    assert _rewrite("interpeller", "interpeler", "interpella", "interpella") == "interpela"


def test_deletionNeedsTheOldSpellingsFollowingLetter() -> None:
    rule = computeSingleEditRule("asseoir", "assoir")
    assert orthoRewriteOccurrence("assoir", rule) is None            # nothing to delete: already reformed
    assert orthoRewriteOccurrence("asseoirai", rule) is not None     # `e` followed by the `o` of the old spelling
    assert orthoRewriteOccurrence("asseyiez", rule) is None          # `assey-` forms keep their `e`
    assert orthoRewriteOccurrence("rasseyons", computeSingleEditRule("rasseoir", "rassoir")) is None


def test_followingLetterGuardIgnoresAccents() -> None:
    rule = computeSingleEditRule("quincaillier", "quincailler")
    assert orthoRewriteOccurrence("quincaillière", rule) is not None
    assert orthoRewriteOccurrence("quincaillier", rule) is not None
