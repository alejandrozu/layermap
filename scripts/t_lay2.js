const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: 1200, height: 800 } });
  const p = await ctx.newPage(); const logs = [];
  p.on('pageerror', e => logs.push('PAGEERROR ' + e.message)); p.on('console', m => { if (m.type() === 'error') logs.push('console: ' + m.text()); });
  await p.goto('http://localhost:8765/index.html'); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForTimeout(2500);
  logs.push(JSON.stringify(await p.evaluate(async () => {
    await crackWorldTo(2); await crackOp(nodes.get('USA'), 2);
    view.lon = -98; view.lat = 38; view.s = 14; clampView();
    S.satOn = true; S.satOp = 100; syncLayersUI();
    setTool('crack', 'combine');
    for (const nm of ['Oklahoma', 'Kansas', 'Nebraska']) sel.add(display.find(n => n.name === nm).id);
    combineSelected();
    state.colors.set(display.find(n => n.name === 'Texas').id, '#e07a5f');
    state.deleted.add(display.find(n => n.name === 'Florida').id);
    recompute(); requestRender(true);
    return display.length;
  })));
  await p.waitForTimeout(3000); await p.screenshot({ path: '/tmp/T1.png' });
  await p.evaluate(() => { S.satOp = 55; opacityChanged(); setMode('delete'); }); await p.waitForTimeout(1500);
  await p.screenshot({ path: '/tmp/T2.png' });
  // export with layers (whole world)
  const data = await p.evaluate(async () => {
    const w = 2000, h = 1000, v = { lon: 10, lat: 0, s: 2000 / 360 };
    await layersReady(w, h, 1, v);
    const oc = document.createElement('canvas'); oc.width = w; oc.height = h; paintMap(oc.getContext('2d'), w, h, 1, v, { export: true });
    return oc.toDataURL('image/jpeg', 0.8);
  });
  fs.writeFileSync('/tmp/T3.jpg', Buffer.from(data.split(',')[1], 'base64'));
  logs.push(JSON.stringify(await p.evaluate(() => [LAY.sat.cache.size, [...LAY.sat.cache.keys()].filter(k => k.startsWith('3/')).length])));
  console.log(logs.join('\n')); await b.close();
})();
