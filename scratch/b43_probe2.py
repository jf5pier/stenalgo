"""B43 probe 2: localize the seed divergence INSIDE the augmented pass.

Phase --dump-candidates (run once, seed 0): computes structuralCandidates the
normal way and pickles them (they are seed-stable -- proven by probe 1).
Phase default: loads theory + the pickled candidates, enters
temporarilyAugmented, and digests, in order:
  A  the augmented theory's word lists (append order check)
  B1 extractDiscriminatingFeatures(theory): discBy canon/raw, ordered canon
  C  buildFeasibleDiscriminatorOptions output (canon)
  D  selectSharedDiscriminators output: chosen (canon) + unresolved count
  E  buildDiscriminatorSelection output: featuresetWords raw/canon + top
     colliding keys (the ("nofeature",) mega-key check)
Run under PYTHONHASHSEED=0 and 1 and diff.
"""
import gc
import hashlib
import json
import os
import pickle
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CANDIDATES_PATH = os.environ.get("B43_CANDIDATES", "scratch/b43-candidates.pickle")
t0 = time.perf_counter()


def _wordKey(w):
    return [w.ortho, w.phonology, w.lemme, w.gramCat.name, w.gender, w.number,
            w.infoVerb or "", w.rawSyllCV, w.rawOrthosyllCV]


def digest(name, obj):
    raw = json.dumps(obj, ensure_ascii=False, default=str)
    print(f"DIGEST {name:34} {hashlib.sha256(raw.encode()).hexdigest()[:16]}", flush=True)


def _canon(items):
    return sorted(items, key=lambda x: json.dumps(x, ensure_ascii=False, default=str))


def stage(name):
    print(f"### STAGE {name} [{time.perf_counter() - t0:7.1f}s]", flush=True)


def main() -> None:
    dump = "--dump-candidates" in sys.argv
    from util.completeVerbParadigms import (
        EXCEPTIONS_PATH, VERBISTE_CONJUGATIONS_PATH, VERBISTE_VERBS_PATH,
        findStructuralCandidates, loadTheoryAndKeyboard, temporarilyAugmented,
    )
    from src.featureextractor import (
        buildDiscriminatorSelection, buildFeasibleDiscriminatorOptions,
        extractDiscriminatingFeatures, selectSharedDiscriminators,
    )
    from src.verbparadigm import (
        ConjugationEndingTables, crossLemmaFeatureSetCollisions,
        deriveConjugationEndingTables, loadVerbModelExceptions,
        loadVerbisteTemplates, parseConjugationTemplates,
    )

    theory, _ = loadTheoryAndKeyboard()
    if dump:
        templates = loadVerbisteTemplates(VERBISTE_VERBS_PATH)
        exceptions = loadVerbModelExceptions(EXCEPTIONS_PATH)
        conjugations = parseConjugationTemplates(VERBISTE_CONJUGATIONS_PATH)
        discBy, _, sld = extractDiscriminatingFeatures(theory)
        tables = deriveConjugationEndingTables(theory, templates, exceptions)
        candidates, _ = findStructuralCandidates(
            sld, theory, templates, exceptions, conjugations, tables)
        # Words are picklable dataclasses; keep (lgc, template, missingFeatures,
        # siblings) lightweight by rebuilding UndersampledLemma on load.
        payload = [(_lgc, info.template, sorted(info.missingFeatures),
                    sorted(info.siblingLemmeGramCats), gen, ref)
                   for _lgc, info, gen, ref in candidates]
        with open(CANDIDATES_PATH, "wb") as f:
            pickle.dump(payload, f)
        print(f"dumped {len(candidates)} candidates to {CANDIDATES_PATH}", flush=True)
        return

    from src.verbparadigm import UndersampledLemma
    with open(CANDIDATES_PATH, "rb") as f:
        payload = pickle.load(f)
    candidates = [
        (lgc, UndersampledLemma(lemmeGramCat=lgc, template=template,
                                missingFeatures=frozenset(missing),
                                siblingLemmeGramCats=frozenset(siblings)),
         gen, ref)
        for lgc, template, missing, siblings, gen, ref in payload
    ]
    if os.environ.get("B43_REHASH"):
        for _l, _i, gen, _r in candidates:
            gen._hash = hash(f"{gen.ortho}{gen.phonology}{gen.lemme}{gen.gramCat.name}{gen.gender}{gen.number}")
        print("rehashed generated words under current seed", flush=True)
    print(f"loaded {len(candidates)} candidates", flush=True)

    stage("A: augmented theory word lists")
    with temporarilyAugmented(theory, candidates):
        digest("augmented-theory", [
            [str(s), [_wordKey(w) for w in ws]] for s, ws in theory.items()
        ])
        stage("B1: augmented extract")
        augDiscBy, augOrdered, _ = extractDiscriminatingFeatures(theory)
        raw = [[f, sorted(_wordKey(w) for w in ws)] for f, ws in augDiscBy.items()]
        digest("discBy-aug-canon", sorted(raw))
        digest("discBy-aug-raw", raw)
        del raw
        digest("ordered-aug-canon", sorted(augOrdered))
        stage("C: feasible options")
        feasible = buildFeasibleDiscriminatorOptions(theory, augDiscBy)
        digest("feasible-canon", sorted(
            [str(s), l, [[_wordKey(w), sorted(feats)] for w, feats in byWord.items()]]
            for (s, l), byWord in feasible.items()
        ))
        stage("D: shared selection")
        chosen, unresolved = selectSharedDiscriminators(feasible)
        digest("chosen-canon", _canon([[_wordKey(w), f] for w, f in chosen.items()]))
        print(f"COUNT unresolved={len(unresolved)}", flush=True)
        stage("E: featuresetWords")
        fsw = {}
        for byWord in feasible.values():
            sel = []
            for w in byWord:
                if w in chosen:
                    sel.append((chosen[w], w))
                elif w in unresolved:
                    sel.append(("nofeature", w))
            if not sel:
                continue
            fs = tuple(fw[0] for fw in sel)
            fsw[fs] = fsw.get(fs, []) + [tuple(fw[1] for fw in sel)]
        digest("fsw-aug-raw", [
            [list(fs), [[_wordKey(w) for w in wt] for wt in wts]]
            for fs, wts in fsw.items()
        ])
        digest("fsw-aug-canon", _canon(
            [list(fs), [[_wordKey(w) for w in wt] for wt in wts]]
            for fs, wts in fsw.items()
        ))
        collisions = crossLemmaFeatureSetCollisions({k: v for k, v in fsw.items()})
        for fs, lemmas in sorted(collisions.items(), key=lambda kv: -len(kv[1]))[:5]:
            print(f"TOPKEY {len(lemmas):5d} lemmas  {fs}", flush=True)
    stage("done")


if __name__ == "__main__":
    main()
