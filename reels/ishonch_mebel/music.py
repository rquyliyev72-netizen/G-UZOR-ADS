#!/usr/bin/env python3
"""Reel uchun oddiy, quvnoq fon musiqasi (sintez): akkordlar, pluck, baraban, o'tish 'whoosh'lari.
Ishlatish: python3 music.py chiqish.wav [davomiylik_s]"""
import sys, wave
import numpy as np

SR = 44100
out = sys.argv[1]; dur = float(sys.argv[2]) if len(sys.argv) > 2 else 36.0
n = int(SR * dur); t = np.arange(n) / SR
mix = np.zeros(n); rng = np.random.default_rng(7)
BPM = 116; beat = 60 / BPM; bar = beat * 4

def note(f, start, length, amp, kind='pluck'):
    i0 = int(start * SR); m = min(int(length * SR), n - i0)
    if m <= 0: return
    tt = np.arange(m) / SR
    if kind == 'pluck':
        w = np.sin(2*np.pi*f*tt) + .35*np.sin(4*np.pi*f*tt) + .12*np.sin(6*np.pi*f*tt); env = np.exp(-tt*6)
    elif kind == 'pad':
        w = sum(np.sin(2*np.pi*f*d*tt) for d in (1, 1.003, .997)) / 3; env = np.minimum(1, tt/.25) * np.minimum(1, (length-tt)/.3)
    elif kind == 'bass':
        w = np.tanh(2*np.sin(2*np.pi*f*tt)); env = np.exp(-tt*3)
    mix[i0:i0+m] += amp * w * env * np.minimum(1, tt/.004)

hz = lambda midi: 440 * 2 ** ((midi - 69) / 12)
prog = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]  # Am F C G
nb = int(dur / bar) + 1
for b in range(nb):
    root, ch = prog[b % 4]; t0 = b * bar
    for m in ch: note(hz(m + 12), t0, bar, .05, 'pad')
    for k in range(8):
        note(hz(root - 12), t0 + k*beat/2, beat/2, .16 if k % 2 == 0 else .09, 'bass')
    arp = ch + [ch[1] + 12, ch[2] + 12, ch[0] + 24, ch[2] + 12, ch[1] + 12]
    for k, m in enumerate(arp): note(hz(m + 12), t0 + k*beat/2, beat, .07, 'pluck')
    for k in range(4):  # kick
        i0 = int((t0 + k*beat) * SR); m = min(int(.25*SR), n - i0)
        if m > 0:
            tt = np.arange(m)/SR; mix[i0:i0+m] += .5*np.sin(2*np.pi*(50 + 90*np.exp(-tt*30))*tt)*np.exp(-tt*9)
        for off in (.5,):  # hat
            i0 = int((t0 + (k+off)*beat) * SR); m = min(int(.05*SR), n - i0)
            if m > 0: mix[i0:i0+m] += .06*rng.standard_normal(m)*np.exp(-np.arange(m)/SR*80)
        if k in (1, 3):  # clap
            i0 = int((t0 + k*beat) * SR); m = min(int(.12*SR), n - i0)
            if m > 0: mix[i0:i0+m] += .12*rng.standard_normal(m)*np.exp(-np.arange(m)/SR*30)

for c in (5, 10, 16.5, 25, 30):  # whoosh
    i0 = int((c - .45) * SR); m = int(.6*SR); tt = np.arange(m)/SR
    noise = np.convolve(rng.standard_normal(m), np.ones(12)/12, 'same')
    mix[i0:i0+m] += .25 * noise * np.sin(np.pi*tt/.6) ** 2
for c in (4.0, 5.6, 10.3, 12.0, 12.6, 13.2, 25.1, 26.6, 27.1, 27.6, 30.1):  # 'ding'
    note(hz(88), c, .6, .08, 'pluck'); note(hz(95), c + .05, .6, .05, 'pluck')

mix *= np.minimum(1, t/.5) * np.minimum(1, (dur - t)/1.5)
mix = np.tanh(mix * 1.1) * .85
pcm = (mix * 32767).astype(np.int16)
with wave.open(out, 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(np.repeat(pcm[:, None], 2, 1).tobytes())
