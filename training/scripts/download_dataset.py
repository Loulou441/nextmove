#!/usr/bin/env python3
"""
Download a public sports-detection dataset from Roboflow Universe in YOLO format.

We fine-tune a COCO-pretrained YOLO backbone on a domain-specific (pickleball /
tennis / padel) detection dataset. This is standard transfer learning.

Usage:
    # 1. Get a free Roboflow API key: https://app.roboflow.com/settings/api
    # 2. Put it in training/.env as ROBOFLOW_API_KEY=xxxx  (or pass --api-key)
    # 3. Run:
    python scripts/download_dataset.py --sport padel

The dataset is downloaded to data/<sport>_dataset/ in YOLOv8 format (with a
data.yaml you can point train_yolo.py at).

NOTE: Always check and record each dataset's license. The chosen datasets are
published on Roboflow Universe under open / public-domain licenses — attribute
them accordingly.
"""

import argparse
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass

from roboflow import Roboflow


# Public Roboflow Universe datasets (workspace / project / version).
DATASETS = {
    "pickleball": {
        "workspace": "racket-ai",
        "project": "pickleball-iiv9m",
        "version": 5,
        "note": "Pickleball ball/paddle/player detection (Roboflow Universe). Has two empty placeholder classes to drop.",
    },
    "tennis": {
        "workspace": "yolov8-xo2x7",
        "project": "tennisballtracker-mp7wb",
        "version": 1,
        "note": "Tennis ball tracking dataset (~2486 images, Roboflow Universe).",
    },
    # Dedicated padel detection dataset (Plaimaker). Public Domain license.
    # The sibling project padel-mhxdf is a *keypoint/pose* model and does NOT
    # fit our bounding-box detector, so we use the detection project here.
    "padel": {
        "workspace": "plaimaker",
        "project": "padel-tkrqs",
        "version": None,  # None -> resolve latest version at download time
        "note": "Padel detection dataset by Plaimaker (Roboflow Universe, Public Domain).",
    },
}


def download(sport: str, api_key: str, out_root: Path) -> Path:
    if sport not in DATASETS:
        raise ValueError(f"Unknown sport '{sport}'. Options: {list(DATASETS)}")

    cfg = DATASETS[sport]
    print(f"Downloading '{sport}' dataset: {cfg['note']}")

    rf = Roboflow(api_key=api_key)
    project = rf.workspace(cfg["workspace"]).project(cfg["project"])

    # Resolve the version: use the pinned one, or fall back to the latest.
    version_num = cfg.get("version")
    if version_num is None:
        versions = project.versions()
        if not versions:
            raise RuntimeError(f"No versions found for {cfg['workspace']}/{cfg['project']}")
        # versions() returns newest-first; take the first one's id
        version_num = int(str(versions[0].version).split("/")[-1])
        print(f"  Resolved latest version: v{version_num}")

    print(f"  Source: {cfg['workspace']}/{cfg['project']} v{version_num}")
    version = project.version(version_num)

    dest = out_root / f"{sport}_dataset"
    dest.parent.mkdir(parents=True, exist_ok=True)

    # yolov8 export gives train/valid/test folders + data.yaml
    dataset = version.download("yolov8", location=str(dest))
    print(f"\n✅ Downloaded to: {dataset.location}")

    # Surface the real class names so we know what the app must map.
    data_yaml = Path(dataset.location) / "data.yaml"
    if data_yaml.exists():
        print(f"\n   data.yaml classes (check these map to ball/player in the app):")
        for line in data_yaml.read_text().splitlines():
            if line.strip().startswith(("names", "nc", "-")) or "names" in line:
                print(f"     {line}")
    print(f"\n   Point training at: {data_yaml}")
    return Path(dataset.location)


def main():
    parser = argparse.ArgumentParser(description="Download a public sports dataset from Roboflow")
    parser.add_argument("--sport", choices=list(DATASETS), default="pickleball")
    parser.add_argument("--api-key", default=os.getenv("ROBOFLOW_API_KEY"))
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data")
    args = parser.parse_args()

    if not args.api_key:
        print("Error: no Roboflow API key.")
        print("  Get one free at https://app.roboflow.com/settings/api")
        print("  Then set ROBOFLOW_API_KEY in training/.env or pass --api-key.")
        return

    download(args.sport, args.api_key, args.out)


if __name__ == "__main__":
    main()
