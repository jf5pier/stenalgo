#!/usr/bin/python
# coding: utf-8
#
from src.keyboard import Keyboard, Strokes
from src.word import Word, WordFeature, LemmeGramCat, WordOrtho
from tqdm import tqdm
from collections import defaultdict

verboseLemmes: list[str] = [] # ["fait", "faire"]
verboseWords: list[str] = [] # ["fais", "fait", "faits", "faites"]

def greedyOptimizeDiscriminator (
        theory: dict[Strokes, list[Word]],
        wordIsDiscrminatedByFeature: dict[WordFeature, set[Word]],
        orderedFeaturesSelected: list[WordFeature]
    ) -> dict[tuple[WordFeature, ...], list[tuple[Word, ...]]]:
    """
    """
    featuresetWords: dict[tuple[WordFeature, ...], list[tuple[Word, ...]]] = {}
    for strokes, selectedWords in tqdm(theory.items(), desc="Grouping words by feature set",
                               unit=" homophones", ascii=True, ncols=100):
        # Split homophone word group by lemme
        wordByLemme: dict[LemmeGramCat, list[Word]] = {word.lemmeGramCat:[] for word in selectedWords}
        for word in selectedWords:
            wordByLemme[word.lemmeGramCat].append(word)

        # Discriminate homophones words sharing the same lemme
        for lemme, lemmeWords in wordByLemme.items():
            if lemme in verboseLemmes and lemmeWords[0].ortho in verboseWords:
                print(strokes, "\n   ",  [w.ortho for w in selectedWords])
                print("   ", [w.ortho for w in lemmeWords])
                for w in selectedWords:
                    print(w.ortho, "\n   ", w.getFeatures())
                # sys.exit(1)
            # Only interested in discriminating features if there are multiple words for the same lemme
            if len(lemmeWords) > 1:
                selectedFeatureWord: list[tuple[WordFeature, Word]] = []
                wordsToAssignToFeature: list[Word] = lemmeWords[:]
                possibleFeatures = orderedFeaturesSelected[:]
                while len(wordsToAssignToFeature) > 0:
                    if len(possibleFeatures) == 0:
                        # Ran out of features to try
                        while(len(wordsToAssignToFeature) > 0):
                            word = wordsToAssignToFeature.pop(0)
                            selectedFeatureWord.append(("nofeature", word))
                            if lemme in verboseLemmes and lemmeWords[0].ortho in verboseWords:
                                print("   !No feature found for word", word.ortho)
                        continue
                    # Go through the features from the most popular to the least
                    feature = possibleFeatures.pop(0)
                    for wi, word in enumerate(wordsToAssignToFeature):
                        if word in wordIsDiscrminatedByFeature[feature]:
                            selectedFeatureWord.append((feature, word))
                            _ = wordsToAssignToFeature.pop(wi)
                            # Other words sharing the same orthograph are also discriminated by the more popular feature
                            # Remove them from the list of words to assign to a feature
                            wordsToAssignToFeature = [w for w in wordsToAssignToFeature
                                if w.ortho != word.ortho]
                            break
                featureSet: tuple[WordFeature, ...] = tuple(fw[0] for fw in selectedFeatureWord)
                featuresetWords[featureSet] = featuresetWords.get(featureSet, []) \
                    + [tuple(fw[1] for fw in selectedFeatureWord)]

    featuresetWords = {
        fs:ws for fs, ws in sorted(featuresetWords.items(), key=lambda item: len(item[1]),
                                   reverse=True)
    }
    
    print(f"{len(featuresetWords)} different feature sets found.")
    for f1, (featureset, words) in list(enumerate(featuresetWords.items()))[:20]:
        if True: #"nofeature" in featureset:
            print(f"{f1}. Feature set is used to discriminate {len(words)} words:")
            print(f"".join([f"{f:>15} " for f in featureset]))
            debugFeatureNb = 9
            #nbPrint = -1 if f1 == debugFeatureNb else 5
            nbPrint = 5
            grepWords: list[str] = []
            for wordTuple in words[:nbPrint]:
                if f1 == 9 :
                    grepWords += [wordTuple[-1].ortho]
                    orthoER = wordTuple[-1].ortho
                    orthoEZ: WordOrtho = orthoER[:-1] + "z"
                    #print(f"untracked_src/copyLineFromTo.py resources/Lexique383.tsv 2 0 3 {orthoER} VER {orthoEZ} VER 6 1 17 22 23 24 26")
                    #print(f"untracked_src/copyLineFromTo.py resources/LexiqueInfraCorrespondance.tsv 2 0 2 {orthoER} VER {orthoEZ} VER 3 1 -4 5")
                #else :
                print(f"".join([f"{word.ortho:>15} " for word in wordTuple]))
            #print("egrep \"" + "|".join([f"^{w[:-1]}[rz]\\b" for w in grepWords]) +'"')

            #        "  ", 'egrep "' + "|".join([f"^{w.ortho}\\b" for w in wordTuple]) +'"')
            # print('egrep "' + "|".join([f"^{w.ortho}\\b" for wordTuple in words for w in wordTuple]) +'"')

    # print("Most popular features:")
    # print("\n".join([f"{feature}: {len(words)} words" for feature, words in sorted(wordsUsingFeature.items(), key=lambda item: len(item[1]), reverse=True)]))

    return featuresetWords
