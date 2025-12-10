# Cross-Profile Session Sync Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER AUTHENTICATION LAYER                           │
│                     (Microsoft OAuth - Same Credentials)                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
┌──────────────────────────────────┐  ┌──────────────────────────────────┐
│     Chrome Profile A             │  │     Chrome Profile B             │
│  ┌────────────────────────────┐  │  │  ┌────────────────────────────┐  │
│  │   Frontend (React/Next.js) │  │  │  │   Frontend (React/Next.js) │  │
│  │                            │  │  │  │                            │  │
│  │  • User logs in            │  │  │  │  • User logs in            │  │
│  │  • initAuth() called       │  │  │  │  • initAuth() called       │  │
│  │  • fetchAndMergeSessions() │  │  │  │  • fetchAndMergeSessions() │  │
│  └────────────────────────────┘  │  │  └────────────────────────────┘  │
│               │                   │  │               │                   │
│               │ GET /sessions     │  │               │ GET /sessions     │
│               │ ?include_messages │  │               │ ?include_messages │
│               │ =true             │  │               │ =true             │
│               ▼                   │  │               ▼                   │
│  ┌────────────────────────────┐  │  │  ┌────────────────────────────┐  │
│  │   localStorage             │  │  │  │   localStorage             │  │
│  │                            │  │  │  │                            │  │
│  │  chat_sessions: [          │  │  │  │  chat_sessions: [          │  │
│  │    {                       │  │  │  │    {                       │  │
│  │      id: "session1",       │  │  │  │      id: "session1", ◄─────┼──┼─┐
│  │      messages: [...]       │  │  │  │      messages: [...]       │  │ │
│  │    },                      │  │  │  │    },                      │  │ │
│  │    {                       │  │  │  │    {                       │  │ │
│  │      id: "session2",       │  │  │  │      id: "session2", ◄─────┼──┼─┤
│  │      messages: [...]       │  │  │  │      messages: [...]       │  │ │
│  │    }                       │  │  │  │    }                       │  │ │
│  │  ]                         │  │  │  │  ]                         │  │ │
│  └────────────────────────────┘  │  │  └────────────────────────────┘  │ │
│               │                   │  │               │                   │ │
│               │ POST /sessions    │  │               │ POST /sessions    │ │
│               │ /save (with msgs) │  │               │ /save (with msgs) │ │
└───────────────┼───────────────────┘  └───────────────┼───────────────────┘ │
                │                                      │                     │
                └──────────────────┬───────────────────┘                     │
                                   ▼                                         │
        ┌─────────────────────────────────────────────────────────┐         │
        │              BACKEND API (FastAPI)                       │         │
        │  ┌───────────────────────────────────────────────────┐  │         │
        │  │  POST /chat/sessions/save                         │  │         │
        │  │  • Receives session with messages                 │  │         │
        │  │  • Validates user authentication                  │  │         │
        │  │  • Calls mongodb_memory.save_session()            │  │         │
        │  └───────────────────────────────────────────────────┘  │         │
        │                           │                              │         │
        │  ┌───────────────────────────────────────────────────┐  │         │
        │  │  GET /chat/sessions/user/{user_id}                │  │         │
        │  │  ?include_messages=true                           │  │         │
        │  │  • Validates user authentication                  │  │         │
        │  │  • Calls mongodb_memory.get_user_sessions()       │  │         │
        │  │  • Returns all sessions with messages             │  │         │
        │  └───────────────────────────────────────────────────┘  │         │
        └───────────────────────────┬─────────────────────────────┘         │
                                    ▼                                        │
        ┌─────────────────────────────────────────────────────────┐         │
        │         MongoDB Atlas (Cloud Database)                  │         │
        │  ┌───────────────────────────────────────────────────┐  │         │
        │  │  Collection: chat_sessions                        │  │         │
        │  │                                                   │  │         │
        │  │  Document Structure:                              │  │         │
        │  │  {                                                │  │         │
        │  │    session_id: "cf.conversation.20251208.abc",   │  │◄────────┘
        │  │    user_id: "user@cloudfuze.com",                │  │  SAME DATA
        │  │    title: "Chat about features",                 │  │  AVAILABLE
        │  │    created_at: ISODate(...),                     │  │  TO BOTH
        │  │    updated_at: ISODate(...),                     │  │  PROFILES
        │  │    message_count: 6,                             │  │
        │  │    messages: [                                   │  │
        │  │      {role: "user", content: "..."},             │  │
        │  │      {role: "assistant", content: "..."}         │  │
        │  │    ]                                             │  │
        │  │  }                                                │  │
        │  │                                                   │  │
        │  │  Indexes:                                         │  │
        │  │  • session_id (unique)                           │  │
        │  │  • user_id                                       │  │
        │  │  • updated_at (desc)                             │  │
        │  └───────────────────────────────────────────────────┘  │
        └─────────────────────────────────────────────────────────┘
```

## Data Flow Sequence

### Scenario 1: User Creates Chat in Profile A

```
┌─────────┐                  ┌──────────┐                ┌─────────┐
│Profile A│                  │ Backend  │                │ MongoDB │
└────┬────┘                  └────┬─────┘                └────┬────┘
     │                            │                           │
     │ 1. User sends message      │                           │
     ├───────────────────────────►│                           │
     │                            │                           │
     │ 2. Save to localStorage    │                           │
     │    (immediate)             │                           │
     │◄───────────────────────────┤                           │
     │                            │                           │
     │ 3. POST /chat/sessions/save│                           │
     │    (with full messages)    │                           │
     ├───────────────────────────►│                           │
     │                            │                           │
     │                            │ 4. Store in MongoDB       │
     │                            ├──────────────────────────►│
     │                            │                           │
     │                            │ 5. Confirm saved          │
     │                            │◄──────────────────────────┤
     │                            │                           │
     │ 6. Success response        │                           │
     │◄───────────────────────────┤                           │
     │                            │                           │
```

### Scenario 2: User Opens Profile B (Same Account)

```
┌─────────┐                  ┌──────────┐                ┌─────────┐
│Profile B│                  │ Backend  │                │ MongoDB │
└────┬────┘                  └────┬─────┘                └────┬────┘
     │                            │                           │
     │ 1. User logs in            │                           │
     ├───────────────────────────►│                           │
     │                            │                           │
     │ 2. Auth successful         │                           │
     │◄───────────────────────────┤                           │
     │                            │                           │
     │ 3. initAuth() called       │                           │
     │                            │                           │
     │ 4. fetchAndMergeSessions() │                           │
     │                            │                           │
     │ 5. GET /sessions/user/...  │                           │
     │    ?include_messages=true  │                           │
     ├───────────────────────────►│                           │
     │                            │                           │
     │                            │ 6. Query user sessions    │
     │                            ├──────────────────────────►│
     │                            │                           │
     │                            │ 7. Return all sessions    │
     │                            │    with messages          │
     │                            │◄──────────────────────────┤
     │                            │                           │
     │ 8. Sessions array          │                           │
     │    [{id, title, messages}] │                           │
     │◄───────────────────────────┤                           │
     │                            │                           │
     │ 9. Merge with localStorage │                           │
     │    (add missing sessions)  │                           │
     │                            │                           │
     │ 10. Render UI with all     │                           │
     │     sessions visible       │                           │
     │                            │                           │
```

## Key Components

### 1. Frontend Session Manager
**Location**: `frontend/src/app/page.tsx`

**Responsibilities**:
- Manage localStorage sessions
- Sync sessions to backend on save
- Fetch sessions from backend on login
- Merge backend and local sessions
- Render session history UI

**Key Functions**:
```typescript
getAllSessions()              // Get sessions from localStorage
saveAllSessions(sessions)     // Save sessions to localStorage
syncSessionToBackend(session) // Upload session to backend
fetchAndMergeUserSessions()   // Download and merge sessions
```

### 2. Backend Session API
**Location**: `app/endpoints.py`

**Responsibilities**:
- Authenticate requests
- Validate session data
- Store/retrieve sessions from MongoDB
- Enforce user access control

**Key Endpoints**:
```python
POST   /chat/sessions/save              # Save session with messages
GET    /chat/sessions/user/{user_id}    # Get all user sessions
GET    /chat/sessions/{session_id}      # Get specific session
DELETE /chat/sessions/{session_id}      # Delete session (future)
```

### 3. MongoDB Memory Manager
**Location**: `app/mongodb_memory.py`

**Responsibilities**:
- Manage MongoDB connection
- CRUD operations for sessions
- Index management
- Data transformation

**Key Methods**:
```python
save_session(session_data)                    # Store session
get_user_sessions(user_id, include_messages)  # Retrieve sessions
get_session_by_id(session_id, include_messages) # Get one session
```

### 4. MongoDB Database
**Collection**: `chat_sessions`

**Responsibilities**:
- Persistent storage
- Cross-profile data source
- Query optimization via indexes
- Data consistency

**Indexes**:
```javascript
{ session_id: 1 }      // Unique, for lookups
{ user_id: 1 }         // For user queries
{ updated_at: -1 }     // For sorting (recent first)
```

## Security Model

```
┌──────────────────────────────────────────────────────────┐
│                   Security Layers                         │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  1. Microsoft OAuth Authentication                        │
│     • User must login with @cloudfuze.com email          │
│     • JWT token issued on successful auth                │
│                                                           │
│  2. API Authentication (require_auth)                     │
│     • All endpoints require valid JWT token              │
│     • Token verified with Microsoft Graph API            │
│                                                           │
│  3. Authorization (verify_user_access)                    │
│     • User can only access their own sessions            │
│     • user_id extracted from verified token              │
│     • IDOR protection: user_id must match token          │
│                                                           │
│  4. Data Isolation                                        │
│     • Sessions filtered by user_id in MongoDB            │
│     • No cross-user data leakage possible                │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## Performance Characteristics

### Write Performance (Save Session)
- **Operation**: Single MongoDB upsert
- **Time Complexity**: O(1)
- **Network**: 1 HTTP request
- **Typical Latency**: 50-100ms

### Read Performance (Fetch Sessions)
- **Operation**: MongoDB query with limit
- **Time Complexity**: O(log n) with index
- **Network**: 1 HTTP request
- **Typical Latency**: 100-200ms
- **Data Transfer**: ~20KB for 50 sessions with messages

### Merge Performance (Client-side)
- **Operation**: Set-based deduplication
- **Time Complexity**: O(n + m) where n=local, m=backend
- **Typical Time**: <10ms for 100 sessions

## Scalability Considerations

### Current Limits
- **Sessions per user**: 50 (default limit)
- **Messages per session**: Unlimited (practical limit ~1000)
- **Message size**: ~200 bytes average
- **Document size**: ~20KB per session (well under 16MB limit)

### Future Optimizations
1. **Pagination**: Cursor-based for >50 sessions
2. **Lazy Loading**: Load messages on-demand
3. **Compression**: gzip for large message arrays
4. **Caching**: Redis for frequently accessed sessions
5. **Sharding**: Partition by user_id for scale

## Error Handling

```
┌──────────────────────────────────────────────────────────┐
│              Error Scenarios & Handling                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  1. Network Failure (Fetch)                               │
│     • Fallback to localStorage only                       │
│     • User sees local sessions                            │
│     • Retry on next login                                 │
│                                                           │
│  2. Network Failure (Save)                                │
│     • Session saved locally                               │
│     • Background retry (future enhancement)               │
│     • User can continue chatting                          │
│                                                           │
│  3. Authentication Expired                                │
│     • Redirect to login                                   │
│     • Sessions preserved in localStorage                  │
│     • Sync after re-authentication                        │
│                                                           │
│  4. MongoDB Connection Error                              │
│     • Backend returns 500 error                           │
│     • Frontend falls back to localStorage                 │
│     • Admin alerted via logs                              │
│                                                           │
│  5. Duplicate Session IDs                                 │
│     • Set-based merge prevents duplicates                 │
│     • Existing session not overwritten                    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## Monitoring & Observability

### Metrics to Track
1. **Session Sync Success Rate**: % of successful syncs
2. **Fetch Latency**: Time to fetch sessions on login
3. **Session Count per User**: Average and max
4. **Message Count per Session**: Average and max
5. **Storage Size**: MongoDB collection size growth

### Logging Points
```javascript
[SESSIONS] Fetching sessions from backend for user: {user_id}
[SESSIONS] Fetched {count} sessions from backend
[SESSIONS] Added {count} sessions from backend
[SESSION] Failed to sync session to backend: {error}
[SESSION] Saved session {session_id} for user {user_id}
```

### Health Checks
- MongoDB connection status
- API endpoint response times
- Session sync success rate
- User authentication rate

---

**Last Updated**: December 8, 2025
**Version**: 1.0
**Status**: Production Ready

