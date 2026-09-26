#!/usr/bin/env python
"""Create a sample dataset for development and testing.

Downloads a small set of CC0-licensed media files for testing the DAM system.
"""

import os
import sys
import urllib.request
from pathlib import Path
from typing import List, Tuple


SAMPLE_FILES = [
    # Images (from Unsplash/CC0 sources - small thumbnails)
    {
        "url": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=400&h=300&fit=crop",
        "path": "images/modern_living_room.jpg",
        "description": "Modern living room interior"
    },
    {
        "url": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=300&fit=crop",
        "path": "images/luxury_bedroom.jpg",
        "description": "Luxury bedroom design"
    },
    {
        "url": "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400&h=300&fit=crop",
        "path": "images/kitchen_renovation.jpg",
        "description": "Modern kitchen interior"
    },
    {
        "url": "https://images.unsplash.com/photo-1504307651254-35680f356bae?w=400&h=300&fit=crop",
        "path": "images/office_workspace.jpg",
        "description": "Office workspace interior"
    },
    {
        "url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=400&h=300&fit=crop",
        "path": "images/construction_site.jpg",
        "description": "Construction site with workers"
    },
    
    # Videos (small sample clips from Pixabay/CC0)
    # Note: These are placeholder URLs - real implementation would use actual video files
    # For now, we'll create placeholder info files
    
    # Documents (sample PDFs)
]

# Alternative: Create synthetic test files using Python
def create_synthetic_images(output_dir: Path) -> List[Path]:
    """Create simple synthetic images for testing."""
    from PIL import Image, ImageDraw, ImageFont
    
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    
    test_images = [
        ("modern_living_room.jpg", "Modern Living Room\nSofa, Coffee Table, Large Window", (200, 180, 160)),
        ("luxury_bedroom.jpg", "Luxury Bedroom\nKing Bed, Nightstands, Chandelier", (180, 160, 140)),
        ("kitchen_renovation.jpg", "Kitchen Renovation\nIsland, Cabinets, Stainless Steel", (160, 180, 200)),
        ("office_workspace.jpg", "Office Workspace\nDesk, Monitor, Ergonomic Chair", (140, 160, 180)),
        ("construction_site.jpg", "Construction Site\nExcavator, Workers, Building Frame", (180, 140, 120)),
        ("apartment_floor_plan.jpg", "Apartment Floor Plan\n2BR, Living Room, Kitchen, Bath", (120, 180, 140)),
    ]
    
    for filename, text, bg_color in test_images:
        img = Image.new('RGB', (640, 480), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # Draw text
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (640 - text_width) // 2
        y = (480 - text_height) // 2
        
        draw.text((x, y), text, fill=(255, 255, 255), font=font)
        
        # Add border
        draw.rectangle([0, 0, 639, 479], outline=(100, 100, 100), width=3)
        
        filepath = output_dir / filename
        img.save(filepath, quality=85)
        created.append(filepath)
        print(f"Created: {filepath}")
    
    return created


def create_synthetic_videos(output_dir: Path) -> List[Path]:
    """Create info files for video placeholders (actual videos would need ffmpeg)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    
    video_infos = [
        ("construction_timelapse.txt", "construction_timelapse.mp4", "Construction timelapse showing building progress over several weeks"),
        ("customer_testimonial.txt", "customer_testimonial.mp4", "Customer testimonial about residential project experience"),
        ("project_walkthrough.txt", "project_walkthrough.mp4", "Virtual walkthrough of completed residential development"),
    ]
    
    for info_filename, video_filename, description in video_infos:
        info_path = output_dir / info_filename
        info_path.write_text(f"Placeholder for: {video_filename}\nDescription: {description}\n\nNote: Replace with actual video file for testing.")
        created.append(info_path)
        
        # Also create empty video placeholder
        video_path = output_dir / video_filename
        video_path.write_bytes(b"")  # Empty file - will be skipped by validator
        created.append(video_path)
        print(f"Created placeholder: {video_path}")
    
    return created


def create_synthetic_pdfs(output_dir: Path) -> List[Path]:
    """Create simple PDF documents for testing."""
    import fitz  # PyMuPDF
    
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    
    pdf_docs = [
        ("residential_brochure.pdf", "Residential Project Brochure", [
            "Residential Development Overview",
            "Modern apartment complexes with premium amenities",
            "Floor plans: 1BR, 2BR, 3BR units available",
            "Location: Prime downtown area",
            "Amenities: Pool, gym, rooftop terrace, parking",
            "Pricing: Starting from $450,000",
            "Contact: sales@developer.com"
        ]),
        ("apartment_floor_plan.pdf", "Apartment Floor Plans", [
            "Floor Plan - 2 Bedroom Unit",
            "Total Area: 1,200 sq ft",
            "Bedrooms: 2 (Master with ensuite)",
            "Bathrooms: 2",
            "Living Room: 20x15 ft",
            "Kitchen: 12x10 ft with island",
            "Balcony: 8x6 ft",
            "Storage: Walk-in closet + linen closet"
        ]),
        ("project_proposal.pdf", "Project Proposal - Commercial Complex", [
            "Executive Summary",
            "Proposed 20-story mixed-use development",
            "Retail: Ground floor (15,000 sq ft)",
            "Office: Floors 2-10 (120,000 sq ft)",
            "Residential: Floors 11-20 (80 units)",
            "Parking: 3-level underground (200 spaces)",
            "Green Building: LEED Gold target",
            "Timeline: 24 months construction",
            "Budget: $85M"
        ]),
    ]
    
    for filename, title, content_lines in pdf_docs:
        doc = fitz.open()
        
        for i, line in enumerate(content_lines):
            page = doc.new_page()
            page.insert_text((72, 72), title, fontsize=24)
            page.insert_text((72, 120), line, fontsize=14)
            if i > 0:
                page.insert_text((72, 150), f"Page {i+1} content: {line}", fontsize=12)
        
        filepath = output_dir / filename
        doc.save(filepath)
        doc.close()
        created.append(filepath)
        print(f"Created: {filepath}")
    
    return created


def create_dataset_manifest(output_dir: Path, all_files: List[Path]):
    """Create a manifest file documenting the dataset."""
    manifest_path = output_dir / "DATASET_MANIFEST.md"
    
    images = [f for f in all_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
    videos = [f for f in all_files if f.suffix.lower() in ['.mp4', '.mov', '.mkv', '.avi', '.webm']]
    documents = [f for f in all_files if f.suffix.lower() == '.pdf']
    placeholders = [f for f in all_files if f.suffix.lower() == '.txt']
    
    total_size = sum(f.stat().st_size for f in all_files if f.exists())
    
    content = f"""# Sample Dataset Manifest

Generated: {__import__('datetime').datetime.now().isoformat()}

## Statistics
- Total files: {len(all_files)}
- Total size: {total_size / 1024:.1f} KB
- Images: {len(images)}
- Videos: {len(videos)} (placeholders only)
- Documents: {len(documents)}
- Placeholders: {len(placeholders)}

## Files

### Images ({len(images)})
"""
    for img in images:
        size = img.stat().st_size if img.exists() else 0
        content += f"- {img.name} ({size / 1024:.1f} KB)\n"
    
    content += f"\n### Videos ({len(videos)})\n"
    for vid in videos:
        size = vid.stat().st_size if vid.exists() else 0
        content += f"- {vid.name} ({size / 1024:.1f} KB)\n"
    
    content += f"\n### Documents ({len(documents)})\n"
    for doc in documents:
        size = doc.stat().st_size if doc.exists() else 0
        content += f"- {doc.name} ({size / 1024:.1f} KB)\n"
    
    manifest_path.write_text(content)
    print(f"Created manifest: {manifest_path}")


def main():
    """Create the sample dataset."""
    base_dir = Path(__file__).parent.parent / "data" / "sample"
    base_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating sample dataset...")
    print(f"Output directory: {base_dir}")
    
    all_files = []
    
    # Create images
    print("\n--- Creating synthetic images ---")
    images_dir = base_dir / "media" / "images"
    all_files.extend(create_synthetic_images(images_dir))
    
    # Create videos (placeholders)
    print("\n--- Creating video placeholders ---")
    videos_dir = base_dir / "media" / "videos"
    all_files.extend(create_synthetic_videos(videos_dir))
    
    # Create PDFs
    print("\n--- Creating synthetic PDFs ---")
    docs_dir = base_dir / "media" / "documents"
    all_files.extend(create_synthetic_pdfs(docs_dir))
    
    # Create manifest
    print("\n--- Creating manifest ---")
    create_dataset_manifest(base_dir, all_files)
    
    print(f"\n✓ Sample dataset created at {base_dir}")
    print(f"  Total files: {len(all_files)}")
    print("\nTo use this dataset, set in .env:")
    print(f"  MEDIA_ROOT={base_dir / 'media'}")


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install pillow pymupdf")
        sys.exit(1)