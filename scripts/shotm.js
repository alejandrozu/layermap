// usage: node shotm.js out.png [w h mobile] [actions]
const { chromium, devices } = require('playwright');
(async () => {
  const [out, w, h, mob] = [process.argv[2], +(process.argv[3]||390), +(process.argv[4]||844), process.argv[5]==='1'];
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, isMobile: mob, hasTouch: mob });
  const p = await ctx.newPage(); const logs = [];
  p.on('pageerror', e => logs.push('PAGEERROR ' + e.message)); p.on('console', m => { if (m.type()==='error') logs.push('console: ' + m.text()); });
  await p.goto('http://localhost:8765/index.html'); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForTimeout(2500);
  const acts = JSON.parse(process.argv[6] || '[]');
  const cdp = mob ? await ctx.newCDPSession(p) : null;
  const touch = (type, pts) => cdp.send('Input.dispatchTouchEvent', { type, touchPoints: pts.map(([x, y], i) => ({ x, y, id: i })) });
  for (const a of acts) {
    if (a.tap) await p.touchscreen.tap(a.tap[0], a.tap[1]);
    if (a.click) await p.mouse.click(a.click[0], a.click[1]);
    if (a.sel) await p.click(a.sel);
    if (a.press) { await touch('touchStart', [a.press.slice(0, 2)]); await p.waitForTimeout(a.press[2] || 700); await touch('touchEnd', []); }
    if (a.swipe) { const [x1, y1, x2, y2] = a.swipe; await touch('touchStart', [[x1, y1]]); for (let i = 1; i <= 12; i++) { await touch('touchMove', [[x1 + (x2 - x1) * i / 12, y1 + (y2 - y1) * i / 12]]); await p.waitForTimeout(25); } await touch('touchEnd', []); }
    if (a.pinch) { const [cx, cy, d1, d2] = a.pinch; await touch('touchStart', [[cx - d1, cy], [cx + d1, cy]]); for (let i = 1; i <= 10; i++) { const d = d1 + (d2 - d1) * i / 10; await touch('touchMove', [[cx - d, cy], [cx + d, cy]]); await p.waitForTimeout(25); } await touch('touchEnd', []); }
    if (a.dbl) { await p.touchscreen.tap(a.dbl[0], a.dbl[1]); await p.waitForTimeout(120); await p.touchscreen.tap(a.dbl[0], a.dbl[1]); }
    if (a.rclick) await p.mouse.click(a.rclick[0], a.rclick[1], { button: 'right' });
    if (a.key) await p.keyboard.press(a.key);
    if (a.mclick) { await p.keyboard.down(a.mclick[2]); await p.mouse.click(a.mclick[0], a.mclick[1]); await p.keyboard.up(a.mclick[2]); }
    if (a.eval) logs.push('EVAL ' + JSON.stringify(await p.evaluate(a.eval)));
    if (a.shot) await p.screenshot({ path: a.shot });
    await p.waitForTimeout(a.wait || 500);
  }
  await p.screenshot({ path: out }); console.log(logs.join('\n')); await b.close();
})();
