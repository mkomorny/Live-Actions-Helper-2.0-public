"""Pixel-compares a screenshot of the real implementation against a reference preview shot.

    python fidelity_diff.py REFERENCE.png ACTUAL.png [--tol 24] [--max-diff 0.02] [--out diff.png]

Both images should be 1360x820 (the size the references were captured at). A pixel is
'different' when any channel differs by more than --tol (0-255; the default absorbs
font anti-aliasing). Exit 0 when the different-pixel fraction is <= --max-diff.
Reference shots live in previews/redesign-round/shots/ (see HANDOFF-redesign-for-opus.md).
"""
import argparse, sys
from PIL import Image, ImageChops

ap = argparse.ArgumentParser()
ap.add_argument("ref"); ap.add_argument("actual")
ap.add_argument("--tol", type=int, default=24); ap.add_argument("--max-diff", type=float, default=0.02)
ap.add_argument("--out", default="diff.png")
a = ap.parse_args()
r, x = Image.open(a.ref).convert("RGB"), Image.open(a.actual).convert("RGB")
if r.size != x.size:
    print(f"SIZE MISMATCH: reference {r.size} vs actual {x.size}"); sys.exit(2)
d = ImageChops.difference(r, x)
mask = d.point(lambda v: 255 if v > a.tol else 0).convert("L").point(lambda v: 255 if v else 0)
bad = mask.histogram()[255] / (r.width * r.height)
vis = Image.blend(x, Image.new("RGB", x.size, (255, 0, 0)), 0.0)
vis.paste((255, 0, 0), mask=mask)
vis.save(a.out)
print(f"different pixels: {bad:.2%} (limit {a.max_diff:.2%}) -> {'PASS' if bad <= a.max_diff else 'FAIL'}; diff image: {a.out}")
sys.exit(0 if bad <= a.max_diff else 1)
