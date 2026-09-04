from pathlib import Path
from PIL import Image, ImageDraw

out = Path(__file__).resolve().parents[1] / "assets" / "photodock.ico"
out.parent.mkdir(exist_ok=True)
sizes = [16, 24, 32, 48, 64, 128, 256]
images = []
for size in sizes:
    im = Image.new("RGBA", (size, size), "#1769e8")
    d = ImageDraw.Draw(im)
    s = size
    d.rectangle((s*.18,s*.34,s*.82,s*.82), fill="white")
    d.rectangle((s*.34,s*.23,s*.66,s*.36), fill="white")
    d.rectangle((s*.30,s*.43,s*.70,s*.70), fill="#1769e8")
    d.rectangle((s*.36,s*.49,s*.64,s*.64), fill="#75b5ff")
    images.append(im)
images[-1].save(out, format="ICO", sizes=[(s,s) for s in sizes], append_images=images[:-1])
print(out)
