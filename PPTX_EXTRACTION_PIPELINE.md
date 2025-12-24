# PPTX Separate Extraction Pipeline

## Overview

This implementation provides a **separate extraction pipeline for PowerPoint (PPTX) files** that keeps them out of the main vectorstore ingestion. This is the recommended approach because:

✅ **Keeps main vectorstore clean** - No low-semantic-density presentation content  
✅ **No token waste** - PPTX slides are often visual-heavy with minimal text  
✅ **Full control** - Extract, summarize, or selectively ingest PPTX content later  
✅ **Easy to debug** - Separate pipeline makes it easy to troubleshoot  

---

## How It Works

### Architecture

```
SharePoint Files
    │
    ├── PDF, DOCX, XLSX, TXT → Main Vectorstore (normal ingestion)
    │
    └── PPTX files → Separate Pipeline → JSON/Text files (separate storage)
```

### Flow

1. **SharePoint Scanner** detects PPTX files during normal ingestion
2. **PPTX Processor** extracts slide content separately (if enabled)
3. **Content Saved** to `./data/pptx_extracted/` as JSON files
4. **Main Ingestion** skips PPTX files (they're already extracted separately)

---

## Configuration

Add these to your `.env` file:

```bash
# Enable separate PPTX extraction pipeline
ENABLE_PPTX_PIPELINE=true

# Output directory for extracted PPTX content
PPTX_OUTPUT_DIR=./data/pptx_extracted

# Output format: "json" or "text"
PPTX_SAVE_FORMAT=json
```

### Options

- **`ENABLE_PPTX_PIPELINE`**: Set to `true` to enable separate PPTX extraction
- **`PPTX_OUTPUT_DIR`**: Where to save extracted PPTX content (default: `./data/pptx_extracted`)
- **`PPTX_SAVE_FORMAT`**: Output format - `json` (structured) or `text` (plain text)

---

## Installation

### Required Dependencies

The PPTX processor supports two extraction methods:

#### Option 1: python-pptx (Recommended - Fast & Native)

```bash
pip install python-pptx
```

#### Option 2: Unstructured Library (Fallback)

```bash
pip install "unstructured[pptx]"
```

**Note**: The processor will automatically use `python-pptx` if available, falling back to `unstructured` if not.

---

## Usage

### Automatic Extraction (During Normal Ingestion)

When `ENABLE_PPTX_PIPELINE=true`, PPTX files are automatically extracted during SharePoint ingestion:

```bash
# Normal ingestion will now extract PPTX separately
python -m app.vectorstore  # or your ingestion script
```

**Output**: PPTX files are extracted and saved to `PPTX_OUTPUT_DIR` as JSON files.

### Standalone Extraction Script

You can also run PPTX extraction independently:

```bash
python scripts/extract_pptx_from_sharepoint.py
```

This script:
- Scans SharePoint for all PPTX files
- Extracts slide content from each file
- Saves results as JSON files
- Provides a summary report

---

## Output Format

### JSON Format (Default)

Each extracted PPTX file creates a JSON file with:

```json
{
  "file_name": "Presentation.pptx",
  "file_path": "/path/to/file.pptx",
  "extraction_date": "2025-12-22T15:30:00",
  "total_slides": 25,
  "slides_with_content": 23,
  "slides": [
    {
      "slide_number": 1,
      "content": "# Title\n\nBullet point 1\nBullet point 2",
      "notes": "Speaker notes if available",
      "has_content": true
    },
    ...
  ],
  "combined_content": "--- Slide 1 ---\n...\n--- Slide 2 ---\n...",
  "metadata": {
    "source": "sharepoint_sales",
    "file_url": "https://...",
    "folder_path": "Documents > Presentations"
  }
}
```

### Text Format

If `PPTX_SAVE_FORMAT=text`, output is plain text:

```
File: Presentation.pptx
Total Slides: 25
Extraction Date: 2025-12-22T15:30:00

================================================================================

--- Slide 1 ---
# Title
Bullet point 1
Bullet point 2

--- Slide 2 ---
...
```

---

## Integration with Main Pipeline

### During SharePoint Ingestion

When the SharePoint extractor encounters a PPTX file:

1. **If `ENABLE_PPTX_PIPELINE=true`**:
   - Downloads PPTX file bytes
   - Extracts slide content using PPTX processor
   - Saves to `PPTX_OUTPUT_DIR`
   - **Skips from main ingestion** (continues to next file)

2. **If `ENABLE_PPTX_PIPELINE=false`**:
   - Logs: `[INFO] Skipping binary file content for *.pptx`
   - Creates metadata-only document (file name, folder path)
   - Adds to main vectorstore (no slide content)

### Benefits

- **Main vectorstore stays clean** - No PPTX slide content mixed in
- **PPTX content available separately** - Can be queried/searchable later
- **No performance impact** - Extraction happens in parallel, doesn't slow ingestion

---

## Future Enhancements

### Optional: PPTX Vectorstore

You can create a separate vectorstore for PPTX content:

```python
from app.pptx_processor import PPTXProcessor
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

# Load extracted PPTX files
processor = PPTXProcessor()
extractions = processor.batch_extract_directory("./data/pptx_extracted")

# Create documents from extractions
documents = []
for ext in extractions:
    # Create document per slide or combined
    doc = Document(
        page_content=ext["combined_content"],
        metadata=ext["metadata"]
    )
    documents.append(doc)

# Create separate vectorstore
embeddings = OpenAIEmbeddings()
pptx_vectorstore = Chroma.from_documents(documents, embeddings, persist_directory="./data/pptx_vectorstore")
```

### Optional: Slide Summarization

Before embedding, you can summarize slides:

```python
# Summarize each slide
for slide in extraction["slides"]:
    summary = llm.summarize(slide["content"])
    slide["summary"] = summary

# Then embed summaries instead of full content
```

---

## Troubleshooting

### Issue: "python-pptx not available"

**Solution**: Install python-pptx:
```bash
pip install python-pptx
```

The processor will fall back to `unstructured` if available.

### Issue: "No PPTX files extracted"

**Check**:
1. Is `ENABLE_PPTX_PIPELINE=true` in `.env`?
2. Are there PPTX files in SharePoint?
3. Check logs for extraction errors

### Issue: "Extraction returns empty content"

**Possible causes**:
- PPTX file is image-only (no text)
- Corrupted PPTX file
- Protected/encrypted PPTX file

**Solution**: Check the PPTX file manually. The processor will still save metadata even if content extraction fails.

---

## Files Created

### Core Files

- **`app/pptx_processor.py`** - Main PPTX extraction processor
- **`scripts/extract_pptx_from_sharepoint.py`** - Standalone extraction script
- **`config.py`** - Configuration options (ENABLE_PPTX_PIPELINE, etc.)

### Modified Files

- **`app/sharepoint_graph_extractor.py`** - Added PPTX detection and separate extraction
- **`app/vectorstore.py`** - (No changes needed - works automatically)

---

## Summary

✅ **Separate PPTX pipeline implemented**  
✅ **Automatic extraction during ingestion**  
✅ **Configurable via environment variables**  
✅ **Outputs structured JSON files**  
✅ **No impact on main vectorstore**  
✅ **Standalone script available**  

**Next Steps**:
1. Set `ENABLE_PPTX_PIPELINE=true` in your `.env`
2. Install `python-pptx`: `pip install python-pptx`
3. Run normal ingestion - PPTX files will be extracted separately
4. Check `./data/pptx_extracted/` for extracted content

