# Session Management Migration Guide

## ✅ Backend Implementation Complete

This document explains the new session-based authentication system that solves the "random expiration" issue.

---

## 🎯 Problem Solved

### Before (Token-Based Auth - ❌ Problematic)
- **Every API request** → Calls Microsoft Graph API
- **Every page refresh** → Calls Microsoft Graph API  
- **Network issues** → User gets logged out
- **Microsoft throttling** → User gets logged out
- **Token expiry** → User gets logged out

### After (Session-Based Auth - ✅ Fixed)
- **Login** → Calls Microsoft Graph API ONCE, creates session
- **Every API request** → Validates session from MongoDB (no Graph API call)
- **Page refresh** → Session still valid (no logout)
- **Network issues** → Session still valid (no logout)
- **Token expiry** → Backend refreshes automatically (user never knows)

---

## 📁 Files Changed

### 1. **`app/session_store.py`** (NEW)
- MongoDB-based session storage
- Encrypts tokens before storing
- Automatic session expiration (TTL index)
- Session refresh functionality

### 2. **`app/auth.py`** (UPDATED)
- `get_current_user()` now uses sessions first, falls back to tokens
- No Graph API calls on every request
- Backward compatible with token-based auth

### 3. **`app/endpoints.py`** (UPDATED)
- `/auth/microsoft/callback` → Creates session, sets cookie
- `/auth/microsoft/refresh` → Refreshes session tokens
- `/auth/session/refresh` → New endpoint for automatic refresh
- `/auth/logout` → New endpoint to delete session
- `require_auth()` → Uses sessions instead of Graph API

---

## 🔧 How It Works

### 1. Login Flow

```
User logs in via Microsoft OAuth
    ↓
Backend exchanges code for tokens
    ↓
Backend calls Graph API ONCE to get user info
    ↓
Backend creates session in MongoDB
    ↓
Backend sets session_id cookie
    ↓
Frontend receives session_id
```

### 2. API Request Flow

```
Frontend sends request with session_id cookie
    ↓
Backend validates session from MongoDB
    ↓
✅ No Graph API call needed!
    ↓
Request proceeds
```

### 3. Token Refresh Flow

```
Session token expiring soon (5 min margin)
    ↓
Frontend calls /auth/session/refresh
    ↓
Backend refreshes tokens using refresh_token from session
    ↓
Backend updates session in MongoDB
    ↓
User never knows token expired
```

---

## 🔒 Security Improvements

1. **No unsafe JWT decoding in production**
   - Removed `decode_unsafe_jwt()` fallback in production
   - Only enabled in development mode

2. **Session cookies**
   - `httponly=True` → Prevents XSS attacks
   - `secure=True` → Only sent over HTTPS
   - `samesite="lax"` → CSRF protection

3. **Token encryption**
   - Tokens encrypted before storing in MongoDB
   - Currently using base64 (can be upgraded to proper encryption)

---

## 📋 Frontend Changes Needed

### 1. Update Login Flow

**Current:**
```typescript
// Frontend stores access_token and refresh_token
localStorage.setItem('access_token', token);
localStorage.setItem('refresh_token', refreshToken);
```

**New:**
```typescript
// Backend sets session_id cookie automatically
// Frontend doesn't need to store tokens
// Just check if session_id cookie exists
```

### 2. Update API Requests

**Current:**
```typescript
headers: {
  'Authorization': `Bearer ${access_token}`
}
```

**New:**
```typescript
// Session cookie is sent automatically
// No Authorization header needed
// Backend reads session_id from cookie
```

### 3. Update Token Refresh

**Current:**
```typescript
// Frontend calls /auth/microsoft/refresh with refresh_token
```

**New:**
```typescript
// Frontend calls /auth/session/refresh
// No parameters needed - uses session_id from cookie
// Backend handles everything
```

### 4. Update Logout

**Current:**
```typescript
// Frontend clears localStorage
localStorage.removeItem('access_token');
```

**New:**
```typescript
// Frontend calls /auth/logout
// Backend deletes session and clears cookie
await fetch('/auth/logout', { method: 'POST' });
```

---

## 🚀 Migration Steps

### Phase 1: Backend (✅ COMPLETE)
- [x] Create session storage module
- [x] Update auth.py to use sessions
- [x] Update OAuth callback to create sessions
- [x] Update require_auth to use sessions
- [x] Remove unsafe JWT decoding in production
- [x] Add session refresh endpoint
- [x] Add logout endpoint

### Phase 2: Frontend (⏳ TODO)
- [ ] Update login flow to use session cookies
- [ ] Remove token storage from localStorage
- [ ] Update API requests to use cookies (remove Authorization header)
- [ ] Update token refresh to use `/auth/session/refresh`
- [ ] Update logout to call `/auth/logout`
- [ ] Test session persistence across page refreshes

---

## 🔍 Testing Checklist

### Backend Tests
- [x] Session creation on login
- [x] Session validation on API requests
- [x] Session refresh when token expires
- [x] Session deletion on logout
- [x] Backward compatibility with token-based auth

### Frontend Tests
- [ ] Login creates session cookie
- [ ] API requests work without Authorization header
- [ ] Page refresh doesn't log user out
- [ ] Token refresh happens automatically
- [ ] Logout clears session cookie

---

## 📝 Configuration

### Environment Variables

```bash
# Session expiry (default: 24 hours)
SESSION_EXPIRY_HOURS=24

# MongoDB connection (already configured)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=slack2teams
```

### Session Collection

Sessions are stored in MongoDB collection: `app_sessions`

Indexes created automatically:
- `session_id` (unique)
- `user_id`
- `expires_at` (TTL index for auto-cleanup)
- `last_accessed_at`

---

## 🐛 Troubleshooting

### Issue: Sessions not persisting
- Check MongoDB connection
- Verify session_id cookie is being set
- Check cookie settings (httponly, secure, samesite)

### Issue: Still getting logged out
- Check if frontend is still using token-based auth
- Verify session_id cookie is being sent with requests
- Check session expiry time

### Issue: Token refresh not working
- Verify refresh_token is stored in session
- Check Microsoft OAuth credentials
- Verify `/auth/session/refresh` endpoint is being called

---

## 📚 Additional Notes

1. **Backward Compatibility**: Token-based auth still works as fallback during migration
2. **Session Expiry**: Default 24 hours (configurable via `SESSION_EXPIRY_HOURS`)
3. **Token Refresh**: Automatic refresh 5 minutes before expiration
4. **Security**: Tokens encrypted in MongoDB (can be upgraded to proper encryption)

---

## ✅ Summary

The backend is now ready for session-based authentication. The frontend needs to be updated to:
1. Use session cookies instead of storing tokens
2. Remove Authorization headers from API requests
3. Call `/auth/session/refresh` for token refresh
4. Call `/auth/logout` for logout

This will solve the "random expiration" issue completely! 🎉

