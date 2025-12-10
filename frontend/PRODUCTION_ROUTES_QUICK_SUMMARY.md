# Production Routes - Quick Summary (1-Page)

## USER JOURNEY IN PRODUCTION

```
STEP 1: User Visits App
        ↓
   https://ai.cloudfuze.com/
        ↓
   Route: /
   File: page.tsx
   Action: Show spinner → router.replace('/chat/new')

STEP 2: Redirected to New Chat
        ↓
   https://ai.cloudfuze.com/chat/new
        ↓
   Route: /chat/new
   File: chat/new/page.tsx
   Actions:
     ✓ Check localStorage for user
     ✓ Verify token with Microsoft
     ✓ Check @cloudfuze.com domain
     ✓ If invalid → redirect /login
     ✓ Wait for marked.js library
     ✓ Initialize chat app (no session yet)
     ✓ Show empty chat interface

STEP 3: User Types & Sends First Message
        ↓
   User enters: "How do I migrate files?"
   Clicks send button
        ↓
   Backend processes request
   Streams response
   Session created
        ↓
   URL AUTO-CHANGES to:
   /chat/cf.conversation.20251208.abc123
        ↓
   Route: /chat/[sessionId]
   File: chat/[sessionId]/page.tsx
   Session now appears in sidebar

STEP 4: User Can Browse Other Sessions
        ↓
   Click on another session in sidebar
        ↓
   Route: /chat/cf.conversation.20251207.xyz789
   (Same route, different sessionId)

STEP 5: User Clicks on "Others Chat"
        ↓
   URL changes to:
   /chat/others/user_chat_alice123
        ↓
   Route: /chat/others/[sessionId]
   File: chat/others/[sessionId]/page.tsx
   Actions:
     ✓ Detect "user_chat_" format
     ✓ Fetch from backend (not localStorage)
     ✓ Load in read-only mode
     ✓ Disable input field
     ✓ Show: "Read-only mode - You cannot send"
```

---

## ROUTE MAP

```
┌─────────────────────────────────────────────────────┐
│ ALL ROUTES IN PRODUCTION                            │
└─────────────────────────────────────────────────────┘

PUBLIC ROUTES (No auth needed):
  /           → Redirects to /chat/new
  /login      → Microsoft OAuth login

PROTECTED ROUTES (Auth required):
  /chat/new                   → Start new chat
  /chat/[sessionId]           → View/edit own chat
  /chat/others/[sessionId]    → View others chat (read-only)
  /chats                      → Browse all chats grid
```

---

## WHAT HAPPENS AT EACH ROUTE

### **Route: / (Root)**
```
Timeline: < 1 second
Flow:     Load → Show spinner → router.replace → /chat/new
```

### **Route: /chat/new (New Chat)**
```
Timeline: 1-2 seconds
Actions:
  1. Auth check (localStorage + Microsoft)
  2. Wait for marked.js
  3. Initialize chat app
  4. Show empty interface
Status:   Ready for user input
Next:     When first message sent → auto navigate to /chat/[id]
```

### **Route: /chat/[sessionId] (Own Chat)**
```
Timeline: Instant (from localStorage)
Actions:
  1. Extract sessionId from URL
  2. Auth check
  3. Load session from localStorage
  4. Display messages + history
Status:   Full access (read/write)
Can Do:   Send messages, edit, delete, view sidebar
```

### **Route: /chat/others/[sessionId] (Others Chat)**
```
Timeline: 1-2 seconds (backend API call)
Actions:
  1. Extract sessionId from URL
  2. Auth check
  3. Detect "user_chat_" format
  4. API call to fetch messages
  5. Load in read-only mode
Status:   Read-only access
Can Do:   View messages, copy text
Cannot:   Send messages, edit, delete
```

---

## AUTHENTICATION CHECKS (Every Protected Route)

```
1. localStorage Check
   ├─ Get 'user' from browser storage
   └─ If missing → Redirect to /login

2. Token Verification
   ├─ If NOT back/forward navigation:
   │  └─ Verify token with Microsoft Graph API
   │     └─ GET https://graph.microsoft.com/v1.0/me
   │     └─ Timeout: 10 seconds
   │     └─ If fails → Redirect to /login
   └─ If back/forward → Skip (performance optimization)

3. Domain Check
   ├─ Check if email ends with @cloudfuze.com
   └─ If not → Redirect to /login with error

4. UI Render
   ├─ If auth fails → null (redirect happens)
   └─ If auth passes → Render component
```

---

## DATA STORAGE LOCATIONS

```
OWN CHAT SESSIONS:
  Storage: Browser's localStorage
  Key: "chat_sessions_{userId}"
  Speed: Instant load
  Example:
    {
      id: "cf.conversation.20251208.abc123",
      title: "Migration Planning",
      messages: [...]
    }

OTHERS CHATS:
  Storage: Temporary object only
  Source: Backend API
  Key: NOT saved to localStorage
  Speed: API dependent
  Cleanup: Destroyed after viewing

USER INFO:
  Storage: localStorage
  Key: "user"
  Content: {
    id, email, access_token, refresh_token
  }
```

---

## SESSION ID FORMAT DETECTION

```
Format 1: cf.conversation.20251208.abc123
  ├─ Starts with "cf.conversation."
  ├─ Generated on first message
  └─ Route: /chat/[sessionId]
     └─ Load from localStorage
     └─ Full read/write access

Format 2: user_chat_alice123
  ├─ Starts with "user_chat_"
  ├─ Indicates someone else's chat
  └─ Route: /chat/others/[sessionId]
     └─ Load from backend
     └─ Read-only access only

Detection Logic:
  if (sessionId.startsWith('user_chat_')) {
    → It's Others Chat → Read-only
  } else {
    → It's own chat → Read/write
  }
```

---

## MESSAGE FLOW (Production)

```
USER SENDS MESSAGE IN /chat/new:

Step 1: Input
        └─ User types message

Step 2: Send
        └─ POST /api/chat/send
        └─ Body: { message, session_id: null }
        └─ Headers: { Authorization: Bearer token }

Step 3: Backend Process
        └─ Process message
        └─ Generate response
        └─ Stream back (chunk by chunk)

Step 4: Render
        └─ Each chunk arrives
        └─ marked.js renders markdown
        └─ Display in UI
        └─ Auto-scroll down

Step 5: Save Session
        └─ Generate sessionId (if new)
        └─ Save to localStorage
        └─ Save to backend

Step 6: Navigate
        └─ 100ms after response completes
        └─ router.push(/chat/cf.conversation...)
        └─ URL updates
        └─ Page re-renders with session
        └─ Session appears in sidebar

Result: User on /chat/[sessionId] route
```

---

## ERROR SCENARIOS

```
SCENARIO 1: Token Expired
  → User sees: "Redirecting to login..."
  → Action: localStorage cleared
  → Result: Redirect to /login

SCENARIO 2: Wrong Email Domain
  → User sees: "Only CloudFuze emails allowed"
  → Action: localStorage cleared
  → Result: Redirect to /login

SCENARIO 3: Network Error
  → User sees: "Network error, please retry"
  → Action: None (message stays in input)
  → Result: User can retry when online

SCENARIO 4: Backend Error (5xx)
  → User sees: "Server error, try later"
  → Action: Error logged with trace_id
  → Result: User can still view messages

SCENARIO 5: Invalid Session ID
  → User goes to: /chat/invalid_session_id
  → Action: Session not found in localStorage
  → Result: Show empty chat or error
```

---

## PERFORMANCE IN PRODUCTION

```
ROUTE LOAD TIMES:

/                    → < 1 sec (redirect only)
/login               → 2-3 sec (OAuth setup)
/chat/new            → 2-3 sec (auth + init)
/chat/[id]           → < 500ms (localStorage)
/chat/others/[id]    → 1-2 sec (API call)
/chats               → 500ms (localStorage)

OPTIMIZATIONS:

1. Session Cache
   └─ Load from localStorage (fast)
   └─ No repeated API calls

2. Back/Forward Skip
   └─ Skip token verification on back button
   └─ Instant navigation

3. Lazy Loading
   └─ marked.js loaded on demand
   └─ Sidebar history fetched async

4. Streaming
   └─ Messages arrive incrementally
   └─ User sees responses faster
```

---

## PRODUCTION SECURITY

```
✅ AUTHENTICATION
   • Microsoft OAuth (standard)
   • Access token required
   • CloudFuze domain check

✅ DATA ISOLATION
   • User-specific localStorage keys
   • Others chats not saved
   • Read-only for others

✅ API SECURITY
   • Bearer token in header
   • Backend validates token
   • Session ownership verified

✅ SESSION MANAGEMENT
   • Token refresh on demand
   • Auto re-auth on error
   • Automatic logout

✅ XSS PROTECTION
   • React HTML escaping
   • Markdown from trusted source
   • No user-generated HTML
```

---

## TROUBLESHOOTING IN PRODUCTION

```
USER CAN'T CHAT:
  → Check: Is /chat/new loading?
  → Check: Is auth working? (/login)
  → Check: Is email @cloudfuze.com?
  → Check: Is backend reachable?

MESSAGES NOT SENDING:
  → Check: Network connectivity
  → Check: Token still valid (10 sec check)
  → Check: Backend /chat/send endpoint
  → Check: localStorage size limits

URL NOT CHANGING AFTER MESSAGE:
  → Check: Session saved to localStorage
  → Check: sessionId generated correctly
  → Check: router.push working
  → Manual refresh: Browser refresh

OTHERS CHATS NOT LOADING:
  → Check: User has access permission
  → Check: Backend endpoint working
  → Check: Token has correct scope
  → Manual: Try direct URL

SIDEBAR EMPTY:
  → Check: Sessions saved to localStorage
  → Check: userId matches in keys
  → Manual: Browser DevTools → Application → localStorage
```

---

## ONE-LINER SUMMARY

**Production routing automatically handles authentication, session management, message streaming, and read-only access for others' chats with intelligent URL-based routing that uses localStorage for own sessions and backend for others' sessions.**

---

## DEPLOYMENT COMMANDS (Example)

```bash
# Build production bundle
npm run build

# Start production server
npm run start

# Monitor production logs
npm run logs

# Restart service
npm run restart
```

---

This covers everything about how routes work in production! 🚀

