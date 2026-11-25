// usage: node topo2geo.js in.json object out.geojson
const fs=require('fs'); const tc=require('/home/claude/tools/node_modules/topojson-client');
const t=JSON.parse(fs.readFileSync(process.argv[2])); const fc=tc.feature(t,t.objects[process.argv[3]]);
fs.writeFileSync(process.argv[4], JSON.stringify(fc));
