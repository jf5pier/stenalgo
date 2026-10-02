#!/usr/bin/env python3
"""Compare two Plover JSON dictionaries (BEFORE vs AFTER)."""

import json
from pathlib import Path
from collections import defaultdict

# Load dictionaries
before_path = Path("/home/jfsp/stenalgo/scratch/b44-before/plover_stenalgo_dictionary.json")
after_path = Path("/home/jfsp/stenalgo/plover_stenalgo_dictionary.json")

with open(before_path) as f:
    before = json.load(f)

with open(after_path) as f:
    after = json.load(f)

# Task 1: Entry counts and changes
before_count = len(before)
after_count = len(after)

before_stenos = set(before.keys())
after_stenos = set(after.keys())

removed_stenos = before_stenos - after_stenos
added_stenos = after_stenos - before_stenos
common_stenos = before_stenos & after_stenos

# Find changed entries (same steno, different word)
changed_stenos = [s for s in common_stenos if before[s] != after[s]]

print(f"BEFORE: {before_count} entries")
print(f"AFTER: {after_count} entries")
print(f"Removed stenos: {len(removed_stenos)}")
print(f"Added stenos: {len(added_stenos)}")
print(f"Changed stenos (same key, different value): {len(changed_stenos)}")
print()

# Task 2: Spellings reachable before but not after, and vice versa
before_spellings = set(before.values())
after_spellings = set(after.values())

only_before_spellings = before_spellings - after_spellings
only_after_spellings = after_spellings - before_spellings

print(f"Spellings only in BEFORE: {len(only_before_spellings)}")
if len(only_before_spellings) <= 60:
    for spelling in sorted(only_before_spellings):
        print(f"  {spelling}")
else:
    examples = sorted(list(only_before_spellings))[:30]
    print(f"  (showing 30 examples)")
    for spelling in examples:
        print(f"  {spelling}")
print()

print(f"Spellings only in AFTER: {len(only_after_spellings)}")
if len(only_after_spellings) <= 60:
    for spelling in sorted(only_after_spellings):
        print(f"  {spelling}")
else:
    examples = sorted(list(only_after_spellings))[:30]
    print(f"  (showing 30 examples)")
    for spelling in examples:
        print(f"  {spelling}")
print()

# Task 3: Changed stenos (20 examples)
print(f"Changed stenos examples (showing up to 20):")
for steno in sorted(changed_stenos)[:20]:
    print(f"  {steno}: {before[steno]} -> {after[steno]}")
print()

# Task 4: Specific words mapping
specific_words = ["panse", "pense", "conte", "compte", "butte", "bute",
                  "admis", "garanties", "subits", "hais", "fête", "entre", "heurte"]

print("Specific words - stenos in BEFORE and AFTER:")
for word in specific_words:
    before_stenos_for_word = [s for s, w in before.items() if w == word]
    after_stenos_for_word = [s for s, w in after.items() if w == word]
    print(f"\n{word}:")
    print(f"  BEFORE ({len(before_stenos_for_word)}): {sorted(before_stenos_for_word)}")
    print(f"  AFTER ({len(after_stenos_for_word)}): {sorted(after_stenos_for_word)}")
print()

# Task 5: Check for marks on alternates in AFTER
# A steno with '/' is an alternate; check if the part before the last '/' contains '*' or '#'
marks_on_alternates = []
for steno in after.keys():
    if '/' in steno:
        # Split by '/' and check all parts except the last
        parts = steno.split('/')
        for part in parts[:-1]:  # All parts except the last
            if '*' in part or '#' in part:
                marks_on_alternates.append(steno)
                break

print(f"Stenos in AFTER with marks on alternates: {len(marks_on_alternates)}")
if len(marks_on_alternates) > 0:
    examples = sorted(marks_on_alternates)[:10]
    print(f"Examples (showing up to 10):")
    for steno in examples:
        print(f"  {steno} -> {after[steno]}")
print()

# Write to file
output_file = Path("/home/jfsp/stenalgo/scratch/b44-plover-diff.txt")
with open(output_file, "w") as f:
    f.write("PLOVER DICTIONARY COMPARISON: BEFORE vs AFTER\n")
    f.write("=" * 70 + "\n\n")

    f.write("1. ENTRY COUNTS AND CHANGES\n")
    f.write("-" * 70 + "\n")
    f.write(f"BEFORE: {before_count} entries\n")
    f.write(f"AFTER: {after_count} entries\n")
    f.write(f"Removed stenos: {len(removed_stenos)}\n")
    f.write(f"Added stenos: {len(added_stenos)}\n")
    f.write(f"Changed stenos (same key, different value): {len(changed_stenos)}\n\n")

    f.write("2. SPELLINGS REACHABLE BEFORE BUT NOT AFTER\n")
    f.write("-" * 70 + "\n")
    f.write(f"Count: {len(only_before_spellings)}\n")
    if len(only_before_spellings) <= 60:
        for spelling in sorted(only_before_spellings):
            f.write(f"  {spelling}\n")
    else:
        f.write(f"(showing 30 examples)\n")
        examples = sorted(list(only_before_spellings))[:30]
        for spelling in examples:
            f.write(f"  {spelling}\n")
    f.write("\n")

    f.write("3. SPELLINGS REACHABLE AFTER BUT NOT BEFORE\n")
    f.write("-" * 70 + "\n")
    f.write(f"Count: {len(only_after_spellings)}\n")
    if len(only_after_spellings) <= 60:
        for spelling in sorted(only_after_spellings):
            f.write(f"  {spelling}\n")
    else:
        f.write(f"(showing 30 examples)\n")
        examples = sorted(list(only_after_spellings))[:30]
        for spelling in examples:
            f.write(f"  {spelling}\n")
    f.write("\n")

    f.write("4. CHANGED STENOS (SAME KEY, DIFFERENT VALUE)\n")
    f.write("-" * 70 + "\n")
    f.write(f"Count: {len(changed_stenos)}\n")
    f.write(f"Examples (showing up to 20):\n")
    for steno in sorted(changed_stenos)[:20]:
        f.write(f"  {steno}: {before[steno]} -> {after[steno]}\n")
    f.write("\n")

    f.write("5. SPECIFIC WORDS - STENOS IN BEFORE AND AFTER\n")
    f.write("-" * 70 + "\n")
    for word in specific_words:
        before_stenos_for_word = [s for s, w in before.items() if w == word]
        after_stenos_for_word = [s for s, w in after.items() if w == word]
        f.write(f"\n{word}:\n")
        f.write(f"  BEFORE ({len(before_stenos_for_word)}): {sorted(before_stenos_for_word)}\n")
        f.write(f"  AFTER ({len(after_stenos_for_word)}): {sorted(after_stenos_for_word)}\n")
    f.write("\n")

    f.write("6. MARKS ON ALTERNATES IN AFTER\n")
    f.write("-" * 70 + "\n")
    f.write(f"Stenos with marks on alternates: {len(marks_on_alternates)}\n")
    if len(marks_on_alternates) > 0:
        f.write(f"Examples (showing up to 10):\n")
        examples = sorted(marks_on_alternates)[:10]
        for steno in examples:
            f.write(f"  {steno} -> {after[steno]}\n")
    f.write("\n")

print("Report written to scratch/b44-plover-diff.txt")
