#!/usr/bin/env python3
"""
build-icon.py - The Lounge's icons, cut from the Vader painting (hero.webp). Hector picked this one on 2026-09-16 over
VaderClawd and Gargantua (preview version 2): helmet, cigarette smoke and the blade for the home screen; the helmet and the
blade for the browser tab and the header square, the close-up that still reads at 16 points.

  python3 tools/build-icon.py        # writes apple-touch-icon.png, favicon-32.png, favicon-16.png and face.png, prints the header's data URI size

The painting's shadows are lifted a touch (gamma 0.78) so the black helmet keeps its shape at icon size; whites and red stay.
Crops are in the painting's own pixels (736 x 1408).
"""
import base64, io, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME_BOX = (160, 540, 560, 940)   # helmet, smoke, blade to the corner
TAB_BOX = (215, 590, 515, 890)    # helmet and the base of the blade
GAMMA = .78


def cut(src, box):
    lut = [int(255 * ((i / 255) ** GAMMA)) for i in range(256)]
    return src.crop(box).point(lut * 3)


def main():
    src = Image.open(os.path.join(ROOT, 'hero.webp')).convert('RGB')
    home, tab = cut(src, HOME_BOX), cut(src, TAB_BOX)
    out = {'apple-touch-icon.png': home.resize((180, 180), Image.LANCZOS),
           'favicon-32.png': tab.resize((32, 32), Image.LANCZOS),
           'favicon-16.png': tab.resize((16, 16), Image.LANCZOS),
           'face.png': tab.resize((56, 56), Image.LANCZOS)}   # the header's 28-point square, 2x
    for name, im in out.items():
        im.save(os.path.join(ROOT, name), optimize=True)
        print('wrote', name, im.size)
    buf = io.BytesIO(); out['face.png'].save(buf, 'PNG', optimize=True)
    print('face data URI', len('data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()), 'chars')


if __name__ == '__main__':
    main()
