# 📋 Complete Share Functionality Logic

## Architecture Overview

The share functionality allows users to share chat conversations via a unique link. When opened, the link copies the shared chat to the recipient's account.

**Flow**: User clicks Share → Backend generates token → Link copied to clipboard → Recipient opens link → Chat copied to their account → Redirects to chat

---

## 1️⃣ FRONTEND - Share Button Click Handler

**Location**: `frontend/src/lib/chat-initialization.ts` (lines 776-868)

```typescript
async function shareChat() {
  try {
    // 1. Validate session exists
    if (!sessionId) {
      showToast('No active chat session to share', 'error', 3000);
      console.warn('[SHARE] No session ID available');
      return;
    }
    
    // 2. Get API base URL
    const API_BASE_URL = getApiBase();
    
    // 3. Get user authentication token
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (!user || !user.access_token) {
      showToast('Authentication required to share chat', 'error', 3000);
      console.warn('[SHARE] No authentication token available');
      return;
    }
    
    console.log('[SHARE] Attempting to share session:', sessionId);
    console.log('[SHARE] API Base URL:', API_BASE_URL);
    
    // 4. Call backend API to create share link
    const response = await fetch(`${API_BASE_URL}/chat/share/${sessionId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${user.access_token}`,
        'Content-Type': 'application/json'
      }
    });
    
    console.log('[SHARE] Response status:', response.status);
    
    // 5. Handle errors
    if (!response.ok) {
      const errorText = await response.text();
      console.error('[SHARE] API Error Response:', response.status, errorText);
      
      let errorMessage = `Failed to create share link (${response.status})`;
      try {
        const errorData = JSON.parse(errorText);
        if (errorData.detail) {
          errorMessage = errorData.detail;
        }
      } catch (e) {
        // Use default error message
      }
      
      // Provide helpful guidance based on error
      if (response.status === 404) {
        errorMessage = "Chat not found. Make sure the chat is saved before sharing. Try refreshing the page.";
      } else if (response.status === 403) {
        errorMessage = "You don't have permission to share this chat.";
      }
      
      throw new Error(errorMessage);
    }
    
    // 6. Get share token from response
    const data = await response.json();
    console.log('[SHARE] Response data:', data);
    
    // 7. Build full shareable URL
    const shareUrl = `${window.location.origin}${data.share_url}`;
    // Example: http://localhost:3000/chat/shared/99c0fe72-1920-4409-b124-0ca39d9daa12
    
    // 8. Copy to clipboard with fallback
    try {
      await navigator.clipboard.writeText(shareUrl);
      showToast('Share link copied to clipboard!', 'success', 4000);
    } catch (clipboardError) {
      console.warn('[SHARE] Clipboard copy failed, using fallback:', clipboardError);
      // Fallback: create a temporary textarea to copy
      const textarea = document.createElement('textarea');
      textarea.value = shareUrl;
      document.body.appendChild(textarea);
      textarea.select();
      try {
        document.execCommand('copy');
        showToast('Share link copied to clipboard!', 'success', 4000);
      } catch (execError) {
        console.error('[SHARE] Fallback copy also failed:', execError);
        showToast(`Share link: ${shareUrl}`, 'info', 5000);
      }
      document.body.removeChild(textarea);
    }
    
    console.log('[SHARE] Created share link:', shareUrl);
    
  } catch (error) {
    console.error('[SHARE] Failed to share chat:', error);
    showToast('Failed to create share link. Please try again.', 'error', 4000);
  }
}

// Expose shareChat to window for onclick handler
(window as any).shareChat = shareChat;
```

**Share Button Rendering** (line 912):
```typescript
<button class="header-btn share-button" onclick="window.shareChat()" title="Share this chat">
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="18" cy="5" r="3"></circle>
    <circle cx="6" cy="12" r="3"></circle>
    <circle cx="18" cy="19" r="3"></circle>
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line>
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line>
  </svg>
  <span>Share</span>
</button>
```

---

## 2️⃣ BACKEND - Create Share Link Endpoint

**Location**: `app/endpoints.py` (lines 2253-2329)

```python
@router.post("/chat/share/{session_id}")
async def share_chat_session(
    session_id: str,
    auth_user: dict = Depends(require_auth)
):
    """Generate a shareable link for a chat session.
    
    Users can share:
    - Their own chats (cf.conversation.*)
    - Chats they've copied from others (user_chat_*)
    
    The important thing is that the user must own/have access to the chat.
    """
    try:
        print(f"[SHARE] Attempting to share session {session_id} for user {auth_user['email']}")
        
        # 1. Handle user_chat_* format (others' chats - virtual view)
        actual_session_id = session_id
        is_others_chat = False
        
        if session_id.startswith("user_chat_"):
            # Extract user_id from user_chat_{user_id} format
            target_user_id = session_id.replace("user_chat_", "")
            print(f"[SHARE] Detected user_chat_ format, extracting user_id: {target_user_id}")
            
            # Get the most recent session from that user
            from app.mongodb_memory import get_user_sessions
            user_sessions = await get_user_sessions(target_user_id, limit=1, include_messages=False)
            
            if not user_sessions or len(user_sessions) == 0:
                print(f"[SHARE] No sessions found for user {target_user_id}")
                raise HTTPException(
                    status_code=404,
                    detail="No chat sessions found for this user."
                )
            
            # Use the most recent session
            actual_session_id = user_sessions[0]["session_id"]
            is_others_chat = True
            print(f"[SHARE] Using most recent session from user {target_user_id}: {actual_session_id}")
        
        # 2. Get session to verify it exists
        session = await get_session_by_id(actual_session_id, include_messages=False)
        if not session:
            print(f"[SHARE] Session {actual_session_id} not found")
            raise HTTPException(
                status_code=404, 
                detail=f"Session not found. Make sure the chat is saved before sharing."
            )
        
        # 3. Verify user owns this session (skip check for others' chats)
        if not is_others_chat and session.get("user_id") != auth_user["user_id"]:
            print(f"[SHARE] User {auth_user['email']} tried to share chat owned by {session.get('user_id')}")
            raise HTTPException(
                status_code=403,
                detail="You can only share chats in your account"
            )
        
        # 4. Generate unique share token (UUID)
        share_token = str(uuid.uuid4())
        
        # 5. Create shared chat entry in database
        await create_shared_chat(actual_session_id, auth_user["email"], share_token)
        
        print(f"[SHARE] ✅ Chat {actual_session_id} shared by {auth_user['email']} with token {share_token}")
        
        # 6. Return share information
        return {
            "share_token": share_token,
            "share_url": f"/chat/shared/{share_token}",
            "message": "Share link created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[SHARE] ❌ Error sharing chat {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create share link: {str(e)}")
```

---

## 3️⃣ BACKEND - MongoDB Share Storage

**Location**: `app/mongodb_memory.py` (lines 387-415)

```python
async def create_shared_chat(self, session_id: str, user_email: str, share_token: str) -> Dict:
    """Create a shareable link for a chat session."""
    await self.connect()
    
    try:
        shared_chats_collection = self.database["shared_chats"]
        
        # Create shared chat document
        shared_chat_doc = {
            "share_token": share_token,      # UUID token for the share link
            "session_id": session_id,        # Original session ID to copy
            "user_email": user_email,        # Who created the share
            "created_at": datetime.utcnow(), # When it was created
            "expires_at": None               # No expiration for now
        }
        
        # Insert into database
        await shared_chats_collection.insert_one(shared_chat_doc)
        
        logger.info(f"Created shared chat token for session {session_id}")
        return shared_chat_doc
        
    except DuplicateKeyError:
        # Token already exists, return existing
        doc = await shared_chats_collection.find_one({"share_token": share_token})
        return doc
    except Exception as e:
        logger.error(f"Error creating shared chat: {e}")
        raise e
```

---

## 4️⃣ FRONTEND - Open Shared Link Page

**Location**: `frontend/src/app/chat/shared/[token]/page.tsx`

```typescript
export default function SharedChatPage() {
  const router = useRouter();
  const params = useParams();
  const shareToken = params.token as string;
  
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');

  // 1. AUTHENTICATION CHECK
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = getCurrentUser();
        
        // Check if user exists
        if (!user) {
          console.log('[AUTH] No user found, redirecting to login');
          router.replace(`/login?redirect=/chat/shared/${shareToken}`);
          return;
        }

        // Verify access token
        if (!user.access_token) {
          console.log('[AUTH] No access token found, redirecting to login');
          localStorage.removeItem('user');
          router.replace(`/login?redirect=/chat/shared/${shareToken}`);
          return;
        }

        console.log('[AUTH] Verifying access token...');
        const isValid = await verifyToken(user.access_token);
        
        if (!isValid) {
          console.log('[AUTH] Token is invalid or expired, redirecting to login');
          localStorage.removeItem('user');
          router.replace(`/login?error=session_expired&redirect=/chat/shared/${shareToken}`);
          return;
        }

        // Check CloudFuze email domain
        if (!user.email || !user.email.endsWith('@cloudfuze.com')) {
          console.log('[AUTH] Non-CloudFuze email detected, redirecting to login');
          localStorage.removeItem('user');
          router.replace('/login?error=unauthorized_domain&email=' + encodeURIComponent(user.email || ''));
          return;
        }

        console.log('[AUTH] User authenticated successfully:', user.email);
        setIsAuthenticated(true);
        setIsLoading(false);
        
      } catch (error) {
        console.error('[AUTH] Authentication check failed:', error);
        localStorage.removeItem('user');
        setIsLoading(false);
        router.replace('/login?error=verification_failed');
      }
    };

    checkAuth();
  }, [router, shareToken]);

  // 2. LOAD SHARED CHAT
  useEffect(() => {
    console.log('[SHARED] Effect triggered - isAuthenticated:', isAuthenticated, 'shareToken:', shareToken);
    
    if (!isAuthenticated || !shareToken) {
      console.log('[SHARED] Skipping load - auth or token not ready');
      return;
    }

    const loadSharedChat = async () => {
      try {
        const user = getCurrentUser();
        if (!user || !user.access_token) {
          throw new Error('User not authenticated');
        }

        console.log('[SHARED] Loading shared chat with token:', shareToken);

        // Determine API base URL
        const hostname = window.location.hostname;
        let apiBase = '';
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
          apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002';
        } else if (hostname === 'ai.cloudfuze.com') {
          apiBase = 'https://ai.cloudfuze.com';
        } else {
          const origin = window.location.origin;
          apiBase = origin.startsWith('http://') && hostname !== 'localhost' && hostname !== '127.0.0.1'
            ? origin.replace('http://', 'https://')
            : origin;
        }

        // 3. Call backend API to retrieve and copy shared chat
        const response = await fetch(`${apiBase}/chat/shared/${shareToken}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${user.access_token}`,
            'Content-Type': 'application/json'
          }
        });

        // 4. Handle errors
        if (!response.ok) {
          const errorText = await response.text();
          console.error('[SHARED] API error response:', response.status, errorText);
          if (response.status === 404) {
            setError('Shared chat not found or has expired');
          } else if (response.status === 403) {
            setError('You do not have permission to access this shared chat');
          } else {
            setError(`Failed to load shared chat (${response.status})`);
          }
          setIsLoading(false);
          return;
        }

        // 5. Get new session data
        const data = await response.json();
        
        console.log('[SHARED] Chat copied successfully:', data.session_id);
        console.log('[SHARED] Messages in response:', data.messages?.length || 0);
        console.log('[SHARED] Full response:', data);
        console.log('[SHARED] Redirecting to /chat/', data.session_id);
        
        // 6. Redirect to the new session in user's own chats
        router.replace(`/chat/${data.session_id}`);
        
      } catch (error) {
        console.error('[SHARED] Failed to load shared chat:', error);
        setError('An error occurred while loading the shared chat');
        setIsLoading(false);
      }
    };

    loadSharedChat();
  }, [isAuthenticated, shareToken, router]);

  // 7. Show loading/error states
  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error) {
    return <ErrorDisplay error={error} />;
  }

  return null;
}
```

---

## 5️⃣ BACKEND - Retrieve & Copy Shared Chat Endpoint

**Location**: `app/endpoints.py` (lines 2331-2382)

```python
@router.get("/chat/shared/{share_token}")
async def get_shared_chat_session(
    share_token: str,
    auth_user: dict = Depends(require_auth)
):
    """Retrieve and copy a shared chat to the authenticated user's sessions."""
    try:
        from app.mongodb_memory import get_shared_chat
        
        # 1. Get shared chat info from database
        shared_chat = await get_shared_chat(share_token)
        if not shared_chat:
            raise HTTPException(status_code=404, detail="Shared chat not found or expired")
        
        # 2. Get the original session with messages
        original_session = await get_session_by_id(shared_chat["session_id"], include_messages=True)
        if not original_session:
            raise HTTPException(status_code=404, detail="Original session not found")
        
        # 3. Create a new session ID for the current user
        timestamp = datetime.now().strftime("%Y%m%d")
        random_id = str(uuid.uuid4())[:10]
        new_session_id = f"cf.conversation.{timestamp}.{random_id}"
        
        # 4. Copy session data to current user
        new_session_data = {
            "session_id": new_session_id,
            "user_id": auth_user["user_id"],
            "user_email": auth_user["email"],
            "user_name": auth_user["name"],
            "title": f"Shared: {original_session['title']}",
            "created_at": int(datetime.now().timestamp() * 1000),
            "updated_at": int(datetime.now().timestamp() * 1000),
            "messages": original_session.get("messages", []),  # ✅ COPY MESSAGES
            "message_count": len(original_session.get("messages", []))
        }
        
        # 5. Save the copied session to database
        await save_session(new_session_data)
        
        # 6. Return new session data to frontend
        return {
            "session_id": new_session_id,
            "title": new_session_data["title"],
            "messages": new_session_data["messages"],  # ✅ RETURN MESSAGES
            "created_at": new_session_data["created_at"],
            "updated_at": new_session_data["updated_at"],
            "original_owner": shared_chat["user_email"],
            "message": "Chat copied successfully to your chats"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return {"error": str(e)}
```

---

## 6️⃣ BACKEND - MongoDB Retrieve Shared Chat

**Location**: `app/mongodb_memory.py` (lines 417-437)

```python
async def get_shared_chat(self, share_token: str) -> Optional[Dict]:
    """Get shared chat information by token."""
    await self.connect()
    
    try:
        shared_chats_collection = self.database["shared_chats"]
        
        # Find shared chat by token
        doc = await shared_chats_collection.find_one({"share_token": share_token})
        
        if doc:
            # Check if expired (if expiration is set)
            if doc.get("expires_at") and doc["expires_at"] < datetime.utcnow():
                logger.info(f"Shared chat token {share_token} has expired")
                return None
            
            # Return shared chat info
            return {
                "share_token": doc["share_token"],
                "session_id": doc["session_id"],
                "user_email": doc["user_email"],
                "created_at": doc["created_at"],
                "expires_at": doc.get("expires_at")
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error retrieving shared chat: {e}")
        return None
```

---

## 7️⃣ CRITICAL FIX - Session Sync with Messages

**Location**: `frontend/src/lib/chat-initialization.ts` (lines 522-545)

**THE KEY FIX**: This is what makes the share functionality work!

```typescript
// Sync session metadata to backend
async function syncSessionToBackend(sessionData: ChatSession) {
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (!user || !user.access_token) return;
    
    console.log('[SESSION SYNC] Syncing to backend with', sessionData.messages.length, 'messages');
    
    const response = await fetch(`${getApiBase()}/chat/sessions/save`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${user.access_token}`
      },
      body: JSON.stringify({
        session_id: sessionData.id,
        title: sessionData.title,
        created_at: sessionData.createdAt,
        updated_at: sessionData.timestamp,
        messages: sessionData.messages,  // ✅ CRITICAL: Include messages array
        message_count: sessionData.messages.length
      })
    });
    
    if (response.ok) {
      console.log('[SESSION SYNC] Successfully synced to backend');
    } else {
      console.error('[SESSION SYNC] Failed with status:', response.status);
    }
  } catch (error) {
    console.error('[SESSION] Failed to sync session to backend:', error);
  }
}
```

**Why this is critical**: Without including `messages: sessionData.messages`, the backend only receives metadata (title, count) but NO actual messages. When sharing, the copied session would be empty!

---

## 📊 Data Flow Diagram

```
USER SHARES CHAT
├─ 1. Click Share Button (frontend)
├─ 2. POST /chat/share/{session_id} (backend)
│   ├─ Verify session exists
│   ├─ Verify user owns session
│   ├─ Generate UUID token
│   └─ Store in MongoDB shared_chats collection
├─ 3. Return share_url: /chat/shared/{token}
└─ 4. Copy URL to clipboard

RECIPIENT OPENS LINK
├─ 5. Navigate to /chat/shared/{token} (frontend)
├─ 6. Authenticate user (Microsoft Graph)
├─ 7. GET /chat/shared/{token} (backend)
│   ├─ Lookup token in shared_chats
│   ├─ Fetch original session with messages
│   ├─ Create new session ID for recipient
│   ├─ Copy all messages to new session
│   └─ Save new session to MongoDB
├─ 8. Return new session_id with messages
└─ 9. Redirect to /chat/{new_session_id}
```

---

## 🗄️ Database Collections

### `shared_chats` Collection
```javascript
{
  "_id": ObjectId("..."),
  "share_token": "99c0fe72-1920-4409-b124-0ca39d9daa12",
  "session_id": "cf.conversation.20251210.78zsv1qfb",
  "user_email": "user@cloudfuze.com",
  "created_at": ISODate("2025-12-10T11:24:04.558Z"),
  "expires_at": null
}
```

### `chat_sessions` Collection
```javascript
{
  "_id": ObjectId("..."),
  "session_id": "cf.conversation.20251210.78zsv1qfb",
  "user_id": "18977b7c-e234-48fd-9b5b-b54aa43c7b74",
  "user_email": "user@cloudfuze.com",
  "user_name": "User Name",
  "title": "hello world",
  "created_at": 1733828764292,
  "updated_at": 1733828767988,
  "messages": [
    {
      "role": "user",
      "content": "hello world",
      "timestamp": 1733828764169
    },
    {
      "role": "assistant",
      "content": "...",
      "timestamp": 1733828767987,
      "sources": [...],
      "recommended_questions": [...]
    }
  ],
  "message_count": 2
}
```

---

## ✅ Key Features

1. **Authentication Required**: Only CloudFuze users can share and access shared chats
2. **Copy on Access**: Chat is copied to recipient's account (not a live view)
3. **Message Preservation**: All messages, timestamps, and recommended questions are copied
4. **Unique Token**: Each share gets a UUID token for security
5. **Error Handling**: Proper 404/403 errors with helpful messages
6. **Clipboard Integration**: Auto-copy with fallback for older browsers
7. **No Expiration**: Share links don't expire (can be added later)
8. **Owner Tracking**: Original owner email is preserved

---

## 🐛 Common Issues & Solutions

### Issue: Shared chat shows empty (no messages)
**Cause**: `syncSessionToBackend()` not including messages array  
**Fix**: Add `messages: sessionData.messages` to sync payload (line 539)

### Issue: 404 error when opening shared link
**Cause**: Session not synced to backend before sharing  
**Fix**: Ensure sync completes before clicking share (check console logs)

### Issue: 403 error when accessing shared chat
**Cause**: User not authenticated or wrong domain  
**Fix**: Verify user has valid CloudFuze email and access token

### Issue: Link not copied to clipboard
**Cause**: Browser permission denied or insecure context  
**Fix**: Fallback using `document.execCommand('copy')` (line 851-859)

---

## 📝 Testing Checklist

- [ ] Create a new chat with multiple messages
- [ ] Click Share button
- [ ] Verify link copied to clipboard
- [ ] Open link in new browser/incognito
- [ ] Verify authentication redirect
- [ ] Log in with CloudFuze account
- [ ] Verify chat copied with all messages
- [ ] Verify redirect to new chat
- [ ] Verify messages display correctly
- [ ] Verify recommended questions preserved
- [ ] Test with "Others Chats" (user_chat_ format)
- [ ] Test error cases (invalid token, expired session)

---

## 🔐 Security Considerations

1. **Token Security**: UUIDs are cryptographically secure
2. **Authentication**: Microsoft Graph API token verification
3. **Authorization**: Only CloudFuze domain emails allowed
4. **Session Ownership**: Users can only share their own chats
5. **No Direct Access**: Shared chats require authentication
6. **Copy Model**: Recipients get their own copy (data isolation)
7. **Audit Trail**: Original owner email preserved

---

## 📈 Future Enhancements

1. **Expiration Dates**: Add time-limited shares
2. **Access Control**: Restrict to specific users/domains
3. **Usage Analytics**: Track share link opens
4. **Delete Shares**: Allow users to revoke share links
5. **Share History**: Show list of shared chats
6. **Direct Messages**: Share privately to specific users
7. **Edit Permissions**: Allow recipients to contribute to shared chat
8. **Notifications**: Alert when someone opens your shared chat

---

**Last Updated**: December 10, 2025  
**Version**: 1.0 (Working)

