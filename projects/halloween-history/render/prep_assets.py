"""Cut real reference photos into RGBA cutouts -> ../assets/cut/*.png  (run once; outputs are committed).
Needs: rembg (u2net), opencv-python-headless. Renders of stills only read assets/cut/.
Source credits: ../assets/CREDITS.md
"""
import os
import numpy as np, cv2
from PIL import Image
from rembg import remove, new_session

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'assets', 'src'); OUT = os.path.join(HERE, '..', 'assets', 'cut')
os.makedirs(OUT, exist_ok=True)
u2 = new_session('u2net')


def rem(name, box, out, maxside=None):
    im = Image.open(os.path.join(SRC, name)).convert('RGB').crop(box)
    if maxside:
        im.thumbnail((maxside, maxside))
    o = remove(im, session=u2)
    o.save(os.path.join(OUT, out)); print(out, o.size)
    return o


# 1 Mari Lwyd figure (sheet + decorated horse skull); right edge = reins leaving frame -> fade out
o = rem('mari_lwyd_llangynwyd_evans_1904-1910.jpg', (450, 950, 1600, 3820), 'mari_lwyd.png')
a = np.asarray(o).copy(); w = a.shape[1]
ramp = np.clip((w - 60 - np.arange(w)) / 40, 0, 1)
a[..., 3] = (a[..., 3] * ramp[None, :]).astype(np.uint8)
Image.fromarray(a).save(os.path.join(OUT, 'mari_lwyd.png'))

# 2 Irish Halloween cloth mask (Horniman): GrabCut on 800px-wide copy, then upscale matte
im = cv2.imread(os.path.join(SRC, 'irish_halloween_mask_horniman.jpg'))
sc = im.shape[1] / 800
sm = cv2.resize(im, (800, int(im.shape[0] / sc)))
m = np.zeros(sm.shape[:2], np.uint8)
cv2.grabCut(sm, m, (170, 55, 470, 440), np.zeros((1, 65)), np.zeros((1, 65)), 6, cv2.GC_INIT_WITH_RECT)
m = np.where((m == 1) | (m == 3), 255, 0).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = np.where(lab == k, 255, 0).astype(np.uint8)
big = cv2.resize(m, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_LINEAR)
big = cv2.GaussianBlur(big, (0, 0), 2)
x0, y0, x1, y1 = 900, 250, 3700, 2850
rgb = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)[y0:y1, x0:x1]
rgba = np.dstack([rgb, big[y0:y1, x0:x1]])
img = Image.fromarray(rgba); img.thumbnail((1600, 1600)); img.save(os.path.join(OUT, 'irish_mask.png')); print('irish_mask.png', img.size)

# 3 Dennison 1920 black-cat paper face (page 36, 300 dpi)
# printed halftone: matte = dark ink region, holes filled, largest component (rembg merged the frame line)
im = Image.open(os.path.join(SRC, 'dennison_bogie_book_1920_p36_300dpi.jpg')).convert('RGB').crop((1020, 735, 1400, 1060))
g = cv2.GaussianBlur(cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2GRAY), (0, 0), 2.0)
m = (g < 95).astype(np.uint8) * 255
clip = np.zeros_like(m)
cv2.ellipse(clip, (160, 172), (138, 122), 0, 0, 360, 255, -1)
cv2.fillPoly(clip, [np.array([(8, 30), (95, 85), (30, 140)]), np.array([(325, 22), (240, 85), (310, 140)])], 255)
m = cv2.bitwise_and(m, clip)
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
k = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); m = np.where(lab == k, 255, 0).astype(np.uint8)
cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
fill = np.zeros_like(m); cv2.drawContours(fill, cnts, -1, 255, -1)
fill = cv2.GaussianBlur(fill, (0, 0), 1.0)
Image.fromarray(np.dstack([np.asarray(im), fill])).save(os.path.join(OUT, 'dennison_cat.png')); print('dennison_cat.png', im.size)

# 4 Turnip jack-o'-lantern (Geni)
rem('turnip_jackolantern_geni.jpg', (0, 0, 547, 505), 'turnip.png')

# 5 Carved pumpkin (CC0), right-hand pumpkin
rem('carved_pumpkin_teutschmann_cc0.jpg', (1850, 650, 3200, 1950), 'pumpkin.png')

# --- v0.3 shot 03 additions (run after sources are in assets/src/) ---
# Skekler: color-threshold straw + rembg union; see one-off script history in commit message.
# Country Life Irish mask: rembg or GrabCut on Traditional-irish-halloween-mask.jpg
# Outputs: cut/skekler.png, cut/irish_mask_country_life.png
# Horniman irish_mask.png unchanged from v0.2.


def build_skekler_silhouette():
    """Clean organic Skekler silhouette (no museum bg). Photo was too contaminated by glass/case;
    silhouette treatment only needs shape + straw-like luminance, so we synthesize both.
    Output: ../assets/cut/skekler.png
    """
    import numpy as np, cv2
    from PIL import Image
    H, W = 2400, 1100
    rng = np.random.default_rng(1031)
    cx = W // 2
    mask = np.zeros((H, W), np.uint8)
    for y in range(60, 620):
        t = (y - 60) / 560
        half = (22 + t * 120) if t < 0.84 else (22 + 0.84 * 120 + (t - 0.84) / 0.16 * 70)
        j = 4 * np.sin(y / 10.0) + 2.5 * np.sin(y / 4.1)
        mask[y, max(0, int(cx - half + j)):min(W, int(cx + half + j))] = 255
    top_y, bot_y = 760, 2150
    for y in range(top_y, bot_y):
        t = (y - top_y) / (bot_y - top_y)
        if t < 0.14: half = 190 + t / 0.14 * 80
        elif t < 0.48: half = 270 + (t - 0.14) / 0.34 * 90
        else: half = 360 - (t - 0.48) / 0.52 * 50
        j = 6 * np.sin(y / 12.0) + 4 * np.sin(y / 4.8) + rng.normal(0, 1.4)
        mask[y, max(0, int(cx - half + j)):min(W, int(cx + half + j))] = 255
    for x in range(W):
        if mask[bot_y - 8, x] == 0: continue
        fl = int(abs(rng.normal(85, 40))); fl = max(12, min(160, fl))
        if rng.random() < 0.28: fl = int(fl * 0.4)
        for yy in range(bot_y, min(H - 1, bot_y + fl)):
            if abs(x - cx) < 380 - (yy - bot_y) * 0.2 and rng.random() > 0.12:
                mask[yy, x] = 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    alpha = cv2.GaussianBlur(mask, (0, 0), 1.5)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cols = cv2.GaussianBlur(rng.normal(0, 1, W).astype(np.float32).reshape(1, -1), (0, 0), 1.3).ravel()
    fibre = 105 + 28 * cols[None, :] + 10 * np.sin(xx / 5.0) + 5 * np.sin(xx / 2.3) + rng.normal(0, 3.5, (H, W)).astype(np.float32)
    for yb, th, dark in ((560, 30, 0.35), (800, 40, 0.40)):
        band = np.exp(-0.5 * ((yy - yb) / th) ** 2)
        fibre = fibre * (1 - dark * band) + (55 + rng.normal(0, 5, (H, W))) * band * 0.7 + fibre * band * 0.3
    dist = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    fibre *= (0.48 + 0.58 * (dist / (dist.max() + 1e-6)) ** 0.6)
    fibre[:620] *= np.linspace(1.12, 1.0, 620)[:, None]
    Lt = np.clip((np.clip(fibre, 0, 255) - 35) / 145, 0, 1)
    lo, hi = np.array([42, 24, 14], np.float32), np.array([168, 132, 88], np.float32)
    rgb = (lo * (1 - Lt[..., None]) + hi * Lt[..., None]).clip(0, 255).astype(np.uint8)
    rgb[mask == 0] = 0
    ys, xs = np.where(alpha > 10)
    img = Image.fromarray(np.dstack([rgb[ys.min():ys.max() + 1, xs.min():xs.max() + 1],
                                     alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1].astype(np.uint8)]))
    img.thumbnail((560, 1450), Image.LANCZOS)
    out = os.path.join(OUT, 'skekler.png'); img.save(out); print('skekler silhouette', img.size)
