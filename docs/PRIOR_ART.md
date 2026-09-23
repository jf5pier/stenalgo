# Prior art

Stenalgo is not the first programmatically generated stenographic theory, and not the first
French one either. This survey positions it against the existing theories, dictionaries and
systems: what they already solve, what they leave open, and where Stenalgo's
optimization-first approach differs.

Dated 2026-09: it reflects the state of these projects when surveyed (2026-09-15); links,
statuses and commit counts may have drifted since.

## Survey (researched 2026-09-15)

- **[Pluvier](https://github.com/Vermoot/Pluvier)** — the closest analog: a French,
  "real-time friendly, conflict-free" theory for Plover, dictionary programmatically generated
  from Lexique (same corpus family as this project), rules derived from the Québec
  LaSalle/TAO method ([blog post](http://plover.stenoknight.com/2021/11/pluvier-french-dictionary-generator.html)),
  Ireland layout, manual briefs layered on top of generated outlines. Work-in-progress (~80
  commits, no releases). Its homophone stance is "distinct outline per word via rules + briefs,"
  with frequency-prioritized disambiguation still open — this project's core problem appears
  unsolved there too. Its translated LaSalle rule docs are mineable; "optimization-first, custom
  ergonomics, systematic feature-based disambiguation on a 26-key board" is this project's
  differentiation — no community project found uses constraint solvers or optimizes finger
  strain.
- **[Lapwing theory](https://plover.wiki/index.php/Lapwing_theory)** (Aerick, 2022) — the model
  for "systematic conflict-free theory as a maintained artifact with pedagogy"
  ([Lapwing for Beginners](https://lapwing.aerick.ca/lapwing-for-beginners/),
  [dictionaries](https://github.com/aerickt/steno-dictionaries)); exists precisely because
  Plover theory had conflicts. Its [Javelin appendix](https://lapwing.aerick.ca/Appendix-C.html)
  runs Lapwing on embedded firmware — the dual-target pattern (one dictionary, Plover *and*
  onboard) already proven in English.
- **[Javelin](https://github.com/jthlim/javelin-steno)** (Jeffrey Lim) — embedded steno engine
  firmware with onboard dictionaries (standalone, no host Plover), two dictionary formats, a
  firmware builder; runs on Uni v4/Polyglot/Asterisk
  ([overview](https://stenokeyboards.com/blogs/posts/embedded-steno),
  [wiki](https://plover.wiki/index.php/Javelin)). This is the prior art the
  dictionary-densification stage should be designed against.
- **[Regenpfeifer](https://github.com/mkrnr/plover_regenpfeifer)** — same genre for German:
  programmatically generated, rule-based dictionary for Plover; the author's
  [design writeup](https://stenoblog.com/working-on-a-german-steno-theory/) covers rule-based
  word→stroke conversion at theory scale.
- **[Plover discussion #1372](https://github.com/openstenoproject/plover/discussions/1372)** —
  codifying English Plover-theory rules as a script;
  [Di's steno-dictionaries](https://github.com/didoesdigital/steno-dictionaries) are the
  maintained-artifact + tooling precedent (Typey Type).
- Historical context: **Grandjean** (legacy French stenotype, available as a Plover plugin) is
  the anti-pattern — not conflict-free, needs host-side homonym disambiguation software.
  **Michela** (Italian parliamentary machine steno) is the existence proof that a fully
  systematic national-language machine theory supports professional realtime. The
  [steno layouts page](https://plover.wiki/index.php/Steno_layouts_and_supported_languages)
  catalogs the language-plugin landscape; Plover's
  [Designing Steno Systems](https://plover.readthedocs.io/en/latest/system_dev.html) gives the
  layout/theory/dictionary decomposition.
- **Academic literature on automated steno-theory generation: essentially none found** (nearest
  formal work is HCI chorded-keyboard assignment research). The niche is open.

---

For how this prior art shaped Stenalgo's design — the layout approach, the dual-target
Plover/embedded-engine architecture, and the two homophone mechanisms — see
[ARCHITECTURE.md](ARCHITECTURE.md).
