"""Prototype: output-preserving speedup of extractDiscriminatingFeatures (S2 slowdown).
Generated from src/featureextractor.py by rewriting the per-group feature scan (lines 72-88).
Usage: PYTHONHASHSEED=0 env/bin/python scratch/perf_extract_fast.py
"""
import contextlib, hashlib, io, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.featureextractor import *  # noqa
from src.featureextractor import extractDiscriminatingFeatures, groupWordsByLemme, verboseLemmes, verboseWords, _featureComplexity
import src.featureextractor as _fe
globals().update({k: v for k, v in vars(_fe).items() if not k.startswith("__")})


def extractDiscriminatingFeaturesFast(theory: dict[Strokes, list[Word]]) \
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
            # List of Words that have a certain feature
            groupFeatures = set().union(*(wordFeatureSets[w] for w in lemmeWords))
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
                print("lemmeOrthoFeatures: ", [(f, sum(map(len, d.values()))) for f, d in lemmeOrthoFeatures.items()])

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


def _wk(w):
    return [w.ortho, w.phonology, w.lemme, w.gramCat.name, w.gender, w.number, w.infoVerb or ""]


def _digest(res):
    discBy, ordered, sld = res
    obj = [[[f, [_wk(w) for w in ws]] for f, ws in discBy.items()], ordered,
           [[str(s), l, [[_wk(w), fs] for w, fs in byW.items()]] for (s, l), byW in sld.items()]]
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


def _run(fn, theory):
    t = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        res = fn(theory)
    return time.perf_counter() - t, res


if __name__ == "__main__":
    from util.completeVerbParadigms import loadTheoryAndKeyboard
    theory, _ = loadTheoryAndKeyboard()
    dt, res = _run(extractDiscriminatingFeatures, theory)
    d0 = _digest(res); del res
    print(f"original  {dt:7.1f}s  digest {d0}", flush=True)
    dt, res = _run(extractDiscriminatingFeaturesFast, theory)
    d1 = _digest(res); del res
    print(f"fast      {dt:7.1f}s  digest {d1}", flush=True)
    print("IDENTICAL (raw order)" if d0 == d1 else "DIFFERENT", flush=True)
