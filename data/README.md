# Data Directory

This directory contains media files for the DAM system. It is **not tracked by git**.

## Structure

```
data/
├── media/
│   ├── images/
│   ├── videos/
│   └── documents/
└── sample/          # Optional small sample dataset
```

## Setup

1. Create the directory structure:
```bash
mkdir -p data/media/{images,videos,documents}
```

2. Add your media files:
```bash
# Images
cp /path/to/photos/*.jpg data/media/images/

# Videos
cp /path/to/videos/*.mp4 data/media/videos/

# Documents
cp /path/to/pdfs/*.pdf data/media/documents/
```

## Supported Formats

| Type | Extensions |
|------|------------|
| Images | jpg, jpeg, png, webp |
| Videos | mp4, mov, mkv, avi, webm |
| Documents | pdf |

## Configuration

Set `MEDIA_ROOT` in `.env`:
```env
MEDIA_ROOT=./data/media
```

## Sample Dataset

For development without large files, create a sample dataset:
```bash
mkdir -p data/sample/{images,videos,documents}
# Add a few small test files
```

Then set:
```env
MEDIA_ROOT=./data/sample
```

## Dataset Statistics

Record your dataset stats here:

```
Total size:
Total assets:
Images:
Videos:
Documents:
Source:
License:
Date added:
```