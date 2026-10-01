#!/bin/bash
cd /home/jfsp/stenalgo
run() { echo "=================== $1 '$2' /$3/ keys $4"; PYTHONUNBUFFERED=1 PYTHONPATH=. env/bin/python scratch/fusion_growth.py "$1" "$2" "$3" "$4" 2>&1 | grep -v legal ; }
run prefix 'ae|ai|aî|e|ei|he|hé|oe|é|éh' e 2,5
run suffix 'ccion|cion|cyon|sion|ssion|tion|tions' 'sj§' 16,17,20
run prefix 'au|aux|hau|haut|ho|hô|o|oh|ô' o 17,18,19
run suffix 'ger|gée' Ze 16,24
run suffix 'cher|chée|scher|sher' Se 9,24,25
run suffix 've|ver|wé' ve 16,17,18
run prefix 'pa|pei|pâ' pa 2,5
run suffix 'man|mand|mant|ment|ments|mmant|mment' 'm@' 16,20,25
