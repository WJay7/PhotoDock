from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
out = root / "assets" / "photodock.ico"
out.parent.mkdir(exist_ok=True)
sizes = [16, 24, 32, 48, 64, 128, 256]
png = root / "assets" / "photodock-camera.png"
if png.exists():
    base = Image.open(png).convert("RGBA")
else:
    base = Image.new("RGBA", (256, 256), "#90A4AE")
    d = ImageDraw.Draw(base)
    d.rectangle((24, 78, 232, 224), fill="#212121")
    d.rectangle((48, 58, 208, 92), fill="#B0BEC5")
    d.rectangle((68, 105, 188, 225), fill="#616161")
    d.ellipse((82, 119, 174, 211), fill="#E0E0E0")
    d.ellipse((96, 133, 160, 197), fill="#2F7889")
images = [base.resize((size, size), Image.Resampling.LANCZOS) for size in sizes]
images[-1].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[:-1])
print(out)
