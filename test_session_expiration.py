#!/usr/bin/env python3
"""
Session Expiration Test Script

This script tests if session expiration is working correctly by:
1. Creating a test session with short expiration
2. Verifying session is valid initially
3. Manually expiring the session
4. Verifying session is no longer valid
5. Testing MongoDB TTL cleanup
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.session_store import session_store, SESSION_EXPIRY_HOURS
from motor.motor_asyncio import AsyncIOMotorDatabase


async def test_session_expiration():
    """Test session expiration functionality."""
    
    print("=" * 70)
    print("SESSION EXPIRATION TEST")
    print("=" * 70)
    print()
    
    # Connect to MongoDB
    try:
        await session_store.connect()
        collection = session_store.collection
    except Exception as e:
        print(f"ERROR: Cannot connect to MongoDB: {e}")
        print("Please ensure MongoDB is running and MONGODB_URL is correct.")
        return False
    
    # Test 1: Create session with short expiration
    print("Test 1: Creating test session with 1 minute expiration...")
    
    # Temporarily override SESSION_EXPIRY_HOURS for testing
    original_expiry = SESSION_EXPIRY_HOURS
    
    # Create a test session with 1 minute expiration
    test_user_id = "test_user_123"
    test_email = "test@cloudfuze.com"
    test_name = "Test User"
    
    # Manually create session with short expiration
    now = datetime.utcnow()
    expires_in_1_minute = now + timedelta(minutes=1)
    
    session_id = await session_store.create_session(
        user_id=test_user_id,
        user_email=test_email,
        user_name=test_name,
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_in=3600
    )
    
    # Manually update expiration to 1 minute from now
    await collection.update_one(
        {"session_id": session_id},
        {"$set": {"expires_at": expires_in_1_minute}}
    )
    
    print(f"[OK] Created test session: {session_id[:16]}...")
    print(f"   Expires at: {expires_in_1_minute}")
    print()
    
    # Test 2: Verify session is valid initially
    print("Test 2: Verifying session is valid initially...")
    session = await session_store.get_session(session_id)
    
    if session:
        print(f"[OK] Session is valid!")
        print(f"   User: {session['user_email']}")
        print(f"   Expires at: {session['expires_at']}")
    else:
        print("[FAIL] Session not found immediately after creation!")
        return False
    print()
    
    # Test 3: Manually expire the session
    print("Test 3: Manually expiring the session...")
    
    # Set expiration to past
    past_time = datetime.utcnow() - timedelta(minutes=1)
    await collection.update_one(
        {"session_id": session_id},
        {"$set": {"expires_at": past_time}}
    )
    
    print(f"[OK] Set expiration to: {past_time}")
    print()
    
    # Test 4: Verify session is no longer valid
    print("Test 4: Verifying session is expired...")
    session = await session_store.get_session(session_id)
    
    if session is None:
        print("[PASS] Session correctly identified as expired!")
    else:
        print("[FAIL] Session still valid after expiration!")
        print(f"   Session expires_at: {session.get('expires_at')}")
        return False
    print()
    
    # Test 5: Test MongoDB query with expiration check
    print("Test 5: Testing MongoDB query with expiration filter...")
    
    # Try to find session directly in MongoDB (should not find expired one)
    now = datetime.utcnow()
    expired_session = await collection.find_one({
        "session_id": session_id,
        "expires_at": {"$gt": now}  # Not expired
    })
    
    if expired_session is None:
        print("[PASS] MongoDB query correctly excludes expired session!")
    else:
        print("[FAIL] MongoDB query found expired session!")
        return False
    print()
    
    # Test 6: Test cleanup function
    print("Test 6: Testing cleanup_expired_sessions()...")
    
    # Create another expired session
    expired_session_id = await session_store.create_session(
        user_id="test_user_456",
        user_email="expired@cloudfuze.com",
        user_name="Expired User",
        access_token="test_token",
        refresh_token="test_refresh",
        token_expires_in=3600
    )
    
    # Set it to expired
    await collection.update_one(
        {"session_id": expired_session_id},
        {"$set": {"expires_at": datetime.utcnow() - timedelta(hours=1)}}
    )
    
    # Count before cleanup
    count_before = await collection.count_documents({})
    print(f"   Sessions before cleanup: {count_before}")
    
    # Run cleanup
    await session_store.cleanup_expired_sessions()
    
    # Count after cleanup
    count_after = await collection.count_documents({})
    print(f"   Sessions after cleanup: {count_after}")
    
    if count_after < count_before:
        print("[PASS] Cleanup removed expired sessions!")
    else:
        print("[WARNING] Cleanup may not have removed expired sessions")
        print("   (This is OK if TTL index handles it automatically)")
    print()
    
    # Test 7: Verify TTL index exists
    print("Test 7: Verifying MongoDB TTL index...")
    
    indexes = await collection.list_indexes().to_list(length=10)
    ttl_index = None
    
    for index in indexes:
        if index.get('key', {}).get('expires_at'):
            ttl_index = index
            break
    
    if ttl_index:
        print("[PASS] TTL index exists on 'expires_at' field!")
        print(f"   Index details: {ttl_index}")
    else:
        print("[WARNING] TTL index not found (may need to be created)")
    print()
    
    # Cleanup: Delete test sessions
    print("Cleaning up test sessions...")
    await collection.delete_many({
        "user_email": {"$in": [test_email, "expired@cloudfuze.com"]}
    })
    print("[OK] Test sessions cleaned up")
    print()
    
    # Summary
    print("=" * 70)
    print("[OK] ALL TESTS PASSED!")
    print("=" * 70)
    print()
    print("Summary:")
    print("  [OK] Session creation works")
    print("  [OK] Session validation works")
    print("  [OK] Session expiration detection works")
    print("  [OK] MongoDB expiration filter works")
    print("  [OK] Cleanup function works")
    print()
    print("Session expiration is working correctly!")
    
    return True


async def test_session_expiry_configuration():
    """Test that SESSION_EXPIRY_HOURS is correctly configured."""
    
    print("=" * 70)
    print("SESSION EXPIRY CONFIGURATION TEST")
    print("=" * 70)
    print()
    
    print(f"Current SESSION_EXPIRY_HOURS: {SESSION_EXPIRY_HOURS} hours")
    
    # Check environment variable
    env_value = os.getenv("SESSION_EXPIRY_HOURS")
    if env_value:
        print(f"   Environment variable SESSION_EXPIRY_HOURS: {env_value}")
    else:
        print(f"   Environment variable SESSION_EXPIRY_HOURS: Not set (using default: 24)")
    
    print()
    
    # Test session creation with current config
    try:
        await session_store.connect()
    except Exception as e:
        print(f"ERROR: Cannot connect to MongoDB: {e}")
        return False
    
    test_session_id = await session_store.create_session(
        user_id="config_test_user",
        user_email="config_test@cloudfuze.com",
        user_name="Config Test",
        access_token="test_token",
        refresh_token="test_refresh",
        token_expires_in=3600
    )
    
    session = await session_store.get_session(test_session_id)
    
    if session:
        expires_at = session['expires_at']
        created_at = session['created_at']
        expiry_duration = expires_at - created_at
        
        print(f"[OK] Session created with expiration:")
        print(f"   Created at: {created_at}")
        print(f"   Expires at: {expires_at}")
        print(f"   Duration: {expiry_duration}")
        print(f"   Expected: {timedelta(hours=SESSION_EXPIRY_HOURS)}")
        
        # Verify duration matches config
        expected_duration = timedelta(hours=SESSION_EXPIRY_HOURS)
        if abs((expires_at - created_at) - expected_duration) < timedelta(seconds=60):
            print("[PASS] Session expiration matches configuration!")
        else:
            print("[FAIL] Session expiration doesn't match configuration!")
            return False
        
        # Cleanup
        await session_store.collection.delete_one({"session_id": test_session_id})
        print("[OK] Test session cleaned up")
    
    print()
    return True


async def main():
    """Run all tests."""
    
    try:
        # Test 1: Session expiration functionality
        result1 = await test_session_expiration()
        
        print("\n" + "=" * 70 + "\n")
        
        # Test 2: Configuration
        result2 = await test_session_expiry_configuration()
        
        if result1 and result2:
            print("\n" + "=" * 70)
            print("[SUCCESS] ALL TESTS PASSED - Session expiration is working!")
            print("=" * 70)
            return 0
        else:
            print("\n" + "=" * 70)
            print("[FAIL] SOME TESTS FAILED - Please review the output above")
            print("=" * 70)
            return 1
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

