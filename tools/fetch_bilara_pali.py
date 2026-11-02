#!/usr/bin/env python3
"""Retrieve a reproducible, non-approved Pāli source snapshot from Bilara.

Does not claim MCU 45-volume completeness. Requires git and network access.
"""
import argparse
import json
import subprocess
from pathlib import Path

URL = "https://github.com/suttacentral/bilara-data.git"

def run(cmd, cwd=None):
    return subprocess.check_output(cmd,cwd=cwd,text=True).strip()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dest",default="build/bilara-data")
    ap.add_argument("--ref",default="published",help="Git commit SHA preferred for reproducibility")
    args=ap.parse_args()
    dest=Path(args.dest).resolve()
    if dest.exists():
        ap.error("Destination already exists; refusing to alter source snapshot")
    dest.parent.mkdir(parents=True,exist_ok=True)
    run(["git","clone","--filter=blob:none","--no-checkout","--sparse",URL,str(dest)])
    run(["git","sparse-checkout","set","root/pli/ms"],cwd=dest)
    run(["git","checkout",args.ref],cwd=dest)
    sha=run(["git","rev-parse","HEAD"],cwd=dest)
    root=dest/"root"/"pli"/"ms"
    files=list(root.rglob("*.json"))
    if not files:
        raise RuntimeError("Bilara Pāli root JSON not found")
    manifest={"source":URL,"requested_ref":args.ref,"source_commit":sha,
              "root_path":"root/pli/ms","json_files":len(files),
              "mcu_volumes_verified":0,"review_status":"UNREVIEWED",
              "note":"Source files retrieved, not imported into Android or verified against MCU edition."}
    (dest/"pali-source-manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(manifest,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
