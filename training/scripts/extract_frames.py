#!/usr/bin/env python3
"""
Extract frames from video files for training dataset preparation.
Supports MP4, MOV, M4V formats with configurable frame rate.
"""

import argparse
import cv2
from pathlib import Path
import sys


def extract_frames(video_path: Path, output_dir: Path, fps: int = 5, prefix: str = "frame"):
    """Extract frames from video at specified frame rate."""
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}")
        return False
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Error: Could not open video: {video_path}")
        return False
    
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, int(video_fps / fps))
    
    print(f"Video: {video_path.name}")
    print(f"  FPS: {video_fps:.2f}, Total frames: {total_frames}")
    print(f"  Extracting every {frame_interval} frames (target {fps} fps)")
    
    frame_count = 0
    saved_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % frame_interval == 0:
            output_path = output_dir / f"{prefix}_{saved_count:06d}.jpg"
            cv2.imwrite(str(output_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
            saved_count += 1
        
        frame_count += 1
    
    cap.release()
    print(f"  Extracted {saved_count} frames to {output_dir}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Extract frames from videos for training")
    parser.add_argument("input", type=Path, help="Input video file or directory")
    parser.add_argument("output", type=Path, help="Output directory for frames")
    parser.add_argument("--fps", type=int, default=5, help="Target frame rate (default: 5)")
    parser.add_argument("--prefix", type=str, default="frame", help="Frame filename prefix")
    
    args = parser.parse_args()
    
    if args.input.is_file():
        success = extract_frames(args.input, args.output, args.fps, args.prefix)
        sys.exit(0 if success else 1)
    elif args.input.is_dir():
        video_extensions = {".mp4", ".mov", ".m4v"}
        videos = [f for f in args.input.iterdir() if f.suffix.lower() in video_extensions]
        
        if not videos:
            print(f"No video files found in {args.input}")
            sys.exit(1)
        
        print(f"Found {len(videos)} video(s)")
        success_count = 0
        
        for video in videos:
            video_output = args.output / video.stem
            if extract_frames(video, video_output, args.fps, args.prefix):
                success_count += 1
        
        print(f"\nCompleted: {success_count}/{len(videos)} videos processed")
        sys.exit(0 if success_count == len(videos) else 1)
    else:
        print(f"Error: Input path does not exist: {args.input}")
        sys.exit(1)


if __name__ == "__main__":
    main()
