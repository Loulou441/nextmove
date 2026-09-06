#!/usr/bin/env python3
"""
Convert annotation formats between COCO JSON, YOLO txt, and Pascal VOC XML.
"""

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple


def coco_to_yolo(coco_path: Path, output_dir: Path, image_dir: Path):
    """Convert COCO JSON to YOLO format (one txt file per image)."""
    with open(coco_path) as f:
        coco = json.load(f)
    
    # Build category id to index mapping
    cat_id_to_idx = {cat["id"]: idx for idx, cat in enumerate(coco["categories"])}
    
    # Group annotations by image
    img_annotations = {}
    for ann in coco["annotations"]:
        img_id = ann["image_id"]
        if img_id not in img_annotations:
            img_annotations[img_id] = []
        img_annotations[img_id].append(ann)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for img in coco["images"]:
        img_id = img["id"]
        img_w, img_h = img["width"], img["height"]
        
        # Create YOLO txt file
        txt_path = output_dir / f"{Path(img['file_name']).stem}.txt"
        
        if img_id not in img_annotations:
            # Create empty file for images without annotations
            txt_path.touch()
            continue
        
        with open(txt_path, "w") as f:
            for ann in img_annotations[img_id]:
                # COCO bbox: [x, y, width, height] (top-left corner)
                x, y, w, h = ann["bbox"]
                
                # Convert to YOLO format: [class_idx, x_center, y_center, width, height] (normalized)
                x_center = (x + w / 2) / img_w
                y_center = (y + h / 2) / img_h
                norm_w = w / img_w
                norm_h = h / img_h
                
                class_idx = cat_id_to_idx[ann["category_id"]]
                f.write(f"{class_idx} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}\n")
    
    print(f"Converted {len(coco['images'])} images to YOLO format in {output_dir}")


def yolo_to_coco(yolo_dir: Path, image_dir: Path, output_path: Path, class_names: List[str]):
    """Convert YOLO format to COCO JSON."""
    images = []
    annotations = []
    ann_id = 1
    
    for img_id, img_path in enumerate(sorted(image_dir.glob("*.jpg")) + sorted(image_dir.glob("*.png")), 1):
        # Read image dimensions
        import cv2
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        
        h, w = img.shape[:2]
        
        images.append({
            "id": img_id,
            "file_name": img_path.name,
            "width": w,
            "height": h
        })
        
        # Read YOLO annotations
        txt_path = yolo_dir / f"{img_path.stem}.txt"
        if not txt_path.exists():
            continue
        
        with open(txt_path) as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                
                class_idx, x_center, y_center, norm_w, norm_h = map(float, parts)
                
                # Convert to COCO format
                bbox_w = norm_w * w
                bbox_h = norm_h * h
                bbox_x = (x_center * w) - (bbox_w / 2)
                bbox_y = (y_center * h) - (bbox_h / 2)
                
                annotations.append({
                    "id": ann_id,
                    "image_id": img_id,
                    "category_id": int(class_idx) + 1,  # COCO uses 1-indexed categories
                    "bbox": [bbox_x, bbox_y, bbox_w, bbox_h],
                    "area": bbox_w * bbox_h,
                    "iscrowd": 0
                })
                ann_id += 1
    
    categories = [{"id": i + 1, "name": name} for i, name in enumerate(class_names)]
    
    coco = {
        "images": images,
        "annotations": annotations,
        "categories": categories
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(coco, f, indent=2)
    
    print(f"Converted {len(images)} images to COCO format: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Convert annotation formats")
    parser.add_argument("--format", choices=["coco2yolo", "yolo2coco"], required=True)
    parser.add_argument("--input", type=Path, required=True, help="Input file or directory")
    parser.add_argument("--output", type=Path, required=True, help="Output file or directory")
    parser.add_argument("--images", type=Path, help="Image directory (required for conversions)")
    parser.add_argument("--classes", type=str, help="Comma-separated class names (for yolo2coco)")
    
    args = parser.parse_args()
    
    if args.format == "coco2yolo":
        if not args.images:
            parser.error("--images required for coco2yolo")
        coco_to_yolo(args.input, args.output, args.images)
    elif args.format == "yolo2coco":
        if not args.images or not args.classes:
            parser.error("--images and --classes required for yolo2coco")
        class_names = [c.strip() for c in args.classes.split(",")]
        yolo_to_coco(args.input, args.images, args.output, class_names)


if __name__ == "__main__":
    main()
