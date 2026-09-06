#!/bin/bash
# Quick start script for training pipeline setup

set -e

echo "=================================="
echo "NextMove Training Pipeline Setup"
echo "=================================="

# Check Python version
echo -e "\n[1/6] Checking Python version..."
python3 --version || { echo "Error: Python 3 not found"; exit 1; }

# Create virtual environment
echo -e "\n[2/6] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo -e "\n[3/6] Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo -e "\n[4/6] Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Download pretrained weights
echo -e "\n[5/6] Downloading pretrained YOLO weights..."
mkdir -p models/pretrained
if [ ! -f "models/pretrained/yolov8n.pt" ]; then
    wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt \
         -O models/pretrained/yolov8n.pt
    echo "✓ Pretrained weights downloaded"
else
    echo "✓ Pretrained weights already exist"
fi

# Create directory structure
echo -e "\n[6/6] Creating directory structure..."
mkdir -p data/{raw,frames,annotations,train,val,test}
mkdir -p data/train/{images,labels}
mkdir -p data/val/{images,labels}
mkdir -p data/test/{images,labels}
mkdir -p models/{checkpoints,exported}
echo "✓ Directory structure created"

echo -e "\n=================================="
echo "Setup Complete!"
echo "=================================="
echo -e "\nNext steps:"
echo "1. Place your videos in data/raw/"
echo "2. Extract frames: python scripts/extract_frames.py data/raw/ data/frames/"
echo "3. Annotate frames using CVAT, Label Studio, or Roboflow"
echo "4. Export annotations to data/annotations/ (YOLO format)"
echo "5. Split dataset: python scripts/split_dataset.py --images data/frames/ --labels data/annotations/ --output data/"
echo "6. Train model: python scripts/train_yolo.py --config configs/pickleball_yolo.yaml"
echo -e "\nSee README.md for detailed instructions"
