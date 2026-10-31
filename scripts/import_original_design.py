#!/usr/bin/env python3
"""Validate and import ORIGINAL Myanmar Tipitaka 20 screen images and logo. No fabricated fallbacks."""
from __future__ import annotations
import io, json, re, sys, zipfile
from pathlib import Path
from PIL import Image

root=Path(__file__).resolve().parents[1]
source=root/"design-source"
screens=root/"app/src/main/assets/screens"
logo_out=root/"app/src/main/res/drawable-nodpi/tipitaka_original_logo.png"
formats={".png",".jpg",".jpeg",".webp"}
def number(name):
    stem=Path(name).stem
    pattern=r"(?i)(?:screen|page|mockup|ui)[ _.-]*(0?[1-9]|1[0-9]|20)(?![0-9])"
    m=re.search(pattern,stem)
    if not m: m=re.search(r"(?<![0-9])(0?[1-9]|1[0-9]|20)(?![0-9])",stem)
    return int(m.group(1)) if m else None

data=[]
if source.exists():
    for file in source.rglob("*"):
        if not file.is_file():continue
        if file.suffix.lower() in formats:
            data.append((file.name,file.read_bytes()))
        elif file.suffix.lower()==".zip":
            with zipfile.ZipFile(file) as archive:
                for item in archive.infolist():
                    if item.is_dir() or Path(item.filename).suffix.lower() not in formats:continue
                    if item.file_size>40000000:raise ValueError("Oversized image "+item.filename)
                    data.append((item.filename,archive.read(item)))
pages={}
logos=[]
for name,contents in data:
    leaf=Path(name).name
    if re.search(r"(?i)logo|app[_ -]?icon|ic[_ -]?launcher",leaf):
        logos.append((name,contents));continue
    n=number(leaf)
    if n is not None:
        if n in pages:raise ValueError(f"Duplicate screen {n:02d}: {name} and {pages[n][0]}")
        pages[n]=(name,contents)
missing=[n for n in range(1,21) if n not in pages]
if missing or len(logos)!=1:
    print("Exact UI build BLOCKED. Missing screen numbers:",missing,file=sys.stderr)
    print("Original logo candidates:",len(logos),". Exactly one required.",file=sys.stderr)
    print("Upload design-source/Myanmar_Tipitaka_UIUX_20_Screens_Assets.zip with SCREEN_01..SCREEN_20 plus logo.png",file=sys.stderr)
    sys.exit(2)
screens.mkdir(parents=True,exist_ok=True)
logo_out.parent.mkdir(parents=True,exist_ok=True)
manifest=[]
for n in range(1,21):
    name,contents=pages[n]
    with Image.open(io.BytesIO(contents)) as img:
        img.load()
        w,h=img.size
        if w<500 or h<850 or w>=h:raise ValueError("Invalid portrait artwork for screen "+str(n)+": "+str((w,h)))
        target=screens/f"screen_{n:02d}.png"
        if Path(name).suffix.lower()==".png":
            target.write_bytes(contents)
        else: img.save(target,"PNG")
        manifest.append({"number":n,"source":name,"size":[w,h]})
with Image.open(io.BytesIO(logos[0][1])) as img:
    img.load()
    img.convert("RGBA").save(logo_out,"PNG")
(root/"exact_assets_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
print("Exact UI verified: 20 original screens and one original logo imported.")
