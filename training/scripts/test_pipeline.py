#!/usr/bin/env python3
"""
Test script to verify training pipeline setup.
Checks dependencies, directory structure, and basic functionality.
"""

import sys
from pathlib import Path


def check_dependencies():
    """Check if required packages are installed."""
    print("Checking dependencies...")
    required = {
        'torch': 'PyTorch',
        'ultralytics': 'Ultralytics YOLO',
        'coremltools': 'Core ML Tools',
        'cv2': 'OpenCV',
        'yaml': 'PyYAML'
    }
    
    missing = []
    for module, name in required.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT INSTALLED")
            missing.append(name)
    
    return len(missing) == 0, missing


def check_directories():
    """Check if required directories exist."""
    print("\nChecking directory structure...")
    required_dirs = [
        'data/raw',
        'data/frames',
        'data/annotations',
        'data/train/images',
        'data/train/labels',
        'data/val/images',
        'data/val/labels',
        'data/test/images',
        'data/test/labels',
        'models/pretrained',
        'models/checkpoints',
        'models/exported',
        'configs',
        'scripts'
    ]
    
    base = Path(__file__).parent.parent
    missing = []
    
    for dir_path in required_dirs:
        full_path = base / dir_path
        if full_path.exists():
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - MISSING")
            missing.append(dir_path)
    
    return len(missing) == 0, missing


def check_configs():
    """Check if config files exist."""
    print("\nChecking configuration files...")
    base = Path(__file__).parent.parent
    configs = [
        'configs/pickleball_yolo.yaml',
        'configs/tennis_yolo.yaml',
        'configs/padel_yolo.yaml',
    ]
    
    missing = []
    for config in configs:
        config_path = base / config
        if config_path.exists():
            print(f"  ✓ {config}")
        else:
            print(f"  ✗ {config} - MISSING")
            missing.append(config)
    
    return len(missing) == 0, missing


def check_pretrained_weights():
    """Check if pretrained weights exist."""
    print("\nChecking pretrained weights...")
    base = Path(__file__).parent.parent
    weights_path = base / 'models/pretrained/yolov8n.pt'
    
    if weights_path.exists():
        size_mb = weights_path.stat().st_size / 1024 / 1024
        print(f"  ✓ yolov8n.pt ({size_mb:.1f} MB)")
        return True
    else:
        print(f"  ✗ yolov8n.pt - MISSING")
        print(f"    Download: wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt")
        return False


def check_gpu():
    """Check GPU availability."""
    print("\nChecking GPU availability...")
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"  ✓ GPU available: {gpu_name}")
            return True
        else:
            print(f"  ⚠ No GPU available (training will use CPU)")
            return False
    except Exception as e:
        print(f"  ✗ Error checking GPU: {e}")
        return False


def main():
    print("="*60)
    print("NextMove Training Pipeline - Setup Verification")
    print("="*60)
    
    results = []
    
    # Check dependencies
    deps_ok, missing_deps = check_dependencies()
    results.append(("Dependencies", deps_ok))
    
    # Check directories
    dirs_ok, missing_dirs = check_directories()
    results.append(("Directories", dirs_ok))
    
    # Check configs
    configs_ok, missing_configs = check_configs()
    results.append(("Configs", configs_ok))
    
    # Check pretrained weights
    weights_ok = check_pretrained_weights()
    results.append(("Pretrained Weights", weights_ok))
    
    # Check GPU (optional)
    gpu_ok = check_gpu()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    all_ok = all(ok for _, ok in results)
    
    for name, ok in results:
        status = "✓ PASS" if ok else "✗ FAIL"
        print(f"{name:20s}: {status}")
    
    if gpu_ok:
        print(f"{'GPU':20s}: ✓ Available")
    else:
        print(f"{'GPU':20s}: ⚠ Not available (optional)")
    
    print("="*60)
    
    if all_ok:
        print("\n✓ All checks passed! Ready to train.")
        print("\nNext steps:")
        print("1. Place videos in data/raw/")
        print("2. Extract frames: python scripts/extract_frames.py data/raw/ data/frames/")
        print("3. Annotate frames and export to data/annotations/")
        print("4. Split dataset: python scripts/split_dataset.py --images data/frames/ --labels data/annotations/ --output data/")
        print("5. Train: python scripts/train_yolo.py --config configs/pickleball_yolo.yaml")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        
        if missing_deps:
            print("\nInstall missing dependencies:")
            print("  pip install -r requirements.txt")
        
        if missing_dirs:
            print("\nCreate missing directories:")
            print("  Run: bash scripts/quick_start.sh")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
