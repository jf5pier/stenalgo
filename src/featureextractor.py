#!/usr/bin/python
# coding: utf-8
#
from src.keyboard import Keyboard, Strokes
from src.word import Word
from tqdm import tqdm
from collections import defaultdict

verboseLemmes: list[str] = [] # ["fait", "faire"]
verboseWords: list[str] = [] # ["fais", "fait", "faits", "faites"]
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
    for lemme in tqdm([word.lemmeGramCat for words in theory.values() for word in words],
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
    orthosUsingFeature: dict[str, dict[str, list[Word]]] = {feature: defaultdict(list) for feature in list(allFeatures)}
    # List (for each word) of list of features (str) for which each feature is a word 
    # discriminator in the group of homophone words sharing the samme lemme
    strokeLemmeDiscriminators: dict[tuple[Strokes, str], dict[Word, list[str]]] = defaultdict(lambda: defaultdict(list))
    wordIsDiscrminatedByFeature: dict[str, set[Word]] = {feature: set() for feature in list(allFeatures)}
    wordIsDiscrminatedFromByFeature: dict[str, set[Word]] = {feature: set() for feature in list(allFeatures)}

    nbDiscriminatorsOfWord: dict[Word, int] = {word: 0 for words in theory.values() for word in words}
    allWords: list[Word] = sorted(list(set(word for words in theory.values() for word in words)), key=lambda w: w.ortho)

    strokeLemmeSingleWords: dict[tuple[Strokes, str], Word] = {}

    for strokes, selectedWords in tqdm(theory.items(), desc="Scaning discriminating features",
                               unit=" homophones", ascii=True, ncols=100):
        # Split homophone word group by lemme
        wordByLemme: dict[str, list[Word]] = {word.lemmeGramCat:[] for word in selectedWords}
        for word in selectedWords:
            wordByLemme[word.lemmeGramCat].append(word)

        # Discriminate homophones words sharing the same lemme
        for lemme, lemmeWords in wordByLemme.items():
            # List of Words that have a certain feature
            lemmeWordFeatures = {
                feature: list(filter(lambda w: feature in wordFeatures[w], lemmeWords)) 
                for feature in allFeatures }

            # List of Words that either have a certain feature, or a Word with the same orthograph does
            lemmeOrthoWordFeatures: dict[str, list[Word]] = {
                feature: list(filter( lambda w: feature in wordFeatures[w] or
                    any((feature in wordFeatures[ow] and ow.ortho == w.ortho) for ow in lemmeWords),
                    lemmeWords)) for feature in allFeatures }

            # Dictionnary of word orthographs and their list of Words for which the feature is present
            lemmeOrthoFeatures: dict[str, dict[str, list[Word]]] = {
                feature: {
                    ortho: list(filter(lambda w: w.ortho == ortho, wordsUsing))
                    for ortho in set(w.ortho for w in wordsUsing)
                } for feature, wordsUsing in lemmeOrthoWordFeatures.items()
            }

            if lemme in verboseLemmes and lemmeWords[0].ortho in verboseWords:
                print("Extract strokes", strokes, " lemme ", lemme, [w.ortho for w in lemmeWords])
                print("lemmeWordFeatures: ",list(filter(lambda x: x[1]>0, [(f,len(lemmeWordFeatures[f])) for f in lemmeWordFeatures])))
                print("lemmeOrthoWordFeatures: ",list(filter(lambda x: x[1]>0,  [(f,len(lemmeOrthoWordFeatures[f])) for f in lemmeWordFeatures])))

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
                        # This is a discriminating feature for this word orthograph
                        # wordsFeatureDict = strokeLemmeDiscriminators[(strokes, lemme)]
                        # wordFeatureDict = wordsFeatureDict.get(wordsUsing[0], [])
                        # wordFeatureDict += [selectedFeature]
                        strokeLemmeDiscriminators[(strokes, lemme)][wordsUsing[0]] += [selectedFeature]
                        # Popularity of the feature as a discriminator
                        wordIsDiscrminatedByFeature[selectedFeature].add(wordsUsing[0])
                        # if lemme in verboseLemmes and lemmeWords[0].ortho in verboseWords:
                        #     print(f"Word {wordsUsing[0].ortho} of lemme {lemme} is discriminated by feature {selectedFeature}")
                        
                        # Other words that are discriminated from this word by its feature
                        otherWords = list(filter(lambda w: w != wordsUsing[0], lemmeWords))
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

    #print(orderedFeaturesSelected)
    return wordIsDiscrminatedByFeature, orderedFeaturesSelected


