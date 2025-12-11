# Undo the partial transformation of middle "E" phonemes to "e" when the final vowel is "e"
# The vocalic harmony rule is reverted to the fidelity to the root.

awk -F'\t' -v OFS='\t' '$2 ~ /E[RtsplkmdvjnfbZwzSgNG]{1,4}e$/ { 
  print $3 }' resources/Lexique383.tsv | sort -u >lemmes_possible_ECe_corretion

awk -F'\t' -v OFS='\t' 'NR==FNR { lemmes[$0]; next } $3 in lemmes && $2 ~ /e[RtsplkmdvjnfbZwzSgNG]{1,4}e$/ { 
  print $1 }' lemmes_possible_ECe_corretion resources/Lexique383.tsv >words_ECe_correction

awk -F'\t' -v OFS='\t' 'NR==FNR { lemmes[$0]; next } $3 in lemmes && $2 ~ /e[RtsplkmdvjnfbZwzSgNG]{1,4}e$/ {
   PHON = gensub(/e([RtsplkmdvjnfbZwzSgNG]{1,4}e)$/, "E\\1", "1", $2);
   CV = gensub(/e-([RtsplkmdvjnfbZwzSgNG]{1,4}e)$/, "E-\\1", "1", $23);
   r=""; for(i=length(PHON);i>0;i--) r=r substr(PHON,i,1); REVPHON=r ;
   $2 = PHON; $23 = CV; $27 = REVPHON ; } {
   print $0}' lemmes_possible_ECe_corretion resources/Lexique383.tsv >resources/Lexique383_racine.tsv

awk -F'\t' -v OFS='\t' 'NR==FNR { words[$0]; next } $1 in words && $2 ~ /e[RtsplkmdvjnfbZwzSgNG]{1,4}e$/ {
  PHON = gensub(/e([RtsplkmdvjnfbZwzSgNG]{1,4}e)$/, "E\\1", "1", $2);
  GRAPHPHON = gensub(/^(.*)(-e)(([^-]|-[^e])*)(-e)(([^-]|-[^eE])*)$/, "\\1-E\\3\\5\\6",1, $5);
  $2 = PHON; $5 = GRAPHPHON ; } {
  print $0 }' words_ECe_correction resources/LexiqueInfraCorrespondance.tsv >resources/LexiqueInfraCorrespondance_racine.tsv
