#!/usr/bin/env python3
"""
Normalize a Roboflow YOLO export that mixes segmentation polygons and detection
boxes into pure detection labels.

The Plaimaker padel-tkrqs export stores most annotations as polygons:
    <class> x1 y1 x2 y2 ... xn yn        (normalized, variable length)
and some as detection boxes:
    <class> xc yc w h                    (normalized, 5 fields)

YOLO's *detection* trainer refuses any label file that mixes these, so it
silently drops nearly every image. This script rewrites each label file so
every row is a detection box (polygon -> tight bounding box via min/max of its
points), producing a clean detection dataset in place.

Usage:
    python scripts/seg_to_bbox.py --dataset data/padel_dataset
    # add --dry-run to preview counts without writing
"""

import argparse
from pathlib import Path


def poly_to_bbox(coords):
    """coords = [x1,y1,x2,y2,...] normalized -> (xc, yc, w, h) normalized."""
    xs = coords[0::2]
    ys = coords[1::2]
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    xc = (x_min + x_max) / 2
    yc = (y_min + y_max) / 2
    w = x_max - x_min
    h = y_max - y_min
    return xc, yc, w, h


def clamp01(v):
    return min(max(v, 0.0), 1.0)


def convert_file(path: Path):
    """Rewrite one label file to pure detection rows. Returns (rows, converted_polys)."""
    out_lines = []
    converted = 0
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        cls = parts[0]
        nums = [float(x) for x in parts[1:]]

        if len(nums) == 4:
            xc, yc, w, h = nums  # already a detection box
        elif len(nums) >= 6 and len(nums) % 2 == 0:
            xc, yc, w, h = poly_to_bbox(nums)  # polygon -> box
            converted += 1
        else:
            # malformed / unexpected row — skip it
            continue

        xc, yc, w, h = clamp01(xc), clamp01(yc), clamp01(w), clamp01(h)
        if w <= 0 or h <= 0:
            continue
        out_lines.append(f"{cls} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}")

    return out_lines, converted


def main():
    parser = argparse.ArgumentParser(description="Convert mixed seg/detection YOLO labels to pure detection boxes")
    parser.add_argument("--dataset", type=Path, required=True, help="Dataset root (contains train/valid/test)")
    parser.add_argument("--dry-run", action="store_true", help="Report only, don't write")
    args = parser.parse_args()

    total_files = 0
    total_rows = 0
    total_converted = 0

    for split in ("train", "valid", "test"):
        label_dir = args.dataset / split / "labels"
        if not label_dir.is_dir():
            continue
        files = sorted(label_dir.glob("*.txt"))
        for f in files:
            lines, converted = convert_file(f)
            total_files += 1
            total_rows += len(lines)
            total_converted += converted
            if not args.dry_run:
                f.write_text("\n".join(lines) + ("\n" if lines else ""))
        print(f"  {split}: {len(files)} label files processed")

    action = "would write" if args.dry_run else "wrote"
    print(f"\n{action} {total_rows} detection rows across {total_files} files "
          f"({total_converted} polygons converted to boxes)")


if __name__ == "__main__":
    main()
