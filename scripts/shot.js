// usage: node shot.js out.png [actions-json]
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1400, height: 850 } });
  const logs = []; p.on('console', m => logs.push(m.type() + ': ' + m.text())); p.on('pageerror', e => logs.push('PAGEERROR ' + e.message));
  await p.goto('http://localhost:8765/index.html'); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForTimeout(2500);
  const acts = JSON.parse(process.argv[3] || '[]');
  for (const a of acts) {
    if (a.click) { await p.mouse.click(a.click[0], a.click[1], a.opt || {}); }
    if (a.dbl) { await p.mouse.click(a.dbl[0], a.dbl[1]); await p.waitForTimeout(80); await p.mouse.click(a.dbl[0], a.dbl[1]); }
    if (a.right) { await p.mouse.click(a.right[0], a.right[1], { button: 'right' }); }
    if (a.key) await p.keyboard.press(a.key);
    if (a.sel) await p.click(a.sel);
    if (a.text) await p.locator('#menu .it span', { hasText: new RegExp('^' + a.text + '$') }).last().click();
    if (a.zoomto) await p.evaluate(z => { view.lon = z[0]; view.lat = z[1]; view.s = z[2]; clampView(); requestRender(true); }, a.zoomto);
    if (a.eval) logs.push('EVAL ' + JSON.stringify(await p.evaluate(a.eval)));
    if (a.wheel) { await p.mouse.move(a.wheel[0], a.wheel[1]); await p.mouse.wheel(0, a.wheel[2]); }
    if (a.move) { await p.mouse.move(a.move[0], a.move[1]); }
    if (a.shot) await p.screenshot({ path: a.shot });
    await p.waitForTimeout(a.wait || 600);
  }
  await p.screenshot({ path: process.argv[2] });
  console.log(logs.join('\n')); await b.close();
})();
