#!/usr/bin/env python
"""
Download a curated set of CC0/public domain test files for the DAM system.
Downloads images, videos, and PDFs from free sources.
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from tqdm import tqdm as tqdm_module
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import json


# Curated test files - using direct URLs from free sources
# These are small, representative files for testing
TEST_FILES = {
    "images": [
        {
            "url": "https://images.unsplash.com/photo-1600585154526-990dced4d0d4?w=800&q=80",
            "filename": "modern_living_room.jpg",
            "description": "Modern living room interior"
        },
        {
            "url": "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=800&q=80",
            "filename": "luxury_bedroom.jpg",
            "description": "Luxury bedroom design"
        },
        {
            "url": "https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?w=800&q=80",
            "filename": "modern_kitchen.jpg",
            "description": "Modern kitchen interior"
        },
        {
            "url": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&q=80",
            "filename": "office_workspace.jpg",
            "description": "Office workspace interior"
        },
        {
            "url": "https://images.unsplash.com/photo-1504307651254-35680f356bae?w=800&q=80",
            "filename": "construction_site.jpg",
            "description": "Construction site with workers"
        },
        {
            "url": "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&q=80",
            "filename": "apartment_floor_plan.jpg",
            "description": "Apartment floor plan layout"
        },
        {
            "url": "https://images.unsplash.com/photo-1600585152220-90363fe4e125?w=800&q=80",
            "filename": "modern_bathroom.jpg",
            "description": "Modern bathroom design"
        },
        {
            "url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=800&q=80",
            "filename": "building_exterior.jpg",
            "description": "Modern building exterior"
        },
        {
            "url": "https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?w=800&q=80",
            "filename": "city_skyline.jpg",
            "description": "City skyline at sunset"
        },
        {
            "url": "https://images.unsplash.com/photo-1480074568708-e7b720bb3f09?w=800&q=80",
            "filename": "residential_street.jpg",
            "description": "Residential neighborhood street"
        },
    ],
    "videos": [
        # Note: Direct video downloads from Pexels/Pixabay require API keys.
        # These are placeholder URLs - user should download manually or use API.
        # We'll create placeholder files instead.
    ],
    "documents": [
        # We'll generate synthetic PDFs instead of downloading
    ],
}


def download_file(url: str, filepath: Path, timeout: int = 30) -> bool:
    """Download a single file with progress bar."""
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as f:
            if total_size > 0:
                with tqdm_module(total=total_size, unit='B', unit_scale=True, 
                         desc=filepath.name, leave=False) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        return True
    except Exception as e:
        print(f"  ✗ Failed to download {filepath.name}: {e}")
        if filepath.exists():
            filepath.unlink()
        return False


def create_synthetic_pdfs(output_dir: Path) -> list:
    """Create synthetic PDF documents for testing."""
    import fitz  # PyMuPDF
    
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    
    pdf_docs = [
        {
            "filename": "residential_brochure.pdf",
            "title": "Residential Project Brochure",
            "pages": [
                "Residential Development Overview\n\nModern apartment complexes with premium amenities",
                "Floor Plans Available:\n• 1 Bedroom: 650-750 sq ft\n• 2 Bedroom: 950-1,100 sq ft\n• 3 Bedroom: 1,200-1,450 sq ft",
                "Location & Amenities:\n• Prime downtown location\n• Walking distance to transit\n• Rooftop terrace & pool\n• Fitness center\n• Secure parking\n• 24/7 concierge",
                "Pricing & Contact:\n• Starting from $450,000\n• Flexible financing available\n• Contact: sales@developer.com\n• Phone: (555) 123-4567"
            ]
        },
        {
            "filename": "apartment_floor_plan.pdf",
            "title": "Apartment Floor Plans",
            "pages": [
                "2 Bedroom Unit - Floor Plan\n\nTotal Area: 1,050 sq ft",
                "Room Dimensions:\n• Master Bedroom: 14' x 12' (with walk-in closet)\n• Bedroom 2: 11' x 10'\n• Living Room: 18' x 14'\n• Kitchen: 12' x 10' (with island)\n• Bathrooms: 2 full baths\n• Balcony: 8' x 6'",
                "Features:\n• Open concept living/dining\n• Stainless steel appliances\n• Quartz countertops\n• In-unit washer/dryer\n• Central HVAC\n• Sound-insulated walls",
                "Building Amenities:\n• Rooftop deck with city views\n• Package lockers\n• Bike storage\n• Pet-friendly\n• EV charging stations"
            ]
        },
        {
            "filename": "construction_project_proposal.pdf",
            "title": "Project Proposal - Commercial Complex",
            "pages": [
                "Executive Summary\n\nProposed 12-story mixed-use development\nDowntown Commercial District",
                "Project Scope:\n• Retail: Ground floor (8,000 sq ft)\n• Office: Floors 2-6 (72,000 sq ft)\n• Residential: Floors 7-12 (48 units)\n• Parking: 2-level underground (120 spaces)",
                "Specifications:\n• Green Building: LEED Silver target\n• Structural: Steel frame with concrete core\n• Facade: Curtain wall with high-performance glazing\n• HVAC: VRF system with heat recovery\n• Timeline: 18 months construction",
                "Budget & Schedule:\n• Total Budget: $42M\n• Design Phase: Months 1-3\n• Construction: Months 4-18\n• Commissioning: Month 19\n• Occupancy: Month 20"
            ]
        },
        {
            "filename": "interior_design_catalog.pdf",
            "title": "Interior Design Catalog 2024",
            "pages": [
                "Modern Interior Collection\n\nCurated designs for residential & commercial spaces",
                "Living Room Concepts:\n• Minimalist Scandinavian\n• Mid-century Modern\n• Industrial Loft\n• Coastal Contemporary",
                "Kitchen Designs:\n• Open plan with island\n• Galley efficiency\n• Chef's kitchen\n• Compact urban",
                "Materials & Finishes:\n• Natural wood (oak, walnut, ash)\n• Stone (marble, quartz, granite)\n• Metal accents (brass, matte black)\n• Sustainable fabrics",
                "Contact our design team:\n• design@interiorstudio.com\n• (555) 987-6543\n• Free initial consultation"
            ]
        },
        {
            "filename": "building_specifications.pdf",
            "title": "Technical Building Specifications",
            "pages": [
                "Building Technical Specifications\n\nProject: Riverside Commercial Tower\nAddress: 100 Riverside Drive",
                "Structural:\n• Foundation: Drilled piers to bedrock\n• Frame: Reinforced concrete moment frame\n• Floors: 8\" post-tensioned concrete slab\n• Seismic: Zone 4 compliant",
                "Envelope:\n• Curtain wall: Double-glazed low-E\n• R-value: R-15 walls, R-30 roof\n• Air barrier: Fluid-applied membrane\n• Waterproofing: Hot-applied rubberized asphalt",
                "MEP Systems:\n• Electrical: 480V/277V 3-phase\n• Emergency: 500kW diesel generator\n• Plumbing: WaterSense fixtures\n• Fire: NFPA 13 sprinkler + standpipe",
                "Certifications:\n• Target: LEED Gold v4.1\n• Energy: ASHRAE 90.1-2019\n• Commissioning: ASHRAE 202\n• WELL Building Standard: Silver"
            ]
        },
    ]
    
    for doc in pdf_docs:
        pdf_path = output_dir / doc["filename"]
        doc_obj = fitz.open()
        
        for i, page_text in enumerate(doc["pages"]):
            page = doc_obj.new_page()
            # Title
            page.insert_text((72, 72), doc["title"], fontsize=20, fontname="helv")
            # Page number
            page.insert_text((72, 100), f"Page {i+1} of {len(doc['pages'])}", fontsize=10, color=(0.5, 0.5, 0.5))
            # Content
            page.insert_text((72, 140), page_text, fontsize=11, fontname="helv")
        
        doc_obj.save(pdf_path)
        doc_obj.close()
        created.append(pdf_path)
        print(f"  ✓ Created: {doc['filename']} ({len(doc['pages'])} pages)")
    
    return created


def create_placeholder_videos(output_dir: Path) -> list:
    """Create placeholder video files (empty files with .mp4 extension).
    Real videos should be downloaded manually from Pexels/Pixabay."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    created = []
    
    video_placeholders = [
        ("construction_timelapse.mp4", "Construction timelapse - building progress over weeks"),
        ("customer_testimonial.mp4", "Customer testimonial - residential project review"),
        ("project_walkthrough.mp4", "Virtual walkthrough - completed development tour"),
        ("office_interior.mp4", "Modern office interior - workspace tour"),
        ("construction_site.mp4", "Active construction site - workers and equipment"),
    ]
    
    for filename, description in video_placeholders:
        video_path = output_dir / filename
        # Create a minimal valid MP4 container (just the header)
        # This is a placeholder - replace with real videos for testing
        mp4_header = bytes([
            0x00, 0x00, 0x00, 0x18,  # Box size (24 bytes)
            0x66, 0x74, 0x79, 0x70,  # 'ftyp'
            0x69, 0x73, 0x6F, 0x6D,  # major brand: 'isom'
            0x00, 0x00, 0x02, 0x00,  # minor version
            0x69, 0x73, 0x6F, 0x6D,  # compatible brands
            0x69, 0x73, 0x6F, 0x32,
            0x61, 0x76, 0x63, 0x31,
            0x6D, 0x70, 0x34, 0x31,
        ])
        video_path.write_bytes(mp4_header)
        created.append(video_path)
        print(f"  ⚠ Placeholder: {filename} - {description}")
        print(f"     Replace with real video from Pexels/Pixabay for full testing")
    
    return created


def create_manifest(output_dir: Path, all_files: list):
    """Create a manifest file documenting the dataset."""
    manifest_path = output_dir / "DATASET_MANIFEST.md"
    
    images = [f for f in all_files if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
    videos = [f for f in all_files if f.suffix.lower() in ['.mp4', '.mov', '.mkv', '.avi', '.webm']]
    documents = [f for f in all_files if f.suffix.lower() == '.pdf']
    
    total_size = sum(f.stat().st_size for f in all_files if f.exists())
    
    content = f"""# Test Dataset Manifest

Generated: {__import__('datetime').datetime.now().isoformat()}
Total files: {len(all_files)}
Total size: {total_size / (1024*1024):.2f} MB

## Statistics
- Images: {len(images)} files
- Videos: {len(videos)} files (placeholders)
- Documents: {len(documents)} files

## Files

### Images ({len(images)})
"""
    for img in images:
        size = img.stat().st_size if img.exists() else 0
        content += f"- {img.name} ({size / 1024:.1f} KB)\n"
    
    content += f"\n### Videos ({len(videos)}) [PLACEHOLDERS - Replace with real files]\n"
    for vid in videos:
        size = vid.stat().st_size if vid.exists() else 0
        content += f"- {vid.name} ({size} bytes)\n"
    
    content += f"\n### Documents ({len(documents)})\n"
    for doc in documents:
        size = doc.stat().st_size if doc.exists() else 0
        content += f"- {doc.name} ({size / 1024:.1f} KB)\n"
    
    content += """
## Notes
- Images: Downloaded from Unsplash (Unsplash License - free commercial use)
- Videos: Placeholder files only. Download real videos from Pexels/Pixabay for full testing.
- PDFs: Synthetic documents generated with PyMuPDF.

## Usage
Set in .env:
```
MEDIA_ROOT=./data/media
```

Then run:
```
make migrate
make dev
# In UI: /indexing → Start Indexing
```
"""
    
    manifest_path.write_text(content)
    print(f"\n✓ Manifest created: {manifest_path}")


def verify_downloads(files: list) -> dict:
    """Verify downloaded files are valid."""
    results = {"valid": 0, "corrupt": 0, "missing": 0, "details": []}
    
    for f in files:
        if not f.exists():
            results["missing"] += 1
            results["details"].append(f"{f.name}: MISSING")
            continue
        
        size = f.stat().st_size
        if size == 0:
            results["corrupt"] += 1
            results["details"].append(f"{f.name}: EMPTY (0 bytes)")
            continue
        
        # Quick validation by extension
        ext = f.suffix.lower()
        valid = False
        
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            try:
                from PIL import Image
                with Image.open(f) as img:
                    img.verify()
                valid = True
            except:
                pass
        elif ext == '.pdf':
            try:
                import fitz
                doc = fitz.open(f)
                valid = doc.page_count > 0
                doc.close()
            except:
                pass
        elif ext in ['.mp4', '.mov', '.webm']:
            # Check for MP4 header
            try:
                header = f.read_bytes(12)
                if b'ftyp' in header[4:8]:
                    valid = True
            except:
                pass
        
        if valid:
            results["valid"] += 1
            results["details"].append(f"{f.name}: OK ({size/1024:.1f} KB)")
        else:
            results["corrupt"] += 1
            results["details"].append(f"{f.name}: INVALID ({size} bytes)")
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Download test dataset for DAM system")
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default=Path("./data/media"),
        help="Output directory for media files"
    )
    parser.add_argument(
        "--images-only", 
        action="store_true",
        help="Only download images"
    )
    parser.add_argument(
        "--skip-images", 
        action="store_true",
        help="Skip image downloads"
    )
    parser.add_argument(
        "--verify", 
        action="store_true",
        help="Verify existing files"
    )
    parser.add_argument(
        "--workers", 
        type=int, 
        default=4,
        help="Number of parallel downloads"
    )
    
    args = parser.parse_args()
    
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    images_dir = output_dir / "images"
    videos_dir = output_dir / "videos"
    documents_dir = output_dir / "documents"
    
    all_files = []
    
    if args.verify:
        print("Verifying existing files...")
        for subdir in [images_dir, videos_dir, documents_dir]:
            if subdir.exists():
                files = list(subdir.rglob("*"))
                files = [f for f in files if f.is_file()]
                if files:
                    results = verify_downloads(files)
                    print(f"\n{subdir.name}: {results['valid']} valid, {results['corrupt']} corrupt, {results['missing']} missing")
                    for detail in results['details']:
                        print(f"  {detail}")
        return
    
    print(f"Creating test dataset in: {output_dir}")
    print("=" * 60)
    
    # Download images
    if not args.skip_images:
        print("\n📥 Downloading images from Unsplash...")
        images_dir.mkdir(parents=True, exist_ok=True)
        
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = []
            for img_info in TEST_FILES["images"]:
                filepath = images_dir / img_info["filename"]
                if not filepath.exists():
                    futures.append(executor.submit(download_file, img_info["url"], filepath))
                else:
                    print(f"  ⊙ Exists: {img_info['filename']}")
                    all_files.append(filepath)
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    # Find which file was downloaded
                    for img_info in TEST_FILES["images"]:
                        filepath = images_dir / img_info["filename"]
                        if filepath.exists() and filepath not in all_files:
                            all_files.append(filepath)
                            break
        
        # Add any existing images
        for f in images_dir.glob("*"):
            if f.is_file() and f not in all_files:
                all_files.append(f)
    
    # Create placeholder videos
    if not args.images_only:
        print("\n🎬 Creating video placeholders...")
        print("   (Replace with real videos from Pexels/Pixabay for full testing)")
        video_files = create_placeholder_videos(videos_dir)
        all_files.extend(video_files)
    
    # Create synthetic PDFs
    if not args.images_only:
        print("\n📄 Creating synthetic PDF documents...")
        pdf_files = create_synthetic_pdfs(documents_dir)
        all_files.extend(pdf_files)
    
    # Create manifest
    print("\n📋 Creating dataset manifest...")
    create_manifest(output_dir, all_files)
    
    # Verify
    print("\n✅ Verifying downloads...")
    results = verify_downloads(all_files)
    print(f"\nResults: {results['valid']} valid, {results['corrupt']} corrupt, {results['missing']} missing")
    
    for detail in results['details']:
        status = "✓" if "OK" in detail else "✗"
        print(f"  {status} {detail}")
    
    print(f"\n{'='*60}")
    print(f"Dataset ready at: {output_dir}")
    print(f"Total files: {len(all_files)}")
    print(f"\nNext steps:")
    print(f"  1. Set in .env: MEDIA_ROOT={output_dir}")
    print(f"  2. Run: make migrate && make dev")
    print(f"  3. In UI: /indexing → Start Indexing")
    print(f"  4. Search at /search")


if __name__ == "__main__":
    # Check dependencies
    try:
        import requests
        import tqdm
        import fitz
        from PIL import Image
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install requests tqdm pymupdf pillow")
        sys.exit(1)
    
    main()