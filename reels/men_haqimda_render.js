// "Men haqimda" videosini render qilish: node men_haqimda_render.js [chiqish.mp4]
// Har bir kadr uchun CSS animatsiyalar aniq vaqtga o'tkaziladi va skrinshot olinadi.
// Talab: playwright (chromium), ffmpeg.
// Faqat preview kadrlar: node men_haqimda_render.js --preview 2,6,12
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');

const FPS = 30, DURATION = 22;
const args = process.argv.slice(2);

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.join(__dirname, 'men_haqimda.html'));
  await page.evaluate(() => document.fonts.ready);
  await page.waitForLoadState('networkidle');

  if (args[0] === '--preview') {
    for (const t of args[1].split(',').map(Number)) {
      await page.evaluate(t => window.seek(t), t);
      await page.screenshot({ path: path.join(args[2] || '.', `frame_${t}.png`) });
    }
    return browser.close();
  }

  const out = args[0] || path.join(__dirname, 'men_haqimda.mp4');
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS),
    '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'slow', '-crf', '19',
    '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const total = FPS * DURATION;
  for (let i = 0; i < total; i++) {
    await page.evaluate(t => window.seek(t), i / FPS);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95 });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) process.stdout.write(`${i}/${total}\n`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('Tayyor:', out);
})();
