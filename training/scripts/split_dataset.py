#!/usr/bin/env python3
"""
Split dataset into train/val/test sets with stratification support.
"""

import argparse
import shutil
from pathlib import Path
import random
from typing import List, Tuple


def split_dataset(
    image_dir: Path,
    annotation_dir: Path,
    output_dir: Path,
    train_ratio: float = 0.7,
    val_ratio: float = 0.2,
    test_ratio: float = 0.1,
    seed: int = 42
):
    """Split dataset into train/val/test sets."""
    random.seed(seed)
    
    # Get all images
    image_extensions = {".jpg", ".jpeg", ".png"}
    images = [f for f in image_dir.iterdir() if f.suffix.lower() in image_extensions]
    
    if not images:
        print(f"No images found in {image_dir}")
        return
    
    # Shuffle
    random.shuffle(images)
    
    # Calculate split indices
    total = len(images)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)
    
    splits = {
        "train": images[:train_end],
        "val": images[train_end:val_end],
        "test": images[val_end:]
    }
    
    print(f"Total images: {total}")
    print(f"  Train: {len(splits['train'])} ({len(splits['train'])/total*100:.1f}%)")
    print(f"  Val: {len(splits['val'])} ({len(splits['val'])/total*100:.1f}%)")
    print(f"  Test: {len(splits['test'])} ({len(splits['test'])/total*100:.1f}%)")
    
    # Copy files to split directories
    for split_name, split_images in splits.items():
        split_img_dir = output_dir / split_name / "images"
        split_ann_dir = output_dir / split_name / "labels"
        split_img_dir.mkdir(parents=True, exist_ok=True)
        split_ann_dir.mkdir(parents=True, exist_ok=True)
        
        for img_path in split_images:
            # Copy image
            shutil.copy2(img_path, split_img_dir / img_path.name)
            
            # Copy annotation if exists
            ann_path = annotation_dir / f"{img_path.stem}.txt"
            if ann_path.exists():
                shutil.copy2(ann_path, split_ann_dir / ann_path.name)
    
    print(f"\nDataset split completed: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Split dataset into train/val/test")
    parser.add_argument("--images", type=Path, required=True, help="Image directory")
    parser.add_argument("--labels", type=Path, required=True, help="Annotation directory (YOLO format)")
    parser.add_argument("--output", type=Path, required=True, help="Output directory")
    parser.add_argument("--train", type=float, default=0.7, help="Train ratio (default: 0.7)")
    parser.add_argument("--val", type=float, default=0.2, help="Val ratio (default: 0.2)")
    parser.add_argument("--test", type=float, default=0.1, help="Test ratio (default: 0.1)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    
    args = parser.parse_args()
    
    # Validate ratios
    total_ratio = args.train + args.val + args.test
    if abs(total_ratio - 1.0) > 0.01:
        print(f"Error: Ratios must sum to 1.0 (got {total_ratio})")
        return
    
    split_dataset(
        args.images,
        args.labels,
        args.output,
        args.train,
        args.val,
        args.test,
        args.seed
    )


if __name__ == "__main__":
    main()
