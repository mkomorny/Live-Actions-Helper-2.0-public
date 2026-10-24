"""Makes gallery thumbnails from shots/*.png into shots/thumbs/*.jpg"""
from pathlib import Path
from PIL import Image
S = Path(__file__).resolve().parent.parent / "shots"
(S / "thumbs").mkdir(exist_ok=True)
for f in S.glob("*.png"):
    im = Image.open(f).convert("RGB")
    im.resize((680, round(680 * im.height / im.width)), Image.LANCZOS).save(S / "thumbs" / (f.stem + ".jpg"), quality=82)
print(len(list((S / "thumbs").glob("*.jpg"))), "thumbs")
