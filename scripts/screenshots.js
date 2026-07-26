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

  console.log('📸 Starting screenshot capture...\n');

  // 1. HOMEPAGE
  console.log('1/9 🏠 Homepage...');
  await page.goto(baseUrl, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(outDir, '01-homepage.png'), fullPage: true });
  console.log('   ✅ Saved: 01-homepage.png');

  // 2. CART / ORDERS PAGE
  console.log('2/9 🛒 Orders page...');
  await page.goto(`${baseUrl}/orders`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: path.join(outDir, '02-orders.png'), fullPage: true });
  console.log('   ✅ Saved: 02-orders.png');

  // 3. ADMIN DASHBOARD
  console.log('3/9 ⚙️ Admin Dashboard...');
  await page.goto(`${baseUrl}/admin`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(outDir, '03-admin-dashboard.png'), fullPage: true });
  console.log('   ✅ Saved: 03-admin-dashboard.png');

  // 4. AI ASSISTANT - Welcome screen
  console.log('4/9 🤖 AI Assistant - Welcome...');
  await page.goto(`${baseUrl}/chat`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: path.join(outDir, '04-ai-welcome.png'), fullPage: true });
  console.log('   ✅ Saved: 04-ai-welcome.png');

  // Helper: send a chat message and wait for response
  async function sendChat(query, waitMs = 10000) {
    const input = await page.$('input[type="text"]');
    if (!input) {
      console.log('   ⚠️ Chat input not found, trying form submit...');
      return;
    }
    await input.click();
    await input.fill(query);
    await page.waitForTimeout(500);
    // Try Enter key
    await page.keyboard.press('Enter');
    console.log(`   ⏳ Waiting ${waitMs/1000}s for response...`);
    await page.waitForTimeout(waitMs);
  }

  // 5. AI ASSISTANT - Support Agent
  console.log('5/9 🎧 Support Agent - Return policy...');
  await page.goto(`${baseUrl}/chat`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await sendChat('Can I return a damaged item from order O2010?', 12000);
  await page.screenshot({ path: path.join(outDir, '05-ai-support.png'), fullPage: true });
  console.log('   ✅ Saved: 05-ai-support.png');

  // 6. AI ASSISTANT - Inventory Agent
  console.log('6/9 📦 Inventory Agent - Stock check...');
  await sendChat('Do we have white t-shirts in stock?', 12000);
  await page.screenshot({ path: path.join(outDir, '06-ai-inventory.png'), fullPage: true });
  console.log('   ✅ Saved: 06-ai-inventory.png');

  // 7. AI ASSISTANT - Fraud Agent (CrewAI)
  console.log('7/9 🛡️ Fraud Agent - CrewAI analysis...');
  await sendChat('Check order O2004 for fraud', 20000);
  await page.screenshot({ path: path.join(outDir, '07-ai-fraud.png'), fullPage: true });
  console.log('   ✅ Saved: 07-ai-fraud.png');

  // 8. AI ASSISTANT - Full conversation with all agents
  console.log('8/9 🤖 Full conversation history...');
  await page.screenshot({ path: path.join(outDir, '08-ai-full-chat.png'), fullPage: true });
  console.log('   ✅ Saved: 08-ai-full-chat.png');

  // 9. API DOCS
  console.log('9/9 📖 API Documentation...');
  await page.goto(`${apiUrl}/docs`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: path.join(outDir, '09-api-docs.png'), fullPage: true });
  console.log('   ✅ Saved: 09-api-docs.png');

  console.log('\n✅ All 9 screenshots captured in docs/images/');
  await browser.close();
})();
