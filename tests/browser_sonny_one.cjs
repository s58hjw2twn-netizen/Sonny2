/* Optional real-browser integration check. Start the loopback demo first. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
      const context = await browser.newContext({viewport});
      await context.route('**/*', route => new URL(route.request().url()).origin === 'http://127.0.0.1:8765' ? route.continue() : route.abort());
      const page = await context.newPage();
      const errors = []; page.on('pageerror', e => errors.push(String(e)));
      await page.goto('http://127.0.0.1:8765');
      await page.getByRole('status').filter({hasText:'Local server connected'}).waitFor();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
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
      assert.deepEqual(errors, []);
      console.log(`PASS ${viewport.width}x${viewport.height}: chat, consent, persistence, forgetting, erasure, injection, retry, layout`);
      await context.close();
    }
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
