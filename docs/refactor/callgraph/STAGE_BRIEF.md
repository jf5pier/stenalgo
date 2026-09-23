# Brief for Per-Stage Call Graphs (Pass 1b)

Shared instructions for the four stage agents. Repo: /home/jfsp/stenalgo, branch `docs-refactor`.

## Constraints
- READ-ONLY everywhere except your own output file `docs/refactor/callgraph/<NN>-<stage>.md`.
- Do NOT run `dictionary.py`, `lexique.py`, `src.elicitation`, `util/build_*`, `util/export_*`, or
  delete pickles (another job is rewriting artifacts concurrently). Reading, grepping, and small
  read-only `env/bin/python -c` snippets (e.g. loading a JSON/TSV to count rows, loading
  `FirstTheory.pickle` to inspect shape) are fine.
- Do not modify code. Record suspected bugs; never fix them.

## Inputs
- `docs/refactor/callgraph/00-skeleton.md` — stage table, **dataset state names** (§3) and the
  **seed glossary** (§4). Reuse those terms verbatim in every Input state / Result line. If you
  need a new term, define it once in your "New glossary terms" section and use it consistently.
- Existing docs may be stale; the code is the source of truth.

## Naming rule (user preference, mandatory)
Every stage/phase/step is cited by a descriptive name with its code in parentheses, e.g.
"Marker Grouping (Phase G)", "Lexicon Building (S1)". Never write a bare "Phase G" or "S3".
Each call section heading also gets a descriptive name first, the function name second.

## Output structure
```
# <Stage descriptive name> (<code>)

## Overview
<ASCII call tree of this stage, 1 line per expanded call: "<code>.<n> descriptive name — func (file:line)">
<3–6 sentence plain-words narrative: dataset in, dataset out, why this stage exists>

## Calls
### <Descriptive name> — <funcName> (<code>.<n>)   <file:line>
Called by: <descriptive name (<code>.<m>)>
Input state: <what the dataset looks like at entry, in glossary terms; include sizes when known>
Transformation: <plain words, what it does and the key rules/thresholds/constants>
Result: <expected output, same terminology; include sizes when known>
Artifacts: reads <files> / writes <files>   (omit if none)
Helpers not expanded: <func (file:line), ...>
Notes: <optional: surprising behaviour, doc drift, links to specs>

## New glossary terms
- **Term** — definition. Code anchor. (Preferred synonym / Avoid notes if relevant.)

## Suspected bugs
- <file:line> — <defect in one sentence>. Scenario: <concrete input/state → wrong output/crash>.
  Confidence: high/medium/low. (Verify by reading the code; no speculation without a scenario.)

## Dead-code observations
- <func/file:line> — <why it looks unreachable from the pipeline entry points>. (Feeds Dead-Code Removal (Pass 5).)

## Doc drift
- <doc file:line> says X; code says Y.
```

## Depth rule
Expand every call that transforms or filters the dataset, or decides something (a rule, a
threshold, a tie-break). Collapse pure helpers (formatting, parsing one field, lookups, getters,
tiny utilities) into "Helpers not expanded". Number calls in execution order (`S2.1`, `S2.2`,
nested `S2.4.1`). Target length: 250–600 lines. Verify every file:line anchor.
