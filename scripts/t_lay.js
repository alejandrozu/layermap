const { chromium } = require('playwright');
(async () => {
  const [w, h, mob] = [+process.argv[2] || 1400, +process.argv[3] || 850, process.argv[4] === '1'];
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: mob ? 2 : 1, isMobile: mob, hasTouch: mob });
  const p = await ctx.newPage(); const logs = [];
  p.on('pageerror', e => logs.push('PAGEERROR ' + e.message)); p.on('console', m => { if (m.type() === 'error') logs.push('console: ' + m.text()); });
  await p.goto('http://localhost:8765/index.html'); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForTimeout(2500);
  const ev = async f => logs.push(JSON.stringify(await p.evaluate(f)));
  await p.click('#layersBtn'); await p.waitForTimeout(300);
  await p.click('#satOn', { force: true }); await p.waitForTimeout(2500);
  await p.screenshot({ path: '/tmp/L1.png' });
  await ev(() => [S.satOn, LAY.sat.cache.size, lastFullMs.toFixed(1)]);
  await p.evaluate(async () => { await crackWorldTo(2); }); await p.waitForTimeout(500);
  await p.evaluate(() => { view.lon = 8; view.lat = 47; view.s = 70; clampView(); requestRender(true); }); await p.waitForTimeout(3000);
  await p.screenshot({ path: '/tmp/L2.png' });
  await ev(() => [LAY.sat.cache.size, [...LAY.sat.cache.keys()].slice(0, 8), lastFullMs.toFixed(1)]);
  await p.click('#elevOn', { force: true }); await p.waitForTimeout(3000);
  await p.evaluate(() => { $('#satOn').click(); }); await p.waitForTimeout(1500);
  await p.screenshot({ path: '/tmp/L3.png' });
  await ev(() => [S.satOn, S.elevOn, LAY.elev.cache.size, !!WATER, lastFullMs.toFixed(1)]);
  // opacity drag speed
  await ev(() => { const t0 = performance.now(); for (let i = 0; i < 20; i++) { S.elevOp = 30 + i; opacityChanged(); } return ['20 composites ms', (performance.now() - t0).toFixed(1)]; });
  console.log(logs.join('\n')); await b.close();
})();
