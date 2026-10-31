#!/usr/bin/env python3
"""Fetch the user's 20 exact Drive UI screenshots; fail closed if missing."""
from pathlib import Path
from PIL import Image
import hashlib, io, json, sys
import gdown

IDS = ["1NEIE6MsOetzIsJ5FpRTOExks-612viKG","1nprRe8uJTQrIUkf2_4xy7n0KtKHEqXPU","1JlFSA2cmM79fU5yGIfN6A4NpEk1sOqRV","1o0C-ZKO098pyjU3JxdzTYh2Pw5RuqHhm","1F1Vz_3YSBpi6jBK2yHefYuHfYTeZ1OI1","1hRB9VDZKtrMRMi6VWPWCobwTLUb8p4_v","10THAgfRqayDU8AjHjgqsFywJJvQfvD9E","1wUzsnM5_q7ZjIHc03-YWZUlAX1nOY7Rs","1UC3rJaobvGcYpZjgRUFJDwugXeiq9k3Z","1p5cuEc-Y0C2NWk2n9g_kjUxJUuk7HxCS","1RMUY3yrFKS71-1U9vIcdsn0N0btp2DQG","1Z2fA0gesF9lrEhCmPaMTiw9nF4YXfwIJ","1Ha1qlbeREAkgdiNQOV6WyX21hB9lrALA","1OY8I5q27Mhj1WiGpDiudo3rXmNem0UA-","1lc4aMe1GNCW5gvOs2OGOzKVM9oGV1oJT","1nVURuNIzPaN81lDOVcIlOlqMttXh8EGs","122KN5-y7Wu_SmV2LrnbOaURZ7UfA7vf5","1UHLcUouSsvLkLblIIknSBNTosQGlFQMc","1_fBiEZhOsdU9jYqlhu4uhz2kOdwUbeeW","1DRpb0XuKIyeAi5uJWJHkAfo47SxpBpG-"]
root = Path(__file__).resolve().parents[1]
out = root / "app/src/main/assets/screens"
out.mkdir(parents=True, exist_ok=True)
manifest = []
for n, fid in enumerate(IDS, 1):
    target = out / f"screen_{n:02d}.png"
    print(f"Fetching original Page {n:02d} from Drive {fid}", flush=True)
    result = gdown.download(id=fid, output=str(target), quiet=False, fuzzy=True)
    if result is None or not target.exists():
        sys.exit(f"FAILED to fetch Page {n:02d}. Confirm 'Anyone with the link: Viewer' in Google Drive.")
    try:
        with Image.open(target) as im:
            im.verify()
        with Image.open(target) as im:
            w, h = im.size
            if im.format != "PNG" or w < 450 or h < 700 or w >= h:
                raise ValueError(f"unexpected artwork dimensions/format: {w}x{h} {im.format}")
    except Exception as ex:
        sys.exit(f"INVALID page {n:02d}: {ex}")
    manifest.append({"number":n, "drive_id":fid, "size":[w,h], "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
(root / "exact_assets_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print("All 20 exact Drive screenshots imported successfully.", flush=True)
