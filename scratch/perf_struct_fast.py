"""Prototype: output-preserving speedup of detectUndersampledLemmas (S2 slowdown).
Index strokeLemmeDiscriminators by lemmeGramCat (the fullFeatureSpace rescan) and
compute each lemma's leave-one-out sibling union from per-template feature counts
(the quadratic sibling loop). Compares raw-order digests against the original.
Usage: PYTHONHASHSEED=0 env/bin/python scratch/perf_struct_fast.py
"""
import contextlib
import hashlib
import io
import json
import os
import sys
import time
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import src.verbparadigm as vp
import util.completeVerbParadigms as cvp
from perf_extract_fast import extractDiscriminatingFeaturesFast


def detectUndersampledLemmasFast(strokeLemmeDiscriminators, verbisteTemplates, exceptions):
    lemmeGramCats = {lgc for (_s, lgc) in strokeLemmeDiscriminators}
    templateByLemmeGramCat = {}
    for lemmeGramCat in lemmeGramCats:
        lemme = vp.lemmeOfVerbLemmeGramCat(lemmeGramCat)
        if lemme is None:
            continue
        template = vp.getTrustedTemplate(lemme, verbisteTemplates, exceptions)
        if template is not None:
            templateByLemmeGramCat[lemmeGramCat] = template
    lemmeGramCatsByTemplate = {}
    for lemmeGramCat, template in templateByLemmeGramCat.items():
        lemmeGramCatsByTemplate.setdefault(template, []).append(lemmeGramCat)

    # Same insertion order as fullFeatureSpace: groups in dict order, words in dict order.
    featureSpaceByLemmeGramCat = {lgc: set() for lgc in templateByLemmeGramCat}
    for (_s, groupLemme), wordFeatures in strokeLemmeDiscriminators.items():
        space = featureSpaceByLemmeGramCat.get(groupLemme)
        if space is not None:
            for features in wordFeatures.values():
                space.update(features)

    undersampled = {}
    for template, siblingGroup in lemmeGramCatsByTemplate.items():
        if len(siblingGroup) < 2:
            continue
        counts = Counter()
        for lgc in siblingGroup:
            counts.update(featureSpaceByLemmeGramCat[lgc])
        for lgc in siblingGroup:
            ownSpace = featureSpaceByLemmeGramCat[lgc]
            canonicalSpace = {f for f, n in counts.items() if n - (f in ownSpace) > 0}
            if ownSpace < canonicalSpace:
                undersampled[lgc] = vp.UndersampledLemma(
                    lemmeGramCat=lgc, template=template,
                    missingFeatures=frozenset(canonicalSpace - ownSpace),
                    siblingLemmeGramCats=frozenset(o for o in siblingGroup if o != lgc),
                )
    return undersampled


def _wk(w):
    return [w.ortho, w.phonology, w.lemme, w.gramCat.name, w.gender, w.number, w.infoVerb or ""]


def _d(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode()).hexdigest()[:16]


def _undersampledDigest(u):
    return _d([[k, v.template, list(v.missingFeatures), list(v.siblingLemmeGramCats)] for k, v in u.items()])


def _candidatesDigest(cands):
    return _d([[lgc, info.template, list(info.missingFeatures), _wk(g), _wk(r)] for lgc, info, g, r in cands])


def _quiet(fn, *a):
    t = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        res = fn(*a)
    return time.perf_counter() - t, res


if __name__ == "__main__":
    theory, _ = cvp.loadTheoryAndKeyboard()
    templates = vp.loadVerbisteTemplates(cvp.VERBISTE_VERBS_PATH)
    exceptions = vp.loadVerbModelExceptions(cvp.EXCEPTIONS_PATH)
    conjugations = vp.parseConjugationTemplates(cvp.VERBISTE_CONJUGATIONS_PATH)
    _, (_discBy, _ordered, sld) = _quiet(extractDiscriminatingFeaturesFast, theory)
    tables = vp.deriveConjugationEndingTables(theory, templates, exceptions)

    dt0, u0 = _quiet(vp.detectUndersampledLemmas, sld, templates, exceptions)
    dt1, u1 = _quiet(detectUndersampledLemmasFast, sld, templates, exceptions)
    print(f"detect original {dt0:7.1f}s {_undersampledDigest(u0)}  n={len(u0)}", flush=True)
    print(f"detect fast     {dt1:7.1f}s {_undersampledDigest(u1)}  n={len(u1)}", flush=True)
    print("keys same order:", list(u0) == list(u1), flush=True)
    print("content equal:", u0 == u1, flush=True)
    nm = sum(list(u0[k].missingFeatures) != list(u1[k].missingFeatures) for k in u0)
    ns = sum(list(u0[k].siblingLemmeGramCats) != list(u1[k].siblingLemmeGramCats) for k in u0)
    print(f"missingFeatures iteration-order diffs: {nm}; siblings iteration-order diffs: {ns}", flush=True)
    for k in u0:
        if list(u0[k].missingFeatures) != list(u1[k].missingFeatures):
            print("example", k, list(u0[k].missingFeatures)[:6], "|", list(u1[k].missingFeatures)[:6], flush=True)
            break
    del u0, u1

    args = (sld, theory, templates, exceptions, conjugations, tables)
    dt0, (c0, _) = _quiet(cvp.findStructuralCandidates, *args)
    d0 = _candidatesDigest(c0); c0s = c0
    cvp.detectUndersampledLemmas = detectUndersampledLemmasFast
    dt1, (c1, _) = _quiet(cvp.findStructuralCandidates, *args)
    d1 = _candidatesDigest(c1); n1 = len(c1)
    print("candidates same (lgc, generated word) sequence:", [(c[0], *_wk(c[2])) for c in c0s] == [(c[0], *_wk(c[2])) for c in c1], flush=True)
    del c1
    print(f"structural original {dt0:7.1f}s {d0}", flush=True)
    print(f"structural fast     {dt1:7.1f}s {d1}  n={n1}", flush=True)
    print("IDENTICAL (raw order)" if d0 == d1 else "DIFFERENT", flush=True)
