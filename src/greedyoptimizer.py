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

def getAmbiguousMultiphonemes(theory: dict[tuple[tuple[int, ...], ...], list[Word]],
                              keyboard: Keyboard) -> dict[str, list[Word]]:

    ambiguousMultiphonemes: dict[str, list[Word]]= {}
    for strokes, words in theory.items():
        if len(words) > 1:
            phonemesPressed: str = keyboard.strokesToString(strokes)
            ambiguousMultiphonemes[phonemesPressed] = words
    return ambiguousMultiphonemes

def optimizeTheory(theory: dict[Strokes, list[Word]], keyboard: Keyboard) \
        -> dict[Strokes, dict[str, dict[str, list[tuple[Word, list[str]]]]]]:
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
        for feature in word.getFeatures():
            allFeatures.add(feature)
            wordFeatures[word] = wordFeatures.get(word, []) + [feature]

    # Words for which the feature is present
    wordsUsingFeature: dict[str, list[Word]] = {feature: [] for feature in list(allFeatures)}
    # List (for each word) of list of features (str) for which each feature is a word 
    # discriminator in the group of homophone words sharing the samme lemme
    strokeLemmeDiscriminators: dict[tuple[Strokes, str], dict[Word, list[str]]] = {}
    wordIsDiscrminatedByFeature: dict[str, list[Word]] = {feature: [] for feature in list(allFeatures)}
    wordIsDiscrminatedFromByFeature: dict[str, list[Word]] = {feature: [] for feature in list(allFeatures)}



    # wordDiscriminatedBy: dict[Word, list[IntVar]] = {
    #     word:[] for words in theory.values() for word in words}
    # wordIsDiscrminated: dict[Word, IntVar] = {}
    # orthoDiscriminatedBy: dict[tuple[str, str], list[IntVar]] = {}
    # orthoIsDiscrminated: dict[tuple[str, str], IntVar] = {}
        
    for strokes, words in tqdm(theory.items(), desc="Scaning discriminating features",
                               unit=" homophones", ascii=True, ncols=100):
        # Split homophone word group by lemme
        wordByLemme: dict[str, list[Word]] = {word.lemme:[] for word in words}
        for word in words:
            wordByLemme[word.lemme].append(word)

        # Discriminate homophones words sharing the same lemme
        for lemme, lemmeWords in wordByLemme.items():
            phonemesPressed: str = keyboard.strokesToString(strokes)
            lemmeWordFeatures = {
                feature: list(filter(lambda w: feature in wordFeatures[w], lemmeWords)) 
                for feature in allFeatures }

            for feature, wordsUsing in lemmeWordFeatures.items():
                if len(wordsUsing) > 0:
                    # Popularity of the feature
                    wordsUsingFeature[feature] += wordsUsing
                if len(wordsUsing) == 1:
                    # This is a discriminating feature for this word
                    wordFeatureDict = strokeLemmeDiscriminators.get((strokes, lemme), {wordsUsing[0]: []})
                    wordFeatureDict[wordsUsing[0]] += [feature]
                    strokeLemmeDiscriminators[(strokes, lemme)] = wordFeatureDict
                    # Popularity of the feature as a discriminator
                    wordIsDiscrminatedByFeature[feature] += [wordsUsing[0]]
                    
                    # Other words that are discriminated from this word by its feature
                    otherWords = list(filter(lambda w: w != wordsUsing[0], lemmeWords))
                    wordIsDiscrminatedFromByFeature[feature] += otherWords


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
