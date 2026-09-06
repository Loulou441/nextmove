#!/usr/bin/env python3
"""
Validate trained YOLO model on test set.
Computes metrics and generates validation report.
"""

import argparse
from pathlib import Path
import yaml
from ultralytics import YOLO
import json


def validate_model(model_path: Path, config_path: Path, save_json: bool = True):
    """Validate model and compute metrics."""
    
    if not model_path.exists():
        print(f"Error: Model not found: {model_path}")
        return None
    
    if not config_path.exists():
        print(f"Error: Config not found: {config_path}")
        return None
    
    # Load config
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    print(f"Validating model: {model_path.name}")
    print(f"  Config: {config_path.name}")
    print(f"  Classes: {config['nc']}")
    
    # Load model
    model = YOLO(str(model_path))
    
    # Run validation
    print("\nRunning validation...")
    results = model.val(
        data=str(config_path),
        batch=config.get('batch', 16),
        imgsz=config.get('imgsz', 640),
        conf=config.get('conf', 0.3),
        iou=config.get('iou', 0.5),
        max_det=config.get('max_det', 100),
        device=config.get('device', 0),
        save_json=save_json,
        verbose=True
    )
    
    # Print metrics
    print("\n" + "="*60)
    print("VALIDATION RESULTS")
    print("="*60)
    
    metrics = results.results_dict
    print(f"\nOverall Metrics:")
    print(f"  mAP@0.5:      {metrics.get('metrics/mAP50(B)', 0):.4f}")
    print(f"  mAP@0.5:0.95: {metrics.get('metrics/mAP50-95(B)', 0):.4f}")
    print(f"  Precision:    {metrics.get('metrics/precision(B)', 0):.4f}")
    print(f"  Recall:       {metrics.get('metrics/recall(B)', 0):.4f}")
    
    # Per-class metrics
    if hasattr(results, 'box'):
        box_metrics = results.box
        if hasattr(box_metrics, 'ap_class_index') and hasattr(box_metrics, 'ap50'):
            print(f"\nPer-Class Metrics (mAP@0.5):")
            class_names = config['names']
            for idx, ap in zip(box_metrics.ap_class_index, box_metrics.ap50):
                class_name = class_names.get(int(idx), f"class_{idx}")
                print(f"  {class_name:15s}: {ap:.4f}")
    
    # Speed metrics
    if hasattr(results, 'speed'):
        speed = results.speed
        print(f"\nSpeed Metrics:")
        print(f"  Preprocess:  {speed.get('preprocess', 0):.1f} ms")
        print(f"  Inference:   {speed.get('inference', 0):.1f} ms")
        print(f"  Postprocess: {speed.get('postprocess', 0):.1f} ms")
        total_time = sum(speed.values())
        print(f"  Total:       {total_time:.1f} ms")
        
        # Check if meets performance target
        if speed.get('inference', 0) < 200:
            print(f"  ✓ Meets < 200ms inference target")
        else:
            print(f"  ✗ Exceeds 200ms inference target")
    
    print("="*60)
    
    # Save results to JSON
    if save_json:
        output_path = model_path.parent / f"{model_path.stem}_validation.json"
        validation_results = {
            "model": str(model_path),
            "config": str(config_path),
            "metrics": {
                "mAP50": float(metrics.get('metrics/mAP50(B)', 0)),
                "mAP50_95": float(metrics.get('metrics/mAP50-95(B)', 0)),
                "precision": float(metrics.get('metrics/precision(B)', 0)),
                "recall": float(metrics.get('metrics/recall(B)', 0))
            }
        }
        
        if hasattr(results, 'speed'):
            validation_results["speed"] = {
                "preprocess_ms": float(speed.get('preprocess', 0)),
                "inference_ms": float(speed.get('inference', 0)),
                "postprocess_ms": float(speed.get('postprocess', 0)),
                "total_ms": float(sum(speed.values()))
            }
        
        with open(output_path, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        print(f"\nValidation results saved to: {output_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Validate YOLO model")
    parser.add_argument(
        "--model",
        type=Path,
        required=True,
        help="Path to trained model (e.g., runs/train/exp/weights/best.pt)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to YAML config file"
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Don't save results to JSON"
    )
    
    args = parser.parse_args()
    
    validate_model(args.model, args.config, not args.no_json)


if __name__ == "__main__":
    main()
