import argparse, io, json, os, zipfile
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("--mods", default="mods")
ap.add_argument("--out", default="resourcepacks/MLauncher-LowRes.zip")
ap.add_argument("--limit", type=int, default=1024)
ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()

before = after = 0
out = None
if not a.dry_run:
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    out = zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED)
    out.writestr("pack.mcmeta", json.dumps(
        {"pack": {"pack_format": 15, "description": "MLauncher LowRes"}}))

for jar in sorted(os.listdir(a.mods)):
    if not jar.endswith(".jar"):
        continue
    with zipfile.ZipFile(os.path.join(a.mods, jar)) as z:
        names = set(z.namelist())
        for n in names:
            p = n.split("/")
            if not (n.endswith(".png") and len(p) > 4 and p[0] == "assets"
                    and p[2] == "textures" and p[3] in ("block", "item")):
                continue
            if n + ".mcmeta" in names:  # анимированные не трогаем
                continue
            try:
                img = Image.open(io.BytesIO(z.read(n)))
                img.load()
            except Exception:
                continue
            w, h = img.size
            before += w * h
            nw, nh = w, h
            while nw > a.limit or nh > a.limit:
                nw, nh = max(1, nw // 2), max(1, nh // 2)
            after += nw * nh
            if (nw, nh) != (w, h):
                print(f"{jar}: {n} {w}x{h} -> {nw}x{nh}")
                if out:
                    buf = io.BytesIO()
                    img.convert("RGBA").resize((nw, nh), Image.LANCZOS).save(buf, "PNG")
                    out.writestr(n, buf.getvalue())

if out:
    out.close()
print(f"Было: {before/1e6:.1f} МП, стало: {after/1e6:.1f} МП")
