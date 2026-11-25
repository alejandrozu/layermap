#!/bin/bash
# $1 = state directory name; extracts block rows: county|cousub|tract|pop|aland|lat|lon  -> <st>.750.txt
set -e
D="$1"; cd /home/claude/raw/us/pl
L=$(curl -s -m 60 "https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/$D/" | grep -o 'href="[a-z][a-z]2020.pl.zip"' | head -1 | sed 's/href="//;s/"//')
st=${L:0:2}
[ -f $st.750.txt ] && exit 0
curl -s -m 900 -o $st.zip "https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/$D/$L"
unzip -o -q $st.zip ${st}geo2020.pl
awk -F'|' 'BEGIN{OFS="|"} $3=="750" {print $15,$18,$33,$91,$85,$93+0,$94+0}' ${st}geo2020.pl > $st.750.tmp && mv $st.750.tmp $st.750.txt
rm -f $st.zip ${st}geo2020.pl
echo "$D $st $(wc -l < $st.750.txt)"
