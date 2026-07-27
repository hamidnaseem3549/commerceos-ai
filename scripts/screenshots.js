const path = require('path');
const { chromium } = require(path.join(__dirname, '..', 'frontend', 'node_modules', 'playwright'));
const outDir = path.join(__dirname, '..', 'docs', 'images');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
  const page = await context.newPage();
  const base = 'http://localhost:3000';

  async function sendChat(query, waitMs = 12000) {
    const input = await page.$('input[type="text"]');
    if (!input) return;
    await input.click();
    await input.fill(query);
    await page.waitForTimeout(300);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(waitMs);
  }

  const orderId = 'O2050';
  console.log(`📍 Order: ${orderId}`);

  // ─── 1. HOMEPAGE FULL ────────────────────────────
  console.log('1/10 🏠 Homepage full...');
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(outDir, '01-storefront-full.png'), fullPage: true });
  console.log('   ✅ 01-storefront-full.png');

  // Hero banner
  const hero = await page.locator('.rounded-3xl').first();
  await hero.screenshot({ path: path.join(outDir, '01-storefront.png') });
  console.log('   ✅ 01-storefront.png');

  // ─── 2-7. AI ASSISTANT ───────────────────────────
  await page.goto(`${base}/chat`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // Support Agent
  console.log('2/10 🎧 Support...');
  await sendChat('Hi! Can you tell me about your store and how to place an order? Also how does delivery work?', 12000);
  await page.screenshot({ path: path.join(outDir, '02-agent-support.png') });
  console.log('   ✅ 02-agent-support.png');

  // Inventory Agent
  console.log('3/10 📦 Inventory...');
  await sendChat('Do you have running shoes in stock? I need a pair for my daily jog.', 12000);
  await page.screenshot({ path: path.join(outDir, '03-agent-inventory.png') });
  console.log('   ✅ 03-agent-inventory.png');

  // Pricing Agent
  console.log('4/10 🏷️ Pricing...');
  await sendChat('What items are currently on sale? Looking for good deals.', 12000);
  await page.screenshot({ path: path.join(outDir, '04-agent-pricing.png') });
  console.log('   ✅ 04-agent-pricing.png');

  // Order Agent
  console.log('5/10 📋 Order...');
  await sendChat(`Can you check the status of my order ${orderId}? I just placed it.`, 12000);
  await page.screenshot({ path: path.join(outDir, '05-agent-order.png') });
  console.log('   ✅ 05-agent-order.png');

  // Fraud Agent
  console.log('6/10 🛡️ Fraud...');
  await sendChat(`Please run a fraud analysis on order ${orderId} to check if everything is safe.`, 20000);
  await page.screenshot({ path: path.join(outDir, '06-agent-fraud.png') });
  console.log('   ✅ 06-agent-fraud.png');

  // All agents
  console.log('7/10 🎯 All agents...');
  await page.screenshot({ path: path.join(outDir, '07-all-agents.png') });
  console.log('   ✅ 07-all-agents.png');

  // ─── 8. ADMIN DASHBOARD ─────────────────────────
  console.log('8/10 ⚙️ Admin...');
  await page.goto(`${base}/admin`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  const pwInput = await page.$('input[type="password"]');
  if (pwInput) { await pwInput.fill('demo123'); await page.keyboard.press('Enter'); await page.waitForTimeout(2000); }
  await page.screenshot({ path: path.join(outDir, '08-admin-dashboard.png') });
  console.log('   ✅ 08-admin-dashboard.png');

  // ─── 9. API DOCS ────────────────────────────────
  console.log('9/10 📖 API Docs...');
  await page.goto('http://localhost:8000/docs', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(outDir, '09-api-docs.png') });
  console.log('   ✅ 09-api-docs.png');

  console.log('\n✅ All screenshots captured!');
  await browser.close();
})();
