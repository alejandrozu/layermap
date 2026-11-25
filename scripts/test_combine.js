// Desktop + phone test of the Combine tool across levels.
// usage: node test_combine.js <w> <h> <mobile 0|1> <outprefix>
const { chromium } = require('playwright');
(async () => {
  const [w, h, mob, out] = [+process.argv[2], +process.argv[3], process.argv[4] === '1', process.argv[5]];
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: 2, isMobile: mob, hasTouch: mob });
  const p = await ctx.newPage(); const logs = [];
  p.on('pageerror', e => logs.push('PAGEERROR ' + e.message));
  p.on('console', m => { if (m.type() === 'error') logs.push('console: ' + m.text()); });
  await p.goto('http://localhost:8765/index.html'); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForTimeout(2500);
  const pos = async (lon, lat) => p.evaluate(([lon, lat]) => {
    const r = cv.getBoundingClientRect();
    return [r.left + W / 2 + (lon - view.lon) * view.s, r.top + H / 2 - (lat - view.lat) * view.s];
  }, [lon, lat]);
  const tap = async (lon, lat) => { const [x, y] = await pos(lon, lat); mob ? await p.touchscreen.tap(x, y) : await p.mouse.click(x, y); await p.waitForTimeout(450); };
  const ev = async (f, a) => { const r = await p.evaluate(f, a); logs.push('EVAL ' + JSON.stringify(r)); return r; };

  // setup: countries, then the US down to states, then Texas one level deeper
  await ev(async () => {
    await crackWorldTo(2);
    await crackOp(nodes.get('USA'), 2);
    const tx = display.find(n => n.name === 'Texas'); await crackOp(tx, 1);
    view.lon = -98; view.lat = 36; view.s = 16; clampView(); requestRender(true);
    return [display.length, tx.kids.map(k => k.name).slice(0, 12)];
  });
  await p.waitForTimeout(800);
  await p.click('#crackTool button[data-t=combine]'); await p.waitForTimeout(200);
  await tap(-97.5, 35.5);   // Oklahoma
  await tap(-98.3, 38.5);   // Kansas
  await tap(-101.8, 35.2);  // Texas panhandle unit (finer level)
  await ev(() => [[...sel].map(id => nodes.get(id)?.name || id), $('#combineBtn').hidden, $('#combineBtn').textContent]);
  await p.screenshot({ path: out + '_sel.png' });
  await p.click('#combineBtn'); await p.waitForTimeout(700);
  await ev(() => [[...state.combos].map(([k, v]) => [k, v.n, v.m.length]), display.filter(n => n.kind === 'combo').map(n => n.name)]);
  await p.screenshot({ path: out + '_combined.png' });
  // paint the combined area
  await p.click('#modes button[data-mode=color]'); await p.waitForTimeout(200);
  await tap(-97.5, 35.5);
  await ev(() => [...state.colors]);
  await p.screenshot({ path: out + '_colored.png' });
  // split it via the menu
  await p.click('#modes button[data-mode=crack]'); await p.waitForTimeout(200);
  const [x, y] = await pos(-97.5, 35.5);
  if (mob) {
    const cdp = await ctx.newCDPSession(p);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y }] });
    await p.waitForTimeout(800);
    await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  } else await p.mouse.click(x, y, { button: 'right' });
  await p.waitForTimeout(500);
  await p.screenshot({ path: out + '_menu.png' });
  await ev(() => [...document.querySelectorAll('#menu .it span')].map(s => s.textContent));
  const split = p.locator('#menu .it', { hasText: 'Split back' });
  await split.click(); await p.waitForTimeout(500);
  await ev(() => [state.combos.size, display.filter(n => n.kind === 'combo').length, [...state.colors].length]);
  // undo restores the combo
  await p.click('#undo'); await p.waitForTimeout(400);
  await ev(() => [state.combos.size]);
  // persistence round trip
  await ev(() => { const pr = project(); return [pr.combos.length]; });
  await p.waitForTimeout(1500);
  await p.reload(); await p.waitForTimeout(4000);
  await ev(() => [state.combos.size, display.filter(n => n.kind === 'combo').map(n => n.name)]);
  console.log(logs.join('\n')); await b.close();
})();
