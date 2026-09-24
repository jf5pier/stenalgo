#!/usr/bin/python
# coding: utf-8
#
from src.keyboard import Keyboard, Strokes
from src.word import Word, WordFeature, LemmeGramCat, WordOrtho, groupWordsByLemme
from tqdm import tqdm
from collections import defaultdict

verboseLemmes: list[str] = [] # ["fait", "faire"]
verboseWords: list[str] = [] # ["fais", "fait", "faits", "faites"]

def _featureComplexity(feature: WordFeature) -> tuple[int, int]:
    """Lower is simpler. Primary: number of ':'-separated verb-tense components
    (e.g. "conditionnel:nbr_p" has 1, "conditionnel" has 0). Secondary: total number
    of components once also splitting gender/number tags on '_' (e.g. "nbr_p" -> 2,
    "conditionnel:nbr_p" -> 3, "conditionnel" -> 1)."""
    colonParts = feature.split(":")
    numColons = len(colonParts) - 1
    totalParts = sum(len(part.split("_")) for part in colonParts)
    return (numColons, totalParts)
def getAmbiguousMultiphonemes(theory: dict[tuple[tuple[int, ...], ...], list[Word]],
                              keyboard: Keyboard) -> dict[str, list[Word]]:

    ambiguousMultiphonemes: dict[str, list[Word]]= {}
    for strokes, words in theory.items():
        if len(words) > 1:
            phonemesPressed: str = keyboard.strokesToString(strokes)
            ambiguousMultiphonemes[phonemesPressed] = words
    return ambiguousMultiphonemes

def extractDiscriminatingFeatures(theory: dict[Strokes, list[Word]]) \
        -> tuple[dict[str, set[Word]], list[str], dict[tuple[Strokes, LemmeGramCat], dict[Word, list[WordFeature]]]]:
    """
    """


    wordFeatures: dict[Word, list[WordFeature]] = {}
    lemmes: set[LemmeGramCat] = set()
    for lemme in tqdm([word.lemmeGramCat for words in theory.values() for word in words],
                      desc="Collecting lemmes", unit=" word", ascii=True, ncols=100):
        lemmes.add(lemme)

    allFeatures: set[WordFeature] = set()
    for word in tqdm([word for words in theory.values() for word in words],
                      desc="Collecting word features", unit=" word", ascii=True, ncols=100):
        for selectedFeature in word.getFeatures():
            allFeatures.add(selectedFeature)
            wordFeatures[word] = wordFeatures.get(word, []) + [selectedFeature]

    wordFeatureSets: dict[Word, set[WordFeature]] = {w: set(fs) for w, fs in wordFeatures.items()}

    # Words for which the feature is present
    wordsUsingFeature: dict[WordFeature, list[Word]] = {feature: [] for feature in list(allFeatures)}
    orthosUsingFeature: dict[WordFeature, dict[WordOrtho, list[Word]]] = {feature: defaultdict(list) for feature in list(allFeatures)}
    # List (for each word) of list of features (str) for which each feature is a word 
    # discriminator in the group of homophone words sharing the samme lemme
    strokeLemmeDiscriminators: dict[tuple[Strokes, LemmeGramCat], dict[Word, list[WordFeature]]] = defaultdict(lambda: defaultdict(list))
    wordIsDiscrminatedByFeature: dict[WordFeature, set[Word]] = {feature: set() for feature in list(allFeatures)}
    wordIsDiscrminatedFromByFeature: dict[WordFeature, set[Word]] = {feature: set() for feature in list(allFeatures)}

    nbDiscriminatorsOfWord: dict[Word, int] = {word: 0 for words in theory.values() for word in words}
    allWords: list[Word] = sorted(list(set(word for words in theory.values() for word in words)), key=lambda w: w.ortho)

    strokeLemmeSingleWords: dict[tuple[Strokes, LemmeGramCat], Word] = {}

    for strokes, selectedWords in tqdm(theory.items(), desc="Scaning discriminating features",
                               unit=" homophones", ascii=True, ncols=100):
        # Split homophone word group by lemme
        wordByLemme: dict[LemmeGramCat, list[Word]] = groupWordsByLemme(selectedWords)

        # Discriminate homophones words sharing the same lemme
        for lemme, lemmeWords in wordByLemme.items():
            # Dictionnary of word orthographs and their list of Words for which the feature is
            # present on the Word, or on a Word of the group with the same orthograph. Only the
            # features some Word of the group carries are visited (an absent feature yields no
            # ortho and contributes nothing below), in allFeatures order so every downstream
            # list and dict keeps its insertion order.
            groupFeatures: set[WordFeature] = set().union(*(wordFeatureSets[w] for w in lemmeWords))
            lemmeOrthoFeatures: dict[WordFeature, dict[WordOrtho, list[Word]]] = {}
            for feature in allFeatures:
                if feature not in groupFeatures:
                    continue
                orthosWithFeature = {w.ortho for w in lemmeWords if feature in wordFeatureSets[w]}
                wordsUsing = [w for w in lemmeWords
                              if feature in wordFeatureSets[w] or w.ortho in orthosWithFeature]
                lemmeOrthoFeatures[feature] = {
                    ortho: list(filter(lambda w: w.ortho == ortho, wordsUsing))
                    for ortho in set(w.ortho for w in wordsUsing)
                }

            if lemme in verboseLemmes and lemmeWords[0].ortho in verboseWords:
                print("Extract strokes", strokes, " lemme ", lemme, [w.ortho for w in lemmeWords])
                print("lemmeOrthoFeatures: ", [(f, sum(map(len, orthoWords.values())))
                                               for f, orthoWords in lemmeOrthoFeatures.items()])

            if len(lemmeWords) == 1:
                strokeLemmeSingleWords[(strokes, lemme)] = lemmeWords[0]

            # strokeLemmeDiscriminators[(strokes,lemme)] = {}
            # strokeLemmeDiscriminators[(strokes, lemme)] = defaultdict(list)
            # for selectedFeature, wordsUsing in lemmeWordFeatures.items():
            # for selectedFeature, wordsUsing in lemmeOrthoWordFeatures.items():
            for selectedFeature, orthoWords in lemmeOrthoFeatures.items():
                for ortho, wordsUsing in orthoWords.items():
                    if len(wordsUsing) > 0:
                        # Popularity of the feature
                        wordsUsingFeature[selectedFeature] += wordsUsing
                        orthosUsingFeature[selectedFeature][ortho] += wordsUsing
                    # if len(wordsUsing) == 1:
                    if len(orthoWords) == 1:
                        # This is a discriminating feature for this word orthograph.
                        # wordsUsing may contain several distinct Words that share this
                        # ortho (a true homograph): only the one(s) that actually carry
                        # the feature natively should get credit, not just the first in
                        # list order -- otherwise a feature exclusive to the *second*
                        # homograph gets misattributed to the first, leaving the real
                        # owner with no usable discriminator at all.
                        owner = next((w for w in wordsUsing if selectedFeature in wordFeatures[w]),
                                     wordsUsing[0])
                        strokeLemmeDiscriminators[(strokes, lemme)][owner] += [selectedFeature]
                        # Popularity of the feature as a discriminator
                        wordIsDiscrminatedByFeature[selectedFeature].add(owner)
                        # if lemme in verboseLemmes and lemmeWords[0].ortho in verboseWords:
                        #     print(f"Word {owner.ortho} of lemme {lemme} is discriminated by feature {selectedFeature}")

                        # Other words that are discriminated from this word by its feature
                        otherWords = list(filter(lambda w: w != owner, lemmeWords))
                        for w in otherWords:
                            wordIsDiscrminatedFromByFeature[selectedFeature].add(w)
                            # if w.lemme in verboseLemmes and lemmeWords[0].ortho in verboseWords:
                            #     print(f"    Word {w.ortho} of lemme {lemme} is discriminated from {wordsUsing[0].ortho} by feature {selectedFeature}")


    # Sort features by their popularity as discriminators
    wordIsDiscrminatedByFeature = {
        feature:words for feature, words in sorted(wordIsDiscrminatedByFeature.items(),
                                                   key=lambda item: len(item[1]), reverse=True)
    }

    print("\nNumber of words without homphones sharing their lemme: %d / %d"%(len(strokeLemmeSingleWords), len(allWords)))
    print("\nMost popular discriminating features:")
    print("\n".join([f"{feature:>25}: discriminate {len(words)} words" +
                     f" from {len(wordIsDiscrminatedFromByFeature[feature])} other words sharing the same lemme." +
                     f" A total of {len(wordsUsingFeature[feature])} words have this feature"
                        for feature, words in list(wordIsDiscrminatedByFeature.items())[:5]]))

    # The greedy part : Go through the features from the currently more impactfull to the least.
    orderedFeaturesSelected: list[WordFeature] = []
    leftOverDiscriminatedFrom: dict[WordFeature, set[Word]] =  {f:set() for f in wordIsDiscrminatedFromByFeature} #deepcopy(wordIsDiscrminatedByFeature)
    for fi in range(len(wordIsDiscrminatedByFeature)):
        # Features not yet used to discriminate a word
        leftOverFeatures = {
            feature: words for feature, words in wordIsDiscrminatedByFeature.items()
            if feature not in orderedFeaturesSelected
        }
        # Remove words that are already discriminated by a previously selected feature
        for preselectedFeature in orderedFeaturesSelected:
            leftOverFeatures = {
                feature: words for feature, words in leftOverFeatures.items()
                if feature is not preselectedFeature
            }
        sortedLeftOverFeatures= {
            feature:words for feature, words in sorted(leftOverFeatures.items(),
                                     key=lambda item: (_featureComplexity(item[0]), -len(item[1])))
        }
        # Greedy pick the best feature
        selectedFeature, selectedWords = list(sortedLeftOverFeatures.items())[0]
        # Update stats of discriminated words
        for preselectedFeature in [orderedFeaturesSelected[-1]] if len(orderedFeaturesSelected) > 0 else []:
            for feature, words in leftOverDiscriminatedFrom.items():
                                       # desc=f"Removing words already discriminated by {preselectedFeature}",
                                       # unit=" features", ascii=True, ncols=100):

                leftOverDiscriminatedFrom[feature] = set()
                for word in words:
                    leftOverDiscriminatedFrom[feature].add(word) if word not in wordIsDiscrminatedFromByFeature[preselectedFeature] else None

        orderedFeaturesSelected.append(selectedFeature)
        print(f"{fi+1}. Feature:{selectedFeature:>25}: discriminates {len(selectedWords):>4}" +
              f" from {len(leftOverDiscriminatedFrom[selectedFeature])} other words sharing the same lemme." +
              f" A total of {len(set(wordsUsingFeature[selectedFeature]))} words have this feature")

    #print(orderedFeaturesSelected)
    return wordIsDiscrminatedByFeature, orderedFeaturesSelected, strokeLemmeDiscriminators


def buildFeasibleDiscriminatorOptions(
        theory: dict[Strokes, list[Word]],
        wordIsDiscrminatedByFeature: dict[WordFeature, set[Word]]
    ) -> dict[tuple[Strokes, LemmeGramCat], dict[Word, set[WordFeature]]]:
    """
    For every homophone group that needs discrimination (multiple words sharing the same
    lemme within a stroke), list every feature that can, on its own, discriminate each word
    from the others sharing that lemme.

    Unlike greedyOptimizeDiscriminator, which commits to a single feature-priority order and
    therefore a single assignment, this returns the full feasible search space per group and
    per word. A global optimizer (`selectSharedDiscriminators`, below) can then pick one feasible
    feature per word across all groups so as to minimize the total number of distinct features
    used, instead of being locked into whichever feature happens to come first in a fixed order.

    Cost is O(groups x words_per_group x features), not O(words_sharing_a_feature^2): no pair
    of words is ever enumerated, so a feature shared by thousands of unrelated lemmes (e.g. a
    plural marker) costs no more than a feature used by two.
    """
    groupFeasibleFeatures: dict[tuple[Strokes, LemmeGramCat], dict[Word, set[WordFeature]]] = {}
    for strokes, selectedWords in theory.items():
        wordByLemme: dict[LemmeGramCat, list[Word]] = groupWordsByLemme(selectedWords)
        for lemme, lemmeWords in wordByLemme.items():
            # Only interested in discriminating features if there are multiple words for the same lemme
            if len(lemmeWords) <= 1:
                continue
            wordFeasibleFeatures: dict[Word, set[WordFeature]] = {
                word: {
                    feature for feature, discriminatedWords in wordIsDiscrminatedByFeature.items()
                    if word in discriminatedWords
                } for word in lemmeWords
            }
            groupFeasibleFeatures[(strokes, lemme)] = wordFeasibleFeatures
    return groupFeasibleFeatures


def selectSharedDiscriminators(
        groupFeasibleFeatures: dict[tuple[Strokes, LemmeGramCat], dict[Word, set[WordFeature]]]
    ) -> tuple[dict[Word, WordFeature], set[Word]]:
    """
    Shared-discriminator selection (a greedy set-cover) over buildFeasibleDiscriminatorOptions's output: repeatedly picks the
    feature that resolves the most still-unresolved words across all groups at once, so a
    feature already justified for one lemma gets reused for another instead of a new one
    being introduced. Words with no feasible feature are returned unresolved (mirrors
    greedyOptimizeDiscriminator's "nofeature" fallback) instead of being silently dropped.

    Within each group, words sharing an orthography (true homographs, or a same-lemma form
    that simply writes the same as another) are collected into a homograph group before
    covering: they write identical text, so only one of them needs to actually own a
    discriminating stroke. This mirrors greedyOptimizeDiscriminator's same-ortho collapse (it
    drops the other words sharing an ortho once one of them is assigned a feature). A homograph
    group's feasible set is the union of its members'; once a feature is chosen for the group,
    it's attributed to whichever member natively carries it in its own feasible set (its
    "owner" -- unique per homograph group by construction, see extractDiscriminatingFeatures's
    owner-picking logic) and the other members get nothing. A homograph group whose union is
    empty leaves *all* its members unresolved.
    """
    homographGroupFeasible: dict[tuple[tuple[Strokes, LemmeGramCat], WordOrtho], set[WordFeature]] = {}
    homographGroupMembers: dict[tuple[tuple[Strokes, LemmeGramCat], WordOrtho], list[Word]] = {}
    for groupKey, wordFeasibleFeatures in groupFeasibleFeatures.items():
        homographGroups: dict[WordOrtho, list[Word]] = defaultdict(list)
        for word in wordFeasibleFeatures:
            homographGroups[word.ortho].append(word)
        for ortho, members in homographGroups.items():
            homographGroupKey = (groupKey, ortho)
            homographGroupMembers[homographGroupKey] = members
            homographGroupFeasible[homographGroupKey] = set().union(*(wordFeasibleFeatures[m] for m in members))

    unresolved: dict[tuple[tuple[Strokes, LemmeGramCat], WordOrtho], set[WordFeature]] = dict(homographGroupFeasible)
    chosen: dict[Word, WordFeature] = {}
    while True:
        featureCounts: dict[WordFeature, int] = defaultdict(int)
        for features in unresolved.values():
            for feature in features:
                featureCounts[feature] += 1
        if not featureCounts:
            break
        # Prefer the feature covering the most still-unresolved homograph groups (a true
        # greedy set-cover, coverage-first); break ties by simplicity
        # (fewest ':'/'_' components), then by name.
        bestFeature = min(sorted(featureCounts),
                           key=lambda feature: (-featureCounts[feature], _featureComplexity(feature)))
        resolvedHomographGroups = [
            homographGroupKey for homographGroupKey, features in unresolved.items() if bestFeature in features
        ]
        for homographGroupKey in resolvedHomographGroups:
            groupKey, _ortho = homographGroupKey
            owner = next(m for m in homographGroupMembers[homographGroupKey]
                         if bestFeature in groupFeasibleFeatures[groupKey][m])
            chosen[owner] = bestFeature
            del unresolved[homographGroupKey]

    unresolvedWords: set[Word] = {
        word for homographGroupKey in unresolved for word in homographGroupMembers[homographGroupKey]
    }
    return chosen, unresolvedWords


def buildDiscriminatorSelection(
        theory: dict[Strokes, list[Word]],
        wordIsDiscrminatedByFeature: dict[WordFeature, set[Word]] | None = None,
    ) -> dict[tuple[WordFeature, ...], list[tuple[Word, ...]]]:
    """
    Single entry point for the adaptive, redundancy-free discriminator selection
    (buildFeasibleDiscriminatorOptions + selectSharedDiscriminators), reshaped into the same
    dict[tuple[WordFeature, ...], list[tuple[Word, ...]]] shape the retired greedy
    discriminator optimizer produced, so every downstream consumer (the verb-paradigm
    tooling) shares one selection instead of each re-deriving its own.

    Pass an already-computed wordIsDiscrminatedByFeature (extractDiscriminatingFeatures's
    first return value) when the caller already has one, to avoid a redundant full-corpus
    re-scan; otherwise it's computed here.
    """
    if wordIsDiscrminatedByFeature is None:
        wordIsDiscrminatedByFeature, _orderedFeatures, _strokeLemmeDiscriminators = \
            extractDiscriminatingFeatures(theory)

    groupFeasibleFeatures = buildFeasibleDiscriminatorOptions(theory, wordIsDiscrminatedByFeature)
    sharedChosen, sharedUnresolved = selectSharedDiscriminators(groupFeasibleFeatures)

    featuresetWords: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]] = {}
    for wordFeasibleFeatures in groupFeasibleFeatures.values():
        selectedFeatureWord: list[tuple[WordFeature, Word]] = []
        for word in wordFeasibleFeatures:
            if word in sharedChosen:
                selectedFeatureWord.append((sharedChosen[word], word))
            elif word in sharedUnresolved:
                selectedFeatureWord.append(("nofeature", word))
            # else: a same-ortho sibling collapsed into its homograph group's owner -- write
            # nothing, mirroring greedyOptimizeDiscriminator's same-ortho collapse.
        if not selectedFeatureWord:
            continue
        featureSet = tuple(fw[0] for fw in selectedFeatureWord)
        featuresetWords[featureSet] = featuresetWords.get(featureSet, []) + \
            [tuple(fw[1] for fw in selectedFeatureWord)]

    return {
        fs: ws for fs, ws in sorted(featuresetWords.items(), key=lambda item: len(item[1]), reverse=True)
    }


