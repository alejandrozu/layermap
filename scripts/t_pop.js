const { chromium } = require('playwright');
(async () => {
  const [w, h, mob] = [+process.argv[2] || 1400, +process.argv[3] || 850, process.argv[4] === '1'];
  const b = await chromium.launch(); const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: mob ? 2 : 1, isMobile: mob, hasTouch: mob });
  const p = await ctx.newPage(); const logs = [];
  p.on('pageerror', e => logs.push('PAGEERROR ' + e.message)); p.on('console', m => { if (m.type() === 'error') logs.push('console: ' + m.text()); });
  await p.goto('http://localhost:8765/index.html'); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForTimeout(2500);
  const ev = async f => logs.push(JSON.stringify(await p.evaluate(f)));
  await ev(() => [fmtPop(47400798), fmtPop(8118835999), fmtPop(999950), fmtPop(1234), fmtPop(999), fmtPop(56462), fmtPop(1000), fmtPop(12.345)]);
  await p.click('#modes button[data-mode=color]'); await p.waitForTimeout(200);
  if (mob) await p.click('#panelClose').catch(() => {});
  await p.click('#popBtn'); await p.waitForTimeout(1500);
  await p.click('#popLabels', { force: true }); await p.click('#popOn', { force: true }); await p.waitForTimeout(500);
  await p.evaluate(async () => { await crackWorldTo(2); }); await p.waitForTimeout(1200);
  await p.screenshot({ path: '/tmp/P1.png' });
  await ev(() => ['world', popOf(root) && fmtPop(popOf(root).v), popOf(nodes.get('USA')), popOf(nodes.get('CHN')).v, popOf(nodes.get('IND')).src, popOf(nodes.get('R:EUR') || root.kids[0]).src]);
  // Spain to comarcas, colour by population
  await p.evaluate(async () => { await crackOp(nodes.get('ESP'), 3); view.lon = -3.7; view.lat = 40; view.s = 70; clampView(); requestRender(true); });
  await p.waitForTimeout(1500);
  await p.click('#popApply'); await p.waitForTimeout(1500);
  await p.screenshot({ path: '/tmp/P2.png' });
  await ev(() => [legend.title, legend.order.slice(0, 7).map(c => legend.labels[c]), state.colors.size]);
  // tooltip
  const r = await p.evaluate(() => { const r = cv.getBoundingClientRect(); return [r.left + W / 2, r.top + H / 2]; });
  if (!mob) { await p.mouse.move(r[0], r[1]); await p.waitForTimeout(400); await ev(() => $('#tip').innerText); }
  // density labels
  await p.evaluate(() => { document.querySelector('#popMetric button[data-m=dens]').click(); }); await p.waitForTimeout(800);
  await p.screenshot({ path: '/tmp/P3.png' });
  // undo restores colours
  await p.evaluate(() => undo()); await p.waitForTimeout(500); await ev(() => ['after undo', state.colors.size]);
  console.log(logs.join('\n')); await b.close();
})();
