#!/usr/bin/env python3
"""
MongoDB Cleanup Script: Remove Bad Sessions

This script removes sessions with invalid identity:
- Missing email
- Empty email
- Email = "USER" (default fallback)
- user_id != email (inconsistent identity)

⚠️ WARNING: Run this ONCE after deploying identity fixes.
This cleans up corrupted sessions created before the fix.

Usage:
    python scripts/cleanup_bad_sessions.py [--yes]
    
    --yes: Skip confirmation prompt (non-interactive)
"""

import os
import sys
import argparse
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Add parent directory to path to import config
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from config import MONGODB_URL, MONGODB_DATABASE

async def cleanup_bad_sessions(skip_confirmation=False):
    """Remove sessions with invalid identity.
    
    Args:
        skip_confirmation: If True, skip user confirmation prompt
    """
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    collection = db["app_sessions"]
    
    print("[SCAN] Scanning for bad sessions...")
    
    # Find bad sessions
    bad_sessions_query = {
        "$or": [
            {"user_email": None},
            {"user_email": ""},
            {"user_email": {"$regex": "^USER$", "$options": "i"}},
            {"user_email": {"$exists": False}},
            # Sessions where user_id != email (inconsistent)
            {"$expr": {"$ne": ["$user_id", {"$toLower": "$user_email"}]}}
        ]
    }
    
    bad_sessions = await collection.find(bad_sessions_query).to_list(length=None)
    count = len(bad_sessions)
    
    if count == 0:
        print("[OK] No bad sessions found. Database is clean!")
        return
    
    print(f"[WARN] Found {count} bad session(s):")
    for session in bad_sessions[:10]:  # Show first 10
        print(f"  - Session: {session.get('session_id', 'N/A')[:8]}...")
        print(f"    Email: {session.get('user_email', 'MISSING')}")
        print(f"    User ID: {session.get('user_id', 'MISSING')}")
    
    if count > 10:
        print(f"  ... and {count - 10} more")
    
    # Ask for confirmation (unless skipped)
    if not skip_confirmation:
        print(f"\n[WARN] This will DELETE {count} bad session(s).")
        response = input("Continue? (yes/no): ").strip().lower()
        
        if response != "yes":
            print("[CANCELLED] Cleanup cancelled.")
            return
    else:
        print(f"\n[INFO] Auto-confirmed: Will DELETE {count} bad session(s).")
    
    # Delete bad sessions
    result = await collection.delete_many(bad_sessions_query)
    deleted_count = result.deleted_count
    
    print(f"[OK] Deleted {deleted_count} bad session(s).")
    print(f"[INFO] Remaining sessions: {await collection.count_documents({})}")
    
    # Also check chat_sessions collection
    print("\n[SCAN] Checking chat_sessions collection...")
    chat_sessions_collection = db["chat_sessions"]
    
    bad_chat_sessions_query = {
        "$or": [
            {"user_email": None},
            {"user_email": ""},
            {"user_email": {"$regex": "^USER$", "$options": "i"}},
            {"user_email": {"$exists": False}},
            {"user_id": None},
            {"user_id": ""},
            {"user_id": {"$exists": False}}
        ]
    }
    
    bad_chat_sessions = await chat_sessions_collection.find(bad_chat_sessions_query).to_list(length=None)
    chat_count = len(bad_chat_sessions)
    
    if chat_count > 0:
        print(f"[WARN] Found {chat_count} bad chat session(s)")
        if not skip_confirmation:
            response = input("Delete bad chat sessions? (yes/no): ").strip().lower()
        else:
            response = "yes"
            print("[INFO] Auto-confirmed: Will delete bad chat sessions.")
        
        if response == "yes":
            chat_result = await chat_sessions_collection.delete_many(bad_chat_sessions_query)
            print(f"[OK] Deleted {chat_result.deleted_count} bad chat session(s).")
        else:
            print("[SKIP] Skipped chat sessions cleanup.")
    else:
        print("[OK] No bad chat sessions found.")
    
    client.close()
    print("\n[OK] Cleanup complete!")

if __name__ == "__main__":
    import asyncio
    
    parser = argparse.ArgumentParser(description="Cleanup bad MongoDB sessions")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt (non-interactive mode)"
    )
    args = parser.parse_args()
    
    asyncio.run(cleanup_bad_sessions(skip_confirmation=args.yes))

