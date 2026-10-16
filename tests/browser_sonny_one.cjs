/* Optional real-browser integration check. Start the loopback demo first. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.SONNY_DEMO_URL || 'http://127.0.0.1:8765';
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    for (const viewport of [{width:1440,height:1000},{width:768,height:1024},{width:390,height:844},{width:320,height:740}]) {
      const context = await browser.newContext({viewport});
      await context.route('**/*', route => new URL(route.request().url()).origin === base ? route.continue() : route.abort());
      const page = await context.newPage();
      const errors = []; page.on('pageerror', e => errors.push(String(e)));
      await page.goto(base);
      await page.getByRole('status').filter({hasText:'Local server connected'}).waitFor();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      if (process.env.SONNY_SCREENSHOT_DIR) {
        fs.mkdirSync(process.env.SONNY_SCREENSHOT_DIR, {recursive:true});
        await page.screenshot({path:path.join(process.env.SONNY_SCREENSHOT_DIR, `sonny-${viewport.width}.png`), fullPage:true});
      }
      await page.getByRole('button', {name:'Help me plan', exact:true}).click();
      await page.getByText('This is a fixed demo plan', {exact:false}).waitFor();
      await page.locator('#memory-input').fill('<img src=x onerror=alert(1)> sample');
      await page.getByRole('button', {name:'Save approved fact'}).click();
      await page.locator('#message').fill('What do you remember?');
      await page.locator('#send').click();
      await page.locator('.assistant').last().filter({hasText:'<img src=x onerror=alert(1)> sample'}).waitFor();
      assert.equal(await page.locator('#memories img').count(), 0);
      assert.equal(await page.evaluate(() => localStorage.length), 0);
      await page.reload();
      assert.equal(await page.locator('#memory-count').textContent(), '0');
      await page.locator('#persist').check();
      await page.locator('#memory-input').fill('Sample preference');
      await page.getByRole('button', {name:'Save approved fact'}).click();
      await page.reload();
      assert.equal(await page.locator('#memory-count').textContent(), '1');
      await page.getByRole('button', {name:'Forget Sample preference'}).click();
      await page.reload();
      assert.equal(await page.locator('#memory-count').textContent(), '0');
      await page.route('**/api/chat', route => route.abort());
      await page.locator('#message').fill('Help me plan');
      await page.locator('#send').click();
      await page.locator('#error').filter({hasText:'Unable to reach'}).waitFor();
      assert.equal(await page.locator('#message').inputValue(), 'Help me plan');
      assert.equal(await page.locator('#send').isEnabled(), true);
      await page.unroute('**/api/chat');
      await page.locator('#send').click();
      await page.locator('.assistant').waitFor();
      await page.getByRole('button', {name:'New conversation'}).click();
      assert.equal(await page.locator('.message').count(), 0);
      await page.getByRole('button', {name:'Erase workspace'}).click();
      assert.equal(await page.evaluate(() => localStorage.getItem('sonny-one-demo-v1')), null);
      // Invalid saved records must not crash the app or become approved facts.
      await page.evaluate(() => localStorage.setItem('sonny-one-demo-v1', JSON.stringify({goal:'demo',memories:['fact'],messages:[null]})));
      await page.reload();
      assert.equal(await page.locator('#memory-count').textContent(), '0');
      await page.locator('#error').filter({hasText:'invalid'}).waitFor();
      await page.getByRole('button', {name:'Erase workspace'}).click();
      // A delayed or malformed response must not destroy an edited draft.
      let release;
      const waiting = new Promise(resolve => {release = resolve;});
      await page.route('**/api/chat', async route => {await waiting; await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({text:'Demo response'})});});
      await page.locator('#message').fill('first request');
      await page.locator('#send').click();
      await page.locator('#reply-status').filter({hasText:'Preparing'}).waitFor();
      await page.locator('#message').fill('next unsent draft'); release();
      await page.locator('.assistant').filter({hasText:'Demo response'}).waitFor();
      assert.equal(await page.locator('#message').inputValue(), 'next unsent draft');
      await page.unroute('**/api/chat');
      await page.route('**/api/chat', route => route.fulfill({status:200,contentType:'application/json',body:'{}'}));
      await page.locator('#send').click();
      await page.locator('#error').filter({hasText:'Unable to reach'}).waitFor();
      assert.equal(await page.locator('.message').count(), 2);
      await page.unroute('**/api/chat');
      await page.evaluate(() => navigator.serviceWorker.ready);
      await page.waitForFunction(() => navigator.serviceWorker.controller !== null);
      const cachedPaths = await page.evaluate(async () => {
        const cache = await caches.open('sonny-one-shell-v1');
        return (await cache.keys()).map(request => new URL(request.url).pathname);
      });
      assert.ok(cachedPaths.includes('/'));
      assert.equal(cachedPaths.some(p => p.startsWith('/api/')), false);
      await context.setOffline(true);
      await page.reload();
      await page.locator('#connection').filter({hasText:'unavailable'}).waitFor();
      await page.locator('#message').fill('Offline draft');
      await page.locator('#send').click();
      await page.locator('#error').filter({hasText:'Unable to reach'}).waitFor();
      assert.equal(await page.locator('#message').inputValue(), 'Offline draft');
      await context.setOffline(false);
      assert.deepEqual(errors, []);
      console.log(`PASS ${viewport.width}x${viewport.height}: chat, consent, persistence, forgetting, erasure, injection, retry, drafts, corrupt storage, offline shell, layout`);
      await context.close();
    }
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
