import json
import sys

with open('scratch/b45-before/plover_stenalgo_dictionary.json', encoding='utf-8') as f:
    before = json.load(f)
with open('plover_stenalgo_dictionary.json', encoding='utf-8') as f:
    after = json.load(f)

before_keys = set(before.keys())
after_keys = set(after.keys())

added = sorted(after_keys - before_keys)
removed = sorted(before_keys - after_keys)
changed = sorted(k for k in (before_keys & after_keys) if before[k] != after[k])

with open('scratch/b45-plover-diff.txt', 'w', encoding='utf-8') as out:
    out.write(f"before entries: {len(before)}\n")
    out.write(f"after entries: {len(after)}\n")
    out.write(f"added strokes: {len(added)}\n")
    out.write(f"removed strokes: {len(removed)}\n")
    out.write(f"changed strokes (same stroke, different spelling): {len(changed)}\n\n")

    out.write("=== ADDED (new stroke -> spelling) ===\n")
    for k in added:
        out.write(f"{k}\t{after[k]}\n")

    out.write("\n=== REMOVED (stroke -> spelling gone) ===\n")
    for k in removed:
        out.write(f"{k}\t{before[k]}\n")

    out.write("\n=== CHANGED (stroke: before -> after) ===\n")
    for k in changed:
        out.write(f"{k}\t{before[k]} -> {after[k]}\n")

print(f"before={len(before)} after={len(after)} added={len(added)} removed={len(removed)} changed={len(changed)}")

# Word-level view: for target words, find which strokes map to them in before/after
targets = ['promis','permis','admis','compromis','enclos','découverte','decouverte','cuite',
           'feinte','jointe','teinte','promise','permise','admise','compromise','enclose',
           'découvert','decouvert','cuit','feint','joint','teint']

def strokes_for_word(d, word):
    return [k for k,v in d.items() if v == word]

print("\n--- target word stroke mapping (before -> after) ---")
for w in targets:
    b = strokes_for_word(before, w)
    a = strokes_for_word(after, w)
    if b != a:
        print(f"{w}: before={b} after={a}")
