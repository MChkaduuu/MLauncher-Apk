#!/usr/bin/env python3
"""
Создаёт ресурспак с уменьшенными текстурами из jar-файлов модов.

Нужен для видеокарт с малым пределом атласа текстур (например, Mali-G76: 8192x8192).
Берёт текстуры block/item, у которых сторона больше --limit, уменьшает их вдвое
(пока не влезут в лимит) и кладёт в zip. Анимированные текстуры не трогает.
Сами моды не меняются. Результат детерминирован: если моды те же, sha256 пака тот же.

Использование:
    python3 tools/make_lowres_pack.py --mods mods --out resourcepacks/MLauncher-LowRes.zip
    python3 tools/make_lowres_pack.py --mods mods --dry-run
"""
import argparse
import io
import json
import os
import zipfile

from PIL import Image

FIXED_DATE = (2020, 1, 1, 0, 0, 0)  # одинаковая дата -> одинаковый sha256 при каждой сборке


def build(mods_dir, out_path, limit=1024, dry_run=False, verbose=True):
    """Возвращает (мегапикселей было, стало). При dry_run zip не создаётся."""
    before = after = 0
    entries = {}  # путь внутри zip -> png-байты

    for jar in sorted(f for f in os.listdir(mods_dir) if f.endswith(".jar")):
        with zipfile.ZipFile(os.path.join(mods_dir, jar)) as z:
            names = set(z.namelist())
            for n in sorted(names):
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
                while nw > limit or nh > limit:
                    nw, nh = max(1, nw // 2), max(1, nh // 2)
                after += nw * nh
                if (nw, nh) != (w, h):
                    if verbose:
                        print(f"{jar}: {n} {w}x{h} -> {nw}x{nh}")
                    if not dry_run and n not in entries:
                        buf = io.BytesIO()
                        img.convert("RGBA").resize((nw, nh), Image.LANCZOS).save(buf, "PNG")
                        entries[n] = buf.getvalue()

    if not dry_run:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as out:
            meta = json.dumps({"pack": {"pack_format": 15, "description": "MLauncher LowRes"}})
            for name, data in [("pack.mcmeta", meta.encode())] + sorted(entries.items()):
                info = zipfile.ZipInfo(name, FIXED_DATE)
                info.compress_type = zipfile.ZIP_DEFLATED
                out.writestr(info, data)
    return before, after


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mods", default="mods")
    ap.add_argument("--out", default="resourcepacks/MLauncher-LowRes.zip")
    ap.add_argument("--limit", type=int, default=1024)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    before, after = build(a.mods, a.out, a.limit, a.dry_run)
    print(f"Было: {before / 1e6:.1f} МП, стало: {after / 1e6:.1f} МП")


if __name__ == "__main__":
    main()
