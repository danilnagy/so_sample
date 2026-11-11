import { expect, test } from '@playwright/test';

/**
 * Offline use: after one online visit the service worker holds the build, so the app, the
 * guide and a first launch (the bundled kits and projects added from the cache) all work
 * with the network off.
 */
test('after one visit the app opens, shows the guide and adds its presets without a network', async ({ page, context }) => {
  await page.goto('/?nowelcome');
  await expect(page.locator('.topbar')).toBeVisible({ timeout: 90000 });
  await page.evaluate(() => navigator.serviceWorker.ready);
  await page.reload();
  await expect(page.locator('.topbar')).toBeVisible();
  expect(await page.evaluate(() => !!navigator.serviceWorker.controller)).toBe(true);

  await context.setOffline(true);
  await page.reload();
  await expect(page.locator('.topbar')).toBeVisible();
  await page.goto('/guide?nowelcome');
  await expect(page.locator('.guide h1')).toHaveText('Guide');

  // A first launch while offline: an empty library gets the bundled kits and projects from the cache.
  await page.evaluate(() => new Promise<void>((done) => {
    const request = indexedDB.deleteDatabase('sosample');
    request.onsuccess = request.onerror = request.onblocked = () => done();
  }));
  await page.goto('/?nowelcome');
  await expect(page.locator('.topbar')).toBeVisible({ timeout: 90000 });
  await expect
    .poll(() =>
      page.evaluate(async () => {
        const open = indexedDB.open('sosample');
        const db = await new Promise<IDBDatabase>((done) => (open.onsuccess = () => done(open.result)));
        const count = (store: string) => new Promise<number>((done) => {
          const request = db.transaction(store).objectStore(store).count();
          request.onsuccess = () => done(request.result);
        });
        return [await count('kits'), await count('projects')];
      }),
    )
    .toEqual([7, 10]);
});
