# Production Routing Guide - Complete Flow

## Overview
This document explains how all routes work together in a production environment and what happens at each step.

---

## 1. URL ENTRY POINTS

### **1.1 User Visits Root Domain**
```
User Action: Opens browser and goes to https://ai.cloudfuze.com/
Request:     GET /
Route:       / (home page)
File:        frontend/src/app/page.tsx
```

**What Happens**:
```
1. Page loads with loading spinner (white background with blue rotating circle)
2. useEffect hook triggers immediately
3. router.replace('/chat/new') redirects user
4. Browser history replaced (user cannot go back to /)
5. User sees /chat/new route
```

**Why replace() instead of push()?**
- `push()` = adds to browser history
- `replace()` = replaces current history entry
- Users shouldn't be able to go back to /

---

## 2. ROUTE HIERARCHY & FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│ User Request: https://ai.cloudfuze.com                      │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │  Route: /               │
        │  File: page.tsx         │
        │  Action: Check if user  │
        │  authenticated?         │
        └────────────┬────────────┘
                     │
              NO ──┬─── YES
                   │
         ┌─────────▼──────┐    ┌───────────┬──────────────┐
         │ Not logged in  │    │ Logged in │              │
         │ Redirect to:   │    │ Redirect  │              │
         │ /login         │    │ to:       │              │
         │                │    │ /chat/new │              │
         └────────────────┘    └───────────┴──────────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │ Route: /chat/new                    │
                        │ File: chat/new/page.tsx             │
                        │ Action: Auth check + Load UI        │
                        └──────────────────┬───────────────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │ STEP 1: Authentication              │
                        │ - Check localStorage for user       │
                        │ - Verify token with Microsoft Graph │
                        │ - Check for @cloudfuze.com email    │
                        │ - If invalid → redirect to /login   │
                        └──────────────────┬───────────────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │ STEP 2: Check marked.js library     │
                        │ - Wait for marked library to load   │
                        │ - This library renders markdown     │
                        │ - Without it, messages won't render │
                        └──────────────────┬───────────────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │ STEP 3: Initialize Chat App         │
                        │ - Call initializeChatApp()          │
                        │ - Create new empty session          │
                        │ - Load suggested questions          │
                        │ - Render empty chat interface       │
                        └──────────────────┬───────────────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │ STEP 4: Show UI                     │
                        │ - Sidebar with "My Chats"           │
                        │ - Empty chat area with suggestions  │
                        │ - Input field ready for message     │
                        └──────────────────┬───────────────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │ User types message and sends...     │
                        └──────────────────┬───────────────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │ STEP 5: First Message Sent          │
                        │ - Message saved to session          │
                        │ - API call to backend: /chat/send   │
                        │ - Response streams back             │
                        │ - Session saved to localStorage     │
                        └──────────────────┬───────────────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │ STEP 6: Auto-Navigation             │
                        │ - After response completes          │
                        │ - URL changes to:                   │
                        │   /chat/cf.conversation.20251208... │
                        │ - Page re-renders with sessionId    │
                        │ - Session now appears in sidebar    │
                        └──────────────────────────────────────┘
```

---

## 3. PRODUCTION ROUTES EXPLAINED

### **Route 1: / (Root/Home)**
```
URL:           https://ai.cloudfuze.com/
File:          frontend/src/app/page.tsx
Middleware:    None (React handles redirect)
Purpose:       Entry point, redirects to /chat/new
Duration:      < 1 second (immediately redirects)

Flow:
  User visits domain
       ↓
  Loads / page
       ↓
  useEffect triggers
       ↓
  router.replace('/chat/new')
       ↓
  Browser goes to /chat/new
```

---

### **Route 2: /login**
```
URL:           https://ai.cloudfuze.com/login
File:          frontend/src/app/login/page.tsx
Middleware:    None (public route)
Purpose:       Microsoft OAuth login
Duration:      Redirects to Microsoft login, then back

Flow:
  User clicks "Login with Microsoft"
       ↓
  Redirects to Microsoft OAuth endpoint
       ↓
  User enters credentials
       ↓
  Microsoft redirects back to app with auth code
       ↓
  Backend exchanges code for token
       ↓
  Token stored in localStorage
       ↓
  Redirects to /chat/new
```

---

### **Route 3: /chat/new (New Chat)**
```
URL:           https://ai.cloudfuze.com/chat/new
File:          frontend/src/app/chat/new/page.tsx
Protected:     YES (requires authentication)
Purpose:       Start a new chat session
Duration:      Until first message sent

Execution Flow in Production:
┌────────────────────────────────────────┐
│ 1. ROUTE LOADS                         │
│    - Browser requests /chat/new        │
│    - Next.js server serves HTML        │
│    - React hydrates page               │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 2. AUTHENTICATION CHECK (Client-side)  │
│    - useEffect runs on component mount │
│    - Check localStorage.getItem('user')│
│    - If no user → redirect to /login   │
│    - Prevent back/forward re-checks    │
│      (Performance: skip API call)      │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 3. TOKEN VALIDATION                    │
│    - If not back/forward navigation:   │
│      • Verify token with Microsoft     │
│      • GET https://graph.microsoft.com │
│    - Timeout: 10 seconds               │
│    - Invalid token → redirect /login   │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 4. DOMAIN CHECK                        │
│    - Check user.email ends with       │
│      @cloudfuze.com                   │
│    - Non-CloudFuze → redirect /login   │
│      with error param                 │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 5. SHOW LOADING STATE (Optional)       │
│    - Loading spinner for UX            │
│    - setIsLoading(true)                │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 6. WAIT FOR MARKED.JS                  │
│    - Check if window.marked exists     │
│    - Poll every 100ms                  │
│    - Timeout: not set (wait forever)   │
│    - This is for markdown rendering    │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 7. INITIALIZE CHAT APP                 │
│    - Call initializeChatApp()          │
│    - initialSessionId = null (new)     │
│    - Create new session ID             │
│    - Load suggested questions          │
│    - Render UI:                        │
│      • ChatSidebar                     │
│      • ChatInterface (empty state)     │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 8. READY FOR INPUT                     │
│    - User sees empty chat              │
│    - Input field active                │
│    - Suggested questions visible       │
│    - Waiting for user message          │
└────────────────────────────────────────┘
```

**Key Points**:
- No session created until first message
- URL stays at `/chat/new` until message sent
- Session ID generated when needed
- Lightweight initial load

---

### **Route 4: /chat/[sessionId] (Active Chat)**
```
URL:           https://ai.cloudfuze.com/chat/cf.conversation.20251208.abc123
File:          frontend/src/app/chat/[sessionId]/page.tsx
Protected:     YES (requires authentication)
Dynamic:       YES (sessionId is dynamic parameter)
Purpose:       View/continue existing chat session

Execution Flow in Production:
┌────────────────────────────────────────┐
│ 1. EXTRACT SESSION ID FROM URL         │
│    - useParams() gets [sessionId]      │
│    - sessionId = params.sessionId      │
│    - Example: cf.conversation.20251208 │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 2. SAME AUTH CHECKS AS /chat/new       │
│    - Verify user logged in             │
│    - Validate token with Microsoft     │
│    - Check CloudFuze domain            │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 3. DETECT SESSION TYPE                 │
│    - Check if sessionId starts with    │
│      "user_chat_" (Others Chat)        │
│    - If YES → load from backend        │
│    - If NO → load from localStorage    │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 4. LOAD SESSION DATA                   │
│                                        │
│ FOR OWN SESSION:                       │
│   - Get from localStorage               │
│   - Key: chat_sessions_{userId}        │
│   - Find session with matching ID      │
│                                        │
│ FOR OTHERS SESSION:                    │
│   - Extract user_id from sessionId     │
│   - API call to backend:               │
│     GET /chat/sessions/messages/{uid}  │
│   - Load messages from other user      │
│   - Set isReadOnly = true              │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 5. RENDER CHAT WITH HISTORY            │
│    - Display all previous messages     │
│    - Markdown rendering active         │
│    - Feedback buttons visible          │
│    - Input field active (own) or       │
│      disabled (others)                 │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 6. LOAD SIDEBAR HISTORY                │
│    - Fetch all user's sessions         │
│    - Fetch others' recent sessions     │
│    - Highlight current session         │
│    - User can click to switch          │
└────────────────────────────────────────┘
```

**Key Points**:
- Fast load (data from localStorage for own sessions)
- Detects session type automatically
- Read-only for Others Chats
- Full history displayed immediately

---

### **Route 5: /chat/others/[sessionId] (Others Chat)**
```
URL:           https://ai.cloudfuze.com/chat/others/user_chat_alice123
File:          frontend/src/app/chat/others/[sessionId]/page.tsx
Protected:     YES (requires authentication)
Dynamic:       YES (sessionId is dynamic parameter)
Purpose:       View other user's chat (READ-ONLY)

Execution Flow in Production:
┌────────────────────────────────────────┐
│ 1. EXTRACT SESSION ID FROM URL         │
│    - useParams() gets [sessionId]      │
│    - sessionId = params.sessionId      │
│    - Example: user_chat_alice123       │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 2. AUTHENTICATION CHECKS               │
│    - Same as other protected routes    │
│    - Verify CloudFuze email            │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 3. INITIALIZE CHAT (Others Mode)       │
│    - Call initializeChatApp()          │
│    - Pass initialSessionId             │
│    - System detects "user_chat_"       │
│    - Knows it's an Others Chat         │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 4. FETCH FROM BACKEND                  │
│    - Extract userId from sessionId     │
│    - API: GET /chat/sessions/messages/ │
│    - Authorization header required     │
│    - Backend returns:                  │
│      { title, messages: [...] }        │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 5. LOAD IN READ-ONLY MODE              │
│    - Messages displayed                │
│    - Input disabled:                   │
│      "Read-only mode - You cannot      │
│       send messages"                   │
│    - Send button disabled              │
│    - Copy/view buttons work            │
└────────────────────┬───────────────────┘
                     │
┌────────────────────▼───────────────────┐
│ 6. NOT SAVED TO LOCALSTORAGE           │
│    - Temporary session object          │
│    - Destroyed after viewing           │
│    - No data pollution                 │
└────────────────────────────────────────┘
```

**Key Points**:
- Separate route for clear URL structure
- Always fetches from backend (not localStorage)
- Temporary session (not saved)
- Always read-only
- No access to user's chat history

---

### **Route 6: /chats (All Chats Grid)**
```
URL:           https://ai.cloudfuze.com/chats
File:          frontend/src/app/chats/page.tsx
Protected:     YES (requires authentication)
Purpose:       Browse all user's chat sessions
Duration:      User can stay indefinitely

Flow:
  User visits /chats
       ↓
  Authentication check
       ↓
  Load all sessions from localStorage
       ↓
  Display as grid/card view
       ↓
  Click card → navigate to /chat/[sessionId]
```

---

## 4. AUTHENTICATION FLOW IN PRODUCTION

```
┌─────────────────────────────────────────────────────┐
│ PRODUCTION AUTHENTICATION ARCHITECTURE              │
└─────────────────────────────────────────────────────┘

     ┌─────────────────────────────────────┐
     │ 1. User Not Logged In               │
     │    Visit: https://ai.cloudfuze.com  │
     └──────────────┬────────────────────┘
                    │
     ┌──────────────▼─────────────────────┐
     │ 2. Redirect to /login              │
     │    Show: Login with Microsoft btn   │
     └──────────────┬────────────────────┘
                    │
     ┌──────────────▼─────────────────────┐
     │ 3. Microsoft OAuth Process         │
     │    - Click "Login with Microsoft"  │
     │    - Redirects to Microsoft        │
     │    - User enters password          │
     │    - Microsoft redirects back      │
     └──────────────┬────────────────────┘
                    │
     ┌──────────────▼─────────────────────┐
     │ 4. Backend Auth Code Exchange      │
     │    Code → Access Token + Refresh   │
     │    Store in localStorage           │
     └──────────────┬────────────────────┘
                    │
     ┌──────────────▼─────────────────────┐
     │ 5. Token Stored in Browser         │
     │    localStorage.setItem('user', {  │
     │      id: "...",                    │
     │      email: "user@cloudfuze.com",  │
     │      access_token: "...",          │
     │      refresh_token: "..."          │
     │    })                              │
     └──────────────┬────────────────────┘
                    │
     ┌──────────────▼─────────────────────┐
     │ 6. Redirect to /chat/new           │
     │    Ready to chat!                  │
     └─────────────────────────────────────┘

ONGOING VERIFICATION:
  On every route entry:
    1. Check if user in localStorage
    2. If NO back/forward nav:
       - Verify token with Microsoft Graph
       - GET https://graph.microsoft.com/v1.0/me
    3. Check email ends with @cloudfuze.com
    4. If invalid → redirect /login
```

---

## 5. MESSAGE FLOW IN PRODUCTION

```
USER SENDS MESSAGE IN /chat/new:

1. USER INPUT
   User types: "How do I migrate files?"
   Clicks send button
                    ↓
2. MESSAGE SAVED TO DOM
   <div class="message user">
     How do I migrate files?
   </div>
                    ↓
3. API REQUEST
   POST /api/chat/send
   Body: {
     message: "How do I migrate files?",
     session_id: null (new session)
   }
   Authorization: Bearer {access_token}
                    ↓
4. STREAMING RESPONSE
   Backend starts streaming response
   Each chunk: { type: 'message', content: '...' }
                    ↓
5. MARKDOWN RENDERING
   As chunks arrive:
   - Build response text
   - marked.js converts markdown
   - HTML rendered in DOM
   - Auto-scroll to bottom
                    ↓
6. SESSION CREATED
   When first message completes:
   - Generate sessionId
   - Save to localStorage
   - Save session object
                    ↓
7. AUTO-NAVIGATION
   100ms after response completes:
   router.push(`/chat/${sessionId}`)
   URL changes to: /chat/cf.conversation.20251208.abc...
                    ↓
8. PAGE RE-RENDERS
   New route loaded
   Same layout, now with sessionId
   Session appears in sidebar
```

---

## 6. SESSION STORAGE IN PRODUCTION

```
LOCALSTORAGE STRUCTURE (Browser):

{
  "user_${userId}": {
    id: "user123",
    email: "user@cloudfuze.com",
    access_token: "eyJ0eXAiOiJKV1QiLCJhbGc...",
    refresh_token: "0.ARcAxRR4Y..."
  },
  
  "chat_sessions_${userId}": [
    {
      id: "cf.conversation.20251208.abc123",
      title: "Migration Planning",
      timestamp: 1733686800000,
      createdAt: 1733686800000,
      messages: [
        { role: "user", content: "How to migrate?" },
        { role: "assistant", content: "CloudFuze..." }
      ]
    }
  ],
  
  "deleted_chat_sessions_${userId}": [
    // Soft-deleted sessions (can be restored)
  ],
  
  "chatbot_session_id_${userId}": "cf.conversation.20251208.abc123",
  
  "recommended_questions_${messageIndex}": [
    "What next?", "How does...?"
  ]
}
```

**Important**:
- All prefixed with userId (multi-user safe)
- Persists even after browser close
- Survives page refresh
- Others Chats NOT stored here (temporary only)

---

## 7. ERROR HANDLING IN PRODUCTION

```
SCENARIO: Token Expires
  1. User on /chat/cf.conversation...
  2. User sends message
  3. API returns 401 Unauthorized
  4. Frontend catches error
  5. localStorage.removeItem('user')
  6. Redirect to /login?error=session_expired
  7. User logs in again with Microsoft

SCENARIO: Non-CloudFuze Email
  1. User logs in with non-work email
  2. Auth check detects email ≠ @cloudfuze.com
  3. localStorage.removeItem('user')
  4. Redirect to /login?error=unauthorized_domain
  5. Show error: "Only CloudFuze emails allowed"

SCENARIO: Network Error
  1. User offline
  2. Message send fails
  3. Show toast: "Network error, please retry"
  4. Message stays in input
  5. User can retry when online

SCENARIO: Server Error (5xx)
  1. Backend returns 500 error
  2. Frontend shows: "Server error, try later"
  3. Logs error with trace_id
  4. User can still view existing messages
```

---

## 8. PERFORMANCE OPTIMIZATIONS IN PRODUCTION

```
WHAT'S OPTIMIZED:

1. Back/Forward Navigation
   - Skip token verification on back button
   - Fast route switching
   - Sidebar refresh still happens

2. Session Loading
   - Own sessions: Load from localStorage (instant)
   - Others sessions: Load from backend (API call)
   - Sidebar lazy loads on demand

3. Markdown Rendering
   - marked.js loaded asynchronously
   - Render as chunks arrive (streaming)
   - Auto-scroll uses requestAnimationFrame

4. localStorage Usage
   - User-specific keys (safe in shared browsers)
   - Cleanup old sessions (optional)
   - Automatic soft-delete of old chats

5. API Calls
   - Authorization headers included
   - Timeout: 10 seconds
   - Error handling for all scenarios
```

---

## 9. SECURITY IN PRODUCTION

```
SECURITY LAYERS:

1. AUTHENTICATION
   ✅ Microsoft OAuth (industry standard)
   ✅ Access token required for all API calls
   ✅ CloudFuze email domain check
   ✅ 10-second token verification timeout

2. DATA ISOLATION
   ✅ Each user has separate localStorage keys
   ✅ Others' chats not saved locally
   ✅ Read-only mode prevents modifications

3. API SECURITY
   ✅ Bearer token in Authorization header
   ✅ Backend validates token
   ✅ Session ownership verified server-side

4. SESSION MANAGEMENT
   ✅ Token refresh before expiry
   ✅ Automatic re-authentication on token error
   ✅ Clean logout (token removed)

5. XSS PROTECTION
   ✅ React/Next.js built-in HTML escaping
   ✅ Markdown rendering from trusted backend
   ✅ No user-generated HTML in messages
```

---

## 10. QUICK REFERENCE: ROUTE BEHAVIORS

| Route | Protected | Source | Speed | Special |
|-------|-----------|--------|-------|---------|
| `/` | ❌ | Client | Instant | Redirects to /chat/new |
| `/login` | ❌ | Server | Medium | OAuth flow |
| `/chat/new` | ✅ | localStorage | Fast | Creates session on 1st msg |
| `/chat/[id]` | ✅ | localStorage | Fast | Own chat or others |
| `/chat/others/[id]` | ✅ | Backend | Medium | Always read-only |
| `/chats` | ✅ | localStorage | Fast | Grid view of all |

---

## 11. PRODUCTION DEPLOYMENT CHECKLIST

```
BEFORE DEPLOYING TO PRODUCTION:

ENVIRONMENT:
  ✅ Set NEXT_PUBLIC_API_URL to production backend
  ✅ Set OAuth client_id to production Microsoft
  ✅ Set OAuth redirect_uri to production domain
  ✅ SSL certificate enabled (HTTPS only)

SECURITY:
  ✅ Cache-Control headers set
  ✅ Content-Security-Policy headers
  ✅ CORS configured for backend
  ✅ Rate limiting enabled

MONITORING:
  ✅ Error logging enabled
  ✅ Performance monitoring active
  ✅ User analytics tracking
  ✅ Session management logs

TESTING:
  ✅ All routes tested in production env
  ✅ Token refresh tested
  ✅ Error handling tested
  ✅ Back/forward navigation tested
  ✅ Different user email domains tested
```

---

## Summary

In production, the routing system works as follows:

1. **Entry Point**: User visits domain → redirects to `/chat/new`
2. **Authentication**: Every protected route verifies user and token
3. **Session Management**: Sessions stored locally for own chats
4. **Others Chats**: Separate route, loaded from backend, always read-only
5. **Auto-Navigation**: After first message, URL updates with session ID
6. **Error Handling**: Invalid tokens redirect to login
7. **Performance**: Local storage for fast loads, backend for Others Chats
8. **Security**: OAuth tokens, email domain check, read-only enforcement

All routes work seamlessly in production with automatic authentication, session management, and error recovery! 🚀

