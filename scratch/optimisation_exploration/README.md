# Optimisation exploration

Hand-run scripts that estimate, per phoneme, the keyboard-effort gain and the collisions created by removing it or fusing it with another phoneme.
Full reference (method, run order, reading the results, deprecation notes): `docs/PHONEME_REMOVAL_EXPLORATION.md`.

```
python scratch/optimisation_exploration/optexp_phoneme_counts.py
python scratch/optimisation_exploration/optexp_phoneme_information.py
python scratch/optimisation_exploration/optexp_phoneme_fusion.py
python scratch/optimisation_exploration/optexp_phoneme_cost.py
python scratch/optimisation_exploration/optexp_phoneme_report.py     # -> out/phoneme_information.md
```
