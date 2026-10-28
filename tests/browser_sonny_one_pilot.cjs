/* Disposable authenticated-pilot browser checks. No private accounts or APIs. */
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.SONNY_DEMO_URL || 'http://127.0.0.1:8766';
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    for (const viewport of [{width:1440,height:1000},{width:390,height:844}]) {
      const context = await browser.newContext({viewport});
      await context.route('**/*', route => new URL(route.request().url()).origin === base ? route.continue() : route.abort());
      const page = await context.newPage();
      const errors = [];page.on('pageerror',e => errors.push(String(e)));
      await page.goto(base);
      await page.locator('#login-panel').waitFor({state:'visible'});
      async function snapshot(name) {
        if (!process.env.SONNY_SCREENSHOT_DIR) return;
        fs.mkdirSync(process.env.SONNY_SCREENSHOT_DIR,{recursive:true});
        await page.screenshot({path:path.join(process.env.SONNY_SCREENSHOT_DIR, `pilot-${name}-${viewport.width}.png`),fullPage:true});
      }
      await snapshot('login');
      async function login(username) {
        await page.locator('#username').fill(username);
        await page.locator('#password').fill('public-browser-test-password');
        await page.getByRole('button',{name:'Sign in',exact:true}).click();
        await page.locator('#pilot-shell').waitFor({state:'visible'});
      }
      await login('alice-demo');
      await page.getByRole('button',{name:'Erase workspace',exact:true}).click();
      await page.locator('#erase:not(:disabled)').waitFor();
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),false);
      await page.locator('#goal').fill('ALICE SAMPLE GOAL');
      await page.getByRole('button',{name:'Save goal',exact:true}).click();
      await page.locator('#save-goal:not(:disabled)').waitFor();
      await page.locator('#memory-input').fill('<img src=x> ALICE SAMPLE FACT');
      await page.getByRole('button',{name:'Save approved fact',exact:true}).click();
      await page.getByRole('button',{name:'Forget <img src=x> ALICE SAMPLE FACT',exact:true}).waitFor();
      assert.equal(await page.locator('#memories img').count(),0);
      await page.locator('#message').fill('What do you remember?');
      await page.locator('#send').click();
      await page.locator('.assistant').filter({hasText:'ALICE SAMPLE FACT'}).waitFor();
      await page.reload();
      await page.locator('.assistant').filter({hasText:'ALICE SAMPLE FACT'}).waitFor();
      assert.equal(await page.locator('#goal').inputValue(),'ALICE SAMPLE GOAL');
      await snapshot('workspace');
      assert.equal(await page.evaluate(() => localStorage.length),0);
      const session = (await context.cookies()).find(cookie => cookie.name === 'sonny_one_session');
      assert.ok(session.httpOnly && session.sameSite === 'Strict');
      await page.getByRole('button',{name:'Correct <img src=x> ALICE SAMPLE FACT',exact:true}).click();
      await page.locator('#memory-input').fill('CORRECTED SAMPLE');
      await page.getByRole('button',{name:'Approve correction',exact:true}).click();
      await page.getByRole('button',{name:'Forget CORRECTED SAMPLE',exact:true}).waitFor();
      await page.getByRole('button',{name:'Forget CORRECTED SAMPLE',exact:true}).click();
      await page.locator('#memory-count').filter({hasText:/^0$/}).waitFor();
      await page.getByRole('button',{name:'New conversation',exact:true}).click();
      await page.locator('.message').first().waitFor({state:'detached'});
      await page.getByRole('button',{name:'Sign out',exact:true}).click();
      await page.locator('#login-panel').waitFor({state:'visible'});
      assert.equal(await page.locator('#chat').textContent(),'');
      assert.equal((await page.request.get(base+'/api/workspace')).status(),401);
      await login('bob-demo');
      assert.equal(await page.locator('#memory-count').textContent(),'0');
      assert.equal(await page.locator('.message').count(),0);
      assert.notEqual(await page.locator('#goal').inputValue(),'ALICE SAMPLE GOAL');
      await context.setOffline(true);
      await page.locator('#message').fill('Help me plan');
      await page.locator('#send').click();
      await page.locator('#error').filter({hasText:'fetch'}).waitFor();
      assert.equal(await page.locator('#message').inputValue(),'Help me plan');
      await context.setOffline(false);
      await page.locator('#send').click();
      await page.locator('.assistant').waitFor();
      await page.getByRole('button',{name:'Erase workspace',exact:true}).click();
      await page.locator('.message').first().waitFor({state:'detached'});
      await page.getByRole('button',{name:'Sign out',exact:true}).click();
      await page.locator('#login-panel').waitFor({state:'visible'});
      assert.deepEqual(errors,[]);
      console.log(`PASS authenticated ${viewport.width}x${viewport.height}: login, cookies, persistence, correction, forget, erasure, logout, account isolation, offline retry`);
      await context.close();
    }
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
