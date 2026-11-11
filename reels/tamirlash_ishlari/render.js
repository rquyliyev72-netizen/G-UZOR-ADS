// "Taʼmirlash ishlari" reel: index.html -> kadrlar -> MP4 (1080x1920, 30fps), musiqa + diktor ovozi bilan.
//   node render.js                    -> tamirlash_ishlari_reel.mp4
//   node render.js --preview 2,6,10   -> preview_<t>.png (index.html vaqt shkalasida)
// Diktor: voice/vo1..5.mp3 (har sahnaga bittadan). Sahnalar ovoz uzunligiga moslab cho'ziladi;
// diktor gapirganda musiqa pasayadi. Fayllar bo'lmasa — faqat musiqa.
// Talab: playwright (chromium), ffmpeg, python3 + numpy.
const http = require('http'), fs = require('fs'), path = require('path');
const { spawn, execFileSync } = require('child_process');
const { chromium } = require('playwright');

const DIR = __dirname, FPS = 30;
const OUT = path.join(DIR, 'tamirlash_ishlari_reel.mp4');
const ORIG = [0, 4.5, 9.5, 14.5, 20, 25];            // index.html dagi sahna chegaralari
const LEAD = 0.45, TAIL = [0.5, 0.5, 0.5, 0.6, 1.6];
const VO = ORIG.slice(0, -1).map((_, i) => path.join(DIR, 'voice', `vo${i + 1}.mp3`));
const HAVE = VO.every(f => fs.existsSync(f));
const dur = f => +execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString();
const LEN = ORIG.slice(0, -1).map((a, i) => Math.max(ORIG[i + 1] - a, HAVE ? LEAD + dur(VO[i]) + TAIL[i] : 0));
const ST = LEN.reduce((acc, l) => (acc.push(acc[acc.length - 1] + l), acc), [0]);
const DURATION = Math.ceil(ST[5] * FPS) / FPS;
const warp = T => { let i = 0; while (i < 4 && T >= ST[i + 1]) i++;
  return ORIG[i] + Math.min(0.9999, Math.max(0, (T - ST[i]) / LEN[i])) * (ORIG[i + 1] - ORIG[i]); };
const unwarp = x => { let i = 0; while (i < 4 && x >= ORIG[i + 1]) i++;
  return ST[i] + (x - ORIG[i]) / (ORIG[i + 1] - ORIG[i]) * LEN[i]; };

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
    execFileSync('python3', [path.join(DIR, 'music.py'), music, String(DURATION), ST.slice(1, 5).join(','),
      [16.0, 16.45, 16.9, 17.35].map(unwarp).join(',')], { stdio: 'inherit' });
    const args = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-i', music];
    if (HAVE) {
      const f = VO.map((v, i) => { args.push('-i', v); const ms = Math.round((ST[i] + LEAD) * 1000);
        return `[${i + 2}:a]aresample=44100,aformat=channel_layouts=stereo,adelay=${ms}|${ms},volume=1.7[v${i}]`; });
      f.push(VO.map((_, i) => `[v${i}]`).join('') + `amix=inputs=${VO.length}:normalize=0,asplit=2[vo][sc]`);
      f.push('[1:a]volume=0.75[m];[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]');
      f.push('[duck][vo]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]');
      args.push('-filter_complex', f.join(';'), '-map', '0:v', '-map', '[a]');
    } else console.error("OGOHLANTIRISH: voice/vo1..5.mp3 topilmadi — faqat musiqa qo'yiladi.");
    args.push('-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-profile:v', 'high',
      '-c:a', 'aac', '-b:a', '192k', '-t', String(DURATION), '-movflags', '+faststart', OUT);
    const ff = spawn('ffmpeg', args, { stdio: ['pipe', 'inherit', 'inherit'] });
    const N = Math.round(FPS * DURATION);
    console.log('Sahnalar (s):', LEN.map(l => l.toFixed(2)).join(', '), '| jami', DURATION.toFixed(2));
    for (let i = 0; i < N; i++) {
      await page.evaluate(t => window.renderAt(t), warp(i / FPS));
      const buf = await page.screenshot({ type: 'jpeg', quality: 92 });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    fs.unlinkSync(music); console.log('Tayyor:', OUT);
  }
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
