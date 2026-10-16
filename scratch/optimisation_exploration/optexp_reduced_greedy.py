"""Greedy search over phoneme variants for the reduced form, on the short-form model (affix + briefs as claimants).
Each step adds the variant with the best estimated drop per word (same estimate as optexp_reduced_outlines.py).
Usage: python scratch/optimisation_exploration/optexp_reduced_greedy.py [--start "Z/onset,d/onset"] [--steps 8] [--min-words 300] [--long]"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import optexp_phoneme_cost as pc  # noqa: E402
import optexp_phoneme_information as pi  # noqa: E402
import optexp_reduced_outlines as ro  # noqa: E402

G = pi.G


def estimate(phs: str) -> tuple[float, int, int]:
    aff, rev, newOut = ro.solve(phs)
    used, freq = G["used"], G["orthoFreq"]
    gain = 0.0
    n = 0
    for o in aff:
        if o in rev or not newOut[o]:
            continue
        best = min(newOut[o], key=pc.rank)
        if pc.rank(best) >= pc.rank(used[o]):
            continue
        gain += freq.get(o, 0.0) * (pc.rank(used[o])[1] - pc.rank(best)[1])
        n += 1
    return gain / G["totalF"], n, len(rev)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="")
    ap.add_argument("--steps", type=int, default=8)
    ap.add_argument("--min-words", type=int, default=300)
    ap.add_argument("--long", action="store_true")
    args = ap.parse_args()
    if args.long:
        original = pi.prepare

        def dictOnly() -> None:
            original()
            G["fixed"] = {"plus_affix": [], "plus_briefs": []}
        pi.prepare = dictOnly
    G["long"] = args.long
    pc.prepareCost()
    cands = sorted(v for v, ws in G["byPh"].items() if len(ws) >= args.min_words)
    print(f"{len(cands)} candidate variants: {cands}", flush=True)
    chosen = [v for v in args.start.split(",") if v]
    best = estimate(",".join(chosen))[0] if chosen else 0.0
    print(f"start {chosen}: drop {best:.3f}", flush=True)
    for step in range(args.steps):
        results = []
        for v in cands:
            if v in chosen:
                continue
            g, n, k = estimate(",".join(chosen + [v]))
            results.append((g, v, n, k))
        results.sort(reverse=True)
        print(f"step {step + 1} top: " + "; ".join(f"{v} {g:.3f}" for g, v, _, _ in results[:5]), flush=True)
        g, v, n, k = results[0]
        if g <= best + 0.02:
            print("no variant adds more than 0.02: stop")
            break
        chosen.append(v)
        best = g
        print(f"+ {v}: drop {g:.3f} per word, {n} reduced, {k} keep  -> {','.join(chosen)}", flush=True)


if __name__ == "__main__":
    main()
