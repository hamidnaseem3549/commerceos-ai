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

  // ─── 1. PLACE A REAL ORDER ─────────────────────
  console.log('📍 Placing a real order...');
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // Add first product to cart
  const addBtn = await page.$('button:has-text("Add to Cart")');
  if (addBtn) await addBtn.click();
  await page.waitForTimeout(1000);

  // Go to cart/checkout
  await page.goto(`${base}/orders`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // Fill checkout form
  await page.goto(`${base}/orders?checkout=true`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // Type checkout info
  const nameInput = await page.$('input[placeholder*="Name"], input[type="text"]');
  // Try to fill checkout form - navigate to orders page
  await page.goto(`${base}/orders`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);

  // Use API to place order (more reliable than UI interactions)
  const orderResp = await page.evaluate(async () => {
    const res = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        customer_name: 'Ahmed Hassan',
        customer_email: 'ahmed.hassan@email.com',
        shipping_country: 'Pakistan',
        product_id: 'P1008',
        quantity: 1
      })
    });
    return res.json();
  });
  const orderId = orderResp.order_id;
  console.log(`   ✅ Order placed: ${orderId}\n`);

  // ─── 2. STOREFRONT HOMEPAGE ─────────────────────
  console.log('1/9 🏠 Homepage...');
  await page.goto(base, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  const hero = await page.locator('.rounded-3xl').first();
  await hero.screenshot({ path: path.join(outDir, '01-storefront.png') });
  console.log('   ✅ 01-storefront.png');

  // ─── 3. AI ASSISTANT - AGENT CONVERSATIONS ──────
  await page.goto(`${base}/chat`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // Agent 1: Customer Support
  console.log('2/9 🎧 Customer Support...');
  await sendChat('Hi! Can you tell me about your store and how I can place an order? Also how does delivery tracking work?', 12000);
  await page.screenshot({ path: path.join(outDir, '02-agent-support.png') });
  console.log('   ✅ 02-agent-support.png');

  // Agent 2: Inventory
  console.log('3/9 📦 Inventory - Running shoes...');
  await sendChat('Do you have running shoes available? Specifically looking for men\'s size 10.', 12000);
  await page.screenshot({ path: path.join(outDir, '03-agent-inventory.png') });
  console.log('   ✅ 03-agent-inventory.png');

  // Agent 3: Pricing
  console.log('4/9 🏷️ Pricing - Sales...');
  await sendChat('Are there any items on sale right now? Looking for good deals.', 12000);
  await page.screenshot({ path: path.join(outDir, '04-agent-pricing.png') });
  console.log('   ✅ 04-agent-pricing.png');

  // Agent 4: Order Management - check the order we just placed
  console.log('5/9 📋 Order Management...');
  await sendChat(`Can you check the status of my order ${orderId}? I just placed it.`, 12000);
  await page.screenshot({ path: path.join(outDir, '05-agent-order.png') });
  console.log('   ✅ 05-agent-order.png');

  // Agent 5: Fraud Agent
  console.log('6/9 🛡️ Fraud Analysis...');
  await sendChat(`Please run a fraud analysis on order ${orderId} to make sure everything is safe.`, 20000);
  await page.screenshot({ path: path.join(outDir, '06-agent-fraud.png') });
  console.log('   ✅ 06-agent-fraud.png');

  // Full conversation
  console.log('7/9 🎯 All agents conversation...');
  await page.screenshot({ path: path.join(outDir, '07-all-agents.png') });
  console.log('   ✅ 07-all-agents.png');

  // ─── 4. ADMIN DASHBOARD ─────────────────────────
  console.log('8/9 ⚙️ Admin Dashboard...');
  await page.goto(`${base}/admin`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  // Login with password from env
  const pwInput = await page.$('input[type="password"]');
  if (pwInput) {
    await pwInput.fill('demo123');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(2000);
  }
  await page.screenshot({ path: path.join(outDir, '08-admin-dashboard.png') });
  console.log('   ✅ 08-admin-dashboard.png');

  // ─── 5. API DOCS ────────────────────────────────
  console.log('9/9 📖 API Docs...');
  await page.goto('http://localhost:8000/docs', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(outDir, '09-api-docs.png') });
  console.log('   ✅ 09-api-docs.png');

  console.log('\n✅ All 9 screenshots captured!');
  await browser.close();
})();
