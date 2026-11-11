#!/usr/bin/env python3
"""E'lon uchun jiddiy, ritmik fon musiqasi (sintez) + boshida ogohlantirish signali.
Ishlatish: python3 music.py chiqish.wav [davomiylik_s] [otish_vaqtlari] [ding_vaqtlari]"""
import sys, wave
import numpy as np

SR = 44100
out = sys.argv[1]; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 27.0
n = int(SR * dur); t = np.arange(n) / SR; mix = np.zeros(n); rng = np.random.default_rng(3)
BPM = 104; beat = 60 / BPM; bar = beat * 4
hz = lambda m: 440 * 2 ** ((m - 69) / 12)

def add(sig, start):
    i0 = int(start * SR); m = min(len(sig), n - i0)
    if m > 0: mix[i0:i0 + m] += sig[:m]

def tone(f, length, amp, kind):
    tt = np.arange(int(length * SR)) / SR
    if kind == 'pad':
        w = sum(np.sin(2 * np.pi * f * d * tt) for d in (1, 1.004, .996)) / 3
        env = np.minimum(1, tt / .4) * np.minimum(1, (length - tt) / .4)
    elif kind == 'bass':
        w = np.tanh(2.5 * np.sin(2 * np.pi * f * tt)); env = np.exp(-tt * 5)
    elif kind == 'pluck':
        w = np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt); env = np.exp(-tt * 9)
    elif kind == 'beep':
        w = np.sign(np.sin(2 * np.pi * f * tt)) * .5 + np.sin(2 * np.pi * f * tt) * .5; env = np.minimum(1, (length - tt) / .02)
    return amp * w * env * np.minimum(1, tt / .005)

prog = [(50, [50, 53, 57]), (46, [46, 50, 53]), (48, [48, 52, 55]), (45, [45, 49, 52])]  # Dm Bb C A
for b in range(int(dur / bar) + 1):
    root, ch = prog[b % 4]; t0 = b * bar
    for m in ch: add(tone(hz(m + 12), bar, .045, 'pad'), t0)
    for k in range(8): add(tone(hz(root - 12), beat / 2, .15 if k % 2 == 0 else .08, 'bass'), t0 + k * beat / 2)
    for k, m in enumerate([ch[0] + 24, ch[2] + 12, ch[1] + 12, ch[2] + 12] * 2): add(tone(hz(m), beat, .05, 'pluck'), t0 + k * beat / 2)
    for k in range(4):
        tt = np.arange(int(.25 * SR)) / SR
        add(.5 * np.sin(2 * np.pi * (48 + 80 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9), t0 + k * beat)
        add(.05 * rng.standard_normal(int(.04 * SR)) * np.exp(-np.arange(int(.04 * SR)) / SR * 90), t0 + (k + .5) * beat)
        if k in (1, 3): add(.1 * rng.standard_normal(int(.12 * SR)) * np.exp(-np.arange(int(.12 * SR)) / SR * 30), t0 + k * beat)

for i in range(4): add(tone(1250, .16, .16, 'beep'), .15 + i * .42)          # ogohlantirish signali
CUTS = [float(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else [4.5, 9.5, 14.5, 20.0]
DINGS = [float(x) for x in sys.argv[4].split(',')] if len(sys.argv) > 4 else [16.0, 16.45, 16.9, 17.35]
for c in CUTS:                                 # o'tish "whoosh"
    m = int(.6 * SR); tt = np.arange(m) / SR
    add(.22 * np.convolve(rng.standard_normal(m), np.ones(12) / 12, 'same') * np.sin(np.pi * tt / .6) ** 2, c - .4)
for c in DINGS: add(tone(hz(86), .4, .06, 'pluck'), c)    # MFY chiqqanda "ding"

mix *= np.minimum(1, t / .3) * np.minimum(1, (dur - t) / 1.5)
pcm = (np.tanh(mix * 1.1) * .85 * 32767).astype(np.int16)
with wave.open(out, 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(pcm[:, None], 2, 1).tobytes())
