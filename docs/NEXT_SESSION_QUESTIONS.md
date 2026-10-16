# Resume note (written 2026-10-10, before a possible clear)

Read `docs/LEXICON_COMPLETION_CONTINUATION.md` first; plan of record `/home/jfsp/.claude/plans/read-docs-lexicon-completion-continuatio-merry-kahn.md`.

## State
- Phases 0-2 done (uncommitted): Mixte rules (`splitGlides` case H, `syllFromPhon` f839141bb5), 29 manual rows (arguer x6, décatie x2, 21 loanwords), `resources/lemmaCorrections.tsv` (liserer), folded en-/em- fix (`storedBreakdown`). Mixte md5 `96a420bff0c4e4c70b9d5f851f9acbe9`; pytest 1548 + 1 known failure; mypy clean.
- Phase 3-4 (single full `python dictionary.py`, expression exports, md5 report, docs) was delegated to a Sonnet agent; if this note is read after a clear, check `git status`, `pipeline_timings.log` and the docs' newest "Update 2026-10-10 (last)" block to see whether it finished. If not, rerun: `rm -f *.pickle; python dictionary.py` (~30 min), then `util.export_expression_data`, `util.export_plover_plugin`.
- Decisions recorded: `b3efd1782d` accept, `64402d8bce` reject (arguer is [aRg8e], applied by manual rows; do NOT run `build_mixte_corrections` for it).

## Questions for the user
1. `rapiécer`: add an è-stem template (derived from `dép:ecer`) to `resources/verbiste/conjugations-fr.xml` + row `rapiécer  rapi:écer  céder  family_template` in `verbModelExceptions.tsv`? (An agent's edit of the XML was denied by the permission classifier.)
2. `écher` and `retraire` have no Synthetic paradigm (no template). Add `écher  s:écher` / `retraire  extra:ire  traire  family_template` rows? (`retraire` has no passé simple by design.)
3. `liseré`/`liserée` keep the accentless spelling and schwa pronunciation with lemma `lisérer`; correct the spelling/phon too?
4. Review the elicitation answers the rebuild agent added, if any (listed in its report / the docs update).
5. Commit? Nothing is committed.

## Update after the full rebuild (rc 0, 1,997 s; 0 unresolved oppositions, 0 conflicts, 0 collisions; pytest 1549 pass, mypy clean; nothing committed)
Results are in the "Update 2026-10-10 (last)" block of LEXICON_COMPLETION_CONTINUATION.md. Decisions needed, because the strokes moved:
6. `ay` split (case H): ~322 words changed strokes although `phon` is unchanged (`ayant` `iej/@` -> `ie/Rw@`, `balayait`): the theory reads the syllable cut of `syll_cv`, so the glide now opens the next syllable (as `payons` already did). Keep (consistent with the glide rulings) or restrict case H?
7. E/e rows (`syllFromPhon`): ~100 words changed strokes (`embouteiller` `te` -> `tie`, `embêter` `sve` -> `svie`, `emmêler` `me` -> `mie`). The plan assumed no theory change (wrong: the theory is not driven by `syll_cv` alone). Check whether the new strokes are wanted or whether `phon` should keep `E`.
8. Also look at: `capharnaüm` gained a final `em`; some words gained `/-k`, `/-l` variants (`braie`, `balayes`, `embouteille`).
Files to compare: `plover_stenalgo_dictionary.json` against git HEAD.
