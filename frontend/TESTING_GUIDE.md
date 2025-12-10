# Testing Guide for Multi-Route Chat Architecture

## Overview
This guide provides instructions for testing the new routing structure of the CloudFuze AI chatbot.

## Prerequisites
1. Backend server running on port 8002 (or configured port)
2. Frontend development server running: `npm run dev`
3. Valid CloudFuze email account for authentication

## Test Scenarios

### 1. Home Route Redirect
**Route**: `/` or `localhost:3000`

**Expected Behavior**:
- Should immediately redirect to `/chat/new`
- Should see loading spinner briefly during redirect
- No errors in console

**Steps**:
1. Navigate to `http://localhost:3000/`
2. Verify redirect happens automatically
3. Check URL changes to `/chat/new`

### 2. New Chat Page
**Route**: `/chat/new`

**Expected Behavior**:
- Empty chat interface with "How can I help you today?" message
- Suggested questions loaded from API
- Sidebar shows existing chat history
- Input textarea is functional
- Character counter appears when typing

**Steps**:
1. Navigate to `http://localhost:3000/chat/new`
2. Verify authentication check passes
3. Check sidebar loads with "My Chats" and "Others Chats" sections
4. Verify suggested questions appear
5. Type in the input field
6. Verify character counter appears
7. Send a message
8. Verify URL updates to `/chat/[sessionId]` format
9. Verify message appears in chat
10. Verify bot response streams in

### 3. Session-Specific Route (Own Chat)
**Route**: `/chat/[sessionId]`

**Expected Behavior**:
- Loads specific session from localStorage
- Displays all messages in that session
- Session is highlighted in sidebar
- Can continue conversation
- Can send new messages
- Messages persist after refresh

**Steps**:
1. Create a new chat with at least 2 messages
2. Note the session ID from URL
3. Navigate to another chat or `/chat/new`
4. Click the original chat in sidebar
5. Verify URL updates to `/chat/[sessionId]`
6. Verify all messages load correctly
7. Verify session is highlighted in sidebar
8. Send a new message
9. Refresh the page
10. Verify messages persist

### 4. Session-Specific Route (Others' Chat - Read-Only)
**Route**: `/chat/user_chat_[userId]`

**Expected Behavior**:
- Loads another user's chat session
- Displays "Viewing read-only chat" banner
- Shows messages but input is disabled (or read-only mode)
- Session appears in "Others Chats" section

**Steps**:
1. Check "Others Chats" section in sidebar
2. Click on another user's chat
3. Verify URL updates to `/chat/user_chat_...`
4. Verify read-only banner appears
5. Verify messages load
6. Verify cannot send messages (or appropriate read-only behavior)

### 5. All Chats Grid View
**Route**: `/chats`

**Expected Behavior**:
- Grid layout of all chat sessions
- Each card shows title, date, preview, message count
- Search functionality works
- Clicking card navigates to session
- Empty state shows when no chats

**Steps**:
1. Navigate to `http://localhost:3000/chats`
2. Verify grid layout displays
3. Verify each session card shows:
   - Title
   - Formatted date ("Today", "Yesterday", etc.)
   - Message preview
   - Message count
4. Test search functionality:
   - Type in search box
   - Verify results filter in real-time
   - Try searching for message content
   - Try searching for session titles
5. Click on a session card
6. Verify navigates to `/chat/[sessionId]`
7. Go back to `/chats`
8. Verify can return to grid view

### 6. Sidebar Functionality
**Common across all routes**

**Expected Behavior**:
- Sidebar shows on all chat routes
- Can toggle open/closed
- "New chat" button works
- Session history organized by date (Today, Yesterday, Older)
- Can click sessions to navigate
- Delete functionality works
- User profile shows
- Logout works

**Steps**:
1. Verify sidebar appears on `/chat/new`, `/chat/[sessionId]`, and `/chats`
2. Click toggle button - verify sidebar closes
3. Click toggle again - verify sidebar opens
4. Click "New chat" button - verify navigates to `/chat/new`
5. Verify sessions grouped by date
6. Test collapsing/expanding date sections
7. Hover over session - verify delete button appears
8. Click delete button - verify confirmation dialog
9. Confirm delete - verify session removed
10. Click user profile - verify dropdown appears
11. Click logout - verify redirects to `/login`

### 7. Navigation Flow
**Testing browser navigation**

**Expected Behavior**:
- Browser back button works
- Browser forward button works
- Bookmarking works
- Direct URL access works
- Refresh maintains state

**Steps**:
1. Start at `/chat/new`
2. Create a new chat (URL becomes `/chat/[sessionId]`)
3. Click browser back button - verify returns to `/chat/new`
4. Click browser forward button - verify returns to `/chat/[sessionId]`
5. Bookmark the session URL
6. Navigate away
7. Use bookmark - verify loads correct session
8. Refresh page - verify session persists
9. Copy URL and open in new tab - verify works

### 8. Authentication Flow
**Testing auth across routes**

**Expected Behavior**:
- All routes require authentication
- Unauthenticated users redirect to `/login`
- Token verification works
- Session persists across routes

**Steps**:
1. Clear localStorage
2. Try accessing `/chat/new` - verify redirects to `/login`
3. Try accessing `/chat/[sessionId]` - verify redirects to `/login`
4. Try accessing `/chats` - verify redirects to `/login`
5. Login with valid CloudFuze account
6. Verify redirects to `/chat/new` after login
7. Navigate between routes - verify stays authenticated
8. Close tab and reopen - verify still authenticated (if token valid)

### 9. Session Creation and Persistence
**Testing session lifecycle**

**Expected Behavior**:
- New sessions created on first message
- Sessions saved to localStorage
- Sessions synced to backend
- Sessions persist across page loads
- Sessions appear in sidebar immediately

**Steps**:
1. Go to `/chat/new`
2. Send first message
3. Verify new session ID created
4. Verify URL updates to `/chat/[sessionId]`
5. Check localStorage - verify session saved
6. Check network tab - verify backend sync call
7. Refresh page - verify session loads
8. Check sidebar - verify session appears in "Today" section
9. Send another message
10. Verify session updates in localStorage
11. Verify session syncs to backend

### 10. Edge Cases

**Test these scenarios**:

1. **Invalid Session ID**:
   - Navigate to `/chat/invalid-session-id`
   - Should redirect to `/chat/new`

2. **Deleted Session**:
   - Delete a session
   - Try accessing it via URL
   - Should redirect to `/chat/new`

3. **Empty Chat History**:
   - Clear all sessions
   - Go to `/chats`
   - Should show "No chats yet" message

4. **Network Errors**:
   - Disconnect network
   - Try sending message
   - Verify error handling

5. **Long Session Titles**:
   - Create chat with very long first message
   - Verify title truncates properly in sidebar and grid

6. **Many Sessions**:
   - Create 50+ sessions
   - Verify sidebar scrolls properly
   - Verify grid view performs well
   - Verify search works with many sessions

## Console Checks

Monitor browser console for:
- No JavaScript errors
- Proper logging with `[AUTH]`, `[SESSION]`, `[CHAT]` prefixes
- No failed network requests (except expected auth failures)
- No React warnings

## Network Checks

Monitor Network tab for:
- Successful API calls to backend
- Proper authentication headers
- Session sync calls after message send
- Suggested questions API call
- Microsoft Graph API token verification

## Performance Checks

- Page load time < 2 seconds
- Route transitions smooth
- No lag when typing in input
- Sidebar renders quickly
- Grid view loads all cards efficiently

## Browser Compatibility

Test in:
- Chrome/Edge (Chromium)
- Firefox
- Safari (if available)

## Mobile Responsiveness

Test on:
- Mobile viewport (DevTools)
- Tablet viewport
- Verify sidebar toggles properly
- Verify grid adapts to screen size

## Known Issues to Watch For

1. **Initialization Logic**: The current implementation has placeholder initialization. Full chat functionality (streaming, markdown, etc.) needs the original `page.tsx` logic integrated.

2. **State Management**: Ensure state doesn't leak between routes.

3. **Memory Leaks**: Check for event listeners not being cleaned up.

4. **Race Conditions**: Watch for auth checks and session loads racing.

## Reporting Issues

When reporting issues, include:
- Route/URL where issue occurred
- Steps to reproduce
- Expected vs actual behavior
- Browser console errors
- Network tab errors
- Screenshots if applicable

