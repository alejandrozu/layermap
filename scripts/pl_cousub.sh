#!/bin/bash
# $1 = state directory name; extracts SUMLEV 060 rows (geo header carries POP100) into <st>.060.txt
set -e
D="$1"; cd /home/claude/raw/us/pl
L=$(curl -s -m 60 "https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/$D/" | grep -o 'href="[a-z][a-z]2020.pl.zip"' | head -1 | sed 's/href="//;s/"//')
st=${L:0:2}
[ -f $st.060.txt ] && exit 0
curl -s -m 600 -o $st.zip "https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/$D/$L"
unzip -o -q $st.zip ${st}geo2020.pl
awk -F'|' '$3=="060" && $5=="00"' ${st}geo2020.pl > $st.060.tmp && mv $st.060.tmp $st.060.txt
rm -f $st.zip ${st}geo2020.pl
echo "$D $st $(wc -l < $st.060.txt)"
