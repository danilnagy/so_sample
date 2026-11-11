import { expect, type Page } from '@playwright/test';

/** A short 16-bit mono WAV of a decaying tone: deterministic, so the waveform draws the same every run. */
export function toneWav(seconds = 0.5, rate = 22050): Buffer {
  const n = Math.round(seconds * rate);
  const data = Buffer.alloc(n * 2);
  for (let i = 0; i < n; i++) {
    const t = i / rate;
    const v = Math.sin(2 * Math.PI * 220 * t) * Math.exp(-t * 6) * 0.8;
    data.writeInt16LE(Math.round(v * 32767), i * 2);
  }
  const header = Buffer.alloc(44);
  header.write('RIFF', 0);
  header.writeUInt32LE(36 + data.length, 4);
  header.write('WAVE', 8);
  header.write('fmt ', 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(1, 22);
  header.writeUInt32LE(rate, 24);
  header.writeUInt32LE(rate * 2, 28);
  header.writeUInt16LE(2, 32);
  header.writeUInt16LE(16, 34);
  header.write('data', 36);
  header.writeUInt32LE(data.length, 40);
  return Buffer.concat([header, data]);
}

/** Taps the notice toast away if one shows, so screenshots do not depend on its timer. */
export async function dismissNotice(page: Page): Promise<void> {
  const toast = page.locator('.toast');
  if (await toast.count()) await toast.click().catch(() => {});
  await page.mouse.move(0, 0);
}

/** Closes whatever is open: menus, pickers, then modals, outermost last. */
export async function closeAll(page: Page): Promise<void> {
  for (let i = 0; i < 5; i++) {
    await page.keyboard.press('Escape');
    await page.waitForTimeout(50);
  }
}

/**
 * Opens the app in a fresh browser profile and fills it with enough to show every surface:
 * two library samples, one of them in a folder, one on Sound 1, one on key 1 of Sound 11,
 * and that kit saved under a name.
 */
export async function seed(page: Page): Promise<void> {
  page.on('dialog', (d) => d.accept());
  // Without the presets: the tests build the little they need themselves.
  await page.goto('/?nopresets&nowelcome');
  await page.waitForSelector('.topbar');
  await page.click('.topbar button:has-text("Library")');
  await page.locator('.modal.wide input[type=file]').setInputFiles([
    { name: 'Rhodes chord long name for wrapping.wav', mimeType: 'audio/wav', buffer: toneWav(0.5) },
    { name: 'Kick.wav', mimeType: 'audio/wav', buffer: toneWav(0.2) },
  ]);
  await expect(page.locator('.library tr.sample')).toHaveCount(2);
  // The kick goes into a folder, typed into its row's folder picker.
  await page.locator('.library tr.sample').filter({ hasText: 'Kick' }).locator('td.folder button').click();
  await page.fill('.folder-picker input', 'Drums');
  await page.keyboard.press('Enter');
  await expect(page.locator('.library tr.sample').filter({ hasText: 'Kick' }).locator('td.folder')).toContainText('Drums');
  await closeAll(page);
  // Sound 1 takes the first sample.
  await page.click('.viewbar button:has-text("Sound")');
  await page.click('.grid.sounds [aria-label^="Sound 1:"]');
  await page.locator('.library tr.sample').filter({ hasText: 'Rhodes' }).locator('button:has-text("Use")').click();
  await expect(page.locator('.modal.wide')).toHaveCount(0);
  // Key 1 of Sound 11 takes the second, and the kit is saved.
  await page.click('.grid.sounds [aria-label^="Sound 11:"]');
  await page.locator('.modal.editor .kit .pad.empty').first().click();
  await page.locator('.library tr.sample').filter({ hasText: 'Kick' }).locator('button:has-text("Use")').click();
  await expect(page.locator('.modal.wide')).toHaveCount(0);
  await page.fill('.modal.editor input.kit-name', 'Test kit');
  await page.click('.modal.editor button:has-text("Kits")');
  await page.click('.kits-menu button:has-text("Save this kit")');
  await closeAll(page);
  // Back to the Pattern view, the app's default, so every modal is photographed over the same background.
  await page.click('.viewbar button:has-text("Pattern")');
  await dismissNotice(page);
}

/**
 * The layout check behind every visual test: the page is no wider than the screen, nothing
 * visible reaches past its edges, and nothing scrolls sideways (an ellipsis is not a scroll).
 */
export async function expectFitsWidth(page: Page): Promise<void> {
  const issues = await page.evaluate(() => {
    const vw = window.innerWidth;
    const out: string[] = [];
    if (document.documentElement.scrollWidth > vw) out.push(`page ${document.documentElement.scrollWidth} > ${vw}`);
    const name = (el: Element) => `${el.tagName.toLowerCase()}${el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : ''}`;
    for (const el of document.querySelectorAll('body *')) {
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      const cs = getComputedStyle(el);
      if (cs.visibility === 'hidden') continue;
      if (r.right > vw + 0.5 || r.left < -0.5) out.push(`${name(el)} spans ${Math.round(r.left)}..${Math.round(r.right)}`);
      const scrolls = cs.overflowX === 'auto' || cs.overflowX === 'scroll' || cs.overflowX === 'hidden';
      if (scrolls && cs.textOverflow !== 'ellipsis' && el.clientWidth > 0 && el.scrollWidth > el.clientWidth + 1) out.push(`${name(el)} scrolls ${el.clientWidth} < ${el.scrollWidth}`);
    }
    return out.slice(0, 10);
  });
  expect(issues, 'everything fits the width').toEqual([]);
}
