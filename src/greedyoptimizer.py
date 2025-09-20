#!/usr/bin/python
# coding: utf-8
#
import atexit
from ortools.sat.python.cp_model import IntVar
from ortools.sat.python import cp_model
from src.keyboard import Keyboard, Strokes
from src.grammar import Phoneme, Syllable
from src.word import Word, GramCat
from src.cpsatprinter import SolutionPrinter
from tqdm import tqdm
from itertools import combinations
from copy import deepcopy


def getAmbiguousMultiphonemes(theory: dict[tuple[tuple[int, ...], ...], list[Word]],
                              keyboard: Keyboard) -> dict[str, list[Word]]:

    ambiguousMultiphonemes: dict[str, list[Word]]= {}
    for strokes, words in theory.items():
        if len(words) > 1:
            phonemesPressed: str = keyboard.strokesToString(strokes)
            ambiguousMultiphonemes[phonemesPressed] = words
    return ambiguousMultiphonemes

def extractDiscriminatingFeatures(theory: dict[Strokes, list[Word]]) \
        -> tuple[dict[str, set[Word]], list[str]]:
    """
    """

    wordFeatures: dict[Word, list[str]] = {}
    lemmes: set[str] = set()
    for lemme in tqdm([word.lemme for words in theory.values() for word in words],
                      desc="Collecting lemmes", unit=" word", ascii=True, ncols=100):
        lemmes.add(lemme)

    allFeatures: set[str] = set()
    for word in tqdm([word for words in theory.values() for word in words],
                      desc="Collecting word features", unit=" word", ascii=True, ncols=100):
        for selectedFeature in word.getFeatures():
            allFeatures.add(selectedFeature)
            wordFeatures[word] = wordFeatures.get(word, []) + [selectedFeature]

    # Words for which the feature is present
    wordsUsingFeature: dict[str, list[Word]] = {feature: [] for feature in list(allFeatures)}
    # List (for each word) of list of features (str) for which each feature is a word 
    # discriminator in the group of homophone words sharing the samme lemme
    strokeLemmeDiscriminators: dict[tuple[Strokes, str], dict[Word, list[str]]] = {}
    wordIsDiscrminatedByFeature: dict[str, set[Word]] = {feature: set() for feature in list(allFeatures)}
    wordIsDiscrminatedFromByFeature: dict[str, set[Word]] = {feature: set() for feature in list(allFeatures)}

    nbDiscriminatorsOfWord: dict[Word, int] = {word: 0 for words in theory.values() for word in words}
    allWords: list[Word] = sorted(list(set(word for words in theory.values() for word in words)), key=lambda w: w.ortho)

    strokeLemmeSingleWords: dict[tuple[Strokes, str], Word] = {}

    for strokes, selectedWords in tqdm(theory.items(), desc="Scaning discriminating features",
                               unit=" homophones", ascii=True, ncols=100):
        # Split homophone word group by lemme
        wordByLemme: dict[str, list[Word]] = {word.lemme:[] for word in selectedWords}
        for word in selectedWords:
            wordByLemme[word.lemme].append(word)

        # Discriminate homophones words sharing the same lemme
        for lemme, lemmeWords in wordByLemme.items():
            lemmeWordFeatures = {
                feature: list(filter(lambda w: feature in wordFeatures[w], lemmeWords)) 
                for feature in allFeatures }
            if len(lemmeWords) == 1:
                strokeLemmeSingleWords[(strokes, lemme)] = lemmeWords[0]

            strokeLemmeDiscriminators[(strokes,lemme)] = {}
            for selectedFeature, wordsUsing in lemmeWordFeatures.items():
                if len(wordsUsing) > 0:
                    # Popularity of the feature
                    wordsUsingFeature[selectedFeature] += wordsUsing
                if len(wordsUsing) == 1:
                    # This is a discriminating feature for this word
                    wordsFeatureDict = strokeLemmeDiscriminators[(strokes, lemme)]
                    wordFeatureDict = wordsFeatureDict.get(wordsUsing[0], [])
                    wordFeatureDict += [selectedFeature]
                    strokeLemmeDiscriminators[(strokes, lemme)][wordsUsing[0]] = wordFeatureDict
                    # Popularity of the feature as a discriminator
                    wordIsDiscrminatedByFeature[selectedFeature].add(wordsUsing[0])
                    
                    # Other words that are discriminated from this word by its feature
                    otherWords = list(filter(lambda w: w != wordsUsing[0], lemmeWords))
                    for w in otherWords:
                        wordIsDiscrminatedFromByFeature[selectedFeature].add(w)


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
    orderedFeaturesSelected: list[str] = []
    leftOverDiscriminatedFrom: dict[str, set[Word]] =  {f:set() for f in wordIsDiscrminatedFromByFeature} #deepcopy(wordIsDiscrminatedByFeature)
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
                                     key=lambda item: len(item[1]), reverse=True)
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

    print(orderedFeaturesSelected)
    return wordIsDiscrminatedByFeature, orderedFeaturesSelected

def greedyOptimizeDiscriminator (
        theory: dict[Strokes, list[Word]],
        wordIsDiscrminatedByFeature: dict[str, list[Word]],
        orderedFeaturesSelected: list[str], keyboard: Keyboard
    ) -> dict[Strokes, dict[str, dict[str, list[tuple[Word, list[str]]]]]]:
    """
    """
    featuresetWords: dict[tuple[str, ...], list[tuple[Word, ...]]] = {}
    for strokes, selectedWords in tqdm(theory.items(), desc="Grouping words by feature set",
                               unit=" homophones", ascii=True, ncols=100):
        # Split homophone word group by lemme
        wordByLemme: dict[str, list[Word]] = {word.lemme:[] for word in selectedWords}
        for word in selectedWords:
            wordByLemme[word.lemme].append(word)

        # Discriminate homophones words sharing the same lemme
        for lemme, lemmeWords in wordByLemme.items():
            # Only interested in discriminating features if there are multiple words for the same lemme
            if len(lemmeWords) > 1:
                selectedFeatureWord: list[tuple[str, Word]] = []
                wordsToAssignToFeature: list[Word] = lemmeWords[:]
                possibleFeatures = orderedFeaturesSelected[:]
                while len(wordsToAssignToFeature) > 0:
                    if len(possibleFeatures) == 0:
                        # Ran out of features to try
                        while(len(wordsToAssignToFeature) > 0):
                            word = wordsToAssignToFeature.pop(0)
                            selectedFeatureWord.append(("nofeature", word))
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
                featureSet: tuple[str, ...] = tuple(fw[0] for fw in selectedFeatureWord)
                featuresetWords[featureSet] = featuresetWords.get(featureSet, []) \
                    + [tuple(fw[1] for fw in selectedFeatureWord)]

    featuresetWords = {
        fs:ws for fs, ws in sorted(featuresetWords.items(), key=lambda item: len(item[1]),
                                   reverse=True)
    }
    for f1, (featureset, words) in enumerate(featuresetWords.items()):
        print(f"{f1}. Feature set is used to discriminate {len(words)} words:")
        print(f"".join([f"{f:>15}" for f in featureset]))
        for wordTuple in words[:2]:
            print(f"".join([f"{word.ortho:>15}" for word in wordTuple]))

                    

    # print("Most popular features:")
    # print("\n".join([f"{feature}: {len(words)} words" for feature, words in sorted(wordsUsingFeature.items(), key=lambda item: len(item[1]), reverse=True)]))


    # print(f"Status : {status}")
    # print(solver.StatusName(status))
    # if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    #     print(f'Total penalty = {solver.ObjectiveValue():,}')
    #     printer.on_solution_callback()
    #     print("Feature discriminating")
    #     selectedFeatures = []
    #     for feature, boolVar in featuresBoolVar.items() :
    #         if solver.Value(boolVar):
    #             print(feature)
    #             selectedFeatures.append(feature)
    #     for feature, boolVar in featurePairsBoolVar.items() :
    #         if solver.Value(boolVar):
    #             print(feature)
    #             selectedFeatures.append(feature)
    #     augmentedTheory: dict[Strokes, dict[str, dict[str, list[tuple[Word, list[str]]]]]] = {}
    #     for strokes, words in tqdm(theory.items(), desc="Scaning discriminating features",
    #                             unit=" homophones", ascii=True, ncols=100):
    #         # Split by lemme
    #         wordByLemme: dict[str, list[Word]] = {word.lemme:[] for word in words}
    #         for word in words:
    #             wordByLemme[word.lemme].append(word)
    #         phonemesPressed: str = keyboard.strokesToString(strokes)
    #         augmentedTheory[strokes] = {}
    #
    #         # Discriminate homophones words sharing the same lemme
    #         for lemme, lemmeWords in wordByLemme.items():
    #             augmentedTheory[strokes][lemme] = {}
    #             orthosOfLemme =list(set(word.ortho for word in lemmeWords))
    #             if len(lemmeWords) == 1:
    #                 print(f"{phonemesPressed}, {lemmeWords[0].ortho} -> (single word for lemme {lemme})")
    #                 augmentedTheory[strokes][lemme][lemmeWords[0].ortho] = [(lemmeWords[0], [])]
    #             else :
    #                 for word in lemmeWords:
    #                     discrimOfWord = list(filter(lambda feature: solver.Value(feature) == 1, wordDiscriminatedBy[word]))
    #                     discrimOfWord = [var.Name().split("_discriminated_by_")[-1] for var in discrimOfWord]
    #
    #                     at = augmentedTheory[strokes][lemme].get(word.ortho, [])
    #                     at.append((word, discrimOfWord))
    #                     augmentedTheory[strokes][lemme][word.ortho] = at
    #                     selectedDiscrim = list(filter(lambda feature: feature in selectedFeatures, discrimOfWord))
    #                     print(f"{phonemesPressed}, {word.ortho} of lemme {lemme} -> discriminated by {discrimOfWord}, selected {selectedDiscrim}")
    #     return augmentedTheory

    return {}
