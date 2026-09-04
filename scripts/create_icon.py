from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parents[1]
out = root / "assets" / "photodock.ico"
out.parent.mkdir(exist_ok=True)
sizes = [16, 24, 32, 48, 64, 128, 256]
sources = {32: "photodock-32.ico", 64: "photodock-64.ico", 96: "photodock-96.ico", 128: "photodock-128.ico"}
images = []
for size in sizes:
    source_size = min(sources, key=lambda candidate: abs(candidate - size))
    image = Image.open(root / "assets" / sources[source_size]).convert("RGBA")
    images.append(image.resize((size, size), Image.Resampling.LANCZOS))
images[-1].save(out, format="ICO", sizes=[(s, s) for s in sizes], append_images=images[:-1])
print(out)
