#!/usr/bin/env python3
"""
build-icon.py - The Lounge's icons from the Vader painting (hero.webp). Hector picked it on 2026-09-16 over VaderClawd and
Gargantua, and the version FITTED IN THE FRAME (preview version 3: "the second one that you fit in the frame"): the whole
figure - helmet, cigarette smoke, hand and the full blade with its glow - centred on the painting's own black, nothing cut.

  python3 tools/build-icon.py        # writes the icon set and face.png, prints the header's data URI size

2026-09-18 (Hector: "i went and deleted the icons and add them again and still i dont see the icons"): every icon file was
correct and served 200, and all four DECODED in real WebKit - so the files were never the problem. Safari keeps its own site-icon
store, which a deleted bookmark does not clear, and the only cure that does not wipe his website data (his hub layout and the
rig's job history live in it) is an icon URL Safari has never asked for. So the set is written TWICE: the original names, which
stay so nothing already cached 404s, and a -v2 set that the page actually declares. If Safari ever caches a miss again, bump
the token to v3 - that is the whole mechanism.

The painting's shadows are lifted a touch (gamma 0.78) so the black helmet keeps its shape at icon size; whites and red stay.
Crops are in the painting's own pixels (736 x 1408).
"""
import base64, io, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURE = (174, 328, 694, 1006)   # everything brighter than the black ground, the blade's glow included (measured)
HOME_MARGIN = 1.12                # room around the figure on the home screen, clear of iPhone's rounded corners
TAB_MARGIN = 1.04
GAMMA = .78


def cut(src, margin):
    x0, y0, x1, y1 = FIGURE
    cx, cy, side = (x0 + x1) / 2, (y0 + y1) / 2, int(max(x1 - x0, y1 - y0) * margin)
    left, top = int(cx - side / 2), int(cy - side / 2)
    square = Image.new('RGB', (side, side), (0, 0, 0))   # the painting's ground is pure black: the square extends it
    square.paste(src.crop((max(0, left), max(0, top), min(src.width, left + side), min(src.height, top + side))), (max(0, -left), max(0, -top)))
    lut = [int(255 * ((i / 255) ** GAMMA)) for i in range(256)]
    return square.point(lut * 3)


def main():
    src = Image.open(os.path.join(ROOT, 'hero.webp')).convert('RGB')
    home, tab = cut(src, HOME_MARGIN), cut(src, TAB_MARGIN)
    out = {'apple-touch-icon.png': home.resize((180, 180), Image.LANCZOS),
           'favicon-32.png': tab.resize((32, 32), Image.LANCZOS),
           'favicon-16.png': tab.resize((16, 16), Image.LANCZOS),
           'face.png': tab.resize((56, 56), Image.LANCZOS),
           # the names the page declares: a URL Safari has no cached answer for, plus the two sizes a
           # web app manifest wants (192 and 512) so the home screen has a second, independent path in.
           'icon-180-v2.png': home.resize((180, 180), Image.LANCZOS),
           'icon-192-v2.png': home.resize((192, 192), Image.LANCZOS),
           'icon-512-v2.png': home.resize((512, 512), Image.LANCZOS),
           'icon-32-v2.png': tab.resize((32, 32), Image.LANCZOS),
           'icon-16-v2.png': tab.resize((16, 16), Image.LANCZOS)}
    for name, im in out.items():
        im.save(os.path.join(ROOT, name), optimize=True)
        print('wrote', name, im.size)
    # favicon.ico as well: Safari asks for one by that name when it wants a site's icon for a bookmark (Hector 2026-09-17:
    # his Safari bookmark still showed a letter). 48, 32 and 16 in the one file.
    ico = tab.resize((48, 48), Image.LANCZOS)
    for name in ('favicon.ico', 'icon-v2.ico'):
        ico.save(os.path.join(ROOT, name), sizes=[(48, 48), (32, 32), (16, 16)])
        print('wrote', name, os.path.getsize(os.path.join(ROOT, name)), 'bytes')
    buf = io.BytesIO(); out['face.png'].save(buf, 'PNG', optimize=True)
    print('face data URI', len('data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()), 'chars')


if __name__ == '__main__':
    main()
