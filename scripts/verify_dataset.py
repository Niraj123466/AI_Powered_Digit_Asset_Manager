#!/usr/bin/env python
"""Verify dataset structure and report statistics."""

import sys
from pathlib import Path
from collections import Counter
import os


def verify_dataset(media_root: Path):
    """Verify dataset structure and report statistics."""
    
    if not media_root.exists():
        print(f"ERROR: Media root does not exist: {media_root}")
        return False
    
    print(f"Verifying dataset at: {media_root}")
    print("=" * 60)
    
    # Expected structure
    expected_dirs = {
        "images": media_root / "images",
        "videos": media_root / "videos", 
        "documents": media_root / "documents",
    }
    
    # Supported extensions
    image_exts = {".jpg", ".jpeg", ".png", ".webp"}
    video_exts = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
    doc_exts = {".pdf"}
    
    stats = {
        "images": {"count": 0, "size": 0, "exts": Counter()},
        "videos": {"count": 0, "size": 0, "exts": Counter()},
        "documents": {"count": 0, "size": 0, "exts": Counter()},
        "other": {"count": 0, "size": 0, "exts": Counter()},
    }
    
    # Check expected directories
    for name, path in expected_dirs.items():
        if path.exists():
            print(f"✓ Found {name}/ directory")
        else:
            print(f"✗ Missing {name}/ directory")
    
    # Walk all files
    total_files = 0
    total_size = 0
    
    for file_path in media_root.rglob("*"):
        if not file_path.is_file():
            continue
        
        total_files += 1
        size = file_path.stat().st_size
        total_size += size
        ext = file_path.suffix.lower()
        
        # Categorize
        if ext in image_exts:
            cat = "images"
        elif ext in video_exts:
            cat = "videos"
        elif ext in doc_exts:
            cat = "documents"
        else:
            cat = "other"
        
        stats[cat]["count"] += 1
        stats[cat]["size"] += size
        stats[cat]["exts"][ext] += 1
    
    # Print statistics
    print("\n" + "=" * 60)
    print("DATASET STATISTICS")
    print("=" * 60)
    
    print(f"\nTotal files: {total_files}")
    print(f"Total size: {format_size(total_size)}")
    
    for cat in ["images", "videos", "documents", "other"]:
        s = stats[cat]
        if s["count"] > 0:
            print(f"\n{cat.upper()}: {s['count']} files, {format_size(s['size'])}")
            for ext, count in s["exts"].most_common():
                print(f"  {ext}: {count}")
    
    # Check for issues
    issues = []
    
    if stats["images"]["count"] == 0:
        issues.append("No image files found")
    if stats["videos"]["count"] == 0:
        issues.append("No video files found")
    if stats["documents"]["count"] == 0:
        issues.append("No document files found")
    if stats["other"]["count"] > 0:
        issues.append(f"Found {stats['other']['count']} unsupported files")
    
    # Check for empty files
    empty_files = []
    for file_path in media_root.rglob("*"):
        if file_path.is_file() and file_path.stat().st_size == 0:
            empty_files.append(file_path.relative_to(media_root))
    
    if empty_files:
        issues.append(f"Found {len(empty_files)} empty files")
        for f in empty_files[:5]:
            issues.append(f"  - {f}")
        if len(empty_files) > 5:
            issues.append(f"  ... and {len(empty_files) - 5} more")
    
    # Check for very large files (>1GB)
    large_files = []
    for file_path in media_root.rglob("*"):
        if file_path.is_file() and file_path.stat().st_size > 1024**3:
            large_files.append((file_path.relative_to(media_root), file_path.stat().st_size))
    
    if large_files:
        issues.append(f"Found {len(large_files)} files >1GB:")
        for f, size in large_files[:5]:
            issues.append(f"  - {f}: {format_size(size)}")
    
    if issues:
        print("\n" + "=" * 60)
        print("ISSUES FOUND:")
        print("=" * 60)
        for issue in issues:
            print(f"  ⚠ {issue}")
    else:
        print("\n" + "=" * 60)
        print("✓ No issues found - dataset looks good!")
        print("=" * 60)
    
    return len(issues) == 0


def format_size(bytes_val):
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} PB"


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify DAM dataset")
    parser.add_argument(
        "--media-root",
        type=Path,
        default=Path("./data/media"),
        help="Path to media root directory"
    )
    args = parser.parse_args()
    
    success = verify_dataset(args.media_root.resolve())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()