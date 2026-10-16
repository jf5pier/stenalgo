# Phoneme optionality is decided before the layout solve, on placeholder phonology

Whether a phoneme occurrence is optional depends on collisions, and collisions depend on the layout the CP-SAT is about to
choose. Instead of iterating solve → rebuild → optionality → solve, optionality is decided once, on the current theory's full
phonology with the 7 keypress groups written as keypress-group placeholders (pseudo-phonemes, so feature-only differences
such as `mot`/`mots` count), and the result is fed to the solve as typed-frequency weights. It is deterministic and costs one
analysis instead of repeated ~13-minute solve-and-rebuild rounds; the real S5–S7 rebuild after the solve remains the final judge
of the outlines. See `docs/PHONOLOGY_REWRITE_PLAN.md` (PRP5, PRP11).
