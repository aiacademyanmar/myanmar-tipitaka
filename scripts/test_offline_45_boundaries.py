#!/usr/bin/env python3
"""Regression checks for boundaries claimed in the 45-book source-aligned catalogue.
These checks DO NOT establish identical wording to the MCU canonical edition.
"""
import importlib.util
from pathlib import Path

path=Path(__file__).with_name("build_offline_45_volumes.py")
spec=importlib.util.spec_from_file_location("tipitaka_mapping",path)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

checks={
 "vinaya/pli-tv-kd/pli-tv-kd4_root-pli-ms.json":4,
 "vinaya/pli-tv-kd/pli-tv-kd5_root-pli-ms.json":5,
 "vinaya/pli-tv-kd/pli-tv-kd10_root-pli-ms.json":5,
 "vinaya/pli-tv-kd/pli-tv-kd11_root-pli-ms.json":6,
 "vinaya/pli-tv-kd/pli-tv-kd14_root-pli-ms.json":6,
 "vinaya/pli-tv-kd/pli-tv-kd15_root-pli-ms.json":7,
 "sutta/dn/dn13_root-pli-ms.json":9,
 "sutta/dn/dn14_root-pli-ms.json":10,
 "sutta/dn/dn23_root-pli-ms.json":10,
 "sutta/dn/dn24_root-pli-ms.json":11,
 "sutta/mn/mn50_root-pli-ms.json":12,
 "sutta/mn/mn51_root-pli-ms.json":13,
 "sutta/mn/mn100_root-pli-ms.json":13,
 "sutta/mn/mn101_root-pli-ms.json":14,
 "sutta/sn/sn11/sn11.1_root-pli-ms.json":15,
 "sutta/sn/sn12/sn12.1_root-pli-ms.json":16,
 "sutta/sn/sn21/sn21.1_root-pli-ms.json":16,
 "sutta/sn/sn22/sn22.1_root-pli-ms.json":17,
 "sutta/sn/sn34/sn34.1_root-pli-ms.json":17,
 "sutta/sn/sn35/sn35.1_root-pli-ms.json":18,
 "sutta/sn/sn44/sn44.1_root-pli-ms.json":18,
 "sutta/sn/sn45/sn45.1_root-pli-ms.json":19,
 "sutta/kn/ja/ja525_root-pli-ms.json":27,
 "sutta/kn/ja/ja526_root-pli-ms.json":28,
 "sutta/kn/tha-ap/tha-ap412_root-pli-ms.json":32,
 "sutta/kn/tha-ap/tha-ap413_root-pli-ms.json":33,
 "abhidhamma/ya/ya7/ya7.1_root-pli-ms.json":38,
 "abhidhamma/ya/ya8/ya8.1_root-pli-ms.json":39,
}
for file,expected in checks.items():
 actual=m.pick_volume(file)
 assert actual==expected, f"{file}: actual={actual}, expected={expected}"
print(f"Checked {len(checks)} structural boundary examples.")
print("Not proof of exact MCU Pali wording or all 45 printed edition volume splits.")
