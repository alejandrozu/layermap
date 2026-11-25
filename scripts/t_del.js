const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const p = await (await b.newContext({ viewport: { width: 1200, height: 800 } })).newPage(); const logs = [];
  p.on('pageerror', e => logs.push('PAGEERROR ' + e.message));
  await p.goto('http://localhost:8765/index.html'); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForTimeout(2500);
  logs.push(JSON.stringify(await p.evaluate(async () => {
    await crackWorldTo(2); await crackOp(nodes.get('USA'), 2);
    view.lon = -98; view.lat = 38; view.s = 14; clampView();
    setTool('crack', 'combine');
    for (const nm of ['Oklahoma', 'Kansas', 'Nebraska']) sel.add(display.find(n => n.name === nm).id);
    combineSelected(); setMode('delete');
    const cid = [...state.combos.keys()][0]; state.deleted.add(cid); recompute(); requestRender(true);
    return [cid, state.combos.get(cid).n, display.filter(n => n.kind === 'combo').length];
  })));
  await p.waitForTimeout(800); await p.screenshot({ path: '/tmp/del.png' });
  const data = await p.evaluate(() => { const oc = document.createElement('canvas'); oc.width = 1200; oc.height = 700; paintMap(oc.getContext('2d'), 1200, 700, 1, { ...view }, { export: true }); return oc.toDataURL(); });
  fs.writeFileSync('/tmp/exp.png', Buffer.from(data.split(',')[1], 'base64'));
  console.log(logs.join('\n')); await b.close();
})();
