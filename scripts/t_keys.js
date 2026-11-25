const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const p = await (await b.newContext({ viewport: { width: 1400, height: 850 } })).newPage(); const logs = [];
  p.on('pageerror', e => logs.push('PAGEERROR ' + e.message));
  await p.goto('http://localhost:8765/index.html'); await p.evaluate(() => localStorage.clear()); await p.reload(); await p.waitForTimeout(2500);
  const pos = (lon, lat) => p.evaluate(([lon, lat]) => { const r = cv.getBoundingClientRect(); return [r.left + W / 2 + (lon - view.lon) * view.s, r.top + H / 2 - (lat - view.lat) * view.s]; }, [lon, lat]);
  const ev = async f => logs.push(JSON.stringify(await p.evaluate(f)));
  const click = async (lon, lat, mod) => { const [x, y] = await pos(lon, lat); if (mod) await p.keyboard.down(mod); await p.mouse.click(x, y); if (mod) await p.keyboard.up(mod); await p.waitForTimeout(700); };
  await p.evaluate(() => crackWorldTo(1)); await p.waitForTimeout(800);
  await click(0, 12, 'Control'); await click(20, 50, 'Control');           // West Africa + Europe
  await ev(() => ['sel', tools.crack, [...sel].map(i => nodes.get(i).name)]);
  await p.keyboard.press('Enter'); await p.waitForTimeout(500);
  await ev(() => ['combos', [...state.combos].map(([k, v]) => v.n), display.length]);
  await p.keyboard.press('m'); await click(0, 12);                          // merge tool on a combo = split
  await ev(() => ['after merge-tool click', tools.crack, state.combos.size, display.length]);
  await p.keyboard.press('Control+z'); await p.waitForTimeout(400);
  await ev(() => ['undo', state.combos.size, display.length]);
  await p.keyboard.press('m'); await click(100, 60, 'Shift');               // shift+click merge back (crack tool)
  await ev(() => ['shift-merge', tools.crack, display.length]);
  await p.keyboard.press('c'); await click(100, 0); await p.keyboard.press('Escape');
  await ev(() => ['esc', sel.size, tools.crack]);
  await p.setViewportSize({ width: 600, height: 850 }); await p.waitForTimeout(500);
  await ev(() => ['narrow', document.body.className]);
  await p.setViewportSize({ width: 1400, height: 850 }); await p.waitForTimeout(500);
  await ev(() => ['wide again', document.body.className]);
  console.log(logs.join('\n')); await b.close();
})();
