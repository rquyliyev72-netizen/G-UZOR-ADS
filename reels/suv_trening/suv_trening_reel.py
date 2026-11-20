#!/usr/bin/env python3
"""G'uzorda suv resurslari treningi — Instagram Reels (1080x1920, 30fps).

Uslub namunadagi "G'uzor tumani hokimligi axborot xizmati" videolariga mos:
to'liq ekranli foto + sekin zoom/pan, tepada oq tuman, pastda to'q ko'k gradient,
chap tepada logotip, sariq teg, sariq vertikal chiziq + oq qalin sarlavha,
sahnalar orasida yumshoq o'tish, oxirida ko'k logotip kartasi (namunadan).

Ishga tushirish:
  python3 suv_trening_reel.py NAMUNA.mp4 OVOZ.mp3 [chiqish.mp4] [--4k]
--4k bilan 2160x3840 (4K) chiqadi, aks holda 1080x1920.
NAMUNA.mp4 — logotip olinadigan namuna video (yakuniy 3D animatsiya shu logotipdan yasaladi).
OVOZ.mp3   — diktor ovozi (fon musiqasiz); sahnalar ovozdagi gaplarga moslanadi.
Talab: Pillow, numpy, ffmpeg.
"""
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = sys.argv[1]
VOICE = sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else os.path.join(HERE, "suv_trening_reel.mp4")
K = 2 if "--4k" in sys.argv else 1   # o'lcham koeffitsiyenti (4K uchun 2)
W, H, FPS = 1080 * K, 1920 * K, 30
FONT_DIR = "/usr/share/fonts/opentype/inter"
YELLOW = (255, 196, 0)
NAVY = (18, 28, 62)
WHITE = (255, 255, 255)

XF = 0.6          # sahnalar orasidagi o'tish
LEAD = 0.35       # sahna gapdan shuncha oldin almashadi
# Ovozdagi gaplarning boshlanish vaqtlari (pauzalar bo'yicha aniqlangan), s:
# 1 kirish, 2 SCADA, 3 texnologiyalar, 4 loyiha/PQ-141, 5 sertifikat, 6 hamkorlar, 7 "Suvni tejaylik"
VOICE_BOUNDS = [0.0, 4.98, 9.45, 15.67, 24.58, 29.76, 36.10]
VOICE_LEN = 39.47

# (rasm, fokus_x boshlanish, fokus_x tugash, zoom bosh, zoom oxir, teg, sarlavha, izoh)
SCENES = [
    ("07_maruza.jpg", 0.66, 0.60, 1.00, 1.08, "#trening",
     "G‘UZORDA SUV\nRESURSLARIDAN OQILONA\nFOYDALANISH BO‘YICHA\nTRENING O‘TKAZILDI", None),
    ("03_scada.jpg", 0.30, 0.66, 1.00, 1.04, "Raqamli monitoring",
     "SCADA: kuzatuv va\nboshqaruv tizimlari", "Zamonaviy boshqaruv yechimlari\nyuzasidan amaliy tavsiyalar berildi"),
    ("06_mashgulot.jpg", 0.42, 0.50, 1.06, 1.00, "Amaliy mashg‘ulot",
     "Suv tejovchi\ntexnologiyalar", "Sug‘orish va ichimlik suvidan\noqilona foydalanish o‘rgatildi"),
    ("04_sertifikat_qolsiqish.jpg", 0.58, 0.62, 1.00, 1.08, "Loyiha",
     "Qishloq joylarni kompleks\nrivojlantirish — II bosqich", "Prezidentning 2024-yil 28-martdagi\nPQ–141-son qarori asosida"),
    ("02_sertifikat_qr.jpg", 0.52, 0.56, 1.06, 1.00, "Sertifikat",
     "Ishtirokchilarga\nsertifikatlar topshirildi", "Treningda soha mutaxassislari\nva mas’ullar ishtirok etdi"),
    ("01_guruh.jpg", 0.22, 0.78, 1.00, 1.00, "Hamkorlik",
     "Islom taraqqiyot banki\nva BMT Taraqqiyot dasturi", "Iqtisodiyot va moliya vazirligi huzuridagi\nBirlashtirilgan loyihalarni amalga oshirish guruhi"),
]
N = len(SCENES)
STARTS = [0.0] + [b - LEAD for b in VOICE_BOUNDS[1:]]   # N sahna + yakuniy karta
OUTRO_START = STARTS[N]
DURATION = VOICE_LEN + 0.6
OUTRO_LEN = DURATION - OUTRO_START
LENS = [STARTS[i + 1] + XF - STARTS[i] for i in range(N)]


def font(w, s):
    return ImageFont.truetype(os.path.join(FONT_DIR, {"black": "Inter-Black.otf", "xb": "Inter-ExtraBold.otf",
                                                      "b": "Inter-Bold.otf", "sb": "Inter-SemiBold.otf"}[w]), s)


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def smooth(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# ---------- namunadan logotip va yakuniy kadrlar ----------
def grab(t, scale=None):
    vf = ["-vf", f"scale={scale}"] if scale else []
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", SAMPLE, "-frames:v", "1",
                          *vf, "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    from io import BytesIO
    return Image.open(BytesIO(raw)).convert("RGB")


card = grab(35.0).crop((72, 328, 645, 900))
LOGO = card.resize((92 * K, 92 * K), Image.LANCZOS).convert("RGBA")
m = Image.new("L", (368, 368), 0)
ImageDraw.Draw(m).rounded_rectangle([0, 0, 367, 367], 80, fill=255)
LOGO.putalpha(m.resize((92 * K, 92 * K), Image.LANCZOS))


# ---------- yakuniy 3D logotip ----------
def ease_back(x, k=1.5):
    x = clamp(x) - 1
    return x * x * ((k + 1) * x + k) + 1


def make_outro_bg():
    """Ko'k radial fon + markazdan o'tuvchi gorizontal nur (namunadagidek)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = W / 2, H * 0.47
    d = np.sqrt(((xx - cx) / W) ** 2 + ((yy - cy) / (H * 0.62)) ** 2)
    g = np.clip(1 - d / 0.85, 0, 1)[..., None]
    dark, mid = np.array([4, 8, 48], np.float32), np.array([18, 48, 190], np.float32)
    img = dark + (mid - dark) * g ** 1.4
    band = np.exp(-((yy - cy) / (H * 0.055)) ** 2)[..., None]
    img += band * np.array([20, 50, 140], np.float32) * 0.55
    return img


OUTRO_BG = make_outro_bg()
CARD_W = int(W * 0.40)                       # avvalgidan kichikroq
SS = 2                                       # chekkalar silliq chiqishi uchun
CW2 = CARD_W * SS
CARD_TEX = card.resize((CW2, CW2), Image.LANCZOS).convert("RGBA")
_cm = Image.new("L", (CW2 * 2, CW2 * 2), 0)
ImageDraw.Draw(_cm).rounded_rectangle([0, 0, CW2 * 2 - 1, CW2 * 2 - 1], int(CW2 * 0.28), fill=255)
CARD_MASK = _cm.resize((CW2, CW2), Image.LANCZOS)
CARD_TEX.putalpha(CARD_MASK)
CANVAS = int(CARD_W * 1.9)
_pad = int(CARD_W * 0.15)
SHADOW = Image.new("RGBA", (int(CARD_W * 1.1) + 2 * _pad, int(CARD_W * 0.16) + 2 * _pad), (0, 0, 0, 0))
ImageDraw.Draw(SHADOW).ellipse([_pad, _pad, SHADOW.width - 1 - _pad, SHADOW.height - 1 - _pad], fill=(0, 0, 20, 170))
SHADOW = SHADOW.filter(ImageFilter.GaussianBlur(CARD_W * 0.04))
_gs = int(CARD_W * 1.8)
GLOW = Image.new("RGBA", (_gs, _gs), (0, 0, 0, 0))
ImageDraw.Draw(GLOW).rounded_rectangle([_gs * 0.2, _gs * 0.2, _gs * 0.8, _gs * 0.8], int(_gs * 0.15),
                                       fill=(90, 160, 255, 150))
GLOW = GLOW.filter(ImageFilter.GaussianBlur(_gs * 0.07))
random.seed(3)
DOTS = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4.5) * K, random.uniform(20, 70) * K,
         random.uniform(0, 6.28)) for _ in range(45)]


def persp_coeffs(dst, src):
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); B.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); B.append(v)
    return np.linalg.solve(np.array(A, float), np.array(B, float))


def project(rx, ry, z0, scale):
    """Karta burchaklarini 3D aylantirib, kanvasga proyeksiyalaydi (2x o'lchamda)."""
    half = CW2 / 2 * scale
    cam = CW2 * 2.6
    a, b = np.radians(rx), np.radians(ry)
    pts = []
    for x, y in ((-half, -half), (half, -half), (half, half), (-half, half)):
        z = z0 * scale
        x1, z1 = x * np.cos(b) + z * np.sin(b), -x * np.sin(b) + z * np.cos(b)
        y1, z2 = y * np.cos(a) - z1 * np.sin(a), y * np.sin(a) + z1 * np.cos(a)
        f = cam / (cam + z2)
        pts.append((CANVAS * SS / 2 + x1 * f, CANVAS * SS / 2 + y1 * f))
    return pts


SRC = [(0, 0), (CW2, 0), (CW2, CW2), (0, CW2)]


def warp(tex, pts, resample=Image.BICUBIC):
    c = persp_coeffs(pts, SRC)
    return tex.transform((CANVAS * SS, CANVAS * SS), Image.PERSPECTIVE, tuple(c), resample)


def glint_tex(u):
    """Karta ustidan o'tuvchi yaltiroq diagonal nur."""
    if u <= -0.4 or u >= 1.4:
        return CARD_TEX
    yy, xx = np.mgrid[0:CW2, 0:CW2].astype(np.float32) / CW2
    band = np.exp(-(((xx + yy) / 2 - u) / 0.07) ** 2) * 0.55
    arr = np.asarray(CARD_TEX, np.float32).copy()
    arr[..., :3] += (255 - arr[..., :3]) * band[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")


def render_outro(lt):
    f = OUTRO_BG.copy()
    img = Image.fromarray(f.clip(0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    for x, y, r, sp, ph in DOTS:
        yy = (y - lt * sp) % H
        al = int(70 + 60 * np.sin(lt * 2 + ph))
        d.ellipse([x - r, yy - r, x + r, yy + r], fill=(150, 190, 255, max(0, al)))
    # harakat: chetdan aylanib kirib keladi, so'ng sekin 3D tebranadi
    p = ease_back(lt / 1.25, 1.3)
    sway = smooth((lt - 1.0) / 0.8)
    ry = -82 * (1 - p) + sway * 13 * np.sin((lt - 1.0) * 1.7)
    rx = 22 * (1 - p) + sway * 6 * np.sin((lt - 1.0) * 1.25 + 0.6)
    scale = 0.55 + 0.45 * ease(lt / 1.1)
    alpha = smooth(lt / 0.35)
    cx, cy = W / 2, H * 0.47 + np.sin(lt * 1.9) * H * 0.006
    # soya
    sh = SHADOW.resize((max(1, int(SHADOW.width * scale)), max(1, int(SHADOW.height * scale))))
    sh.putalpha(Image.fromarray((np.asarray(sh.getchannel("A"), np.float32) * alpha * 0.8).astype(np.uint8)))
    img.alpha_composite(sh, (int(cx - sh.width / 2), int(cy + CARD_W * 0.55 * scale - sh.height / 2 + CARD_W * 0.1)))
    # karta orqasidagi nur
    gl = GLOW.resize((max(1, int(GLOW.width * scale)),) * 2)
    gl.putalpha(Image.fromarray((np.asarray(gl.getchannel("A"), np.float32) * alpha).astype(np.uint8)))
    img.alpha_composite(gl, (int(cx - gl.width / 2), int(cy - gl.height / 2)))
    # qalinlik: orqadan oldinga bir nechta to'q ko'k qatlam
    layer = Image.new("RGBA", (CANVAS * SS, CANVAS * SS), (0, 0, 0, 0))
    T = CW2 * 0.07
    for k in range(7, 0, -1):
        c = (int(10 + 12 * (7 - k)), int(22 + 16 * (7 - k)), int(90 + 18 * (7 - k)), 255)
        solid = Image.new("RGBA", (CW2, CW2), c)
        solid.putalpha(CARD_MASK)
        layer.alpha_composite(warp(solid, project(rx, ry, T * k / 7, scale), Image.BILINEAR))
    layer.alpha_composite(warp(glint_tex((lt - 1.45) / 0.9 * 1.6 - 0.3), project(rx, ry, 0, scale)))
    layer = layer.resize((CANVAS, CANVAS), Image.LANCZOS)
    if alpha < 1:
        layer.putalpha(Image.fromarray((np.asarray(layer.getchannel("A"), np.float32) * alpha).astype(np.uint8)))
    img.alpha_composite(layer, (int(cx - CANVAS / 2), int(cy - CANVAS / 2)))
    return np.asarray(img.convert("RGB"), np.float32)

# ---------- statik qatlamlar ----------
yy = np.linspace(0, 1, H)[:, None]
# tepada oq tuman
top_a = np.clip(1 - yy / 0.22, 0, 1) ** 1.6 * 0.72
# pastda to'q ko'k
bot_a = np.clip((yy - 0.40) / 0.45, 0, 1) ** 1.3 * 0.94
OV = np.zeros((H, W, 4), np.float32)
OV_WHITE = np.broadcast_to(top_a, (H, W)).astype(np.float32)
OV_NAVY = np.broadcast_to(bot_a, (H, W)).astype(np.float32)
NAVY_ARR = np.array(NAVY, np.float32)
# ikkala qatlam bitta ko'paytma + qo'shiluvchi ko'rinishida (tezroq)
OV_MUL = ((1 - OV_NAVY) * (1 - OV_WHITE))[..., None]
OV_ADD = (OV_NAVY[..., None] * NAVY_ARR) * (1 - OV_WHITE[..., None]) + 255 * OV_WHITE[..., None]


def header_layer():
    img = Image.new("RGBA", (W, 220 * K), (0, 0, 0, 0))
    img.alpha_composite(LOGO, (66 * K, 140 * K))
    d = ImageDraw.Draw(img)
    d.text((176 * K, 146 * K), "G‘UZOR TUMANI HOKIMLIGI", font=font("xb", 34 * K), fill=(30, 30, 40))
    d.text((176 * K, 190 * K), "AXBOROT XIZMATI", font=font("xb", 26 * K), fill=(222, 160, 0))
    return img


HEADER = header_layer()

PHOTOS = {}
for s in SCENES:
    im = Image.open(os.path.join(HERE, "photos", s[0])).convert("RGB")
    k = H * 1.12 / im.height  # zoom/pan uchun zaxira
    PHOTOS[s[0]] = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)


def photo_frame(name, fx, z):
    im = PHOTOS[name]
    ch = im.height / 1.12 / z * 1.0
    cw = ch * W / H
    cx = fx * im.width
    cx = min(max(cx, cw / 2), im.width - cw / 2)
    cy = im.height / 2
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return np.asarray(im.resize((W, H), Image.BILINEAR, box=box), np.float32)


def text_block(tag, title, sub):
    """Teg, sariq chiziq, sarlavha va izoh — pastki chap burchakda."""
    img = Image.new("RGBA", (W, 760 * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tl = title.split("\n")
    size = 64 * K
    while max(font("xb", size).getlength(l) for l in tl) > W - 150 * K:
        size -= 2
    ft, fs, fg = font("xb", size), font("b", 36 * K), font("b", 34 * K)
    sl = sub.split("\n") if sub else []
    lh_t, lh_s = int(size * 1.22), 48 * K
    h_text = len(tl) * lh_t + (18 * K + len(sl) * lh_s if sl else 0)
    y0 = (760 - 40) * K - h_text
    # teg
    tw = d.textlength(tag, font=fg)
    d.rounded_rectangle([66 * K, y0 - 92 * K, 66 * K + tw + 36 * K, y0 - 30 * K], 12 * K, fill=YELLOW)
    d.text((84 * K, y0 - 61 * K), tag, font=fg, fill=(20, 20, 30), anchor="lm")
    # chiziq
    d.rectangle([66 * K, y0 + 6 * K, 74 * K, y0 + h_text - 6 * K], fill=YELLOW)
    y = y0
    for line in tl:
        d.text((100 * K, y), line, font=ft, fill=WHITE)
        y += lh_t
    y += 18 * K
    for line in sl:
        d.text((100 * K, y), line, font=fs, fill=YELLOW)
        y += lh_s
    return img, y0


TEXTS = [text_block(s[5], s[6], s[7]) for s in SCENES]
TEXT_Y = H - (760 + 170) * K


def scene_rgb(i, lt):
    name, fx0, fx1, z0, z1 = SCENES[i][:5]
    p = smooth(lt / LENS[i])
    base = photo_frame(name, fx0 + (fx1 - fx0) * p, z0 + (z1 - z0) * p)
    base = base * OV_MUL + OV_ADD
    f = Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert("RGBA")
    f.alpha_composite(HEADER, (0, 0))
    # matn: pastdan siljib chiqadi, sahna oxirida so'nadi
    a = ease((lt - 0.45) / 0.6) * (1 - smooth((lt - (LENS[i] - XF - 0.15)) / 0.45))
    if a > 0.01:
        timg, _ = TEXTS[i]
        t2 = timg.copy()
        t2.putalpha(Image.fromarray((np.asarray(t2.getchannel("A"), np.float32) * a).astype(np.uint8)))
        f.alpha_composite(t2, (int(-40 * K * (1 - a)), TEXT_Y + int(50 * K * (1 - a))))
    return np.asarray(f.convert("RGB"), np.float32)


def render(t):
    if t >= OUTRO_START:
        o = render_outro(t - OUTRO_START)
        a = smooth((t - OUTRO_START) / XF)
        if a >= 1:
            return o
        last = scene_rgb(N - 1, t - STARTS[N - 1])
        return last * (1 - a) + o * a
    i = max(k for k in range(N) if STARTS[k] <= t)
    lt = t - STARTS[i]
    cur = scene_rgb(i, lt)
    if i > 0 and lt < XF:
        prev = scene_rgb(i - 1, t - STARTS[i - 1])
        a = smooth(lt / XF)
        cur = prev * (1 - a) + cur * a
    if t < 0.35:
        cur = cur * (t / 0.35)
    return cur


def render_part(args):
    """Kadrlar [a, b) oralig'ini alohida faylga yozadi (parallel ishlash uchun)."""
    a, b, path = args
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                             "-crf", "18", "-pix_fmt", "yuv420p", "-threads", "1",
                             *(["-profile:v", "high", "-level", "5.2"] if K > 1 else []), path], stdin=subprocess.PIPE)
    for k in range(a, b):
        proc.stdin.write(render(k / FPS).clip(0, 255).astype(np.uint8).tobytes())
        if (k - a) % 60 == 0:
            print(f"  kadr {k} ({a}-{b})", flush=True)
    proc.stdin.close()
    proc.wait()
    return path


def main():
    import multiprocessing as mp
    tmp = OUT + ".noaudio.mp4"
    n = int(DURATION * FPS)
    jobs = os.cpu_count() or 1
    step = -(-n // jobs)
    parts = [(i, min(n, i + step), f"{OUT}.part{j}.mp4") for j, i in enumerate(range(0, n, step))]
    with mp.get_context("fork").Pool(len(parts)) as pool:
        pool.map(render_part, parts)
    lst = OUT + ".parts.txt"
    with open(lst, "w") as fh:
        fh.writelines(f"file '{os.path.abspath(p)}'\n" for _, _, p in parts)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
                    "-c", "copy", tmp], check=True)
    for _, _, p in parts:
        os.remove(p)
    os.remove(lst)
    # faqat diktor ovozi (fon musiqasiz), oxiriga qisqa jimlik
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", VOICE, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-af", "apad", "-t", f"{DURATION:.2f}",
                    "-movflags", "+faststart", OUT], check=True)
    os.remove(tmp)
    print("Tayyor:", OUT, f"({DURATION:.1f} s)")


if __name__ == "__main__":
    if "--preview" in sys.argv:
        times = [b + 1.5 for b in VOICE_BOUNDS] + [DURATION - 0.3]
        ims = [Image.fromarray(render(t).clip(0, 255).astype(np.uint8)).resize((270, 480)) for t in times]
        sheet = Image.new("RGB", (270 * len(ims), 480))
        for j, im in enumerate(ims):
            sheet.paste(im, (j * 270, 0))
        sheet.save(os.path.join(HERE, "preview.png"))
    else:
        main()
