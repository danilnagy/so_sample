import { expect, test, type Page } from '@playwright/test';

import { closeAll, dismissNotice, expectFitsWidth, seed } from './helpers';

/**
 * Every modal and popup at phone widths: each must fit the screen without sideways
 * scrolling, wrapping onto more lines instead, and match its screenshot baseline.
 */
test.describe('modals at phone width', () => {
  test.beforeEach(async ({ page }) => {
    await seed(page);
  });

  /** A press outside the pads and the parameter row, in the gap under the view bar, which drops a step selection. */
  const pressAway = async (page: Page) => {
    const bar = (await page.locator('.viewbar').boundingBox())!;
    await page.mouse.click(bar.x + bar.width / 2, bar.y + bar.height + 4);
  };

  const check = async (page: Page, name: string) => {
    await page.mouse.move(0, 0);
    await expectFitsWidth(page);
    await expect(page).toHaveScreenshot(`${name}.png`);
  };

  test('projects menu', async ({ page }) => {
    await page.click('.topbar button:has-text("Projects")');
    await expect(page.locator('.menu .items')).toBeVisible();
    await check(page, 'projects-menu');
  });

  test('device menu and dialogs', async ({ page }) => {
    await page.click('.topbar button:has-text("Device")');
    await check(page, 'device-menu');
    await page.click('.menu .items button:has-text("Send to PO-33")');
    await expect(page.locator('.modal header')).toContainText('Send to PO-33');
    await check(page, 'device-send');
    await closeAll(page);
    await page.click('.topbar button:has-text("Device")');
    await page.click('.menu .items button:has-text("Import from PO-33")');
    await expect(page.locator('.modal header')).toContainText('Import from PO-33');
    await check(page, 'device-import');
  });

  test('library, inline sample editor and folder picker', async ({ page }) => {
    await page.click('.topbar button:has-text("Library")');
    await expect(page.locator('.library tr.sample')).toHaveCount(2);
    // The heading's select-all box sits over the rows' boxes.
    const headBox = await page.locator('.library thead input[type=checkbox]').boundingBox();
    const rowBox = await page.locator('.library tr.sample input[type=checkbox]').first().boundingBox();
    expect(Math.abs(headBox!.x - rowBox!.x)).toBeLessThan(1);
    // The shape keeps the row height everywhere, drawn narrower here.
    const wave = await page.locator('.library tr.sample .miniwave').first().boundingBox();
    expect(wave!.height).toBe(19);
    await check(page, 'library');
    await page.locator('.library tr.sample td.name').first().click();
    await expect(page.locator('.sample-editor')).toBeVisible();
    await expect(page.locator('.library tr.sample')).toHaveCount(1);
    await check(page, 'library-sample-editor');
    await page.click('.sample-editor button:has-text("Done")');
    // The picker opens from a row's folder and moving the sample takes effect.
    const rhodes = page.locator('.library tr.sample').filter({ hasText: 'Rhodes' });
    await rhodes.locator('td.folder button').click();
    await expect(page.locator('.folder-picker')).toBeVisible();
    // Entries stack without overlapping, each a full button tall, from the moment it opens.
    const boxes = await page.locator('.folder-picker .choices button').evaluateAll((els) => els.map((el) => el.getBoundingClientRect()).map((r) => [r.top, r.bottom, r.height]));
    expect(boxes.length).toBeGreaterThan(1);
    for (const [, , h] of boxes) expect(h).toBe(28);
    for (let i = 1; i < boxes.length; i++) expect(boxes[i][0]).toBeGreaterThanOrEqual(boxes[i - 1][1]);
    await check(page, 'library-folder-picker');
    await page.locator('.folder-picker .choices button', { hasText: 'Drums' }).click();
    await expect(rhodes.locator('td.folder')).toContainText('Drums');
  });

  test('library folder bar renames and keeps its folder across layouts', async ({ page }) => {
    await page.click('.topbar button:has-text("Library")');
    await page.locator('.library .folders button', { hasText: 'Drums' }).click();
    await expect(page.locator('.library tr.sample')).toHaveCount(1);
    const bar = page.locator('.library .folder-bar');
    await expect(bar).toContainText('Drums');
    await expect(bar).toContainText('1 sample');
    await check(page, 'library-folder-bar');
    // Growing to the desktop layout and back keeps the folder selected.
    const { width, height } = page.viewportSize()!;
    await page.setViewportSize({ width: 1280, height: 900 });
    await expect(page.locator('.library .folders button.on')).toHaveText('Drums');
    await expect(page.locator('.library tr.sample')).toHaveCount(1);
    await page.setViewportSize({ width, height });
    await expect(bar).toContainText('Drums');
    // Rename from the bar.
    await bar.locator('button', { hasText: 'Rename' }).click();
    await page.fill('.folder-bar input', 'Percussion');
    await page.keyboard.press('Enter');
    await expect(bar).toContainText('Percussion');
    await expect(page.locator('.library tr.sample td.folder')).toContainText('Percussion');
  });

  test('library choosing for a sound, with a selection', async ({ page }) => {
    await page.click('.viewbar button:has-text("Sound")');
    await page.click('.grid.sounds [aria-label^="Sound 2:"]');
    await expect(page.locator('.modal header')).toContainText('choosing a sample for Sound 2');
    await page.locator('.library thead input[type=checkbox]').check();
    await expect(page.locator('.modal header')).toContainText('2 selected');
    await check(page, 'library-target-selected');
  });

  test('clip editor', async ({ page }) => {
    await page.click('.viewbar button:has-text("Sound")');
    await page.click('.grid.sounds [aria-label^="Sound 1:"]');
    await expect(page.locator('.modal.editor canvas.waveform')).toBeVisible();
    await check(page, 'clip-editor');
  });

  test('kit editor, kits menu and a key window', async ({ page }) => {
    await page.click('.viewbar button:has-text("Sound")');
    await page.click('.grid.sounds [aria-label^="Sound 11:"]');
    await expect(page.locator('.modal.editor .kit')).toBeVisible();
    await check(page, 'kit-editor');
    // The filled pad is the current key: key 1 at first; tapping another filled key moves it and the play button follows.
    await expect(page.locator('.modal.editor .kit .pad.current .pad-key')).toHaveText('1');
    await page.locator('.modal.editor .kit .pad.empty').first().click();
    await page.locator('.library tr.sample').filter({ hasText: 'Kick' }).locator('button:has-text("Use")').click();
    await expect(page.locator('.modal.wide')).toHaveCount(0);
    await page.locator('.modal.editor .kit .pad:not(.empty)').nth(1).click();
    await expect(page.locator('.modal.editor .kit .pad.current .pad-key')).toHaveText('2');
    await page.click('.modal.editor button:has-text("Kits")');
    await expect(page.locator('.kits-menu')).toBeVisible();
    await check(page, 'kit-editor-kits-menu');
    // The button closes its own menu; Escape would close the editor with it.
    await page.click('.modal.editor button:has-text("Kits")');
    await page.click('[aria-label="Edit Sound 11 key 1"]');
    await expect(page.locator('.modal.editor canvas.waveform')).toBeVisible();
    await check(page, 'kit-key-window');
  });

  test('project memory', async ({ page }) => {
    await page.click('.statusbar .memory');
    await expect(page.locator('table.memory tbody tr')).toHaveCount(2);
    // The heading's Sample label starts over the names, Pages ends over the page counts, and the shape keeps its height.
    const sampleHead = await page.locator('table.memory thead th:nth-child(2)').boundingBox();
    const name = await page.locator('table.memory tbody td:nth-child(2)').first().boundingBox();
    expect(Math.abs(sampleHead!.x - name!.x)).toBeLessThan(1);
    const pagesHead = await page.locator('table.memory thead th:nth-child(7)').boundingBox();
    const pages = await page.locator('table.memory tbody td:nth-child(7)').first().boundingBox();
    expect(Math.abs(pagesHead!.x + pagesHead!.width - (pages!.x + pages!.width))).toBeLessThan(1);
    expect((await page.locator('table.memory .miniwave').first().boundingBox())!.height).toBe(19);
    await check(page, 'memory');
  });

  test('pattern picker and tempo popover', async ({ page }) => {
    await page.click('.viewbar button:has-text("Song")');
    await page.click('.song-add');
    await expect(page.locator('.pattern-picker')).toBeVisible();
    await check(page, 'pattern-picker');
    await closeAll(page);
    await page.click('.statusbar .tempo-button');
    await expect(page.locator('.tempo-popover')).toBeVisible();
    await check(page, 'tempo-popover');
  });

  test('sequence parameter row edits the selected step', async ({ page }) => {
    await page.click('.viewbar button:has-text("Pattern")');
    const pads = page.locator('.pad-grid .pad.step');
    // No step selected: the row is there but disabled. Two notes; the last tapped step is selected and outlined, and the row wakes.
    await expect(page.locator('.param-row')).toHaveClass(/disabled/);
    await expect(page.locator('.param-slider')).toBeDisabled();
    const padsTop = (await page.locator('.pad-grid').boundingBox())!.y;
    await pads.nth(0).click();
    await pads.nth(4).click();
    await expect(pads.nth(4)).toHaveClass(/selected/);
    await expect(page.locator('.pad-grid .pad.step.selected')).toHaveCount(1);
    await expect(page.locator('.param-row')).not.toHaveClass(/disabled/);
    expect((await page.locator('.pad-grid').boundingBox())!.y).toBe(padsTop);
    // Volume of step 5 lowered: the value reads in dB; step 5 changes the volume and step 1, round the loop, changes it back, so both get the dot.
    await page.selectOption('.param-select', 'volume');
    await page.locator('.param-slider').fill('20');
    await expect(page.locator('.param-value')).toHaveClass(/locked/);
    await expect(pads.nth(4)).toHaveClass(/changed/);
    await expect(pads.nth(0)).toHaveClass(/changed/);
    // Selecting step 1 shows its own value; tapping the selected note removes it.
    await pads.nth(0).click();
    await expect(pads.nth(0)).toHaveClass(/selected/);
    await expect(pads.nth(0)).toHaveClass(/note/);
    await check(page, 'sequence-parameters');
    await pads.nth(0).click();
    await expect(pads.nth(0)).not.toHaveClass(/note/);
    // Two more notes copy step 5's parameters, so nothing changes any more; a new filter and pitch on step 5 do.
    await pads.nth(8).click();
    await pads.nth(12).click();
    await expect(page.locator('.pad-grid .pad.step.changed')).toHaveCount(0);
    await pads.nth(4).click();
    await page.selectOption('.param-select', 'filter');
    await page.locator('.param-slider').fill('40');
    await page.selectOption('.param-select', 'pitch');
    await page.locator('.param-slider').fill('15');
    await expect(pads.nth(4)).toHaveClass(/changed/);
    // Clear removes the chosen lock alone; Clear all the rest, and the dots go.
    await page.click('.param-clear');
    await expect(page.locator('.param-clear')).toBeDisabled();
    await expect(pads.nth(4)).toHaveClass(/changed/);
    await page.click('.param-clear-all');
    await expect(page.locator('.pad-grid .pad.step.changed')).toHaveCount(0);
    await expect(page.locator('.param-clear-all')).toBeDisabled();
    // A press outside the pads and the row drops the selection; the row stays, disabled.
    await pressAway(page);
    await expect(page.locator('.pad-grid .pad.step.selected')).toHaveCount(0);
    await expect(page.locator('.param-row')).toHaveClass(/disabled/);
  });

  test('FX view carries pattern and effects actions; a pattern copy finishes in the strip', async ({ page }) => {
    await page.click('.viewbar button:has-text("Pattern")');
    await page.locator('.pad-grid .pad.step').nth(0).click();
    await page.click('.viewbar button:has-text("FX")');
    await expect(page.locator('.context .group')).toHaveCount(2);
    await expectFitsWidth(page);
    // The pattern's actions start at the bar's left edge.
    const bar = (await page.locator('.mobile .context').boundingBox())!;
    const firstGroup = (await page.locator('.context .group').first().boundingBox())!;
    expect(Math.abs(firstGroup.x - bar.x)).toBeLessThan(1);
    await page.locator('.context .group', { hasText: 'Pattern' }).locator('button', { hasText: 'Copy' }).click();
    await expect(page.locator('.context .hint')).toHaveText('Copy pattern 1 to…');
    await page.locator('.patterns.compact .pattern', { hasText: /^3$/ }).click();
    await expect(page.locator('.patterns.compact .pattern', { hasText: /^3$/ })).toHaveClass(/filled/);
    await expect(page.locator('.patterns.compact .pattern', { hasText: /^3$/ })).toHaveClass(/on/);
    await check(page, 'fx-actions');
  });

  test('sound list: the label column with mute, solo and a playback monitor, under the strip', async ({ page }) => {
    // Notes on every step of Sound 1, so the monitor lights for the whole bar.
    await page.click('.viewbar button:has-text("Pattern")');
    await page.selectOption('.sound-select', '1');
    for (let i = 0; i < 16; i++) await page.locator('.pad-grid .pad.step').nth(i).click();
    await pressAway(page);
    await page.click('.viewbar button:has-text("Sound")');
    await expect(page.locator('.patterns.compact')).toHaveCount(1);
    await expect(page.locator('.grid.sounds > .label')).toHaveCount(16);
    await expect(page.locator('.grid.sounds .monitor')).toHaveCount(16);
    await expect(page.locator('.grid.sounds .play-column')).toHaveCount(16);
    await expect(page.locator('.grid.sounds .play-column').first()).toBeEnabled();
    await expect(page.locator('.grid.sounds .play-column').nth(1)).toBeDisabled();
    // An audition from the play button lights the monitor over it with the key, and the tile takes no taps.
    await page.locator('.grid.sounds .play-column').first().click();
    const first = page.locator('.grid.sounds .monitor').first();
    // The sample lasts half a second: one poll catches the tile lit with its key.
    await expect.poll(() => first.evaluate((el) => (el.classList.contains('on') ? el.textContent : null)), { timeout: 3000 }).toBe('5');
    expect(await first.evaluate((el) => getComputedStyle(el).pointerEvents)).toBe('none');
    await expect(first).not.toHaveClass(/\bon\b/, { timeout: 5000 });
    await expect(page.locator('.grid.sounds > .mix')).toHaveCount(32);
    await expect(page.locator('.grid.sounds > .label').first()).toContainText('Rhodes');
    await expect(page.locator('.grid.sounds > .label.empty').nth(0)).toContainText('Add sample…');
    await expect(page.locator('.grid.sounds .miniwave')).toHaveCount(1);
    await check(page, 'sound-list');
    // Playing: Sound 1's monitor shows key 5 at every step; the others stay blank.
    await page.click('.statusbar .transport');
    await expect(page.locator('.grid.sounds .monitor').first()).toHaveClass(/\bon\b/);
    await expect(page.locator('.grid.sounds .monitor').first()).toHaveText('5');
    await expect(page.locator('.grid.sounds .monitor.on')).toHaveCount(1);
    await page.click('.statusbar .transport');
    await expect(page.locator('.grid.sounds .monitor.on')).toHaveCount(0);
    // The view bar stays put when the list scrolls.
    const list = page.locator('.grid.sounds');
    if (await list.evaluate((el) => el.scrollHeight > el.clientHeight)) {
      const barTop = (await page.locator('.viewbar').boundingBox())!.y;
      await list.evaluate((el) => (el.scrollTop = 200));
      expect((await page.locator('.viewbar').boundingBox())!.y).toBe(barTop);
      await list.evaluate((el) => (el.scrollTop = 0));
    }
    // Tapping a header opens its editor and makes it the Pattern view's sound.
    await page.click('.grid.sounds [aria-label^="Sound 11:"]');
    await expect(page.locator('.modal.editor .kit')).toBeVisible();
    await closeAll(page);
    await page.click('.viewbar button:has-text("Pattern")');
    await expect(page.locator('.sound-select')).toHaveValue('11');
  });

  test('theme button cycles system, light and dark', async ({ page }) => {
    const theme = () => page.evaluate(() => document.documentElement.dataset.theme ?? 'system');
    await expect(page.locator('.topbar select')).toBeHidden();
    const button = page.locator('.topbar .theme-button');
    await expect(button).toBeVisible();
    expect(await theme()).toBe('system');
    await button.click();
    expect(await theme()).toBe('light');
    await button.click();
    expect(await theme()).toBe('dark');
    await expect(button).toHaveAttribute('aria-label', /Theme: Dark/);
    await dismissNotice(page);
    await check(page, 'view-pattern-dark');
    await button.click();
    expect(await theme()).toBe('system');
    // The choice is saved.
    await button.click();
    await page.reload();
    await page.waitForSelector('.viewbar');
    expect(await theme()).toBe('light');
  });

  test('song rows: a tap selects, the arrows and a drag reorder, the trash removes', async ({ page }) => {
    await page.click('.viewbar button:has-text("Song")');
    const rows = page.locator('.song-row');
    const order = () => rows.locator('.pattern-number').allTextContents();
    // Two more entries from the picker: 1, 3, 5.
    for (const n of ['3', '5']) {
      await page.click('.song-add');
      await page.click(`.pattern-picker button:text-is("${n}")`);
    }
    expect(await order()).toEqual(['Pattern 1', 'Pattern 3', 'Pattern 5']);
    await expect(page.locator('.song-row .icon-button')).toHaveCount(9);
    await expect(rows.nth(0).locator('[aria-label$="up"]')).toBeDisabled();
    await expect(rows.nth(2).locator('[aria-label$="down"]')).toBeDisabled();
    // A tap selects; the selection follows a move.
    await rows.nth(2).locator('.entry').click();
    await expect(rows.nth(2)).toHaveClass(/\bon\b/);
    await check(page, 'song-rows');
    await rows.nth(2).locator('[aria-label$="up"]').click();
    expect(await order()).toEqual(['Pattern 1', 'Pattern 5', 'Pattern 3']);
    await expect(rows.nth(1)).toHaveClass(/\bon\b/);
    // A drag by the handle: the first row to the end.
    const from = (await rows.nth(0).locator('.handle').boundingBox())!;
    const to = (await rows.nth(2).boundingBox())!;
    await page.mouse.move(from.x + from.width / 2, from.y + from.height / 2);
    await page.mouse.down();
    await page.mouse.move(from.x + from.width / 2, to.y + to.height / 2, { steps: 8 });
    await page.mouse.up();
    expect(await order()).toEqual(['Pattern 5', 'Pattern 3', 'Pattern 1']);
    // The trash removes a row; the song keeps its last entry.
    await rows.nth(0).locator('[aria-label^="Remove"]').click();
    expect(await order()).toEqual(['Pattern 3', 'Pattern 1']);
    await rows.nth(0).locator('[aria-label^="Remove"]').click();
    await expect(rows.nth(0).locator('[aria-label^="Remove"]')).toBeDisabled();
    expect(await order()).toEqual(['Pattern 1']);
  });

  test('bottom bar: one row, glyphs on the narrowest screens, notices as a toast', async ({ page }) => {
    await page.click('.statusbar .mode button[aria-label="Song"]');
    const bar = (await page.locator('.statusbar').boundingBox())!;
    expect(bar.height).toBeLessThan(44);
    const controls = await page.locator('.statusbar .transport-group > *, .statusbar .transport-group .mode > *').evaluateAll((els) => els.map((el) => Math.round(el.getBoundingClientRect().top)));
    expect(new Set(controls).size).toBe(1);
    // Under 480px the words give way to glyphs, with the accessible names kept.
    await expect(page.locator('.statusbar .transport .glyph')).toBeVisible();
    await expect(page.locator('.statusbar .transport .word')).toBeHidden();
    await expect(page.locator('.statusbar button[aria-label="Follow"] .glyph')).toHaveText('F');
    await expect(page.locator('.statusbar button[aria-label="Follow"]')).toBeEnabled();
    await page.click('.statusbar .mode button[aria-label="Pattern"]');
    await expect(page.locator('.statusbar button[aria-label="Follow"]')).toBeDisabled();
    await page.click('.statusbar .mode button[aria-label="Song"]');
    await expectFitsWidth(page);
    await check(page, 'bottom-bar-song');
    // A notice is a toast over the bar, gone on a tap: saving Sound 11's kit again says so.
    await page.click('.viewbar button:has-text("Sound")');
    await page.click('.grid.sounds [aria-label^="Sound 11:"]');
    await page.click('.modal.editor button:has-text("Kits")');
    await page.click('.kits-menu button:has-text("Save this kit")');
    await expect(page.locator('.toast')).toBeVisible();
    await expect(page.locator('.toast')).toContainText('Saved kit');
    await page.locator('.toast').click();
    await expect(page.locator('.toast')).toHaveCount(0);
  });

  test('pad views', async ({ page }) => {
    for (const view of ['Sound', 'FX', 'Pattern', 'Song']) {
      await page.click(`.viewbar button:has-text("${view}")`);
      await dismissNotice(page);
      await check(page, `view-${view.toLowerCase()}`);
    }
  });
});
