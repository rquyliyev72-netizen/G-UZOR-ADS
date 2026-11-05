// ISHONCH mebel reel renderer: index.html (Three.js) -> kadrlar -> MP4 (ffmpeg).
// Ishga tushirish:
//   node render.js                      -> build/video.mp4 (ovozsiz) + mix.py -> ishonch_mebel_reel.mp4
//   node render.js --preview 1,4.5,8    -> preview_<t>.png kadrlar (asl 36s vaqt shkalasida)
// Sahnalar diktor ovozi (voice/vo1..6.mp3) uzunligiga moslab cho'ziladi; timeline.json ga yoziladi.
// Talab: playwright (chromium), ffmpeg, python3 + numpy (musiqa uchun).
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn, execFileSync } = require('child_process');
const { chromium } = require('playwright');

const DIR = __dirname, FPS = 30;
const RAW = path.join(DIR, 'build', 'video.mp4');

// --- vaqt shkalasi: asl sahnalar (index.html) -> diktor ovoziga moslangan sahnalar ---
const ORIG = [0, 5, 10, 16.5, 25, 30, 36];
const VO_FALLBACK = [3.12, 7.68, 8.72, 12.16, 9.44, 7.68];   // ElevenLabs takelarining uzunligi (s)
const LEAD = 0.3, TAIL = [0.6, 0.4, 0.6, 0.6, 0.6, 1.5];
function voDur(i) {
  const f = path.join(DIR, 'voice', `vo${i + 1}.mp3`);
  if (!fs.existsSync(f)) return VO_FALLBACK[i];
  return +execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString();
}
const LEN = ORIG.slice(0, -1).map((a, i) => Math.max(ORIG[i + 1] - a, LEAD + voDur(i) + TAIL[i]));
const STARTS = LEN.reduce((acc, l) => (acc.push(acc[acc.length - 1] + l), acc), [0]);
const DURATION = Math.ceil(STARTS[STARTS.length - 1] * FPS) / FPS;
const warp = T => { let i = 0; while (i < 5 && T >= STARTS[i + 1]) i++;
  return ORIG[i] + clampU((T - STARTS[i]) / LEN[i]) * (ORIG[i + 1] - ORIG[i]); };
function clampU(x) { return Math.min(0.99999, Math.max(0, x)); }
fs.mkdirSync(path.join(DIR, 'build'), { recursive: true });
fs.writeFileSync(path.join(DIR, 'timeline.json'), JSON.stringify({ orig: ORIG, starts: STARTS, lead: LEAD, duration: DURATION }, null, 1));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json' };

const server = http.createServer((req, res) => {
  const p = path.join(DIR, decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html');
  if (!p.startsWith(DIR) || !fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, r));
  const url = `http://127.0.0.1:${server.address().port}/index.html`;
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => console.error('PAGE ERROR', e));
  await page.goto(url);
  await page.evaluate(() => window.ready);

  const pi = process.argv.indexOf('--preview');
  if (pi > 0) {
    for (const t of process.argv[pi + 1].split(',').map(Number)) {
      await page.evaluate(t => window.renderAt(t), t);
      await page.screenshot({ path: path.join(DIR, `preview_${t}.png`) });
      console.log('preview', t);
    }
  } else {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high', RAW], { stdio: ['pipe', 'inherit', 'inherit'] });
    const N = Math.round(FPS * DURATION), t0 = Date.now();
    console.log('Sahnalar (s):', LEN.map(l => l.toFixed(2)).join(', '), ' jami', DURATION.toFixed(2));
    for (let i = 0; i < N; i++) {
      await page.evaluate(t => window.renderAt(t), warp(i / FPS));
      const buf = await page.screenshot({ type: 'jpeg', quality: 93 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 60 === 0) console.log(`kadr ${i}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    execFileSync('python3', [path.join(DIR, 'mix.py')], { stdio: 'inherit' });
  }
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
