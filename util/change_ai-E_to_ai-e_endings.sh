# Changes the "E" endings to "e" endings in Lexique files for words ending in "ai"
#

awk -F'\t' -v OFS='\t' ' $1 ~ /ai$/ && $2 ~ /E$/ && $4 ~ /^VER$/ {
  PHON = gensub(/^(.*)E$/, "\\1e", "1", $2);
  CV = gensub(/^(.*)E$/, "\\1e", "1", $23);
  r=""; for(i=length(PHON);i>0;i--) r=r substr(PHON,i,1); REVPHON=r ;
  $2 = PHON; $23 = CV ; $27 = REVPHON ; } {
    print $0}' resources/Lexique383.tsv >resources/Lexique383_modified.tsv.fix_ai

awk -F'\t' -v OFS='\t' ' $1 ~ /ai$/ && $2 ~ /E$/ && $3 ~ /^VER$/ {
  PHON = gensub(/^(.*)E$/, "\\1e", "1", $2);
  GRAPHPHON = gensub(/^(.*)E$/, "\\1e", "1", $5);
  $2 = PHON; $5 = GRAPHPHON ; } {
  print $0}' resources/LexiqueInfraCorrespondance.tsv >resources/LexiqueInfraCorrespondance_modified.tsv.fix_ai
