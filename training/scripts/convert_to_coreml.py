#!/usr/bin/env python3
"""
Convert trained YOLO model to Core ML format for iOS deployment.
Includes quantization and validation.
"""

import argparse
from pathlib import Path
import yaml
from ultralytics import YOLO
import coremltools as ct


def convert_to_coreml(
    model_path: Path,
    config_path: Path,
    output_dir: Path,
    quantize: bool = True,
    nms: bool = True
):
    """Convert YOLO model to Core ML format."""
    
    if not model_path.exists():
        print(f"Error: Model not found: {model_path}")
        return None
    
    # Load config for metadata
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    print(f"Converting model: {model_path.name}")
    print(f"  Classes: {config['nc']}")
    print(f"  Quantization: {quantize}")
    print(f"  Include NMS: {nms}")
    
    # Load YOLO model
    model = YOLO(str(model_path))
    
    # Export to Core ML
    print("\nExporting to Core ML...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Ultralytics export handles Core ML conversion
    export_path = model.export(
        format='coreml',
        imgsz=config.get('imgsz', 640),
        nms=nms,
        int8=quantize
    )
    
    print(f"Model exported to: {export_path}")
    
    # Load and enhance Core ML model with metadata
    mlmodel = ct.models.MLModel(export_path)
    
    # Set metadata
    sport_name = config_path.stem.split('_')[0].capitalize()
    model_version = model_path.stem.split('_')[-1] if '_' in model_path.stem else 'v1'
    
    mlmodel.short_description = f"{sport_name} object detection model"
    mlmodel.author = "NextMove Training Pipeline"
    mlmodel.license = "Proprietary"
    mlmodel.version = model_version
    
    # Add input/output descriptions
    spec = mlmodel.get_spec()
    spec.description.input[0].shortDescription = "Input image (RGB, 640x640)"
    spec.description.output[0].shortDescription = "Bounding boxes [x, y, width, height]"
    spec.description.output[1].shortDescription = "Confidence scores"
    spec.description.output[2].shortDescription = "Class labels"
    
    # Save enhanced model
    output_name = f"{sport_name}Detector_{model_version}.mlmodel"
    output_path = output_dir / output_name
    mlmodel.save(str(output_path))
    
    print(f"\nCore ML model saved: {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Validate conversion
    print("\nValidating conversion...")
    validate_conversion(mlmodel, config)
    
    return output_path


def validate_conversion(mlmodel, config):
    """Validate Core ML model can be loaded and used."""
    import numpy as np
    
    try:
        # Create dummy input
        dummy_input = np.random.rand(1, 3, 640, 640).astype(np.float32)
        
        # Run inference
        prediction = mlmodel.predict({'image': dummy_input})
        
        print("  ✓ Model loads successfully")
        print("  ✓ Inference runs successfully")
        print(f"  Output keys: {list(prediction.keys())}")
        
    except Exception as e:
        print(f"  ✗ Validation failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Convert YOLO to Core ML")
    parser.add_argument(
        "--model",
        type=Path,
        required=True,
        help="Path to trained model (.pt file)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to YAML config file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("models/exported"),
        help="Output directory (default: models/exported)"
    )
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="Disable int8 quantization"
    )
    parser.add_argument(
        "--no-nms",
        action="store_true",
        help="Don't include NMS in model"
    )
    
    args = parser.parse_args()
    
    convert_to_coreml(
        args.model,
        args.config,
        args.output,
        not args.no_quantize,
        not args.no_nms
    )


if __name__ == "__main__":
    main()
