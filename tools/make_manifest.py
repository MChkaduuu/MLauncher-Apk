#!/usr/bin/env python3
"""
Генератор manifest.json для лаунчера (моды + необязательный ресурспак).

Использование (из корня репозитория):
    python3 tools/make_manifest.py mods https://raw.githubusercontent.com/USER/REPO/main/mods \
        --lowres resourcepacks https://raw.githubusercontent.com/USER/REPO/main/resourcepacks

Что делает:
  1. считает sha256 и размер всех jar из папки модов;
  2. с --lowres: собирает resourcepacks/MLauncher-LowRes.zip из текстур модов
     (tools/make_lowres_pack.py) и добавляет его в раздел "resourcepacks";
     лаунчер скачает пак вместе с модами и сам включит его в options.txt;
  3. пишет manifest.json в текущую папку.

Опции:
  --forge 47.4.28   версия Forge в манифесте
  --limit 1024      максимальная сторона текстуры в паке (меньше = легче атлас)
Запускайте заново после каждого изменения набора модов.
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_lowres_pack  # noqa: E402

PACK_NAME = "MLauncher-LowRes.zip"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def entry(path: Path, base_url: str) -> dict:
    return {
        "name": path.name,
        "sha256": sha256_of(path),
        "size": path.stat().st_size,
        "url": f"{base_url}/{quote(path.name)}",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mods_dir")
    ap.add_argument("mods_url")
    ap.add_argument("--lowres", nargs=2, metavar=("PACKS_DIR", "PACKS_URL"))
    ap.add_argument("--forge", default="47.4.28")
    ap.add_argument("--minecraft", default="1.20.1")
    ap.add_argument("--limit", type=int, default=1024)
    a = ap.parse_args()

    mods_dir = Path(a.mods_dir)
    mods = [entry(j, a.mods_url.rstrip("/")) for j in sorted(mods_dir.glob("*.jar"))]

    manifest = {
        "minecraft": a.minecraft,
        "forge": a.forge,
        "generated": int(time.time()),
        "mods": mods,
    }

    if a.lowres:
        packs_dir, packs_url = Path(a.lowres[0]), a.lowres[1].rstrip("/")
        pack = packs_dir / PACK_NAME
        before, after = make_lowres_pack.build(str(mods_dir), str(pack), a.limit, verbose=False)
        print(f"Ресурспак: текстуры {before / 1e6:.1f} МП -> {after / 1e6:.1f} МП (лимит Mali-G76: 67 МП)")
        manifest["resourcepacks"] = [entry(pack, packs_url)]

    Path("manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Готово: {len(mods)} модов"
          + (f" + ресурспак {PACK_NAME}" if a.lowres else "")
          + " записано в manifest.json")


if __name__ == "__main__":
    main()
