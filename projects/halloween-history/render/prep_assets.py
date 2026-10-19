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
