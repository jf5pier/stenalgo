# readingShares.tsv: attribution

`readingShares.tsv` is built by `python -m util.build_reading_shares`. For every ambiguity class of the theory's lexicons
(the set of readings of one spelling of one lemma), it gives the share of each reading as observed in two kinds of
corpus. It keeps only aggregated counts per class and reading, never text from the sources.

## Universal Dependencies French treebanks (gold morphological tags)

Cloned from github.com/UniversalDependencies (commits of 2026-05-06), into the gitignored `ud-french/`:

- **UD_French-ParisStories** (spoken, Paris narratives), licence **CC BY-SA 4.0**. Annotation: Sylvain Kahane,
  Bruno Guillaume, Mariam Nakhlé, Vanessa Gaudray-Bouju, Menel Mahamdi (README).
  https://github.com/UniversalDependencies/UD_French-ParisStories
- **UD_French-Rhapsodie** (spoken), licence **CC BY-SA 4.0**.
  https://github.com/UniversalDependencies/UD_French-Rhapsodie
- **UD_French-GSD** (written), licence **CC BY-SA 4.0**. Reference: Bruno Guillaume, Marie-Catherine de Marneffe,
  Guy Perrier. *Conversion et améliorations de corpus du français annotés en Universal Dependencies.* TAL 60(2), 2019.
  https://github.com/UniversalDependencies/UD_French-GSD
- **UD_French-Sequoia** (written), licence **LGPL-LR**. Reference: Marie Candito, Djamé Seddah. *Le corpus Sequoia :
  annotation syntaxique et exploitation pour l'adaptation d'analyseur par pont lexical.* TALN 2012.
  https://github.com/UniversalDependencies/UD_French-Sequoia

The aggregated counts derived from these treebanks are redistributed under the treebanks' own licences.

## OpenSubtitles (film dialogue, untagged)

Every 400th line of the French monolingual OpenSubtitles v2018 corpus from OPUS
(https://object.pouta.csc.fi/OPUS-OpenSubtitles/v2018/mono/fr.txt.gz), in the gitignored `opensubtitles-fr/sample.txt`
(267,079 lines). Its readings come from the script's own heuristic, not from annotations. Source: http://www.opensubtitles.org/.
Reference: Pierre Lison and Jörg Tiedemann. *OpenSubtitles2016: Extracting Large Parallel Corpora from Movie and TV
Subtitles.* LREC 2016. The corpus is used for counts only and no subtitle text is redistributed.
