#!/bin/bash
# block rows with place: county|cousub|place|tract|pop|aland  -> <st>.750p.txt
set -e
D="$1"; cd /home/claude/raw/us/pl
L=$(curl -s -m 60 "https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/$D/" | grep -o 'href="[a-z][a-z]2020.pl.zip"' | head -1 | sed 's/href="//;s/"//')
st=${L:0:2}
[ -f $st.750p.txt ] && exit 0
curl -s -m 900 -o $st.zip "https://www2.census.gov/programs-surveys/decennial/2020/data/01-Redistricting_File--PL_94-171/$D/$L"
unzip -o -q $st.zip ${st}geo2020.pl
awk -F'|' 'BEGIN{OFS="|"} $3=="750" {print $15,$18,$30,$33,$91,$85} $3=="070" && $5=="00" {print "070",$15,$18,$30,$91,$85,$88 > "'$st'.070.txt"}' ${st}geo2020.pl > $st.750p.tmp && mv $st.750p.tmp $st.750p.txt
rm -f $st.zip ${st}geo2020.pl
