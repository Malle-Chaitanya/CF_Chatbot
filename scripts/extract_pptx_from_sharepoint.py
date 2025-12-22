"""
Standalone script to extract PPTX files from SharePoint separately.

This script can be run independently to extract all PPTX files from SharePoint
without affecting the main vectorstore ingestion.

Usage:
    python scripts/extract_pptx_from_sharepoint.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.sharepoint_graph_extractor import SharePointGraphExtractor
from app.pptx_processor import PPTXProcessor
from config import (
    ENABLE_SHAREPOINT_SALES_SOURCE,
    SHAREPOINT_SALES_SITE_URL,
    PPTX_OUTPUT_DIR
)
from urllib.parse import urlparse
import requests


def extract_all_pptx_from_sharepoint():
    """Extract all PPTX files from SharePoint Sales site."""
    
    if not ENABLE_SHAREPOINT_SALES_SOURCE:
        print("[ERROR] SharePoint Sales source is not enabled in config")
        print("Set ENABLE_SHAREPOINT_SALES_SOURCE=true in your .env file")
        return
    
    print("="*80)
    print("PPTX SEPARATE EXTRACTION PIPELINE")
    print("="*80)
    print(f"Source: {SHAREPOINT_SALES_SITE_URL}")
    print(f"Output Directory: {PPTX_OUTPUT_DIR}")
    print("="*80)
    
    # Initialize extractor
    extractor = SharePointGraphExtractor()
    
    # Extract site URL
    parsed_url = urlparse(SHAREPOINT_SALES_SITE_URL)
    path_parts = [p for p in parsed_url.path.split('/') if p]
    
    if 'sites' in path_parts:
        site_idx = path_parts.index('sites')
        if site_idx + 1 < len(path_parts):
            clean_site_url = f"{parsed_url.scheme}://{parsed_url.netloc}/sites/{path_parts[site_idx + 1]}"
            extractor.site_url = clean_site_url
            print(f"[*] Using site URL: {clean_site_url}")
    
    # Get site and drive IDs
    site_id = extractor.get_site_id()
    if not site_id:
        print("[ERROR] Failed to get site ID")
        return
    
    drive_id = extractor.get_drive_id()
    if not drive_id:
        print("[ERROR] Failed to get drive ID")
        return
    
    # Initialize PPTX processor
    processor = PPTXProcessor(output_dir=PPTX_OUTPUT_DIR)
    
    # Extract all files and process PPTX
    print("\n[*] Scanning SharePoint for PPTX files...")
    all_items = []
    
    def scan_folder(item_id=None, folder_path=None, visited_ids=None):
        """Recursively scan folders for PPTX files."""
        if visited_ids is None:
            visited_ids = set()
        
        if item_id and item_id in visited_ids:
            return []
        
        if item_id:
            visited_ids.add(item_id)
        
        items = extractor.list_items(item_id, folder_path or [])
        pptx_files = []
        
        for item in items:
            item_name = item.get('name', 'Unknown')
            item_id_current = item.get('id')
            item_type = 'folder' if 'folder' in item else 'file'
            web_url = item.get('webUrl', '')
            
            if item_type == 'file':
                file_ext = item_name.rsplit('.', 1)[-1].lower() if '.' in item_name else ''
                if file_ext in ['ppt', 'pptx']:
                    pptx_files.append({
                        'name': item_name,
                        'id': item_id_current,
                        'url': web_url,
                        'folder_path': folder_path or []
                    })
            elif item_type == 'folder':
                # Recursively scan subfolder
                next_folder_path = (folder_path or []) + [item_name]
                subfolder_pptx = scan_folder(item_id_current, next_folder_path, visited_ids)
                pptx_files.extend(subfolder_pptx)
        
        return pptx_files
    
    # Scan for all PPTX files
    pptx_files = scan_folder()
    
    print(f"[OK] Found {len(pptx_files)} PPTX files")
    
    if not pptx_files:
        print("[INFO] No PPTX files found in SharePoint")
        return
    
    # Process each PPTX file
    print("\n[*] Extracting PPTX files...")
    success_count = 0
    error_count = 0
    
    for i, pptx_file in enumerate(pptx_files, 1):
        print(f"\n[{i}/{len(pptx_files)}] Processing: {pptx_file['name']}")
        print(f"   Folder: {' > '.join(pptx_file['folder_path']) if pptx_file['folder_path'] else 'Documents'}")
        
        try:
            # Download PPTX file
            drive_id = extractor.get_drive_id()
            graph_url = f"{extractor.graph_base_url}/drives/{drive_id}/items/{pptx_file['id']}/content"
            from app.sharepoint_auth import sharepoint_auth
            headers = sharepoint_auth.get_headers()
            
            response = requests.get(graph_url, headers=headers, timeout=60, stream=True)
            
            if response.status_code == 200:
                pptx_bytes = response.content
                
                # Prepare metadata
                metadata = {
                    "source": "sharepoint_sales",
                    "file_name": pptx_file['name'],
                    "file_url": pptx_file['url'],
                    "folder_path": " > ".join(pptx_file['folder_path']) if pptx_file['folder_path'] else "Documents",
                    "webUrl": pptx_file['url'],
                    "site_url": str(extractor.site_url)
                }
                
                # Extract PPTX
                result = processor.process_pptx_from_bytes(pptx_bytes, pptx_file['name'], metadata)
                
                if result:
                    # Save extraction
                    processor.save_extraction(result, format="json")
                    print(f"   [OK] Extracted {result['total_slides']} slides")
                    success_count += 1
                else:
                    print(f"   [WARNING] Extraction returned no content")
                    error_count += 1
            else:
                print(f"   [ERROR] Failed to download: HTTP {response.status_code}")
                error_count += 1
                
        except Exception as e:
            print(f"   [ERROR] Failed to process {pptx_file['name']}: {e}")
            error_count += 1
    
    # Summary
    print("\n" + "="*80)
    print("EXTRACTION SUMMARY")
    print("="*80)
    print(f"Total PPTX files found: {len(pptx_files)}")
    print(f"Successfully extracted: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Output directory: {PPTX_OUTPUT_DIR}")
    print("="*80)


if __name__ == "__main__":
    extract_all_pptx_from_sharepoint()

