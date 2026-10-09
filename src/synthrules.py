"""
The synthesis mechanisms gated by a `synth_rule` decision (docs/specs/lexicon-decisions.md section 6): a mechanism
runs only when its decision (kind `synth_rule`, level `-`, signature = the mechanism's name below) is `accept` in
resources/lexiconDecisions.tsv, with the decision's `param` as its parameter (empty = the mechanism's default), or when
it is forced from the command line (`--force-rule NAME[=PARAM]`, for measuring without a decision). Pending, rejected
or absent = the mechanism is off and the generator behaves exactly as before.

Later mechanisms add an entry to SYNTH_RULES and DEFAULT_PARAMS and ask `isRuleActive`.
"""
import os
from collections.abc import Iterable, Mapping

from src.lexicondecisions import ACCEPT, DECISIONS_PATH, Decisions, groupIdFor, loadDecisions

SYNTH_RULES: dict[str, str] = {
    "reference-bar": "reference-validated agreement bar",
    "participle-from-infinitive": "past participles built from the infinitive and the template ending",
    "lost-nasal": "n/m unit reinserted in the infinitive of en-/em- verbs before splicing",
    "homograph-tag": "homograph tag rows copied from the attested row of the same spelling",
    "slot-map": "missing slots derived from the lemma's other forms by a learned slot-to-slot map",
    "glide-future-stem": "future and conditional of -ier/-uer/-ouer verbs: the glide before the schwa of the ending becomes its vowel",
    "infinitive-participle-present": "missing infinitive and present participle rows built from the lemma's other forms and the template",
}
# `participle-from-infinitive` and `homograph-tag` take `strict` (a candidate needs an exact or equivalent reference) or
# `unvalidated` (a candidate without any reference is also accepted when the evidence is plain: see completeVerbParadigms).
DEFAULT_PARAMS: dict[str, str] = {
    "reference-bar": "0.5",
    "participle-from-infinitive": "strict",
    "homograph-tag": "strict",
}
UNVALIDATED_MODES = ("strict", "unvalidated")


def ruleGroupId(name: str) -> str:
    """The decision group id of the mechanism `name`."""
    return groupIdFor("synth_rule", "-", SYNTH_RULES[name])


def parseForcedRules(specs: Iterable[str]) -> dict[str, str]:
    """`--force-rule` values (`NAME` or `NAME=PARAM`) as {name: param}; an unknown name is an error."""
    forced: dict[str, str] = {}
    for spec in specs:
        name, _, param = spec.partition("=")
        if name not in SYNTH_RULES:
            raise ValueError(f"unknown synthesis rule {name!r} (known: {', '.join(sorted(SYNTH_RULES))})")
        forced[name] = param
    return forced


def isRuleActive(name: str, decisions: Decisions | None, forced: Mapping[str, str]) -> tuple[bool, str]:
    """(active, param): forced from the command line, or its decision accepted. `param` is the decision's (or forced)
    param, DEFAULT_PARAMS[name] when empty; "" when inactive."""
    if name in forced:
        return True, forced[name] or DEFAULT_PARAMS.get(name, "")
    decision = decisions.get(ruleGroupId(name)) if decisions is not None else None
    if decision is not None and decision.verdict == ACCEPT:
        return True, decision.param or DEFAULT_PARAMS.get(name, "")
    return False, ""


def loadDecisionsIfPresent(path: str = DECISIONS_PATH) -> Decisions | None:
    return loadDecisions(path) if os.path.exists(path) else None
