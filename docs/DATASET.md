# Dataset Documentation

## Overview

This document describes the dataset requirements, sources, and structure for the AI-Powered Digital Asset Management system.

## Dataset Requirements

The system expects a local directory structure under `MEDIA_ROOT` (default: `./data/media/`):

```
data/
└── media/
    ├── images/
    │   ├── photo1.jpg
    │   ├── photo2.png
    │   └── ...
    ├── videos/
    │   ├── video1.mp4
    │   ├── video2.mov
    │   └── ...
    └── documents/
        ├── brochure1.pdf
        ├── report2.pdf
        └── ...
```

## Supported File Types

| Modality | Extensions |
|----------|------------|
| Images | jpg, jpeg, png, webp |
| Videos | mp4, mov, mkv, avi, webm |
| Documents | pdf |

## Dataset Sources

### Option 1: Sample Dataset (Development)

For development and testing, create a small sample dataset:

```bash
mkdir -p data/media/{images,videos,documents}
# Add a few sample files of each type
```

Sample datasets can be obtained from:
- **Images**: Unsplash (free license), Pexels, or generated via AI
- **Videos**: Pexels Videos, Pixabay, or generated clips
- **Documents**: Sample PDFs from government/public domain sources

### Option 2: Production Dataset

For full evaluation, use a larger dataset (5-10 GB recommended):

#### Images
- **Source**: Unsplash Dataset (unsplash.com/data) - ~25GB, 2M+ photos
- **License**: Unsplash License (free for commercial/non-commercial)
- **Download**: Available via Kaggle or direct download
- **Alternative**: LAION-400M (research only)

#### Videos
- **Source**: Pexels Videos API, Pixabay Videos
- **License**: Free for commercial use
- **Alternative**: Kinetic-400, Something-Something V2 (research)

#### Documents
- **Source**: Public domain PDFs (government reports, academic papers)
- **License**: Public domain / CC0
- **Alternative**: arXiv papers, PubMed Central

## Legal Compliance

**IMPORTANT**: Only use media with verified licenses that permit:
- Local storage and processing
- AI/ML analysis (embedding generation, captioning, OCR)
- Search and retrieval

Do NOT use:
- Copyrighted material without explicit permission
- Scraped content from websites without checking ToS
- Private/proprietary datasets

## Dataset Statistics Template

When documenting your dataset, record:

```
Total size: X GB
Total assets: N
  Images: N (X GB)
  Videos: N (X GB)
  Documents: N (X MB)
Date range: YYYY-MM-DD to YYYY-MM-DD
Source breakdown:
  - Source A: N files
  - Source B: N files
License verification: [Date verified]
```

## Sample Dataset Creation

For quick testing, run:

```bash
python scripts/create_sample_dataset.py
```

This will download a small set of CC0-licensed media files.

## Data Preparation

Before indexing:

1. **Organize files** into `images/`, `videos/`, `documents/` subdirectories
2. **Verify file integrity** - no corrupted files
3. **Check permissions** - ensure read access
4. **Remove unwanted files** - system files, duplicates outside the system

## Scaling Considerations

| Dataset Size | Expected Indexing Time | Storage Needed |
|--------------|------------------------|----------------|
| 100 MB | ~2 min | ~50 MB vectors |
| 1 GB | ~15 min | ~500 MB vectors |
| 10 GB | ~2 hours | ~5 GB vectors |
| 100 GB | ~20 hours | ~50 GB vectors |

For large datasets (>10 GB):
- Ensure adequate disk space for vectors
- Consider GPU acceleration for embeddings
- Monitor memory usage during indexing
- Use SSD storage for better performance