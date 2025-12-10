# Share Functionality - Production Deployment Guide

## Overview
This guide explains how the Share functionality handles different scenarios in a production environment.

---

## 1. DEPLOYMENT INFRASTRUCTURE

### Frontend Deployment
**Technology**: Next.js (static + server-side rendering)
**Hosting Options**:
- Vercel (recommended - native Next.js support)
- AWS Amplify
- Self-hosted with Nginx/Apache

**Key Consideration**:
- Share links point to `http://localhost:3000` in development
- **In production**: Must point to actual domain (e.g., `https://app.cloudfuze.com`)

### Backend Deployment
**Technology**: FastAPI + Python
**Hosting Options**:
- AWS EC2 / ECS
- Google Cloud Run
- Azure Container Instances
- Self-hosted servers

**Key Consideration**:
- Backend must be accessible from users' machines
- CORS must be properly configured
- HTTPS required in production

### Database Deployment
**Technology**: MongoDB Atlas or Self-hosted MongoDB
**Requirements**:
- `shared_chats` collection with proper indexes
- Regular backups
- Connection string security

---

## 2. SHARE LINK GENERATION IN PRODUCTION

### Current Development Flow
```
Frontend (localhost:3000)
    ↓
Backend API (localhost:8002)
    ↓
MongoDB (local instance)
```

### Production Flow
```
Frontend (https://app.cloudfuze.com)
    ↓
Backend API (https://api.cloudfuze.com or same domain)
    ↓
MongoDB Atlas (cloud-hosted)
```

### Share Link Format

**Development**:
```
http://localhost:3000/chat/shared/f98d906d-d68e-42de-a415-e001e4afa0c9
```

**Production**:
```
https://app.cloudfuze.com/chat/shared/f98d906d-d68e-42de-a415-e001e4afa0c9
```

### Configuration Changes Needed

**File**: `frontend/src/lib/chat-initialization.ts`

**Current Code** (Line 752):
```typescript
const API_BASE_URL = getApiBase();
```

**getApiBase() function** (needs to be production-aware):
```typescript
function getApiBase(): string {
  if (typeof window === 'undefined') return '';
  
  // Development
  if (process.env.NODE_ENV === 'development') {
    return 'http://127.0.0.1:8002';
  }
  
  // Production
  const env = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://api.cloudfuze.com';
  return env;
}
```

**Environment Variables Setup**:

**.env.local** (development):
```
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8002
```

**.env.production** (production):
```
NEXT_PUBLIC_API_BASE_URL=https://api.cloudfuze.com
NEXT_PUBLIC_APP_URL=https://app.cloudfuze.com
```

---

## 3. SHARE LINK HANDLING IN PRODUCTION

### When User Clicks Share Button

**Step 1**: Frontend makes authenticated API call
```
POST https://api.cloudfuze.com/chat/share/{sessionId}
Headers: {
  Authorization: Bearer {user_token},
  Content-Type: application/json
}
```

**Step 2**: Backend validates and generates token
```python
# app/endpoints.py (no changes needed!)
@router.post("/chat/share/{session_id}")
async def share_chat_session(
    session_id: str,
    auth_user: dict = Depends(require_auth)
):
    # Validation happens here
    # Token generation here
    # MongoDB storage here
```

**Step 3**: Backend returns share URL
```json
{
  "share_token": "f98d906d-d68e-42de-a415-e001e4afa0c9",
  "share_url": "/chat/shared/f98d906d-d68e-42de-a415-e001e4afa0c9",
  "message": "Share link created successfully"
}
```

**Step 4**: Frontend builds full URL
```typescript
const shareUrl = `${window.location.origin}/chat/shared/${share_token}`;
// Result: https://app.cloudfuze.com/chat/shared/f98d906d-d68e-42de-a415-e001e4afa0c9
```

**Step 5**: Copy to clipboard (same as development)
```typescript
navigator.clipboard.writeText(shareUrl);
// Fallback to document.execCommand('copy') if needed
```

### When Recipient Opens Share Link

**Step 1**: Browser navigates to share link
```
https://app.cloudfuze.com/chat/shared/f98d906d-d68e-42de-a415-e001e4afa0c9
```

**Step 2**: Frontend route `/chat/shared/[token]/page.tsx` loads
- Extracts token from URL params
- Makes authenticated request to backend

**Step 3**: Backend retrieves shared chat
```
GET https://api.cloudfuze.com/chat/shared/f98d906d-d68e-42de-a415-e001e4afa0c9
Headers: {
  Authorization: Bearer {user_token}
}
```

**Step 4**: Backend returns chat data
- Validates token exists
- Checks token hasn't expired
- Returns original chat content

**Step 5**: Frontend displays chat in read-only mode
- Shows "Read-Only" badge
- Shows "Continue in this thread" button
- All security protections active

---

## 4. SECURITY CONSIDERATIONS IN PRODUCTION

### Authentication & Authorization

**Protected Endpoints**:
- ✅ `POST /chat/share/{session_id}` - Requires auth + ownership
- ✅ `GET /chat/shared/{share_token}` - Requires auth
- ✅ All message operations - Require auth

**Token Validation**:
```python
@router.post("/chat/share/{session_id}")
async def share_chat_session(
    session_id: str,
    auth_user: dict = Depends(require_auth)  # ← Validates Bearer token
):
    # Verify user owns the session
    session = await get_session_by_id(session_id)
    if session["user_id"] != auth_user["user_id"]:
        raise HTTPException(status_code=403)
```

### HTTPS/TLS Requirements

**Production Setup**:
```nginx
# Nginx configuration
server {
    listen 443 ssl http2;
    server_name app.cloudfuze.com;
    
    ssl_certificate /path/to/certificate.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://nextjs:3000;
    }
    
    location /api {
        proxy_pass https://api.cloudfuze.com;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name app.cloudfuze.com;
    return 301 https://$server_name$request_uri;
}
```

### CORS Configuration

**Backend (FastAPI)** - `server.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.cloudfuze.com",  # Production frontend
        "https://www.cloudfuze.com",  # With www
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Rate Limiting

**Recommendation**: Implement rate limiting on share endpoint
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/chat/share/{session_id}")
@limiter.limit("10/minute")  # Max 10 shares per minute
async def share_chat_session(...):
    # ... endpoint code ...
```

---

## 5. DATABASE HANDLING IN PRODUCTION

### MongoDB Atlas Setup

**Connection String**:
```
mongodb+srv://username:password@cluster0.mongodb.net/chatdb?retryWrites=true&w=majority
```

**Environment Variable**:
```bash
MONGODB_URI=mongodb+srv://username:password@cluster0.mongodb.net/chatdb
```

### Collection & Indexes

**Collection**: `shared_chats`

**Indexes Created Automatically** (in `mongodb_memory.py`):
```python
await shared_chats_collection.create_index("share_token", unique=True)
await shared_chats_collection.create_index("session_id")
await shared_chats_collection.create_index("user_email")
await shared_chats_collection.create_index("created_at")
```

### TTL Index for Expiration (Optional)

```python
# Auto-delete expired shares after 30 days
await shared_chats_collection.create_index(
    "created_at",
    expireAfterSeconds=2592000  # 30 days
)
```

---

## 6. DEPLOYMENT CHECKLIST

### Pre-Deployment

- [ ] Update `getApiBase()` to support production URLs
- [ ] Set environment variables in production
- [ ] Configure CORS for production domain
- [ ] Set up HTTPS/TLS certificates
- [ ] Test authentication flow
- [ ] Verify MongoDB Atlas connection
- [ ] Set up database backups
- [ ] Configure rate limiting
- [ ] Set up security headers (HSTS, CSP, etc.)
- [ ] Enable logging and monitoring

### Post-Deployment

- [ ] Test share link generation
- [ ] Test share link access with authentication
- [ ] Test read-only mode protection
- [ ] Test "Continue Thread" functionality
- [ ] Monitor error logs
- [ ] Check performance metrics
- [ ] Verify backups are working
- [ ] Set up alerting for errors

---

## 7. HANDLING DIFFERENT DEPLOYMENT SCENARIOS

### Scenario A: Same Domain Deployment
**Frontend**: `https://app.cloudfuze.com`
**Backend**: `https://app.cloudfuze.com/api`

**Changes Needed**:
```typescript
// Update API base URL
const API_BASE_URL = `${window.location.origin}/api`;
```

**Benefits**: Simpler CORS, easier deployment

### Scenario B: Separate Domains
**Frontend**: `https://app.cloudfuze.com`
**Backend**: `https://api.cloudfuze.com`

**Changes Needed**:
```typescript
// Use environment variable
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;
```

**Benefits**: Independent scaling, separate certificates

### Scenario C: Subdomain Deployment
**Frontend**: `https://chat.cloudfuze.com`
**Backend**: `https://api.cloudfuze.com`

**No additional changes** - Works with environment variables

---

## 8. TROUBLESHOOTING IN PRODUCTION

### Share Link Returns 404
**Cause**: Token not found in database
**Solution**: Check MongoDB connection, verify token was saved

### Clipboard Copy Fails
**Cause**: HTTPS + security restrictions
**Solution**: Already handled with fallback to toast notification

### Authentication Fails on Share
**Cause**: Token expired or invalid
**Solution**: User needs to log in again

### Share Link Opens But Chat Doesn't Load
**Cause**: API request failing
**Solution**: Check backend logs, verify API URL in environment

---

## 9. MONITORING & LOGGING

### Key Metrics to Monitor
```python
# In backend logs
- Share creation success/failure rate
- Share link access rate
- Average response time for share operations
- Failed authentication attempts
- Database connection issues
```

### Logging Setup
```python
import logging

logger = logging.getLogger(__name__)

@router.post("/chat/share/{session_id}")
async def share_chat_session(...):
    logger.info(f"Share created: {share_token} for user: {auth_user['email']}")
    logger.error(f"Share failed: {error_message}")
```

---

## 10. PRODUCTION DEPLOYMENT SUMMARY

| Component | Development | Production |
|-----------|-------------|-----------|
| Frontend URL | `http://localhost:3000` | `https://app.cloudfuze.com` |
| Backend URL | `http://localhost:8002` | `https://api.cloudfuze.com` |
| Database | Local MongoDB | MongoDB Atlas |
| HTTPS | ❌ No | ✅ Required |
| CORS | ✅ Loose | ✅ Restricted |
| Authentication | Bearer token | Bearer token + HTTPS |
| Rate Limiting | ❌ No | ✅ Recommended |
| Share Link | `http://localhost:3000/chat/shared/...` | `https://app.cloudfuze.com/chat/shared/...` |
| Clipboard | Browser dependent | Fallback support |
| Logging | Console | Aggregated logging service |

---

## Conclusion

The Share functionality will work seamlessly in production with minimal configuration changes:

1. **Update API base URL** - Point to production backend
2. **Set environment variables** - Domain URLs for both frontend and backend
3. **Configure CORS** - Allow production frontend domain
4. **Set up HTTPS** - Required for production
5. **Configure MongoDB Atlas** - Use production database
6. **Test thoroughly** - Verify all flows work

The architecture is **production-ready** and designed to scale.
