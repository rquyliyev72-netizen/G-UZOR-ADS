#!/usr/bin/env python3
"""Ovozsiz videoga (build/video.mp4) fon musiqasi + diktor ovozini qo'shadi -> ishonch_mebel_reel.mp4.
Diktor fayllari: voice/vo1.mp3 ... vo6.mp3 (har sahna uchun bittadan). Yo'q bo'lsa, faqat musiqa qo'yiladi.
Diktor gapirayotganda musiqa avtomatik pasayadi (sidechain ducking)."""
import json, os, subprocess, sys
D = os.path.dirname(os.path.abspath(__file__))
tl = json.load(open(os.path.join(D, 'timeline.json')))
music = os.path.join(D, 'build', 'music.wav'); out = os.path.join(D, 'ishonch_mebel_reel.mp4')
subprocess.run(['python3', os.path.join(D, 'music.py'), music, os.path.join(D, 'timeline.json')], check=True)
vo = [os.path.join(D, 'voice', f'vo{i}.mp3') for i in range(1, 7)]
have = [v for v in vo if os.path.exists(v)]
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-i', os.path.join(D, 'build', 'video.mp4'), '-i', music]
if len(have) == 6:
    f = []
    for i, v in enumerate(vo):
        cmd += ['-i', v]; ms = int((tl['starts'][i] + tl['lead']) * 1000)
        f.append(f'[{i+2}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume=1.6[v{i}]')
    f.append(''.join(f'[v{i}]' for i in range(6)) + 'amix=inputs=6:normalize=0,asplit=2[vo][sc]')
    f.append('[1:a]volume=0.8[m];[m][sc]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[duck]')
    f.append('[duck][vo]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]')
    cmd += ['-filter_complex', ';'.join(f), '-map', '0:v', '-map', '[a]']
else:
    print(f'OGOHLANTIRISH: diktor fayllari topilmadi ({len(have)}/6) — faqat musiqa qo\'yildi.', file=sys.stderr)
    cmd += ['-map', '0:v', '-map', '1:a']
cmd += ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out]
subprocess.run(cmd, check=True); os.remove(music); print('Tayyor:', out)
