#!/usr/bin/env python3
"""G'uzorda suv resurslari treningi — Instagram Reels (1080x1920, 30fps).

Uslub namunadagi "G'uzor tumani hokimligi axborot xizmati" videolariga mos:
to'liq ekranli foto + sekin zoom/pan, tepada oq tuman, pastda to'q ko'k gradient,
chap tepada logotip, sariq teg, sariq vertikal chiziq + oq qalin sarlavha,
sahnalar orasida yumshoq o'tish, oxirida ko'k logotip kartasi (namunadan).

Ishga tushirish:
  python3 suv_trening_reel.py NAMUNA.mp4 OVOZ.mp3 [chiqish.mp4]
NAMUNA.mp4 — logotip va yakuniy karta olinadigan namuna video.
OVOZ.mp3   — diktor ovozi (fon musiqasiz); sahnalar ovozdagi gaplarga moslanadi.
Talab: Pillow, numpy, ffmpeg.
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE = sys.argv[1]
VOICE = sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else os.path.join(HERE, "suv_trening_reel.mp4")
W, H, FPS = 1080, 1920, 30
FONT_DIR = "/usr/share/fonts/opentype/inter"
YELLOW = (255, 196, 0)
NAVY = (18, 28, 62)
WHITE = (255, 255, 255)

XF = 0.6          # sahnalar orasidagi o'tish
LEAD = 0.35       # sahna gapdan shuncha oldin almashadi
OUTRO_FROM = 34.0  # namunadagi yakuniy karta boshlanishi
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
LOGO = card.resize((92, 92), Image.LANCZOS).convert("RGBA")
m = Image.new("L", (368, 368), 0)
ImageDraw.Draw(m).rounded_rectangle([0, 0, 367, 367], 80, fill=255)
LOGO.putalpha(m.resize((92, 92), Image.LANCZOS))


def outro_frames():
    n = int(OUTRO_LEN * FPS) + 2
    p = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(OUTRO_FROM), "-i", SAMPLE, "-frames:v", str(n),
                        "-vf", f"fps={FPS},scale={W}:{H}:flags=lanczos", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(p, np.uint8).reshape(-1, H, W, 3)


print("Namunadan yakuniy karta olinmoqda...")
OUTRO = outro_frames()

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


def header_layer():
    img = Image.new("RGBA", (W, 220), (0, 0, 0, 0))
    img.alpha_composite(LOGO, (66, 140))
    d = ImageDraw.Draw(img)
    d.text((176, 146), "G‘UZOR TUMANI HOKIMLIGI", font=font("xb", 34), fill=(30, 30, 40))
    d.text((176, 190), "AXBOROT XIZMATI", font=font("xb", 26), fill=(222, 160, 0))
    return img


HEADER = header_layer()

PHOTOS = {}
for s in SCENES:
    im = Image.open(os.path.join(HERE, "photos", s[0])).convert("RGB")
    k = H * 1.12 / im.height  # zoom/pan uchun zaxira
    PHOTOS[s[0]] = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)


def photo_frame(name, fx, z):
    im = PHOTOS[name]
    ch = H / 1.12 * 1.0 / z * 1.12 / 1.12
    ch = im.height / 1.12 / z * 1.0
    cw = ch * W / H
    cx = fx * im.width
    cx = min(max(cx, cw / 2), im.width - cw / 2)
    cy = im.height / 2
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return np.asarray(im.resize((W, H), Image.BILINEAR, box=box), np.float32)


def text_block(tag, title, sub):
    """Teg, sariq chiziq, sarlavha va izoh — pastki chap burchakda."""
    img = Image.new("RGBA", (W, 760), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tl = title.split("\n")
    size = 64
    while max(font("xb", size).getlength(l) for l in tl) > W - 150:
        size -= 2
    ft, fs, fg = font("xb", size), font("b", 36), font("b", 34)
    sl = sub.split("\n") if sub else []
    lh_t, lh_s = int(size * 1.22), 48
    h_text = len(tl) * lh_t + (18 + len(sl) * lh_s if sl else 0)
    y0 = 760 - 40 - h_text
    # teg
    tw = d.textlength(tag, font=fg)
    d.rounded_rectangle([66, y0 - 92, 66 + tw + 36, y0 - 30], 12, fill=YELLOW)
    d.text((84, y0 - 61), tag, font=fg, fill=(20, 20, 30), anchor="lm")
    # chiziq
    d.rectangle([66, y0 + 6, 74, y0 + h_text - 6], fill=YELLOW)
    y = y0
    for line in tl:
        d.text((100, y), line, font=ft, fill=WHITE)
        y += lh_t
    y += 18
    for line in sl:
        d.text((100, y), line, font=fs, fill=YELLOW)
        y += lh_s
    return img, y0


TEXTS = [text_block(s[5], s[6], s[7]) for s in SCENES]
TEXT_Y = H - 760 - 170


def scene_rgb(i, lt):
    name, fx0, fx1, z0, z1 = SCENES[i][:5]
    p = smooth(lt / LENS[i])
    base = photo_frame(name, fx0 + (fx1 - fx0) * p, z0 + (z1 - z0) * p)
    base = base * (1 - OV_NAVY[..., None]) + NAVY_ARR * OV_NAVY[..., None]
    base = base * (1 - OV_WHITE[..., None]) + 255 * OV_WHITE[..., None]
    f = Image.fromarray(base.clip(0, 255).astype(np.uint8)).convert("RGBA")
    f.alpha_composite(HEADER, (0, 0))
    # matn: pastdan siljib chiqadi, sahna oxirida so'nadi
    a = ease((lt - 0.45) / 0.6) * (1 - smooth((lt - (LENS[i] - XF - 0.15)) / 0.45))
    if a > 0.01:
        timg, _ = TEXTS[i]
        t2 = timg.copy()
        t2.putalpha(Image.fromarray((np.asarray(t2.getchannel("A"), np.float32) * a).astype(np.uint8)))
        f.alpha_composite(t2, (int(-40 * (1 - a)), TEXT_Y + int(50 * (1 - a))))
    return np.asarray(f.convert("RGB"), np.float32)


def render(t):
    if t >= OUTRO_START:
        o = OUTRO[min(len(OUTRO) - 1, int((t - OUTRO_START) * FPS))].astype(np.float32)
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


def main():
    tmp = OUT + ".noaudio.mp4"
    n = int(DURATION * FPS)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
                             "-crf", "18", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for k in range(n):
        proc.stdin.write(render(k / FPS).clip(0, 255).astype(np.uint8).tobytes())
        if k % 90 == 0:
            print(f"  kadr {k}/{n}")
    proc.stdin.close()
    proc.wait()
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
