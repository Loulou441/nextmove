#!/usr/bin/env python3
"""
Train YOLO model for racket-sport object detection.
Supports pickleball, tennis, and padel via configurable parameters.
"""

import argparse
from pathlib import Path
import yaml
from ultralytics import YOLO
import torch


def train_model(
    config_path: Path,
    pretrained_weights: str = "yolov8n.pt",
    resume: bool = False,
    device: str = None
):
    """Train YOLO model with specified configuration."""
    
    # Load config
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    print(f"Training configuration: {config_path.name}")
    print(f"  Model: {config.get('model', 'yolov8n')}")
    print(f"  Classes: {config['nc']}")
    print(f"  Epochs: {config.get('epochs', 100)}")
    print(f"  Batch size: {config.get('batch', 16)}")
    print(f"  Image size: {config.get('imgsz', 640)}")
    
    # Check device
    if device is None:
        device = config.get('device', 0)
    
    if device != 'cpu':
        if not torch.cuda.is_available():
            print("Warning: CUDA not available, falling back to CPU")
            device = 'cpu'
        else:
            print(f"  Device: GPU {device}")
    else:
        print("  Device: CPU")
    
    # Initialize model
    if resume:
        # Resume from last checkpoint
        checkpoint_dir = Path(config.get('project', 'runs/train')) / config.get('name', 'exp')
        last_checkpoint = checkpoint_dir / 'weights' / 'last.pt'
        
        if last_checkpoint.exists():
            print(f"Resuming from checkpoint: {last_checkpoint}")
            model = YOLO(str(last_checkpoint))
        else:
            print(f"Warning: Checkpoint not found at {last_checkpoint}, starting fresh")
            model = YOLO(pretrained_weights)
    else:
        print(f"Loading pretrained weights: {pretrained_weights}")
        model = YOLO(pretrained_weights)
    
    # Train
    print("\nStarting training...")
    results = model.train(
        data=str(config_path),
        epochs=config.get('epochs', 100),
        batch=config.get('batch', 16),
        imgsz=config.get('imgsz', 640),
        patience=config.get('patience', 20),
        optimizer=config.get('optimizer', 'AdamW'),
        lr0=config.get('lr0', 0.001),
        lrf=config.get('lrf', 0.01),
        momentum=config.get('momentum', 0.937),
        weight_decay=config.get('weight_decay', 0.0005),
        hsv_h=config.get('hsv_h', 0.015),
        hsv_s=config.get('hsv_s', 0.7),
        hsv_v=config.get('hsv_v', 0.4),
        degrees=config.get('degrees', 0.0),
        translate=config.get('translate', 0.1),
        scale=config.get('scale', 0.5),
        shear=config.get('shear', 0.0),
        perspective=config.get('perspective', 0.0),
        flipud=config.get('flipud', 0.0),
        fliplr=config.get('fliplr', 0.5),
        mosaic=config.get('mosaic', 1.0),
        mixup=config.get('mixup', 0.0),
        conf=config.get('conf', 0.3),
        iou=config.get('iou', 0.5),
        max_det=config.get('max_det', 100),
        device=device,
        project=config.get('project', 'runs/train'),
        name=config.get('name', 'exp'),
        exist_ok=config.get('exist_ok', False),
        save=config.get('save', True),
        save_period=config.get('save_period', 10),
        workers=config.get('workers', 8),
        amp=config.get('amp', True),
        verbose=True
    )
    
    print("\nTraining completed!")
    print(f"Results saved to: {results.save_dir}")
    print(f"Best weights: {results.save_dir}/weights/best.pt")
    
    # Print final metrics
    if hasattr(results, 'results_dict'):
        metrics = results.results_dict
        print("\nFinal metrics:")
        print(f"  mAP@0.5: {metrics.get('metrics/mAP50(B)', 0):.4f}")
        print(f"  mAP@0.5:0.95: {metrics.get('metrics/mAP50-95(B)', 0):.4f}")
        print(f"  Precision: {metrics.get('metrics/precision(B)', 0):.4f}")
        print(f"  Recall: {metrics.get('metrics/recall(B)', 0):.4f}")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Train YOLO model for sports detection")
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to YAML config file (e.g., configs/pickleball_yolo.yaml)"
    )
    parser.add_argument(
        "--weights",
        type=str,
        default="yolov8n.pt",
        help="Pretrained weights (default: yolov8n.pt)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume training from last checkpoint"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device to use (0, 1, 2, etc. for GPU or 'cpu')"
    )
    
    args = parser.parse_args()
    
    if not args.config.exists():
        print(f"Error: Config file not found: {args.config}")
        return
    
    train_model(args.config, args.weights, args.resume, args.device)


if __name__ == "__main__":
    main()
