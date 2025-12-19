# Session Workflow - Simple Explanation

## 🎯 What is a Session?

Think of a session like a **"temporary ID card"** that proves you're logged in.

- **Before (Token-based):** Frontend stored a password (token) and showed it every time
- **Now (Session-based):** Backend gives you an ID card (session_id cookie) that it remembers

---

## 📋 Simple Workflow (Step by Step)

### Step 1: User Logs In

```
User clicks "Sign in with Microsoft"
    ↓
Microsoft asks: "Who are you?"
    ↓
User enters Microsoft credentials
    ↓
Microsoft says: "OK, here's proof" (OAuth code)
    ↓
Frontend sends code to Backend
```

**What happens in backend:**
```python
# Backend receives OAuth code
# 1. Exchanges code for Microsoft tokens
# 2. Gets user info from Microsoft
# 3. Creates a SESSION in MongoDB:
session = {
    "session_id": "abc123...",  # Unique ID
    "user_email": "user@cloudfuze.com",
    "expires_at": "2025-12-20 12:00:00"  # 24 hours from now
}
# 4. Sends session_id to browser as a COOKIE
```

**Result:** Browser now has a `session_id` cookie

---

### Step 2: User Makes API Request

```
User clicks something (e.g., "Load my chats")
    ↓
Frontend makes API call: GET /chat/sessions/all
    ↓
Browser AUTOMATICALLY includes session_id cookie
    ↓
Request goes to Backend
```

**What happens in backend:**
```python
# Backend receives request
# 1. Extracts session_id from cookie
session_id = request.cookies.get("session_id")  # "abc123..."

# 2. Looks up session in MongoDB
session = db.app_sessions.find_one({
    "session_id": "abc123...",
    "expires_at": {"$gt": now}  # Not expired
})

# 3. If found → User is authenticated ✅
# 4. If not found → User is not authenticated ❌ (401 error)
```

**Result:** 
- ✅ Session found → Request succeeds (200 OK)
- ❌ Session not found/expired → Request fails (401 Unauthorized)

---

### Step 3: Session Expires

```
24 hours pass...
    ↓
Session expires_at time is now in the past
    ↓
User makes another API request
    ↓
Backend checks: expires_at < now? → YES (expired!)
    ↓
Backend returns: 401 Unauthorized
    ↓
Frontend redirects to login page
```

**What happens:**
```python
# Backend checks expiration
now = datetime.utcnow()  # Current time
expires_at = session["expires_at"]  # When session expires

if expires_at < now:
    # Session expired!
    return None  # No session found
else:
    # Session still valid
    return session
```

**Result:** User must log in again

---

## 🔄 Complete Flow Diagram

```
┌─────────────┐
│   USER      │
└──────┬──────┘
       │
       │ 1. Clicks "Login"
       ↓
┌─────────────┐
│  FRONTEND   │
│ (Next.js)   │
└──────┬──────┘
       │
       │ 2. Redirects to Microsoft
       ↓
┌─────────────┐
│  MICROSOFT  │
│   OAuth     │
└──────┬──────┘
       │
       │ 3. User enters credentials
       │ 4. Microsoft returns code
       ↓
┌─────────────┐
│  FRONTEND   │
└──────┬──────┘
       │
       │ 5. Sends code to backend
       ↓
┌─────────────┐         ┌─────────────┐
│  BACKEND    │────────▶│  MONGODB    │
│ (FastAPI)   │         │             │
└──────┬──────┘         └─────────────┘
       │
       │ 6. Creates session in MongoDB
       │ 7. Sets session_id cookie
       ↓
┌─────────────┐
│   BROWSER   │
│  (Cookie)   │
└──────┬──────┘
       │
       │ 8. Stores session_id cookie
       │
       │ ──────────────────────────────
       │
       │ 9. User makes API request
       │    (Cookie sent automatically)
       ↓
┌─────────────┐         ┌─────────────┐
│  BACKEND    │────────▶│  MONGODB    │
│ (FastAPI)   │         │             │
└──────┬──────┘         └─────────────┘
       │
       │ 10. Checks session in MongoDB
       │ 11. Validates expires_at > now
       │
       │ ✅ Valid → Returns data
       │ ❌ Expired → Returns 401
```

---

## 🔍 What I Tested (Without MongoDB)

### ✅ What I Verified (Code Logic)

1. **Configuration:**
   - Session expiry is set to 24 hours ✅
   - Cookie calculation is correct ✅

2. **Code Structure:**
   - All expiration code exists ✅
   - MongoDB query filters are correct ✅
   - TTL index is configured ✅

3. **Logic:**
   - Expired session detection works ✅
   - Valid session detection works ✅
   - Cookie expiration matches session ✅

### ❌ What I Could NOT Test (Needs MongoDB)

1. **Actual Database Operations:**
   - Creating real sessions in MongoDB
   - Querying MongoDB for sessions
   - TTL index auto-deletion

2. **End-to-End Flow:**
   - Actual login → session creation
   - Real API requests with cookies
   - Session expiration after 24 hours

---

## 🧪 How to Test with Real MongoDB

### Quick Test (5 minutes)

**1. Start your backend:**
```bash
python server.py
```

**2. Login to your app:**
- Go to `http://localhost:3000/login`
- Click "Sign in with Microsoft"
- Complete login

**3. Check if session was created:**
```bash
# Open MongoDB shell or use MongoDB Compass
# Connect to: mongodb://localhost:27017
# Database: slack2teams
# Collection: app_sessions

# Run this query:
db.app_sessions.find().pretty()
```

**You should see:**
```json
{
  "_id": ObjectId("..."),
  "session_id": "abc123...",
  "user_email": "your@cloudfuze.com",
  "expires_at": ISODate("2025-12-20T12:00:00Z"),  // 24 hours from now
  "created_at": ISODate("2025-12-19T12:00:00Z")
}
```

**✅ If you see this → Session creation is working!**

---

### Test Session Expiration (Manual)

**1. Manually expire a session:**
```javascript
// In MongoDB shell
db.app_sessions.updateOne(
  {session_id: "your_session_id_here"},
  {$set: {expires_at: new Date(Date.now() - 3600000)}}  // 1 hour ago
)
```

**2. Try to use the app:**
- Make an API request (e.g., load chats)
- Should get `401 Unauthorized`
- Should redirect to login

**✅ If this happens → Session expiration is working!**

---

### Test TTL Index (Automatic Cleanup)

**1. Create an expired session:**
```javascript
// In MongoDB shell
db.app_sessions.insertOne({
  "session_id": "test_expired_123",
  "user_email": "test@cloudfuze.com",
  "expires_at": new Date(Date.now() - 3600000),  // 1 hour ago
  "created_at": new Date()
})
```

**2. Wait 1-2 minutes**

**3. Check if it was deleted:**
```javascript
db.app_sessions.find({session_id: "test_expired_123"})
```

**✅ If not found → TTL index is working! (MongoDB auto-deleted it)**

---

## 📊 Summary: What's Working?

### ✅ Confirmed Working (Code Level)

| Component | Status | Evidence |
|-----------|--------|----------|
| Session expiry config | ✅ | 24 hours set correctly |
| Expiration calculation | ✅ | Logic verified |
| MongoDB query filter | ✅ | Code checks `expires_at > now` |
| Cookie expiration | ✅ | Fixed to match session (24 hours) |
| TTL index config | ✅ | Code sets `expireAfterSeconds=0` |
| Cleanup function | ✅ | Code exists and is correct |

### ⚠️ Needs Real Testing (MongoDB Required)

| Component | Status | How to Test |
|-----------|--------|-------------|
| Session creation | ⚠️ | Login and check MongoDB |
| Session validation | ⚠️ | Make API request, check logs |
| Session expiration | ⚠️ | Expire session manually, test API |
| TTL auto-cleanup | ⚠️ | Create expired session, wait, check |

---

## 🎯 Bottom Line

### What I Tested:
✅ **Code logic and structure** - Everything is correctly implemented

### What You Need to Test:
⚠️ **Actual database operations** - Requires MongoDB running

### Is It Working?
**YES** - The code is correct. But you should verify with real MongoDB to be 100% sure.

---

## 🚀 Quick Verification Steps

1. **Start backend:** `python server.py`
2. **Login:** Go to app and login
3. **Check MongoDB:** `db.app_sessions.find().pretty()`
4. **See session?** → ✅ Working!
5. **Don't see session?** → ❌ Problem (check logs)

That's it! If you see a session in MongoDB after login, everything is working! 🎉

