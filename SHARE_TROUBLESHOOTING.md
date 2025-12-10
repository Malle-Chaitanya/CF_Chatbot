# Share Functionality - Troubleshooting Guide

## Error: "Session not found"

### What This Means
```
API Response: 404
Message: "Chat not found. Make sure the chat is saved before sharing."
```

The backend cannot find the chat session in MongoDB.

---

## Troubleshooting Steps

### Step 1: Verify Chat is Saved
**Symptom**: "Session not found" error when trying to share

**Solution**:
1. Make sure you've sent at least one message in the chat
2. Check that the chat appears in your "Own Chats" list
3. Refresh the page with `F5` or `Ctrl+R`
4. Try sharing again

**Why**: The backend only stores chats after they have messages.

### Step 2: Check Session ID
**How to Debug**:
1. Open browser DevTools: `F12`
2. Go to Console tab
3. Look for this log message:
   ```
   [SHARE] Attempting to share session {session_id}
   ```
4. Check if the `session_id` looks correct:
   - Own chats: `cf.conversation.20251209.xxxxx`
   - Copied chats: `user_chat_xxxxx`

### Step 3: Check Backend Logs
**If you see in browser console**:
```
[SHARE] API Error Response: 404 "Session not found"
```

**Check backend terminal for**:
```
[SHARE] Session {session_id} not found
[SHARE] User has sessions: ['cf.conversation.20251209.abc', ...]
```

This shows all sessions the user has. Your session ID should be in this list.

### Step 4: Check Database Connection
**If sharing never works**:
1. Verify MongoDB is running
2. Check MongoDB connection string in environment
3. Restart the backend server

---

## Common Scenarios

### Scenario A: Fresh Chat, Not Yet Saved
```
User opens new chat
    ↓
Clicks Share immediately
    ↓
Error: "Session not found"
```

**Fix**: Send a message first, then try sharing

### Scenario B: Chat Exists but Backend Can't Find It
```
Chat appears in list
    ↓
Click Share
    ↓
Error: "Session not found"
```

**Fix**: 
1. Refresh the page
2. Restart the backend server
3. Check MongoDB connection

### Scenario C: Session ID Mismatch
```
Frontend has: cf.conversation.20251209.abc
Backend looks for: cf.conversation.20251209.def
    ↓
Error: "Session not found"
```

**Fix**:
1. Check browser console for correct session ID
2. Verify it matches backend logs
3. Clear localStorage: `localStorage.clear()` then refresh

---

## Enhanced Error Messages

### 404 - Session Not Found
```
Frontend Message: "Chat not found. Make sure the chat is saved before sharing. Try refreshing the page."
Backend Log: "[SHARE] Session {id} not found. User has sessions: [...]"
```

**Actions**:
- [ ] Save the chat by sending a message
- [ ] Verify it appears in your chat list
- [ ] Refresh the page
- [ ] Try sharing again

### 403 - Permission Denied
```
Frontend Message: "You don't have permission to share this chat."
Backend Log: "[SHARE] User {email} tried to share chat owned by {other_user}"
```

**Actions**:
- [ ] Only share chats in your "Own Chats"
- [ ] Don't try to share someone else's original chat
- [ ] You CAN share chats you copied (they're in your account)

### 500 - Server Error
```
Frontend Message: "Failed to create share link"
Backend Log: "[SHARE] ❌ Error sharing chat {id}: {error}"
```

**Actions**:
- [ ] Check backend server is running
- [ ] Check MongoDB connection
- [ ] Restart the backend
- [ ] Check backend logs for the specific error

---

## How to Debug Sharing Issues

### Enable Detailed Logging

**Frontend** - Open DevTools Console:
```javascript
// Look for these logs:
[SHARE] Attempting to share session: {sessionId}
[SHARE] API Base URL: {url}
[SHARE] Response status: {status}
[SHARE] Created share link: {url}
```

**Backend** - Check terminal/logs:
```
[SHARE] Attempting to share session {id} for user {email}
[SHARE] ✅ Chat {id} shared by {email} with token {token}
```

### Session ID Verification

**Get current session ID**:
```javascript
// In browser console
const sessionId = window.location.pathname.split('/').pop();
console.log('Current Session ID:', sessionId);

// Check if it's in localStorage
const sessions = JSON.parse(localStorage.getItem('sessions') || '[]');
console.log('Saved Sessions:', sessions);
```

### Database Verification

**Check if session exists in MongoDB**:
```javascript
db.chat_sessions.findOne({ session_id: "cf.conversation.20251209.abc" })
```

If returns `null`, the session doesn't exist.

---

## Prevention Tips

### Before Sharing a Chat

1. ✅ Send at least one message (to trigger save)
2. ✅ Refresh the page to sync with backend
3. ✅ Verify it appears in your chat list
4. ✅ Check browser console for session ID

### Recommended Flow

```
1. Start new chat
     ↓
2. Send a message
     ↓
3. Wait for response
     ↓
4. Refresh page (Ctrl+R)
     ↓
5. Click Share
     ↓
✅ Success!
```

---

## Error Message Reference

| Status | Message | Solution |
|--------|---------|----------|
| 404 | "Chat not found..." | Save chat, refresh, try again |
| 403 | "You don't have permission..." | Only share your own chats |
| 500 | "Failed to create share link" | Restart backend, check logs |
| Connection Error | Cannot reach backend | Check backend is running |

---

## Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| Share button doesn't work | Refresh page |
| "Session not found" | Send message, refresh, try again |
| Still not working | Restart backend server |
| Backend logs show error | Check MongoDB connection |

---

## Support Information

When reporting an issue with sharing, provide:
```
1. Session ID: [from console log]
2. Error status: [404, 403, 500, etc]
3. Backend log message: [exact error]
4. Browser console logs: [SHARE] messages
5. Steps to reproduce: [what did you do]
```

Example:
```
Session ID: cf.conversation.20251209.abc123
Error: 404
Backend Log: Session not found. User has sessions: [...]
Console: [SHARE] API Error Response: 404
Steps: 1) Opened chat 2) Clicked Share immediately
Fix Applied: Sent message first, then share worked
```

---

## Conclusion

Most "Session not found" errors are resolved by:
1. **Saving the chat** (send a message)
2. **Refreshing the page** (sync frontend/backend)
3. **Trying again**

If issues persist, check backend logs and MongoDB connection!

