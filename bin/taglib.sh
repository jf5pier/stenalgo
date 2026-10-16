# Shared helpers for the tag tools: tagdef, tagreserve, tagcheck.
# The convention itself is documented in the docs/TAGS.tsv header comments:
# docs/TAGS.tsv maps PREFIX -> the document that defines its items; a tag is
# PREFIX + number (PRP2); the document carries one-line definitions
# <!-- tag: PRP2 | text --> above the item's heading or list item, or as a
# block of such comments immediately after the defining table.

# Resolve the repository root from any directory inside it; fail outside one.
tag_root() {
  local root
  if root="$(git rev-parse --show-toplevel 2>/dev/null)" && [ -n "$root" ]; then
    printf '%s\n' "$root"
    return 0
  fi
  local dir="$PWD"
  while :; do
    if [ -f "$dir/docs/TAGS.tsv" ]; then
      printf '%s\n' "$dir"
      return 0
    fi
    [ "$dir" = / ] && return 1
    dir="$(dirname "$dir")"
  done
}

TAGS_FILE=docs/TAGS.tsv

# The header written when the registry file is created.
tag_registry_header() {
  cat <<'HEADER'
# Tag registry: PREFIX <TAB> repo-relative path <TAB> short description.
# A tag is PREFIX + number (e.g. PREFIX2) and cites one item of exactly one
# document. Rule (mechanical initials): the prefix comes from the file name's
# initials (PHONOLOGY_REWRITE_PLAN.md -> PRP, TODO.md -> TOD; 2-5 uppercase
# letters); a document with several item families appends the family letter
# (PHONOLOGY_REWRITE_BLIND_SPOTS.md -> PRA/PRB/PRC/PRD for its A/B/C/D items);
# on collision, extend with the next word's initial, then further letters,
# until free. Reserve a prefix: bin/tagreserve docs/FILE.md [PREFIX [DESC]]
# (writes nothing if the prefix is taken). Definitions live in the document
# that describes the item, as one line:
#   <!-- tag: PREFIX2 | one-line definition -->
# placed directly above the item's heading or list item, or as a block of such
# comments immediately after the table that defines the items (one per row, in
# row order). Look up: bin/tagdef PREFIX2. Check: bin/tagcheck.
# Standing exclusions (bare on purpose; tagcheck and the reply hook ignore
# unregistered prefixes): pipeline stages S1-S10; code-level ids L1-L4, E1-E6,
# T1-T3.x; the historical docs/history affix families A1-A9, B1-B6, D1-D6;
# Q1-Q7.
HEADER
}

# The registered path of a prefix, or nothing when unregistered.
tag_file_of() {
  awk -F'\t' -v p="$1" '!/^#/ && $1 == p { print $2; exit }' "$TAGS_FILE"
}

# Print the definition text of TAG as found in FILE; exit status 1 when absent.
tag_definition_in() {
  awk -v tag="$1" '
    {
      line = $0
      while (match(line, /<!--[ \t]*tag:[ \t]*[A-Za-z]+[0-9]+[ \t]*\|/)) {
        head = substr(line, RSTART, RLENGTH)
        rest = substr(line, RSTART + RLENGTH)
        if (match(head, /[A-Za-z]+[0-9]+/) && substr(head, RSTART, RLENGTH) == tag) {
          sub(/^[ \t]*/, "", rest)
          end = index(rest, "-->")
          if (end > 0) {
            text = substr(rest, 1, end - 1)
            sub(/[ \t]+$/, "", text)
            print text
            found = 1
            exit
          }
        }
        line = substr(line, RSTART + RLENGTH)
      }
    }
    END { if (found) exit 0; exit 1 }
  ' "$2"
}
