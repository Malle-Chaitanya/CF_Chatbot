# Session Implementation Verification Guide

## 🔍 Quick Verification Checklist

Use this guide to verify that your session-based authentication is working correctly.

---

## ✅ Step 1: Backend Session Creation

### Test: Login and Check Session Creation

**1. Start Backend Server:**
```bash
cd /path/to/project
python server.py
```

**2. Check Backend Logs for Session Creation:**
After successful login, you should see:
```
[SESSION] Created session for user: user@cloudfuze.com (session_id: xxxxxxxx...)
[AUTH] ✅ Session cookie configured: secure=False, httponly=True, samesite=lax, path=/
[AUTH] ✅ Set-Cookie header manually set: session_id=xxxxx...
```

**✅ PASS if:** You see session creation logs  
**❌ FAIL if:** No session creation logs appear

---

## ✅ Step 2: Cookie Setting

### Test: Verify Cookie is Set in Browser

**1. Open Browser DevTools:**
- Press `F12` or `Ctrl+Shift+I`
- Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
- Navigate to **Cookies** → `http://localhost:3000`

**2. After Login, Check for Cookie:**
You should see:
```
Name: session_id
Value: [long hex string, 64 characters]
Domain: localhost
Path: /
HttpOnly: ✓
Secure: (unchecked in dev, checked in production)
SameSite: Lax
```

**✅ PASS if:** Cookie exists with correct attributes  
**❌ FAIL if:** Cookie is missing or has wrong attributes

---

## ✅ Step 3: Session Validation

### Test: Verify Session is Validated on API Calls

**1. Make an API Request:**
Open browser console and run:
```javascript
fetch('/api/proxy/chat/sessions/all?limit=1', {
  credentials: 'include'
}).then(r => console.log('Status:', r.status));
```

**2. Check Backend Logs:**
You should see:
```
[AUTH] User authenticated via session: user@cloudfuze.com
INFO: "GET /chat/sessions/all?limit=1" 200 OK
```

**✅ PASS if:** Status is `200` and logs show session authentication  
**❌ FAIL if:** Status is `401` or logs show "No session_id cookie found"

---

## ✅ Step 4: Frontend Session Check

### Test: Verify Frontend Checks Session Correctly

**1. Open Browser Console:**
- Press `F12`
- Go to **Console** tab

**2. Navigate to `/chat/new`:**
You should see:
```
[SESSION] checkSession called
[AUTH] ✅ User authenticated via session: user@cloudfuze.com
```

**3. Check Network Tab:**
- Go to **Network** tab
- Filter by `sessions/all`
- Click on the request
- Check **Request Headers**:
  ```
  Cookie: session_id=xxxxx...
  ```
- Check **Response**: Should be `200 OK`

**✅ PASS if:** Console shows session check success and network shows cookie  
**❌ FAIL if:** Console shows redirect to login or network shows `401`

---

## ✅ Step 5: Cookie Forwarding (Proxy)

### Test: Verify Proxy Forwards Cookies

**1. Check Proxy Logs:**
In Next.js terminal, after making a request, you should see:
```
[PROXY] GET http://localhost:8002/chat/sessions/all?limit=1
[PROXY] ✅ Found 1 Set-Cookie header(s) via axios - forwarding to browser
```

**2. Check Backend Receives Cookie:**
In backend logs, you should see:
```
[AUTH] User authenticated via session: user@cloudfuze.com
```

**✅ PASS if:** Proxy logs show cookie forwarding and backend authenticates  
**❌ FAIL if:** Proxy doesn't log cookies or backend returns `401`

---

## ✅ Step 6: Session Persistence

### Test: Verify Session Persists Across Page Refresh

**1. Login Successfully:**
- Complete login flow
- Verify cookie is set (Step 2)

**2. Refresh Page:**
- Press `F5` or `Ctrl+R`
- Check browser console for:
  ```
  [AUTH] ✅ User authenticated via session: user@cloudfuze.com
  ```

**3. Check Network Tab:**
- After refresh, check if `/chat/sessions/all` request includes cookie
- Status should be `200 OK`

**✅ PASS if:** User stays logged in after refresh  
**❌ FAIL if:** User is redirected to login after refresh

---

## ✅ Step 7: Logout

### Test: Verify Logout Clears Session

**1. Click Logout:**
- Click logout button in sidebar
- Check browser console for:
  ```
  [AUTH] Logging out...
  ```

**2. Check Backend Logs:**
You should see:
```
[SESSION] Deleted session: xxxxxxxx...
POST /auth/logout 200 OK
```

**3. Verify Cookie is Cleared:**
- Check **Application** → **Cookies**
- `session_id` cookie should be **removed**

**4. Verify Redirect:**
- Should redirect to `/login`
- Should not be able to access `/chat/new` without login

**✅ PASS if:** Cookie is cleared, session deleted, and redirect works  
**❌ FAIL if:** Cookie still exists or session not deleted

---

## 🐛 Common Issues and Fixes

### Issue 1: Cookie Not Set After Login

**Symptoms:**
- Login succeeds but cookie not visible in DevTools
- Next request returns `401 Unauthorized`

**Check:**
1. **Backend logs:** Look for `✅ Set-Cookie header manually set`
2. **Proxy logs:** Look for `✅ Found Set-Cookie header(s)`
3. **Cookie settings:** Verify `secure=False` in development

**Fix:**
- Ensure `ENVIRONMENT` is not set to `production` in dev
- Check `app/endpoints.py` cookie settings (lines 4760-4767)
- Verify proxy forwards `Set-Cookie` header (lines 128-136)

---

### Issue 2: Session Not Validated

**Symptoms:**
- Cookie exists but requests return `401`
- Backend logs show "No session_id cookie found"

**Check:**
1. **Cookie domain:** Ensure cookie domain matches request domain
2. **CORS:** Verify `allow_credentials=True` in `server.py`
3. **Proxy:** Verify proxy forwards cookies to backend

**Fix:**
- Check `server.py` CORS configuration (line 132)
- Verify `credentials: 'include'` in `apiFetch()` (line 19)
- Check proxy cookie forwarding (lines 60-70)

---

### Issue 3: Session Expires Unexpectedly

**Symptoms:**
- User logged out after short time
- `401 Unauthorized` after working

**Check:**
1. **MongoDB:** Verify session exists:
   ```javascript
   db.app_sessions.find({ "session_id": "your_session_id" })
   ```
2. **TTL index:** Check if TTL index is deleting sessions too early
3. **Session expiry:** Verify `SESSION_EXPIRY_HOURS` environment variable

**Fix:**
- Verify `SESSION_EXPIRY_HOURS` is set correctly (default: 24)
- Check MongoDB TTL index configuration
- Verify `expires_at` field in session document

---

### Issue 4: Frontend Redirects to Login

**Symptoms:**
- Page loads but immediately redirects to `/login`
- Console shows "No valid session"

**Check:**
1. **Cookie:** Verify cookie exists in DevTools
2. **Network:** Check if `/chat/sessions/all` request includes cookie
3. **Response:** Check if backend returns `200` or `401`

**Fix:**
- Verify `checkSession()` is called correctly (line 346)
- Check `apiFetch()` includes `credentials: 'include'` (line 19)
- Verify backend `require_auth()` validates session (line 529)

---

## 📊 Verification Test Script

### Manual Test Flow

```bash
# 1. Start Backend
python server.py

# 2. Start Frontend (in another terminal)
cd frontend
npm run dev

# 3. Open Browser
# Navigate to http://localhost:3000/login

# 4. Login
# Click "Sign in with Microsoft"
# Complete OAuth flow

# 5. Verify Cookie (DevTools → Application → Cookies)
# Should see: session_id cookie

# 6. Verify Session Check (Console)
# Should see: [AUTH] ✅ User authenticated via session

# 7. Refresh Page (F5)
# Should stay logged in

# 8. Check Network Tab
# GET /api/proxy/chat/sessions/all?limit=1 → 200 OK

# 9. Logout
# Click logout button
# Should redirect to /login
# Cookie should be removed
```

---

## 🔍 Code Verification Checklist

### Backend Files

- [ ] `app/session_store.py` - `create_session()` exists (line 78)
- [ ] `app/session_store.py` - `get_session()` exists (line 134)
- [ ] `app/endpoints.py` - `/auth/microsoft/callback` sets cookie (line 4785)
- [ ] `app/endpoints.py` - `require_auth()` validates session (line 529)
- [ ] `app/endpoints.py` - `/auth/logout` deletes session (line 4654)
- [ ] `server.py` - CORS allows credentials (line 132)

### Frontend Files

- [ ] `frontend/src/lib/session-utils.ts` - `checkSession()` exists (line 346)
- [ ] `frontend/src/lib/api.ts` - `apiFetch()` includes credentials (line 19)
- [ ] `frontend/src/app/api/proxy/[...path]/route.ts` - Forwards cookies (line 60)
- [ ] `frontend/src/app/api/proxy/[...path]/route.ts` - Forwards Set-Cookie (line 135)
- [ ] `frontend/src/app/login/page.tsx` - Handles OAuth callback (line 448)
- [ ] `frontend/src/app/chat/new/page.tsx` - Checks session on load (line 50)

---

## 🎯 Expected Behavior

### ✅ Working Correctly

1. **Login:**
   - User clicks "Sign in with Microsoft"
   - OAuth flow completes
   - Backend creates session in MongoDB
   - Cookie is set in browser
   - User is redirected to `/chat/new`

2. **Authenticated Requests:**
   - All API requests include `session_id` cookie
   - Backend validates session from MongoDB
   - No Microsoft Graph API calls (except during login)
   - Requests return `200 OK`

3. **Page Refresh:**
   - User refreshes page
   - Frontend checks session
   - Session is valid
   - User stays logged in

4. **Logout:**
   - User clicks logout
   - Backend deletes session from MongoDB
   - Cookie is cleared
   - User is redirected to `/login`

---

## 🚨 Red Flags (Indicates Problem)

### ❌ Backend Issues

- No `[SESSION] Created session` logs after login
- `UnboundLocalError: cannot access local variable 'session_id'`
- `401 Unauthorized` even with valid cookie
- Multiple sessions created for same user

### ❌ Frontend Issues

- Cookie not visible in DevTools after login
- `Failed to fetch` errors
- Immediate redirect to `/login` after login
- `401 Unauthorized` on all API requests

### ❌ Proxy Issues

- No `[PROXY] ✅ Found Set-Cookie header` logs
- `⚠️ Expected Set-Cookie header missing` warnings
- Cookies not forwarded to backend
- Backend receives requests without cookies

---

## 📝 Quick Debug Commands

### Check MongoDB Sessions

```javascript
// In MongoDB shell
use slack2teams
db.app_sessions.find().pretty()

// Count active sessions
db.app_sessions.countDocuments({ "expires_at": { "$gt": new Date() } })

// Find session by user email
db.app_sessions.find({ "user_email": "user@cloudfuze.com" })
```

### Check Backend Logs

```bash
# Look for session creation
grep "Created session" server.log

# Look for authentication
grep "User authenticated via session" server.log

# Look for errors
grep "ERROR\|Exception\|Traceback" server.log
```

### Check Frontend Console

```javascript
// In browser console
// Check if cookie exists
document.cookie

// Check localStorage
localStorage.getItem('user')

// Test session check
fetch('/api/proxy/chat/sessions/all?limit=1', { credentials: 'include' })
  .then(r => console.log('Status:', r.status))
```

---

## ✅ Final Verification

After completing all steps, verify:

1. ✅ Login creates session in MongoDB
2. ✅ Cookie is set in browser
3. ✅ Session is validated on API requests
4. ✅ Frontend checks session correctly
5. ✅ Proxy forwards cookies
6. ✅ Session persists across refresh
7. ✅ Logout clears session and cookie

**If all checks pass → Session implementation is working! 🎉**

---

## 📚 Related Documentation

- **Session Workflow:** `Context_Folder/SESSION_WORKFLOW.md`
- **Production Guide:** `PRODUCTION_SESSION_GUIDE.md`
- **Migration Guide:** `SESSION_MIGRATION_GUIDE.md`

