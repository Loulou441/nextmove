#!/usr/bin/env python3
"""
Bundle the padel training artifacts into a single zip for download.

Collects the three things you need after a training run:
  1. best.pt                      — PyTorch weights
  2. PadelDetector_v1.mlpackage   — Core ML model for iOS (renamed from best.mlpackage)
  3. training_run/                — full run dir (curves, confusion matrix, results.csv)

Usage:
    # after training + Core ML export
    python scripts/package_padel_artifacts.py
    # -> creates padel_artifacts.zip

    # custom run dir / output
    python scripts/package_padel_artifacts.py \
        --run runs/train/padel_detector \
        --out padel_artifacts.zip
"""

import argparse
import shutil
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Package padel training artifacts into one zip")
    parser.add_argument("--run", type=Path, default=Path("runs/train/padel_detector"),
                        help="Ultralytics run directory")
    parser.add_argument("--out", type=Path, default=Path("padel_artifacts.zip"),
                        help="Output zip path")
    args = parser.parse_args()

    run_dir = args.run
    if not run_dir.exists():
        raise SystemExit(f"Run directory not found: {run_dir}\n"
                         "Train first (train_yolo.py --config configs/padel_yolo.yaml).")

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "padel_artifacts"
        staging.mkdir()

        # 1) PyTorch weights
        best_pt = run_dir / "weights" / "best.pt"
        if best_pt.exists():
            shutil.copy2(best_pt, staging / "best.pt")
            print("added best.pt")
        else:
            print("WARNING: best.pt not found — did training finish?")

        # 2) Core ML model (Ultralytics exports as best.mlpackage next to best.pt)
        mlpkg = run_dir / "weights" / "best.mlpackage"
        if mlpkg.exists():
            shutil.copytree(mlpkg, staging / "PadelDetector_v1.mlpackage")
            print("added PadelDetector_v1.mlpackage")
        else:
            print("WARNING: best.mlpackage not found — run the Core ML export first:")
            print("         python -c \"from ultralytics import YOLO; "
                  "YOLO('%s').export(format='coreml', nms=True, imgsz=640)\"" % best_pt)

        # 3) Full training run (exclude the .mlpackage to avoid duplication)
        shutil.copytree(run_dir, staging / "training_run",
                        ignore=shutil.ignore_patterns("*.mlpackage"))
        print("added training_run/")

        # Zip it (make_archive appends .zip)
        base = args.out.with_suffix("")
        archive = shutil.make_archive(str(base), "zip", staging)

    size_mb = Path(archive).stat().st_size / 1e6
    print(f"\n✅ Created {archive} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
