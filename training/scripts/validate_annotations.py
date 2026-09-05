#!/usr/bin/env python3
"""
Validate annotation files for quality and correctness.
Checks for invalid bounding boxes, missing annotations, and class label issues.
"""

import argparse
from pathlib import Path
from typing import List, Tuple
import json


def validate_yolo_annotations(
    image_dir: Path,
    label_dir: Path,
    num_classes: int
) -> Tuple[List[str], List[str], List[str]]:
    """Validate YOLO format annotations."""
    
    errors = []
    warnings = []
    stats = {
        'total_images': 0,
        'images_with_annotations': 0,
        'images_without_annotations': 0,
        'total_annotations': 0,
        'invalid_boxes': 0,
        'invalid_classes': 0
    }
    
    image_files = list(image_dir.glob('*.jpg')) + list(image_dir.glob('*.png'))
    stats['total_images'] = len(image_files)
    
    for img_path in image_files:
        label_path = label_dir / f"{img_path.stem}.txt"
        
        if not label_path.exists():
            stats['images_without_annotations'] += 1
            warnings.append(f"No annotation for image: {img_path.name}")
            continue
        
        stats['images_with_annotations'] += 1
        
        # Read and validate annotations
        with open(label_path) as f:
            lines = f.readlines()
            
            if not lines:
                warnings.append(f"Empty annotation file: {label_path.name}")
                continue
            
            for line_num, line in enumerate(lines, 1):
                parts = line.strip().split()
                
                if len(parts) != 5:
                    errors.append(
                        f"{label_path.name}:{line_num} - "
                        f"Invalid format (expected 5 values, got {len(parts)})"
                    )
                    continue
                
                try:
                    class_idx, x_center, y_center, width, height = map(float, parts)
                    stats['total_annotations'] += 1
                    
                    # Validate class index
                    if class_idx < 0 or class_idx >= num_classes:
                        errors.append(
                            f"{label_path.name}:{line_num} - "
                            f"Invalid class index {int(class_idx)} (must be 0-{num_classes-1})"
                        )
                        stats['invalid_classes'] += 1
                    
                    # Validate bounding box coordinates
                    if not (0 <= x_center <= 1 and 0 <= y_center <= 1):
                        errors.append(
                            f"{label_path.name}:{line_num} - "
                            f"Invalid center coordinates ({x_center:.3f}, {y_center:.3f})"
                        )
                        stats['invalid_boxes'] += 1
                    
                    if not (0 < width <= 1 and 0 < height <= 1):
                        errors.append(
                            f"{label_path.name}:{line_num} - "
                            f"Invalid dimensions ({width:.3f}, {height:.3f})"
                        )
                        stats['invalid_boxes'] += 1
                    
                    # Check for zero-area boxes
                    if width == 0 or height == 0:
                        errors.append(
                            f"{label_path.name}:{line_num} - "
                            f"Zero-area bounding box"
                        )
                        stats['invalid_boxes'] += 1
                
                except ValueError as e:
                    errors.append(
                        f"{label_path.name}:{line_num} - "
                        f"Cannot parse values: {e}"
                    )
    
    return errors, warnings, stats


def print_report(errors: List[str], warnings: List[str], stats: dict):
    """Print validation report."""
    print("\n" + "="*60)
    print("ANNOTATION VALIDATION REPORT")
    print("="*60)
    
    print(f"\nDataset Statistics:")
    print(f"  Total images: {stats['total_images']}")
    print(f"  Images with annotations: {stats['images_with_annotations']}")
    print(f"  Images without annotations: {stats['images_without_annotations']}")
    print(f"  Total annotations: {stats['total_annotations']}")
    
    if stats['total_images'] > 0:
        coverage = stats['images_with_annotations'] / stats['total_images'] * 100
        print(f"  Annotation coverage: {coverage:.1f}%")
    
    print(f"\nIssues Found:")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Invalid boxes: {stats['invalid_boxes']}")
    print(f"  Invalid classes: {stats['invalid_classes']}")
    
    if errors:
        print(f"\nErrors (showing first 10):")
        for error in errors[:10]:
            print(f"  ✗ {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    
    if warnings:
        print(f"\nWarnings (showing first 10):")
        for warning in warnings[:10]:
            print(f"  ⚠ {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")
    
    if not errors and not warnings:
        print("\n✓ All annotations are valid!")
    
    print("="*60)


def main():
    parser = argparse.ArgumentParser(description="Validate annotation files")
    parser.add_argument("--images", type=Path, required=True, help="Image directory")
    parser.add_argument("--labels", type=Path, required=True, help="Label directory (YOLO format)")
    parser.add_argument("--classes", type=int, required=True, help="Number of classes")
    parser.add_argument("--output", type=Path, help="Save report to JSON file")
    
    args = parser.parse_args()
    
    if not args.images.exists():
        print(f"Error: Image directory not found: {args.images}")
        return
    
    if not args.labels.exists():
        print(f"Error: Label directory not found: {args.labels}")
        return
    
    print(f"Validating annotations...")
    print(f"  Images: {args.images}")
    print(f"  Labels: {args.labels}")
    print(f"  Classes: {args.classes}")
    
    errors, warnings, stats = validate_yolo_annotations(
        args.images,
        args.labels,
        args.classes
    )
    
    print_report(errors, warnings, stats)
    
    if args.output:
        report = {
            "stats": stats,
            "errors": errors,
            "warnings": warnings
        }
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to: {args.output}")


if __name__ == "__main__":
    main()
