import { expect, test } from '@playwright/test';

import { expectFitsWidth } from './helpers';

/** The first-visit welcome, the help button and the guide with its live examples. */
test.describe('welcome and guide', () => {
  test('a first visit shows the welcome; dismissed, it stays away', async ({ page }) => {
    await page.goto('/?nopresets');
    const welcome = page.locator('.modal.welcome');
    await expect(welcome).toBeVisible();
    await expect(welcome.locator('button', { hasText: 'Open the guide' })).toBeVisible();
    await expectFitsWidth(page);
    await expect(page).toHaveScreenshot('welcome.png');
    await welcome.locator('button', { hasText: 'Start making' }).click();
    await expect(welcome).toHaveCount(0);
    await page.reload();
    await page.waitForSelector('.topbar');
    await page.waitForTimeout(300);
    await expect(welcome).toHaveCount(0);
  });

  test("the welcome's Open the guide switches to the guide layout", async ({ page }) => {
    await page.goto('/?nopresets');
    await page.locator('.modal.welcome button', { hasText: 'Open the guide' }).click();
    await expect(page).toHaveURL(/\/guide/);
    await expect(page.locator('.guide h1')).toHaveText('Guide');
    await expect(page.locator('.modal.welcome')).toHaveCount(0);
  });

  test('the ? button switches the same app to its guide layout and back, on the same project', async ({ page }) => {
    await page.goto('/?nowelcome');
    await page.waitForSelector('.topbar', { timeout: 60000 });
    await page.fill('.topbar .name', 'Kept');
    const help = page.locator('.topbar .help-button');
    await help.click();
    await expect(page).toHaveURL(/\/guide/);
    await expect(help).toHaveAttribute('aria-pressed', 'true');
    // Every view on one page, each mounted once: the sequencer, the four phone views, the library, the editors, memory, both device dialogs.
    await expect(page.locator('.guide .grid:not(.sounds)')).toHaveCount(1);
    await expect(page.locator('.guide .grid.sounds')).toHaveCount(1);
    await expect(page.locator('.guide .song-list')).toHaveCount(1);
    await expect(page.locator('.guide .param-row')).toHaveCount(1);
    await expect(page.locator('.guide .library')).toHaveCount(1);
    await expect(page.locator('.guide #guide-send .modal, .guide #guide-import .modal')).toHaveCount(2);
    await expect(page.locator('.topbar')).toHaveCount(1);
    await expect(page.locator('.statusbar')).toHaveCount(1);
    const wide = await page.evaluate(() => {
      const out: string[] = [];
      for (const el of document.querySelectorAll('body *')) {
        const r = el.getBoundingClientRect();
        if (r.right > innerWidth + 1 && !el.closest('.guide-frame')) out.push(`${el.tagName}.${String(el.className)} ${Math.round(r.right)}`);
      }
      return [document.documentElement.scrollWidth, innerWidth, ...out.slice(0, 6)];
    });
    expect(wide[0] <= wide[1], JSON.stringify(wide)).toBe(true);
    // The guide edits the real project: a note added on a phone pad shows in the sequencer too.
    await expect(page.locator('.topbar .name')).toHaveValue('Kept');
    await page.locator('.guide .pad-grid .pad.step').first().click();
    await expect(page.locator('.guide .grid:not(.sounds) .cell[data-step="1"][data-sound="1"]')).toHaveClass(/note/);
    // Opening an editor scrolls to it on the page rather than over it.
    await page.locator('.guide .grid:not(.sounds) [aria-label^="Sound 11:"]').click();
    await expect(page.locator('.modal-backdrop .modal.editor .kit')).toHaveCount(1);
    await expect(page.locator('#guide-kit')).toBeInViewport();
    // Back to the usual layout, by the button and by the browser's back button.
    await help.click();
    await expect(page).not.toHaveURL(/\/guide/);
    await expect(page.locator('.guide')).toHaveCount(0);
    await page.goBack();
    await expect(page.locator('.guide')).toHaveCount(1);
    await page.goBack();
    await expect(page.locator('.guide')).toHaveCount(0);
    await expect(page.locator('.topbar .name')).toHaveValue('Kept');
  });

  test('in a frame narrower than them, the pattern bar and FX row keep their columns and the frame scrolls', async ({ page }) => {
    await page.goto('/guide?nopresets&nowelcome');
    const frame = page.locator('.guide-frame', { has: page.locator('.patterns') }).first();
    await expect(frame).toBeVisible();
    const lefts = (sel: string) => frame.locator(sel).evaluateAll((els) => els.map((e) => Math.round(e.getBoundingClientRect().left)));
    const patterns = await lefts('.patterns button.pattern');
    expect(patterns).toHaveLength(16);
    expect(await lefts('.fxrow label.fx')).toEqual(patterns);
    // At a phone's width the frame is narrower than the bars: it scrolls inside, the page does not.
    expect(await frame.evaluate((f) => f.scrollWidth > f.clientWidth)).toBe(true);
    expect(await page.locator('.guide').evaluate((g) => g.scrollWidth - g.clientWidth)).toBe(0);
  });
});
