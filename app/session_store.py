# -*- coding: utf-8 -*-
"""
Backend Session Storage Module

Implements server-side session management using MongoDB.
Sessions are created on login and validated on every request without calling Microsoft Graph API.

This solves the "random expiration" issue by:
1. Creating a session ONCE during login (Graph API called only here)
2. Storing session in MongoDB with expiration
3. Validating sessions from MongoDB on every request (no Graph API calls)
4. Refreshing tokens in the background without user interruption
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
import secrets
import hashlib

logger = logging.getLogger(__name__)

# MongoDB connection
_mongodb_client: Optional[AsyncIOMotorClient] = None
_mongodb_database: Optional[AsyncIOMotorDatabase] = None

# Session configuration
SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))  # 24 hours default
SESSION_COLLECTION = "app_sessions"
TOKEN_REFRESH_MARGIN_MINUTES = 5  # Refresh token 5 minutes before expiration


class SessionStore:
    """
    Manages application sessions in MongoDB.
    
    Sessions contain:
    - session_id: Unique session identifier (sent to frontend as cookie)
    - user_id: Microsoft user ID
    - user_email: User email
    - user_name: User display name
    - access_token: Microsoft access token (encrypted)
    - refresh_token: Microsoft refresh token (encrypted)
    - token_expires_at: When access token expires
    - created_at: Session creation time
    - last_accessed_at: Last time session was used
    - expires_at: When session expires (longer than token expiry)
    """
    
    def __init__(self):
        self.client = None
        self.database = None
        self.collection = None
    
    async def connect(self):
        """Connect to MongoDB."""
        global _mongodb_client, _mongodb_database
        
        if _mongodb_client is None:
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            _mongodb_client = AsyncIOMotorClient(mongodb_url)
            _mongodb_database = _mongodb_client[os.getenv("MONGODB_DATABASE", "slack2teams")]
            logger.info(f"[SESSION] Connected to MongoDB: {mongodb_url}")
        
        self.client = _mongodb_client
        self.database = _mongodb_database
        self.collection = _mongodb_database[SESSION_COLLECTION]
        
        # Create indexes for performance
        await self.collection.create_index("session_id", unique=True)
        await self.collection.create_index("user_id")
        await self.collection.create_index("expires_at", expireAfterSeconds=0)  # TTL index
        await self.collection.create_index("last_accessed_at")
    
    async def create_session(
        self,
        user_id: str,
        user_email: str,
        user_name: str,
        access_token: str,
        refresh_token: str,
        token_expires_in: int = 3600  # seconds
    ) -> str:
        """
        Create a new session after successful Microsoft OAuth login.
        
        Args:
            user_id: Microsoft user ID
            user_email: User email
            user_name: User display name
            access_token: Microsoft access token
            refresh_token: Microsoft refresh token
            token_expires_in: Token expiration in seconds
            
        Returns:
            session_id: Unique session identifier to send to frontend
        """
        await self.connect()
        
        # Generate secure session ID
        session_id = self._generate_session_id()
        
        # Calculate expiration times
        now = datetime.utcnow()
        token_expires_at = now + timedelta(seconds=token_expires_in)
        session_expires_at = now + timedelta(hours=SESSION_EXPIRY_HOURS)
        
        # Encrypt tokens (simple base64 encoding for now - can be improved with proper encryption)
        # In production, use proper encryption library like cryptography
        encrypted_access_token = self._encrypt_token(access_token)
        encrypted_refresh_token = self._encrypt_token(refresh_token)
        
        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "user_email": user_email.lower(),  # Normalize email
            "user_name": user_name,
            "access_token": encrypted_access_token,
            "refresh_token": encrypted_refresh_token,
            "token_expires_at": token_expires_at,
            "created_at": now,
            "last_accessed_at": now,
            "expires_at": session_expires_at
        }
        
        await self.collection.insert_one(session_doc)
        logger.info(f"[SESSION] Created session for user: {user_email} (session_id: {session_id[:8]}...)")
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session by session_id.
        Updates last_accessed_at automatically.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session document or None if not found/expired
        """
        await self.connect()
        
        now = datetime.utcnow()
        
        # Find and update last_accessed_at atomically
        session = await self.collection.find_one_and_update(
            {
                "session_id": session_id,
                "expires_at": {"$gt": now}  # Not expired
            },
            {
                "$set": {"last_accessed_at": now}
            },
            return_document=True
        )
        
        if not session:
            logger.debug(f"[SESSION] Session not found or expired: {session_id[:8]}...")
            return None
        
        # Decrypt tokens
        session["access_token"] = self._decrypt_token(session["access_token"])
        session["refresh_token"] = self._decrypt_token(session["refresh_token"])
        
        return session
    
    async def refresh_session_tokens(
        self,
        session_id: str,
        new_access_token: str,
        new_refresh_token: str,
        token_expires_in: int = 3600
    ) -> bool:
        """
        Refresh access and refresh tokens for an existing session.
        Called when Microsoft access token expires.
        
        Args:
            session_id: Session identifier
            new_access_token: New Microsoft access token
            new_refresh_token: New Microsoft refresh token
            token_expires_in: New token expiration in seconds
            
        Returns:
            True if refresh succeeded, False otherwise
        """
        await self.connect()
        
        now = datetime.utcnow()
        token_expires_at = now + timedelta(seconds=token_expires_in)
        
        # Encrypt new tokens
        encrypted_access_token = self._encrypt_token(new_access_token)
        encrypted_refresh_token = self._encrypt_token(new_refresh_token)
        
        result = await self.collection.update_one(
            {
                "session_id": session_id,
                "expires_at": {"$gt": now}  # Session not expired
            },
            {
                "$set": {
                    "access_token": encrypted_access_token,
                    "refresh_token": encrypted_refresh_token,
                    "token_expires_at": token_expires_at,
                    "last_accessed_at": now
                }
            }
        )
        
        if result.modified_count > 0:
            logger.info(f"[SESSION] Refreshed tokens for session: {session_id[:8]}...")
            return True
        else:
            logger.warning(f"[SESSION] Failed to refresh tokens for session: {session_id[:8]}...")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session (logout).
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        await self.connect()
        
        result = await self.collection.delete_one({"session_id": session_id})
        
        if result.deleted_count > 0:
            logger.info(f"[SESSION] Deleted session: {session_id[:8]}...")
            return True
        return False
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions (called periodically)."""
        await self.connect()
        
        now = datetime.utcnow()
        result = await self.collection.delete_many({"expires_at": {"$lt": now}})
        
        if result.deleted_count > 0:
            logger.info(f"[SESSION] Cleaned up {result.deleted_count} expired sessions")
    
    def _generate_session_id(self) -> str:
        """Generate a secure random session ID."""
        # Generate 32 bytes of random data
        random_bytes = secrets.token_bytes(32)
        # Convert to hex string (64 characters)
        return random_bytes.hex()
    
    def _encrypt_token(self, token: str) -> str:
        """
        Encrypt token for storage.
        
        NOTE: This is a simple implementation. For production, use proper encryption
        like Fernet from cryptography library with a secret key.
        """
        # Simple base64 encoding for now (can be improved)
        import base64
        return base64.b64encode(token.encode()).decode()
    
    def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from storage."""
        import base64
        return base64.b64decode(encrypted_token.encode()).decode()


# Global session store instance
session_store = SessionStore()

