#!/usr/bin/env python3
"""G'uzorda Ishla — Instagram Reels videosi (1080x1920, 30fps).

Ranglar va uslub kanal logotipiga mos: to'q (deyarli qora) fon,
sariq-oltin nur, sariq "pin" belgisi ichida portfel, oq + sariq matn.

Ishga tushirish:  python3 guzorda_ishla_reel.py [chiqish.mp4]
Talab: Pillow, numpy, ffmpeg.
"""
import math
import os
import random
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DURATION = 18.0
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "guzorda_ishla_reel.mp4")

# --- Brend ranglari (logotipdan) ---
BG_TOP = (22, 27, 33)
BG_BOT = (12, 15, 19)
YELLOW = (255, 204, 0)
YELLOW_DEEP = (232, 168, 0)
GOLD_DARK = (110, 88, 10)
WHITE = (255, 255, 255)
INK = (26, 26, 28)
CARD = (24, 29, 35)

FONT_DIR = "/usr/share/fonts/opentype/inter"


def font(weight, size):
    name = {"black": "Inter-Black.otf", "xbold": "Inter-ExtraBold.otf",
            "bold": "Inter-Bold.otf", "semi": "Inter-SemiBold.otf"}[weight]
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


# ---------------- easing ----------------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur)


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    return 3 * x * x - 2 * x * x * x


def ease_out_back(x, s=1.7):
    x -= 1
    return x * x * ((s + 1) * x + s) + 1


def ease_out_bounce(x):
    n1, d1 = 7.5625, 2.75
    if x < 1 / d1:
        return n1 * x * x
    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75
    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375
    x -= 2.625 / d1
    return n1 * x * x + 0.984375


# ---------------- static assets ----------------
def make_background():
    y = np.linspace(0, 1, H)[:, None]
    top, bot = np.array(BG_TOP, float), np.array(BG_BOT, float)
    img = top * (1 - y[..., None]) + bot * y[..., None]
    img = np.broadcast_to(img, (H, W, 3)).copy()
    # nozik setka (logotip doirasidagi kabi)
    grid = np.zeros((H, W), float)
    grid[::54, :] = 1
    grid[:, ::54] = 1
    img += grid[..., None] * np.array([6, 6, 4], float)
    # vinyetka
    yy, xx = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.7)) ** 2)
    img *= (1 - 0.45 * clamp_arr(d - 0.35))[..., None]
    return np.clip(img, 0, 255).astype(np.uint8)


def clamp_arr(a):
    return np.clip(a, 0, 1)


def make_glow(radius, color, strength):
    s = radius * 2
    yy, xx = np.mgrid[0:s, 0:s]
    d = np.sqrt((xx - radius) ** 2 + (yy - radius) ** 2) / radius
    a = np.clip(1 - d, 0, 1) ** 2.2 * strength
    arr = np.zeros((s, s, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def draw_briefcase(d, cx, cy, w, color, accent):
    h = w * 0.72
    r = w * 0.12
    # dasta
    hw, hh, th = w * 0.38, h * 0.32, w * 0.075
    d.rounded_rectangle([cx - hw / 2, cy - h / 2 - hh * 0.75, cx + hw / 2, cy - h / 2 + th],
                        radius=th * 1.2, outline=color, width=int(th))
    # korpus
    d.rounded_rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], radius=r, fill=color)
    # chiziq
    d.rectangle([cx - w / 2, cy - h * 0.08, cx + w / 2, cy - h * 0.02], fill=(70, 66, 50))
    # qulf
    lw, lh = w * 0.13, h * 0.17
    d.rounded_rectangle([cx - lw / 2, cy - h * 0.13, cx + lw / 2, cy - h * 0.13 + lh], radius=lw * 0.2, fill=accent)


def make_pin(size=520):
    """Logotipdagi sariq pin + oq doira + portfel. size = kenglik."""
    S = size * 3
    img = Image.new("RGBA", (S, int(S * 1.32)), (0, 0, 0, 0))
    R = S / 2
    cx, cy = S / 2, R
    tip_y = S * 1.30
    # pin shakli maskasi
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([0, 0, S, S], fill=255)
    ang = math.radians(38)
    p1 = (cx - R * math.cos(ang) * 0.99, cy + R * math.sin(ang) * 0.99)
    p2 = (cx + R * math.cos(ang) * 0.99, cy + R * math.sin(ang) * 0.99)
    md.polygon([p1, p2, (cx, tip_y)], fill=255)
    # gradient (yuqori - och sariq, past - to'q oltin)
    gy = np.linspace(0, 1, img.size[1])[:, None]
    c1, c2 = np.array([255, 214, 30], float), np.array([228, 160, 0], float)
    grad = c1 * (1 - gy[..., None]) + c2 * gy[..., None]
    grad = np.broadcast_to(grad, (img.size[1], img.size[0], 3)).astype(np.uint8)
    body = Image.fromarray(np.dstack([grad, np.array(mask)]), "RGBA")
    # yengil yaltiroq
    hl = Image.new("L", img.size, 0)
    ImageDraw.Draw(hl).ellipse([S * 0.12, S * 0.05, S * 0.62, S * 0.45], fill=70)
    hl = hl.filter(ImageFilter.GaussianBlur(S * 0.06))
    hl = Image.fromarray(np.minimum(np.array(hl), np.array(mask)))
    white = Image.new("RGBA", img.size, (255, 255, 255, 0))
    white.putalpha(hl)
    img = Image.alpha_composite(img, body)
    img = Image.alpha_composite(img, white)
    d = ImageDraw.Draw(img)
    ir = R * 0.66
    d.ellipse([cx - ir, cy - ir, cx + ir, cy + ir], fill=WHITE)
    draw_briefcase(d, cx, cy + ir * 0.06, ir * 1.05, INK, YELLOW)
    return img.resize((size, int(size * 1.32)), Image.LANCZOS)


def make_small_briefcase_icon(size):
    S = size * 3
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([0, 0, S, S], fill=YELLOW)
    draw_briefcase(d, S / 2, S / 2 + S * 0.03, S * 0.5, INK, WHITE)
    return img.resize((size, size), Image.LANCZOS)


_text_cache = {}


def text_img(txt, weight, size, color, tracking=0, stroke=0, stroke_color=None):
    key = (txt, weight, size, color, tracking, stroke, stroke_color)
    if key in _text_cache:
        return _text_cache[key]
    f = font(weight, size)
    # harflararo masofa bilan chizish
    widths = [f.getlength(ch) for ch in txt]
    total = sum(widths) + tracking * (len(txt) - 1)
    asc, desc = f.getmetrics()
    pad = 10 + stroke
    img = Image.new("RGBA", (int(total + pad * 2), asc + desc + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad
    for ch, w in zip(txt, widths):
        d.text((x, pad), ch, font=f, fill=color, stroke_width=stroke,
               stroke_fill=stroke_color or color)
        x += w + tracking
    _text_cache[key] = img
    return img


def with_alpha(img, a):
    if a >= 0.999:
        return img
    out = img.copy()
    al = np.array(out.getchannel("A"), float) * clamp(a)
    out.putalpha(Image.fromarray(al.astype(np.uint8)))
    return out


def paste_center(frame, img, cx, cy, alpha=1.0, scale=1.0, angle=0.0):
    if alpha <= 0.003 or scale <= 0.01:
        return
    im = img
    if abs(scale - 1) > 1e-3:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if abs(angle) > 0.05:
        im = im.rotate(angle, resample=Image.BICUBIC, expand=True)
    im = with_alpha(im, alpha)
    frame.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def rounded_layer(w, h, r, fill, outline=None, width=0):
    S = 2
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=r * S, fill=fill,
                                          outline=outline, width=width * S)
    return img.resize((w, h), Image.LANCZOS)


# ---------------- assets ----------------
print("Assetlar tayyorlanmoqda...")
BG = Image.fromarray(make_background()).convert("RGBA")
GLOW_BIG = make_glow(700, YELLOW, 0.33)
GLOW_MID = make_glow(420, (230, 170, 0), 0.40)
PIN = make_pin(360)
PIN_SMALL = make_pin(230)
ICON = make_small_briefcase_icon(110)

SHADOW = Image.new("RGBA", (240, 60), (0, 0, 0, 0))
ImageDraw.Draw(SHADOW).ellipse([0, 0, 239, 59], fill=(0, 0, 0, 150))
SHADOW = SHADOW.filter(ImageFilter.GaussianBlur(8))


def make_ring(radius, width, color):
    S = 2
    s = radius * 2 + 20
    img = Image.new("RGBA", (s * S, s * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = s * S / 2
    d.ellipse([c - radius * S, c - radius * S, c + radius * S, c + radius * S], outline=color, width=width * S)
    return img.resize((s, s), Image.LANCZOS)


RING = make_ring(460, 3, (230, 180, 20, 200))
DISC = make_glow(540, (120, 95, 10), 0.85)

random.seed(7)
PARTICLES = [(random.uniform(0, W), random.uniform(0, H), random.uniform(2, 6),
              random.uniform(25, 80), random.uniform(0, 6.28)) for _ in range(55)]

JOBS = [("Sotuvchi-konsultant", "To'liq stavka"),
        ("Haydovchi", "Kunlik ish haqi"),
        ("Oshpaz yordamchisi", "Tajribasiz ham"),
        ("Ofis menejeri", "Smenali grafik"),
        ("Usta / Quruvchi", "Yuqori maosh")]
CARD_W, CARD_H = 900, 170
CARD_BG = rounded_layer(CARD_W, CARD_H, 34, CARD + (235,), outline=(255, 204, 0, 120), width=2)
TAG = rounded_layer(150, 54, 27, YELLOW + (255,))
BTN = rounded_layer(760, 150, 75, YELLOW + (255,))


# ---------------- frame composition ----------------
def background(t):
    f = BG.copy()
    # sekin harakatlanuvchi sariq nur
    gx = W * 0.75 + math.sin(t * 0.5) * 140
    gy = H * 0.78 + math.cos(t * 0.4) * 120
    f.alpha_composite(GLOW_BIG, (int(gx - 700), int(gy - 700)))
    gx2 = W * 0.18 + math.cos(t * 0.35) * 100
    gy2 = H * 0.2 + math.sin(t * 0.45) * 90
    f.alpha_composite(make_cached_glow_small(), (int(gx2 - 420), int(gy2 - 420)))
    d = ImageDraw.Draw(f)
    for (x, y, r, sp, ph) in PARTICLES:
        yy = (y - t * sp) % (H + 40) - 20
        xx = x + math.sin(t * 0.8 + ph) * 18
        a = int(90 + 80 * math.sin(t * 2 + ph))
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(255, 205, 40, max(0, a)))
    return f


_small_glow = None


def make_cached_glow_small():
    global _small_glow
    if _small_glow is None:
        _small_glow = make_glow(420, (200, 160, 30), 0.18)
    return _small_glow


def wipe(f, t, t0):
    """Sahnalar orasidagi sariq diagonal o'tish."""
    p = prog(t, t0 - 0.25, 0.5)
    if p <= 0 or p >= 1:
        return
    x = -1300 + p * (W + 2600)
    d = ImageDraw.Draw(f)
    sk = 500
    d.polygon([(x, 0), (x + 700, 0), (x + 700 - sk, H), (x - sk, H)], fill=YELLOW + (255,))
    d.polygon([(x + 720, 0), (x + 760, 0), (x + 760 - sk, H), (x + 720 - sk, H)], fill=(20, 20, 22, 255))


def scene_intro(f, t):
    # 0.0 - 3.6
    out = 1 - prog(t, 3.2, 0.4)
    cx, rc = W / 2, 880
    # disk va halqa
    pd = ease_out_cubic(prog(t, 0.0, 0.8))
    paste_center(f, DISC, cx, rc, alpha=pd * out, scale=0.6 + 0.4 * pd)
    pr = ease_out_back(prog(t, 0.25, 0.8))
    paste_center(f, RING, cx, rc, alpha=clamp(pr) * out, scale=max(0.01, pr), angle=t * 20)
    # pin tushishi (bounce)
    pp = prog(t, 0.3, 1.1)
    drop = ease_out_bounce(pp)
    py = -400 + (640 + 400) * drop
    sh = clamp((pp - 0.3) * 2) * drop
    paste_center(f, SHADOW, cx, 868, alpha=sh * 0.8 * out, scale=0.5 + 0.5 * drop)
    float_y = math.sin(max(0, t - 1.4) * 3) * 8 if t > 1.4 else 0
    paste_center(f, PIN, cx, py + float_y, alpha=out)
    cy = 680
    # matnlar
    p1 = ease_out_cubic(prog(t, 1.2, 0.6))
    t1 = text_img("G‘UZORDA", "black", 140, WHITE, tracking=4)
    paste_center(f, t1, cx, cy + 325 + (1 - p1) * 80, alpha=p1 * out)
    p2 = ease_out_back(prog(t, 1.5, 0.6))
    t2 = text_img("ISHLA", "black", 160, YELLOW, tracking=10)
    paste_center(f, t2, cx, cy + 470, alpha=clamp(p2) * out, scale=max(0.01, 0.6 + 0.4 * p2))
    p3 = ease_out_cubic(prog(t, 2.1, 0.6))
    t3 = text_img("G‘uzor tumanidagi ish e’lonlari", "semi", 50, (225, 225, 225))
    paste_center(f, t3, cx, 1460, alpha=p3 * out)


def scene_question(f, t):
    # 3.6 - 7.0
    lt = t - 3.6
    out = 1 - prog(t, 6.6, 0.4)
    cx = W / 2
    p1 = ease_out_cubic(prog(lt, 0.0, 0.5))
    a = text_img("ISH", "black", 230, WHITE, tracking=6)
    paste_center(f, a, cx - (1 - p1) * 600, 640, alpha=p1 * out)
    # sariq marker ostida "QIDIRYAPSIZMI?"
    b = text_img("QIDIRYAPSIZMI?", "black", 104, INK, tracking=2)
    p2 = ease_in_out(prog(lt, 0.35, 0.5))
    mw = b.width + 40
    bw = int(mw * p2)
    if bw > 4:
        d = ImageDraw.Draw(f)
        d.rounded_rectangle([cx - mw / 2, 795, cx - mw / 2 + bw, 945], radius=18,
                            fill=YELLOW + (int(255 * out),))
    p3 = prog(lt, 0.6, 0.3)
    paste_center(f, b, cx, 870, alpha=p3 * out)
    # pastki matn
    p4 = ease_out_cubic(prog(lt, 1.1, 0.6))
    for i, line in enumerate(["G‘uzordagi eng so‘nggi", "vakansiyalar — bir joyda!"]):
        ti = text_img(line, "xbold", 68, WHITE if i == 0 else YELLOW)
        paste_center(f, ti, cx, 1130 + i * 95 + (1 - p4) * 60, alpha=p4 * out)
    # aylanuvchi kichik pin
    p5 = ease_out_back(prog(lt, 1.5, 0.6))
    bob = math.sin(lt * 3) * 12
    paste_center(f, PIN_SMALL, cx, 1500 + bob, alpha=clamp(p5) * out, scale=max(0.01, p5))


def scene_jobs(f, t):
    # 7.0 - 12.0
    lt = t - 7.0
    out = 1 - prog(t, 11.6, 0.4)
    cx = W / 2
    ph = ease_out_cubic(prog(lt, 0.0, 0.5))
    h1 = text_img("BUGUNGI VAKANSIYALAR", "black", 72, YELLOW, tracking=3)
    paste_center(f, h1, cx, 330 - (1 - ph) * 60, alpha=ph * out)
    d = ImageDraw.Draw(f)
    lw = int(220 * ph)
    d.rectangle([cx - lw, 395, cx + lw, 401], fill=(255, 255, 255, int(160 * out)))
    for i, (title, sub) in enumerate(JOBS):
        p = ease_out_back(prog(lt, 0.35 + i * 0.22, 0.6), 1.2)
        y = 520 + i * 205
        x = cx + (1 - p) * 1100
        a = clamp(p) * out
        card = CARD_BG.copy()
        cd = ImageDraw.Draw(card)
        card.alpha_composite(ICON, (30, (CARD_H - ICON.height) // 2))
        cd.text((165, 34), title, font=font("xbold", 50), fill=WHITE)
        cd.text((165, 100), sub, font=font("semi", 34), fill=(170, 175, 182))
        card.alpha_composite(TAG, (CARD_W - 180, (CARD_H - 54) // 2))
        cd.text((CARD_W - 105, CARD_H // 2), "YANGI", font=font("black", 26), fill=INK, anchor="mm")
        paste_center(f, card, x, y, alpha=a)
    pf = ease_out_cubic(prog(lt, 1.8, 0.6))
    ft = text_img("Har kuni yangi e’lonlar", "xbold", 60, WHITE)
    paste_center(f, ft, cx, 1580 + (1 - pf) * 50, alpha=pf * out)


def scene_employer(f, t):
    # 12.0 - 14.8
    lt = t - 12.0
    out = 1 - prog(t, 14.4, 0.4)
    cx = W / 2
    p1 = ease_out_cubic(prog(lt, 0.0, 0.5))
    a = text_img("ISH BERUVCHIMISIZ?", "black", 92, WHITE, tracking=2)
    paste_center(f, a, cx, 700 + (1 - p1) * 80, alpha=p1 * out)
    p2 = ease_out_back(prog(lt, 0.4, 0.6))
    paste_center(f, PIN_SMALL, cx, 1000 + math.sin(lt * 3) * 10, alpha=clamp(p2) * out,
                 scale=max(0.01, p2 * 0.9))
    p3 = ease_out_cubic(prog(lt, 0.8, 0.6))
    for i, (line, col) in enumerate([("Vakansiyangizni joylang —", WHITE),
                                     ("minglab nomzodlar ko‘radi!", YELLOW)]):
        ti = text_img(line, "xbold", 66, col)
        paste_center(f, ti, cx, 1280 + i * 95 + (1 - p3) * 60, alpha=p3 * out)
    p4 = ease_out_cubic(prog(lt, 1.3, 0.5))
    tt = text_img("Direktga yozing  →", "bold", 50, (210, 210, 210))
    paste_center(f, tt, cx, 1530, alpha=p4 * out)


def scene_cta(f, t):
    # 14.8 - 18.0
    lt = t - 14.8
    cx = W / 2
    fade_end = 1 - prog(t, 17.6, 0.4) * 0.0
    pd = ease_out_cubic(prog(lt, 0.0, 0.6))
    paste_center(f, DISC, cx, 800, alpha=pd, scale=0.6 + 0.3 * pd)
    paste_center(f, RING, cx, 800, alpha=pd * 0.9, scale=max(0.01, 0.88 * pd), angle=-lt * 25)
    pp = ease_out_back(prog(lt, 0.1, 0.6))
    paste_center(f, PIN, cx, 600 + math.sin(lt * 3) * 10, alpha=clamp(pp), scale=max(0.01, pp * 0.8))
    p1 = ease_out_cubic(prog(lt, 0.4, 0.5))
    paste_center(f, text_img("G‘UZORDA", "black", 130, WHITE, tracking=4), cx, 910 + (1 - p1) * 60, alpha=p1)
    paste_center(f, text_img("ISHLA", "black", 150, YELLOW, tracking=10), cx, 1050 + (1 - p1) * 60, alpha=p1)
    # puls tugma
    pb = ease_out_back(prog(lt, 0.8, 0.6))
    pulse = 1 + 0.045 * math.sin(max(0, lt - 1.4) * 7) if lt > 1.4 else 1
    btn = BTN.copy()
    bd = ImageDraw.Draw(btn)
    bd.text((BTN.width / 2, BTN.height / 2), "OBUNA BO‘LING", font=font("black", 64), fill=INK, anchor="mm")
    # tugma atrofida nur
    if lt > 1.4:
        ga = 0.5 + 0.5 * math.sin((lt - 1.4) * 7)
        paste_center(f, GLOW_MID, cx, 1440, alpha=0.6 * ga, scale=0.9)
    paste_center(f, btn, cx, 1440, alpha=clamp(pb) * fade_end, scale=max(0.01, pb * pulse))
    p3 = ease_out_cubic(prog(lt, 1.3, 0.6))
    paste_center(f, text_img("Ish o‘zi sizni topadi!", "xbold", 56, WHITE), cx, 1620 + (1 - p3) * 40, alpha=p3)


def render(t):
    f = background(t)
    if t < 3.6:
        scene_intro(f, t)
    elif t < 7.0:
        scene_question(f, t)
    elif t < 12.0:
        scene_jobs(f, t)
    elif t < 14.8:
        scene_employer(f, t)
    else:
        scene_cta(f, t)
    for t0 in (3.6, 7.0, 12.0, 14.8):
        wipe(f, t, t0)
    # boshida qoradan ochilish
    if t < 0.3:
        f = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), f, t / 0.3)
    return f.convert("RGB")


def main():
    n = int(DURATION * FPS)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
           "-profile:v", "high", "-movflags", "+faststart", OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        proc.stdin.write(render(t).tobytes())
        if i % 60 == 0:
            print(f"  kadr {i}/{n}")
    proc.stdin.close()
    proc.wait()
    print("Tayyor:", OUT)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        for ts in [1.0, 2.8, 5.0, 9.5, 13.5, 17.0, 3.6]:
            render(ts).save(f"preview_{ts:.1f}.png")
    else:
        main()
