# Session-Based Authentication Workflow

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Complete Workflow](#complete-workflow)
4. [Files Involved](#files-involved)
5. [Production Configuration](#production-configuration)
6. [Code References](#code-references)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This document describes the **session-based authentication system** that replaced token-based authentication. The system uses:

- **Backend-managed sessions** stored in MongoDB
- **HttpOnly cookies** for security
- **Automatic token refresh** in the background
- **No frontend token storage** (tokens never leave the backend)

### Key Benefits

✅ **No random logouts** - Sessions persist across page refreshes  
✅ **Secure** - HttpOnly cookies prevent XSS attacks  
✅ **Scalable** - Sessions stored in MongoDB (can scale horizontally)  
✅ **User-friendly** - Seamless experience, tokens refresh automatically  
✅ **Production-ready** - Works with same-domain or cross-domain setups

---

## 🏗️ Architecture

### High-Level Flow

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │         │  Next.js     │         │  FastAPI   │
│             │         │  (Frontend)  │         │  (Backend) │
└──────┬──────┘         └──────┬───────┘         └──────┬──────┘
       │                      │                         │
       │  1. Login Request    │                         │
       ├─────────────────────>│                         │
       │                      │  2. OAuth Callback      │
       │                      ├────────────────────────>│
       │                      │                         │
       │                      │  3. Create Session      │
       │                      │     (MongoDB)           │
       │                      │<────────────────────────│
       │                      │                         │
       │  4. Set Cookie       │                         │
       │     (session_id)     │                         │
       │<─────────────────────┤                         │
       │                      │                         │
       │  5. API Requests     │                         │
       │     (with cookie)     │                         │
       ├─────────────────────>│                         │
       │                      │  6. Validate Session    │
       │                      ├────────────────────────>│
       │                      │     (MongoDB lookup)    │
       │                      │<────────────────────────│
       │  7. Response         │                         │
       │<─────────────────────┤                         │
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND (Next.js)                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐    ┌──────────────────┐                │
│  │  Login Page     │───>│  apiFetch()      │                │
│  │  (page.tsx)     │    │  (api.ts)        │                │
│  └──────────────────┘    └────────┬─────────┘                │
│                                    │                           │
│  ┌──────────────────┐    ┌─────────▼─────────┐                │
│  │  Chat Pages      │───>│  checkSession()   │                │
│  │  (new/page.tsx)  │    │  (session-utils)  │                │
│  └──────────────────┘    └──────────────────┘                │
│                                    │                           │
│                          ┌─────────▼─────────┐                 │
│                          │  Next.js Proxy   │                 │
│                          │  (/api/proxy/*)  │                 │
│                          └─────────┬─────────┘                 │
└────────────────────────────────────┼──────────────────────────┘
                                     │
                                     │ HTTP + Cookies
                                     │
┌────────────────────────────────────┼──────────────────────────┐
│                      BACKEND (FastAPI)                          │
├────────────────────────────────────┼──────────────────────────┤
│                                    │                           │
│  ┌──────────────────┐    ┌─────────▼─────────┐                │
│  │  OAuth Callback  │───>│  Session Store    │                │
│  │  (endpoints.py)  │    │  (session_store)  │                │
│  └──────────────────┘    └─────────┬─────────┘                │
│                                    │                           │
│  ┌──────────────────┐    ┌─────────▼─────────┐                │
│  │  require_auth()  │───>│     MongoDB      │                │
│  │  (endpoints.py)  │    │  (app_sessions)  │                │
│  └──────────────────┘    └──────────────────┘                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Workflow

### Phase 1: User Login

#### Step 1: User Initiates Login

**File:** `frontend/src/app/login/page.tsx`

```typescript
// User clicks "Sign in with Microsoft"
handleMicrosoftLogin() {
  // Generate PKCE code verifier/challenge
  // Redirect to Microsoft OAuth
  window.location.href = `https://login.microsoftonline.com/.../oauth2/v2.0/authorize?...`
}
```

**What Happens:**
- Frontend generates PKCE code verifier
- Stores in `sessionStorage`
- Redirects to Microsoft OAuth

---

#### Step 2: Microsoft OAuth Redirect

**File:** `frontend/src/app/login/page.tsx`

```typescript
// Microsoft redirects back with authorization code
handleOAuthCallback() {
  const code = urlParams.get('code');
  exchangeCodeForToken(code);
}
```

**What Happens:**
- Microsoft redirects to `/login?code=...`
- Frontend extracts `code` from URL
- Calls backend to exchange code for tokens

---

#### Step 3: Backend Exchanges Code for Tokens

**File:** `app/endpoints.py` → `/auth/microsoft/callback`

```python
@router.post("/auth/microsoft/callback")
async def microsoft_oauth_callback(...):
    # 1. Exchange authorization code for tokens
    token_info = await exchange_code_for_tokens(code, code_verifier)
    access_token = token_info["access_token"]
    refresh_token = token_info.get("refresh_token")
    
    # 2. Get user info from Microsoft Graph
    user_info = await get_user_info_from_graph(access_token)
    
    # 3. Create session in MongoDB
    session_id = await session_store.create_session(
        user_id=user_info["id"],
        user_email=user_info["email"],
        user_name=user_info["name"],
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_in=token_info["expires_in"]
    )
    
    # 4. Set session_id cookie in response
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=secure_cookie,  # True in production HTTPS
        samesite=samesite_setting,  # "lax" or "none"
        max_age=86400 * 24,  # 24 hours
        path="/"
    )
    
    # 5. Return user info (NO tokens)
    return {"user_id": ..., "email": ..., "name": ...}
```

**What Happens:**
1. Backend exchanges OAuth code for Microsoft tokens
2. Calls Microsoft Graph API to get user info
3. Creates session in MongoDB with encrypted tokens
4. Sets `session_id` cookie (HttpOnly, Secure)
5. Returns only user info (no tokens)

**Key Files:**
- `app/endpoints.py` (lines 4670-4810)
- `app/session_store.py` (lines 78-132)

---

#### Step 4: Frontend Receives Cookie

**File:** `frontend/src/app/api/proxy/[...path]/route.ts`

```typescript
// Next.js proxy forwards Set-Cookie header
if (setCookieHeaders) {
  setCookies.forEach((cookie) => {
    proxiedResponse.headers.append('Set-Cookie', cookie);
  });
}
```

**What Happens:**
- Next.js proxy receives `Set-Cookie` header from backend
- Forwards it to browser
- Browser stores `session_id` cookie (HttpOnly)

**Key Files:**
- `frontend/src/app/api/proxy/[...path]/route.ts` (lines 96-156)

---

#### Step 5: Frontend Stores User Info

**File:** `frontend/src/app/login/page.tsx`

```typescript
// Store ONLY UI info (no tokens)
const user = {
  id: data.user_id,
  name: data.name,
  email: data.email
};
localStorage.setItem('user', JSON.stringify(user));
```

**What Happens:**
- Frontend stores user info in `localStorage` (for UI display only)
- **NO tokens stored** (tokens stay in backend)
- Redirects to `/chat/new`

---

### Phase 2: Authenticated Requests

#### Step 1: Frontend Makes API Request

**File:** `frontend/src/lib/api.ts`

```typescript
export async function apiFetch(path: string, options: RequestInit = {}) {
  return fetch(`/api/proxy${path}`, {
    ...options,
    credentials: 'include',  // ⭐ CRITICAL: Send cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
}
```

**What Happens:**
- Frontend calls `apiFetch('/chat/sessions/all')`
- Browser automatically includes `session_id` cookie
- Request goes through Next.js proxy

**Key Files:**
- `frontend/src/lib/api.ts` (entire file)

---

#### Step 2: Next.js Proxy Forwards Request

**File:** `frontend/src/app/api/proxy/[...path]/route.ts`

```typescript
// Get cookies from browser request
const browserCookies = request.headers.get('cookie') || '';

// Forward to backend with cookies
axiosResponse = await axios({
  method: method,
  url: `${BACKEND_BASE}/${path}`,
  headers: {
    cookie: browserCookies,  // ⭐ Forward session_id cookie
  },
  data: body,
});
```

**What Happens:**
- Next.js proxy extracts cookies from browser request
- Forwards cookies to FastAPI backend
- Backend receives `session_id` cookie

**Key Files:**
- `frontend/src/app/api/proxy/[...path]/route.ts` (lines 58-77)

---

#### Step 3: Backend Validates Session

**File:** `app/endpoints.py` → `require_auth()`

```python
async def require_auth(request: Request, ...):
    # 1. Get session_id from cookie
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=401, detail="No active session")
    
    # 2. Look up session in MongoDB
    from app.session_store import session_store
    await session_store.connect()
    session = await session_store.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")
    
    # 3. Check if token needs refresh (non-blocking)
    if token_expiring_soon(session):
        logger.info("Token expiring soon, will refresh in background")
    
    # 4. Return user info
    return {
        "user_id": session["user_id"],
        "email": session["user_email"],
        "name": session["user_name"]
    }
```

**What Happens:**
1. Backend extracts `session_id` from cookie
2. Looks up session in MongoDB
3. Validates session is not expired
4. Checks if Microsoft token needs refresh (logs only, doesn't block)
5. Returns user info (no Graph API call)

**Key Files:**
- `app/endpoints.py` (lines 496-620)
- `app/session_store.py` (lines 134-169)

---

#### Step 4: Backend Processes Request

**File:** `app/endpoints.py` → Protected endpoints

```python
@router.get("/chat/sessions/all")
async def get_sessions(
    current_user: dict = Depends(require_auth)  # ⭐ Session validation
):
    # current_user is guaranteed to be valid
    user_id = current_user["user_id"]
    # ... process request
```

**What Happens:**
- Endpoint receives validated user info
- Processes request
- Returns data

---

### Phase 3: Session Check (Frontend)

#### Step 1: Frontend Checks Session

**File:** `frontend/src/lib/session-utils.ts`

```typescript
export async function checkSession(): Promise<boolean> {
  try {
    const res = await apiFetch('/chat/sessions/all?limit=1', {
      method: 'GET'
    });
    return res.status === 200;  // 200 = valid session, 401 = no session
  } catch (err) {
    return false;
  }
}
```

**What Happens:**
- Frontend calls protected endpoint
- If `200 OK` → session is valid
- If `401 Unauthorized` → session expired/invalid

**Key Files:**
- `frontend/src/lib/session-utils.ts` (lines 360-370)

---

#### Step 2: Pages Use Session Check

**File:** `frontend/src/app/chat/new/page.tsx`

```typescript
useEffect(() => {
  const checkAuth = async () => {
    const isLoggedIn = await checkSession();
    
    if (!isLoggedIn) {
      router.replace('/login');
      return;
    }
    
    setIsAuthenticated(true);
  };
  
  checkAuth();
}, [router]);
```

**What Happens:**
- Page loads
- Checks session validity
- Redirects to login if invalid
- Renders content if valid

**Key Files:**
- `frontend/src/app/chat/new/page.tsx` (lines 44-70)
- `frontend/src/app/chat/[sessionId]/page.tsx` (lines 56-90)
- `frontend/src/app/login/page.tsx` (lines 90-105)

---

### Phase 4: Token Refresh (Background)

#### Step 1: Backend Detects Token Expiring

**File:** `app/endpoints.py` → `require_auth()`

```python
# Non-blocking check
if token_expires_at - now < timedelta(minutes=5):
    logger.info("Token expiring soon, will refresh in background")
    # Don't block request - refresh happens in background
```

**What Happens:**
- Backend detects token expires in < 5 minutes
- Logs warning (doesn't block request)
- Frontend can call refresh endpoint

**Key Files:**
- `app/endpoints.py` (lines 532-541)

---

#### Step 2: Frontend Refreshes Session (Optional)

**File:** `frontend/src/lib/session-utils.ts`

```typescript
export async function refreshSession(): Promise<boolean> {
  const response = await apiFetch('/auth/session/refresh', {
    method: 'POST'
  });
  
  if (response.ok) {
    return true;  // Session refreshed
  } else if (response.status === 401) {
    // Session expired - redirect to login
    localStorage.removeItem('user');
    window.location.href = '/login?error=session_expired';
    return false;
  }
}
```

**What Happens:**
- Frontend periodically calls refresh endpoint
- Backend refreshes Microsoft tokens if needed
- Updates session in MongoDB
- Cookie remains the same (no new cookie needed)

**Key Files:**
- `frontend/src/lib/session-utils.ts` (lines 372-399)
- `app/endpoints.py` → `/auth/session/refresh` (lines 4559-4644)

---

#### Step 3: Backend Refreshes Tokens

**File:** `app/endpoints.py` → `/auth/session/refresh`

```python
@router.post("/auth/session/refresh")
async def refresh_session(request: Request):
    session_id = request.cookies.get("session_id")
    
    # Get session from MongoDB
    session = await session_store.get_session(session_id)
    
    # Refresh Microsoft tokens
    new_tokens = await refresh_microsoft_tokens(session["refresh_token"])
    
    # Update session in MongoDB
    await session_store.refresh_session_tokens(
        session_id,
        new_tokens["access_token"],
        new_tokens["refresh_token"],
        new_tokens["expires_in"]
    )
    
    return {"success": True}
```

**What Happens:**
1. Backend gets session from MongoDB
2. Uses refresh token to get new Microsoft tokens
3. Updates session in MongoDB with new tokens
4. Session ID stays the same (cookie unchanged)

**Key Files:**
- `app/endpoints.py` (lines 4559-4644)
- `app/session_store.py` (lines 171-220)

---

### Phase 5: User Logout

#### Step 1: Frontend Calls Logout

**File:** `frontend/src/components/ChatSidebar.tsx`

```typescript
const handleLogoutConfirm = async () => {
  await apiFetch('/auth/logout', {
    method: 'POST'
  });
  
  localStorage.removeItem('user');
  router.push('/login');
};
```

**What Happens:**
- Frontend calls logout endpoint
- Clears user info from localStorage
- Redirects to login

**Key Files:**
- `frontend/src/components/ChatSidebar.tsx` (logout handler)
- `frontend/src/lib/session-utils.ts` (lines 440-450)

---

#### Step 2: Backend Deletes Session

**File:** `app/endpoints.py` → `/auth/logout`

```python
@router.post("/auth/logout")
async def logout(request: Request):
    session_id = request.cookies.get("session_id")
    
    if session_id:
        # Delete session from MongoDB
        await session_store.delete_session(session_id)
    
    # Clear cookie
    response = JSONResponse(content={"success": True})
    response.delete_cookie(key="session_id")
    
    return response
```

**What Happens:**
1. Backend deletes session from MongoDB
2. Clears `session_id` cookie
3. Returns success

**Key Files:**
- `app/endpoints.py` (lines 4647-4668)
- `app/session_store.py` (lines 222-239)

---

## 📁 Files Involved

### Backend Files

#### 1. `app/session_store.py` ⭐ **CORE SESSION LOGIC**

**Purpose:** Manages session storage in MongoDB

**Key Functions:**
- `create_session()` - Creates new session after login
- `get_session()` - Retrieves and validates session
- `refresh_session_tokens()` - Updates Microsoft tokens
- `delete_session()` - Removes session on logout
- `cleanup_expired_sessions()` - Removes expired sessions

**Lines:**
- Session creation: 78-132
- Session retrieval: 134-169
- Token refresh: 171-220
- Session deletion: 222-239

**MongoDB Collection:** `app_sessions`

**Indexes:**
- `session_id` (unique)
- `user_id`
- `expires_at` (TTL index - auto-deletes expired)
- `last_accessed_at`

---

#### 2. `app/endpoints.py` ⭐ **AUTHENTICATION ENDPOINTS**

**Purpose:** Handles OAuth, session creation, and authentication

**Key Endpoints:**

**`POST /auth/microsoft/callback`** (lines 4670-4810)
- Exchanges OAuth code for tokens
- Creates session in MongoDB
- Sets `session_id` cookie
- Returns user info

**`POST /auth/logout`** (lines 4647-4668)
- Deletes session from MongoDB
- Clears `session_id` cookie

**`POST /auth/session/refresh`** (lines 4559-4644)
- Refreshes Microsoft tokens
- Updates session in MongoDB

**`require_auth()`** (lines 496-620)
- Validates session on every protected request
- Extracts `session_id` from cookie
- Looks up session in MongoDB
- Returns user info

**Cookie Configuration:**
- Lines 4750-4807
- Auto-detects production/development
- Sets `Secure`, `HttpOnly`, `SameSite` flags

---

#### 3. `app/auth.py` ⭐ **USER AUTHENTICATION**

**Purpose:** Provides `get_current_user()` for dependency injection

**Key Function:**

**`get_current_user()`** (lines 40-104)
- Priority 1: Session cookie validation
- Priority 2: Bearer token (legacy fallback)
- Returns user info dict

**Usage:**
```python
@router.get("/some-endpoint")
async def some_endpoint(current_user: dict = Depends(get_current_user)):
    # current_user is guaranteed to be valid
    user_id = current_user["id"]
```

---

#### 4. `server.py` ⭐ **CORS CONFIGURATION**

**Purpose:** Configures CORS for cookie-based auth

**Key Configuration:**
- Lines 115-135
- `allow_origins` - Specific origins (required for credentials)
- `allow_credentials=True` - Required for cookies
- Production origin: `https://ai.cloudfuze.com`

---

### Frontend Files

#### 1. `frontend/src/lib/session-utils.ts` ⭐ **SESSION UTILITIES**

**Purpose:** Frontend session management functions

**Key Functions:**

**`checkSession()`** (lines 360-370)
- Checks if user has valid session
- Returns `true` if `200 OK`, `false` if `401`

**`refreshSession()`** (lines 372-399)
- Calls backend refresh endpoint
- Handles session expiry

**`startSessionMonitor()`** (lines 411-436)
- Background session monitoring
- Checks every 5 minutes

**`getCurrentUser()`** (lines 325-342)
- Gets user info from localStorage (UI only)
- Removes any legacy token fields

---

#### 2. `frontend/src/lib/api.ts` ⭐ **API HELPER**

**Purpose:** Centralized API fetch with cookie support

**Key Function:**

**`apiFetch()`** (entire file)
- Routes all requests through `/api/proxy/*`
- Always includes `credentials: 'include'`
- Ensures cookies are sent

**Usage:**
```typescript
const response = await apiFetch('/chat/sessions/all');
```

---

#### 3. `frontend/src/app/api/proxy/[...path]/route.ts` ⭐ **NEXT.JS PROXY**

**Purpose:** Proxies all backend requests, forwards cookies

**Key Functions:**

**`proxyRequest()`** (lines 27-177)
- Forwards requests to FastAPI backend
- Extracts cookies from browser request
- Forwards cookies to backend
- Captures `Set-Cookie` headers from backend
- Forwards `Set-Cookie` to browser

**HTTP Methods:**
- `GET`, `POST`, `PUT`, `DELETE`, `PATCH` (lines 180-221)

**Cookie Forwarding:**
- Lines 96-156
- Uses `axios` to capture `Set-Cookie` headers
- Forwards to browser via `proxiedResponse.headers.append()`

---

#### 4. `frontend/src/app/login/page.tsx` ⭐ **LOGIN PAGE**

**Purpose:** Handles OAuth login flow

**Key Functions:**

**`initializeLoginPage()`** (lines 34-458)
- Loads OAuth configuration
- Handles OAuth callback
- Checks existing session

**`handleOAuthCallback()`** (lines 238-259)
- Processes OAuth redirect
- Calls `exchangeCodeForToken()`

**`exchangeCodeForToken()`** (lines 262-391)
- Exchanges OAuth code for session
- Stores user info (no tokens)
- Redirects to chat

**`checkSessionStatus()`** (lines 91-105)
- Checks if user already logged in
- Redirects to chat if valid

**Session Check:**
- Lines 443-452
- Handles OAuth callback first
- Then checks existing session

---

#### 5. `frontend/src/app/chat/new/page.tsx` ⭐ **CHAT PAGE AUTH**

**Purpose:** Protected page with session validation

**Key Code:**

**Session Check** (lines 44-70)
```typescript
useEffect(() => {
  const checkAuth = async () => {
    const isLoggedIn = await checkSession();
    
    if (!isLoggedIn) {
      router.replace('/login');
      return;
    }
    
    setIsAuthenticated(true);
  };
  
  checkAuth();
}, [router]);
```

**What Happens:**
- Page loads
- Checks session validity
- Redirects if invalid
- Renders if valid

---

#### 6. `frontend/src/app/chat/[sessionId]/page.tsx` ⭐ **SESSION PAGE AUTH**

**Purpose:** Protected page for specific chat session

**Session Check:**
- Same pattern as `chat/new/page.tsx`
- Lines 56-90

---

#### 7. `frontend/src/app/chat/others/[sessionId]/page.tsx` ⭐ **OTHERS CHAT AUTH**

**Purpose:** Protected page for viewing others' chats

**Session Check:**
- Same pattern as other chat pages
- Lines 41-75

---

#### 8. `frontend/src/components/ChatSidebar.tsx` ⭐ **LOGOUT**

**Purpose:** Handles user logout

**Key Function:**

**`handleLogoutConfirm()`** (logout handler)
```typescript
const handleLogoutConfirm = async () => {
  await apiFetch('/auth/logout', { method: 'POST' });
  localStorage.removeItem('user');
  router.push('/login');
};
```

---

#### 9. `frontend/src/components/TokenMonitor.tsx` ⭐ **SESSION MONITOR**

**Purpose:** Background session monitoring

**Key Code:**
```typescript
useEffect(() => {
  startSessionMonitor();  // Checks every 5 minutes
  return () => stopSessionMonitor();
}, []);
```

**What It Does:**
- Starts background session monitor
- Calls `refreshSession()` every 5 minutes
- Stops on component unmount

---

#### 10. `frontend/src/types/chat.ts` ⭐ **TYPE DEFINITIONS**

**Purpose:** TypeScript type definitions

**Key Interface:**

**`User`** (lines 3-10)
```typescript
export interface User {
  id: string;
  name: string;
  email: string;
  // ✅ NO token fields (removed)
}
```

**What Changed:**
- Removed `access_token`, `refresh_token`, `token_expires_at`, `token_issued_at`
- Only UI display fields remain

---

## 🚀 Production Configuration

### Environment Variables

#### Backend (FastAPI)

**Required:**
```bash
# Production environment
ENVIRONMENT=production

# MongoDB connection
MONGODB_URL=mongodb://your-production-mongodb-uri
MONGODB_DATABASE=slack2teams

# Session configuration
SESSION_EXPIRY_HOURS=24  # Optional, defaults to 24
```

**Optional (for cross-origin cookies):**
```bash
# Only if frontend and backend are on different domains
USE_CROSS_ORIGIN_COOKIES=true
```

**CORS Origins:**
- Already configured in `server.py` (line 119)
- Add additional origins if needed:
  ```python
  allowed_origins = [
      "https://ai.cloudfuze.com",  # ✅ Already included
      "https://your-other-domain.com",  # Add if needed
  ]
  ```

---

#### Frontend (Next.js)

**Required (if backend on different domain):**
```bash
# Backend URL (only if different from default)
NEXT_PUBLIC_BACKEND_URL=https://api.cloudfuze.com
```

**If same domain:**
- No environment variable needed
- Proxy automatically uses same domain

---

### Cookie Settings (Automatic)

**Production Detection:**
```python
# In app/endpoints.py (lines 4754-4767)
is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
is_https = request_url.startswith("https://")

if is_production and is_https:
    secure_cookie = True
    samesite_setting = "lax"  # Default (works with proxy)
    # OR "none" if USE_CROSS_ORIGIN_COOKIES=true
```

**Result:**
- ✅ `Secure=True` (HTTPS only)
- ✅ `HttpOnly=True` (XSS protection)
- ✅ `SameSite=Lax` (same-origin) or `None` (cross-origin)
- ✅ `Path=/` (available on all paths)
- ✅ `Max-Age=2073600` (24 hours)

---

### MongoDB Setup

**Required Indexes:**
```javascript
// Run in MongoDB shell or via migration script
db.app_sessions.createIndex({ "session_id": 1 }, { unique: true });
db.app_sessions.createIndex({ "expires_at": 1 }, { expireAfterSeconds: 0 });
db.app_sessions.createIndex({ "user_id": 1 });
db.app_sessions.createIndex({ "last_accessed_at": 1 });
```

**TTL Index:**
- `expires_at` index automatically deletes expired sessions
- No manual cleanup needed

---

### Deployment Scenarios

#### Scenario A: Same Domain (Recommended) ✅

**Setup:**
```
Frontend: https://ai.cloudfuze.com
Backend:  https://ai.cloudfuze.com/api (reverse proxy)
```

**Configuration:**
- ✅ No changes needed
- ✅ Cookies work automatically
- ✅ `SameSite=Lax` (automatic)
- ✅ No CORS issues

**Reverse Proxy (Nginx example):**
```nginx
location /api {
    proxy_pass http://localhost:8002;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

#### Scenario B: Different Domains

**Setup:**
```
Frontend: https://ai.cloudfuze.com
Backend:  https://api.cloudfuze.com
```

**Backend Configuration:**
```bash
# .env
ENVIRONMENT=production
USE_CROSS_ORIGIN_COOKIES=true
```

**Frontend Configuration:**
```bash
# .env.local
NEXT_PUBLIC_BACKEND_URL=https://api.cloudfuze.com
```

**CORS Configuration:**
```python
# server.py - add frontend origin
allowed_origins = [
    "https://ai.cloudfuze.com",  # Frontend
]
```

**Result:**
- ✅ `SameSite=None` (automatic)
- ✅ `Secure=True` (automatic)
- ✅ Cookies work cross-origin

---

## 🔍 Code References

### Backend Session Creation

**File:** `app/endpoints.py`  
**Function:** `microsoft_oauth_callback()`  
**Lines:** 4670-4810

**Key Steps:**
1. Exchange OAuth code (line 4690)
2. Get user info from Graph (line 4700)
3. Create session (line 4734)
4. Set cookie (line 4780)
5. Return user info (line 4777)

---

### Backend Session Validation

**File:** `app/endpoints.py`  
**Function:** `require_auth()`  
**Lines:** 496-620

**Key Steps:**
1. Get session_id from cookie (line 521)
2. Look up session in MongoDB (line 529)
3. Validate session exists (line 531)
4. Check token expiry (line 533)
5. Return user info (line 544)

---

### Frontend Session Check

**File:** `frontend/src/lib/session-utils.ts`  
**Function:** `checkSession()`  
**Lines:** 360-370

**Implementation:**
```typescript
export async function checkSession(): Promise<boolean> {
  const res = await apiFetch('/chat/sessions/all?limit=1');
  return res.status === 200;
}
```

---

### Cookie Forwarding (Proxy)

**File:** `frontend/src/app/api/proxy/[...path]/route.ts`  
**Function:** `proxyRequest()`  
**Lines:** 96-156

**Key Steps:**
1. Extract cookies from browser (line 60)
2. Forward to backend (line 70)
3. Capture Set-Cookie from backend (line 97)
4. Forward to browser (line 152)

---

## 🐛 Troubleshooting

### Issue: Cookies Not Set After Login

**Symptoms:**
- Login succeeds but user immediately logged out
- `401 Unauthorized` on next request

**Check:**
1. **Backend logs:** Look for `✅ Session cookie configured`
2. **Proxy logs:** Look for `✅ Found Set-Cookie header`
3. **Browser DevTools:** Application → Cookies → Check for `session_id`

**Common Causes:**
- `Secure=True` on HTTP (should be `False` in dev)
- `SameSite=None` without `Secure=True`
- CORS not allowing credentials

**Fix:**
- Verify `ENVIRONMENT` is not set to `production` in dev
- Check cookie settings in `app/endpoints.py` (lines 4760-4767)

---

### Issue: Session Expires Unexpectedly

**Symptoms:**
- User logged out after short time
- `401 Unauthorized` after working

**Check:**
1. **MongoDB:** Verify session exists
   ```javascript
   db.app_sessions.find({ "session_id": "your_session_id" })
   ```
2. **Session expiry:** Check `expires_at` field
3. **TTL index:** Verify TTL index exists

**Common Causes:**
- TTL index deleting sessions too early
- `SESSION_EXPIRY_HOURS` set too low
- MongoDB connection issues

**Fix:**
- Verify `SESSION_EXPIRY_HOURS` environment variable
- Check MongoDB TTL index configuration

---

### Issue: CORS Errors in Production

**Symptoms:**
- `CORS policy` errors in browser console
- Requests blocked

**Check:**
1. **Backend CORS:** Verify frontend origin in `allowed_origins`
2. **Credentials:** Verify `allow_credentials=True`
3. **Headers:** Check if custom headers are allowed

**Fix:**
- Add frontend origin to `server.py` (line 119)
- Ensure `allow_credentials=True` (line 132)

---

### Issue: Proxy Not Forwarding Cookies

**Symptoms:**
- Login works but subsequent requests fail
- `Set-Cookie` header not in proxy logs

**Check:**
1. **Proxy logs:** Look for `✅ Found Set-Cookie header`
2. **Axios:** Verify using `axios` (not `fetch`)
3. **Headers:** Check `axiosResponse.headers['set-cookie']`

**Fix:**
- Verify proxy uses `axios` (line 64)
- Check cookie forwarding logic (lines 145-156)

---

## 📊 Session Data Structure

### MongoDB Document Schema

```javascript
{
  "_id": ObjectId("..."),
  "session_id": "70646f34af7a73a26b16457f2788e0173a5e9e2e3197ebfb785570ef22ef8919",
  "user_id": "ab7f12b6-75d1-4812-b416-1679c7fe85c6",
  "user_email": "chaitanya.malle@cloudfuze.com",
  "user_name": "Chaitanya Malle",
  "access_token": "base64_encrypted_token",
  "refresh_token": "base64_encrypted_token",
  "token_expires_at": ISODate("2025-12-18T12:00:00Z"),
  "created_at": ISODate("2025-12-17T12:00:00Z"),
  "last_accessed_at": ISODate("2025-12-17T15:30:00Z"),
  "expires_at": ISODate("2025-12-18T12:00:00Z")  // TTL index uses this
}
```

### Cookie Structure

```
session_id=70646f34af7a73a26b16457f2788e0173a5e9e2e3197ebfb785570ef22ef8919; 
HttpOnly; 
Max-Age=2073600; 
Path=/; 
SameSite=lax
```

---

## ✅ Production Checklist

### Before Deployment

- [ ] Set `ENVIRONMENT=production` in backend
- [ ] Configure production MongoDB URI
- [ ] Add frontend origin to CORS `allowed_origins`
- [ ] Set `NEXT_PUBLIC_BACKEND_URL` if backend on different domain
- [ ] Create MongoDB indexes (see MongoDB Setup section)
- [ ] Test login flow in staging
- [ ] Verify cookies are set (DevTools)
- [ ] Test session persistence (refresh page)
- [ ] Test logout flow
- [ ] Monitor session creation in MongoDB

### After Deployment

- [ ] Verify cookies in production (DevTools)
- [ ] Test login → chat → refresh → still logged in
- [ ] Check backend logs for session creation
- [ ] Monitor MongoDB for session documents
- [ ] Verify TTL index is working (expired sessions auto-deleted)
- [ ] Test logout clears session
- [ ] Monitor for 401 errors (should be rare)

---

## 📚 Additional Resources

- **Session Store:** `app/session_store.py`
- **Authentication:** `app/auth.py`, `app/endpoints.py`
- **Frontend Utils:** `frontend/src/lib/session-utils.ts`
- **API Helper:** `frontend/src/lib/api.ts`
- **Proxy:** `frontend/src/app/api/proxy/[...path]/route.ts`
- **Production Guide:** `PRODUCTION_SESSION_GUIDE.md`

---

## 🎯 Summary

**Session-based authentication is production-ready** with:

✅ **Secure:** HttpOnly, Secure cookies  
✅ **Scalable:** MongoDB-backed sessions  
✅ **User-friendly:** No random logouts  
✅ **Automatic:** Token refresh in background  
✅ **Flexible:** Works same-domain or cross-domain  

**Key Files:**
- Backend: `app/session_store.py`, `app/endpoints.py`, `app/auth.py`
- Frontend: `frontend/src/lib/session-utils.ts`, `frontend/src/lib/api.ts`, `frontend/src/app/api/proxy/[...path]/route.ts`

**Production Changes:**
- Set `ENVIRONMENT=production`
- Configure MongoDB URI
- Add frontend origin to CORS
- Set `NEXT_PUBLIC_BACKEND_URL` if needed

**That's it!** 🚀

