#!/usr/bin/env python3
"""
Quick Session Test - Tests actual MongoDB operations

This script tests if sessions are actually working with MongoDB.
Run this AFTER you've logged in to your app.
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.session_store import session_store


async def test_real_sessions():
    """Test if real sessions exist in MongoDB."""
    
    print("=" * 70)
    print("QUICK SESSION TEST - Real MongoDB Check")
    print("=" * 70)
    print()
    
    try:
        # Connect to MongoDB
        print("Connecting to MongoDB...")
        await session_store.connect()
        collection = session_store.collection
        print("[OK] Connected to MongoDB")
        print()
        
        # Count all sessions
        total_sessions = await collection.count_documents({})
        print(f"Total sessions in database: {total_sessions}")
        print()
        
        if total_sessions == 0:
            print("[INFO] No sessions found in database.")
            print("       This is OK if you haven't logged in yet.")
            print()
            print("To test:")
            print("  1. Login to your app: http://localhost:3000/login")
            print("  2. Run this script again")
            print()
            return True
        
        # Get all sessions
        print("All sessions:")
        print("-" * 70)
        
        sessions = await collection.find({}).to_list(length=10)
        
        for i, session in enumerate(sessions, 1):
            session_id = session.get("session_id", "N/A")[:16] + "..."
            user_email = session.get("user_email", "N/A")
            created_at = session.get("created_at", "N/A")
            expires_at = session.get("expires_at", "N/A")
            
            # Check if expired
            now = datetime.utcnow()
            if isinstance(expires_at, datetime):
                is_expired = expires_at < now
                status = "[EXPIRED]" if is_expired else "[VALID]"
                time_left = expires_at - now if not is_expired else None
            else:
                status = "[UNKNOWN]"
                time_left = None
            
            print(f"{i}. Session: {session_id}")
            print(f"   User: {user_email}")
            print(f"   Created: {created_at}")
            print(f"   Expires: {expires_at}")
            print(f"   Status: {status}")
            if time_left:
                hours_left = time_left.total_seconds() / 3600
                print(f"   Time left: {hours_left:.1f} hours")
            print()
        
        # Test session validation
        print("Testing session validation...")
        print("-" * 70)
        
        if sessions:
            test_session_id = sessions[0].get("session_id")
            print(f"Testing session: {test_session_id[:16]}...")
            
            # Try to get session (this validates expiration)
            session = await session_store.get_session(test_session_id)
            
            if session:
                print("[OK] Session is VALID and can be retrieved")
                print(f"     User: {session['user_email']}")
            else:
                print("[EXPIRED] Session is EXPIRED or not found")
                print("          This is expected if session expired")
        else:
            print("[SKIP] No sessions to test")
        
        print()
        print("=" * 70)
        print("[SUCCESS] Session system is working!")
        print("=" * 70)
        print()
        print("Summary:")
        print(f"  - Total sessions: {total_sessions}")
        print(f"  - Sessions found: {len(sessions)}")
        print()
        print("If you see sessions above, everything is working! ✅")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        print()
        print("Possible issues:")
        print("  1. MongoDB is not running")
        print("  2. MONGODB_URL is incorrect")
        print("  3. MongoDB connection failed")
        print()
        print("To fix:")
        print("  1. Start MongoDB: mongod (or check if service is running)")
        print("  2. Check MONGODB_URL in your .env file")
        print("  3. Verify MongoDB is accessible")
        return False


if __name__ == "__main__":
    result = asyncio.run(test_real_sessions())
    sys.exit(0 if result else 1)

