// "Taʼmirlash ishlari" reel: index.html -> kadrlar -> MP4 (1080x1920, 30fps, musiqa bilan).
//   node render.js                    -> tamirlash_ishlari_reel.mp4
//   node render.js --preview 2,6,10   -> preview_<t>.png
// Talab: playwright (chromium), ffmpeg, python3 + numpy.
const http = require('http'), fs = require('fs'), path = require('path');
const { spawn, execFileSync } = require('child_process');
const { chromium } = require('playwright');

const DIR = __dirname, FPS = 30, DURATION = 27;
const OUT = path.join(DIR, 'tamirlash_ishlari_reel.mp4');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.jpg': 'image/jpeg', '.png': 'image/png' };
const server = http.createServer((req, res) => {
  const p = path.join(DIR, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
  if (!p.startsWith(DIR) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, r));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e));
  await page.goto(`http://127.0.0.1:${server.address().port}/index.html`);
  await page.evaluate(() => window.ready);
  const pi = process.argv.indexOf('--preview');
  if (pi > 0) {
    for (const t of process.argv[pi + 1].split(',').map(Number)) {
      await page.evaluate(t => window.renderAt(t), t);
      await page.screenshot({ path: path.join(DIR, `preview_${t}.png`) });
    }
  } else {
    const music = path.join(DIR, 'music.wav');
    execFileSync('python3', [path.join(DIR, 'music.py'), music, String(DURATION)], { stdio: 'inherit' });
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-i', music, '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
      '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });
    const N = FPS * DURATION;
    for (let i = 0; i < N; i++) {
      await page.evaluate(t => window.renderAt(t), i / FPS);
      const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 90 === 0) console.log(`kadr ${i}/${N}`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    fs.unlinkSync(music); console.log('Tayyor:', OUT);
  }
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
