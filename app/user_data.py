# -*- coding: utf-8 -*-
"""
User Data Helper Module

Loads and provides access to user data from cloudfuze_users.json
"""

import json
import os
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Cache for users data
_users_data: Optional[Dict] = None
_users_by_email: Optional[Dict[str, Dict]] = None


def _load_users_data():
    """Load users.json file and cache it."""
    global _users_data, _users_by_email
    
    if _users_data is not None:
        return _users_data
    
    try:
        # Get the path to users.json (in scripts directory)
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        users_file = os.path.join(script_dir, "scripts", "cloudfuze_users.json")
        
        if not os.path.exists(users_file):
            logger.warning(f"Users file not found: {users_file}")
            _users_data = {"users": []}
            _users_by_email = {}
            return _users_data
        
        with open(users_file, 'r', encoding='utf-8') as f:
            _users_data = json.load(f)
        
        # Build email lookup dictionary for fast access
        _users_by_email = {}
        for user in _users_data.get("users", []):
            email = user.get("mail") or user.get("userPrincipalName", "")
            if email:
                _users_by_email[email.lower().strip()] = user
        
        logger.info(f"Loaded {len(_users_by_email)} users from {users_file}")
        return _users_data
        
    except Exception as e:
        logger.error(f"Error loading users.json: {e}")
        _users_data = {"users": []}
        _users_by_email = {}
        return _users_data


def get_user_job_title(email: str) -> Optional[str]:
    """
    Get job title for a user by email.
    
    Args:
        email: User email address
        
    Returns:
        Job title string or None if not found
    """
    if not email:
        return None
    
    _load_users_data()
    
    if _users_by_email is None:
        return None
    
    email_lower = email.lower().strip()
    user = _users_by_email.get(email_lower)
    
    if user:
        job_title = user.get("jobTitle")
        return job_title if job_title else None
    
    return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """
    Get full user data by email.
    
    Args:
        email: User email address
        
    Returns:
        User dictionary or None if not found
    """
    if not email:
        return None
    
    _load_users_data()
    
    if _users_by_email is None:
        return None
    
    email_lower = email.lower().strip()
    return _users_by_email.get(email_lower)


def reload_users_data():
    """Force reload of users data (useful for testing or updates)."""
    global _users_data, _users_by_email
    _users_data = None
    _users_by_email = None
    _load_users_data()

