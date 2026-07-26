const path = require('path');
const { chromium } = require(path.join(__dirname, '..', 'frontend', 'node_modules', 'playwright'));
const outDir = path.join(__dirname, '..', 'docs', 'images');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();
  const baseUrl = 'http://localhost:3000';
  const apiUrl = 'http://localhost:8000';

  console.log('📸 Capturing the CommerceOS AI story...\n');

  async function sendChat(query, waitMs = 10000) {
    const input = await page.$('input[type="text"]');
    if (!input) { console.log('   ⚠️ No input found'); return; }
    await input.click();
    await input.fill(query);
    await page.waitForTimeout(300);
    await page.keyboard.press('Enter');
    console.log(`   ⏳ "${query.slice(0, 50)}..." — waiting ${waitMs/1000}s`);
    await page.waitForTimeout(waitMs);
  }

  // ─── 1. HOMEPAGE ───────────────────────────────────
  console.log('1/8 🏠 Storefront...');
  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: path.join(outDir, '01-storefront.png'), fullPage: true });
  console.log('   ✅ 01-storefront.png\n');

  // ─── 2. ADMIN DASHBOARD ───────────────────────────
  console.log('2/8 ⚙️ Admin Dashboard...');
  await page.goto(`${baseUrl}/admin`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(outDir, '02-admin-dashboard.png'), fullPage: true });
  console.log('   ✅ 02-admin-dashboard.png\n');

  // ─── 3. CHAT — FULL AGENT STORY ───────────────────
  console.log('3/8 🤖 AI Assistant — Full Agent Journey...');
  await page.goto(`${baseUrl}/chat`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);

  // Agent 1: Order — Track an order
  await sendChat('Where is my order O2001?', 10000);
  // Take screenshot after first agent response
  await page.screenshot({ path: path.join(outDir, '03-agent-order.png'), fullPage: true });
  console.log('   ✅ 03-agent-order.png');

  // Agent 2: Inventory — Check stock
  await sendChat('Do we have white t-shirts in stock?', 12000);
  await page.screenshot({ path: path.join(outDir, '04-agent-inventory.png'), fullPage: true });
  console.log('   ✅ 04-agent-inventory.png');

  // Agent 3: Pricing — Check sales
  await sendChat('Any items on sale right now?', 10000);
  await page.screenshot({ path: path.join(outDir, '05-agent-pricing.png'), fullPage: true });
  console.log('   ✅ 05-agent-pricing.png');

  // Agent 4: Support — Return policy
  await sendChat('Can I return a damaged item from order O2010?', 12000);
  await page.screenshot({ path: path.join(outDir, '06-agent-support.png'), fullPage: true });
  console.log('   ✅ 06-agent-support.png');

  // Agent 5: Fraud — CrewAI analysis (THE STAR)
  await sendChat('Check order O2004 for fraud', 20000);
  await page.screenshot({ path: path.join(outDir, '07-agent-fraud-crewai.png'), fullPage: true });
  console.log('   ✅ 07-agent-fraud-crewai.png');

  // Full conversation — all 5 agents visible
  await page.screenshot({ path: path.join(outDir, '08-all-five-agents.png'), fullPage: true });
  console.log('   ✅ 08-all-five-agents.png\n');

  // ─── 4. SCROLL TO SHOW FRAUD HIGHLIGHT ────────────
  console.log('9/9 📖 API Documentation...');
  await page.goto(`${apiUrl}/docs`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(outDir, '09-api-docs.png'), fullPage: true });
  console.log('   ✅ 09-api-docs.png\n');

  console.log('🎉 All screenshots captured!');
  await browser.close();
})();
