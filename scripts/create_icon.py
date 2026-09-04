from pathlib import Path
from PIL import Image
import cairosvg

root = Path(__file__).resolve().parents[1]
out = root / "assets" / "photodock.ico"
out.parent.mkdir(exist_ok=True)
sizes = [16, 24, 32, 48, 64, 128, 256]
svg = root / "assets" / "photodock-camera.svg"
png = root / "assets" / "photodock-camera.png"
cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=256, output_height=256)
base = Image.open(png).convert("RGBA")
images = [base.resize((size, size), Image.Resampling.LANCZOS) for size in sizes]
images[-1].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[:-1])
png.unlink(missing_ok=True)
print(out)
