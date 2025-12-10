# Multi-Route Chat Architecture Implementation

## Overview
This document describes the new routing structure implemented for the CloudFuze AI chatbot application.

## Route Structure

### 1. `/` (Home Route)
- **File**: `frontend/src/app/page.tsx`
- **Behavior**: Immediately redirects to `/chat/new`
- **Purpose**: Entry point that ensures users always start at the new chat page

### 2. `/chat/new` (New Chat Route)
- **File**: `frontend/src/app/chat/new/page.tsx`
- **Behavior**: 
  - Shows empty chat interface with suggested questions
  - No session ID initially
  - When user sends first message, a new session ID will be created and URL will update to `/chat/[sessionId]`
- **Components Used**:
  - `ChatSidebar` - Shows existing chat history
  - `ChatInterface` - Main chat UI

### 3. `/chat/[sessionId]` (Session-Specific Route)
- **File**: `frontend/src/app/chat/[sessionId]/page.tsx`
- **Behavior**:
  - Loads specific session from localStorage or backend
  - Displays message history for that session
  - Allows continuing the conversation
  - Supports read-only mode for viewing others' chats (sessions starting with `user_chat_`)
- **Components Used**:
  - `ChatSidebar` - Shows all chats with current session highlighted
  - `ChatInterface` - Main chat UI with session data

### 4. `/chats` (All Chats Grid View)
- **File**: `frontend/src/app/chats/page.tsx`
- **Behavior**:
  - Displays all chat sessions in a grid/card layout
  - Shows session title, timestamp, preview, and message count
  - Includes search functionality to filter chats
  - Click on any card navigates to `/chat/[sessionId]`
- **Components Used**:
  - `ChatSidebar` - Common sidebar
  - `SessionCard` - Individual session card component

### 5. `/login` (Login Route)
- **File**: `frontend/src/app/login/page.tsx`
- **Behavior**: Existing login page (unchanged)

## Shared Components

### ChatSidebar (`frontend/src/components/ChatSidebar.tsx`)
- Reusable sidebar component with:
  - Logo and branding
  - New chat button
  - My Chats section (Today, Yesterday, Older)
  - Others Chats section
  - User profile and logout
  - Session history with delete functionality
- **Props**:
  - `isOpen`: boolean - sidebar open/closed state
  - `onToggle`: function - toggle sidebar
  - `onNewChat`: function - handle new chat click
  - `onLoadSession`: function (optional) - handle session load
  - `activeSessionId`: string (optional) - currently active session

### ChatInterface (`frontend/src/components/ChatInterface.tsx`)
- Main chat interface component with:
  - Empty state with welcome message
  - Messages list
  - Input textarea with character limits
  - Suggested questions
  - Feedback modal
  - Scroll to bottom button
- **Props**:
  - `sessionId`: string (optional) - current session ID
  - `onSendMessage`: function (optional) - handle message send

### SessionCard (`frontend/src/components/SessionCard.tsx`)
- Card component for displaying session in grid view
- Shows:
  - Session title
  - Timestamp (formatted as "Today", "Yesterday", "X days ago", or date)
  - Message preview (first 100 characters)
  - Message count
- Clickable to navigate to session

## Utilities

### Session Utils (`frontend/src/lib/session-utils.ts`)
Utility functions for session management:
- `getApiBase()` - Get API base URL
- `getUserStorageKey(key)` - Get user-specific localStorage key
- `createNewSessionId()` - Generate new session ID
- `getCurrentSessionId()` - Get current session from localStorage
- `setCurrentSessionId(sessionId)` - Set current session
- `getAllSessions()` - Get all sessions from localStorage
- `saveAllSessions(sessions)` - Save sessions to localStorage
- `getSessionById(sessionId)` - Get specific session
- `deleteSession(sessionId)` - Soft delete a session
- `syncSessionToBackend(sessionData)` - Sync session to backend
- `fetchAndMergeUserSessions()` - Fetch and merge backend sessions
- `fetchAllUsersChats()` - Get all users' chats
- `loadOthersSession(sessionId)` - Load another user's session
- `getCurrentUser()` - Get current user from localStorage
- `verifyToken(accessToken)` - Verify Microsoft Graph token

### Types (`frontend/src/types/chat.ts`)
TypeScript interfaces and types:
- `User` - User object structure
- `Message` - Chat message structure
- `ChatSession` - Session object structure
- `OtherUserChat` - Other user's chat structure
- `SuggestedQuestion` - Suggested question structure
- Constants: `MAX_PROMPT_LENGTH`, `WARN_PROMPT_LENGTH`

## Navigation Flow

### User Journey Examples:

1. **Starting the app**:
   - User visits `localhost:3000` or `/`
   - Immediately redirected to `/chat/new`
   - Empty chat interface with suggested questions shown
   - Sidebar shows existing chat history

2. **Starting a new conversation**:
   - User is on `/chat/new`
   - User types message and sends
   - New session ID is created (e.g., `cf.conversation.20251208.abc123xyz`)
   - URL updates to `/chat/cf.conversation.20251208.abc123xyz`
   - Conversation continues on this URL

3. **Viewing chat history**:
   - User clicks sidebar chat item
   - Navigates to `/chat/[sessionId]`
   - Session messages load
   - User can continue conversation

4. **Browsing all chats**:
   - User navigates to `/chats` (could add button in sidebar)
   - Grid view of all sessions shown
   - User can search/filter
   - Click on card navigates to `/chat/[sessionId]`

5. **Creating new chat from existing session**:
   - User clicks "New chat" button in sidebar
   - Navigates to `/chat/new`
   - Fresh empty chat interface shown

## Implementation Status

### ✅ Completed:
1. Created shared TypeScript types (`frontend/src/types/chat.ts`)
2. Created session management utilities (`frontend/src/lib/session-utils.ts`)
3. Extracted ChatSidebar component (`frontend/src/components/ChatSidebar.tsx`)
4. Extracted ChatInterface component (`frontend/src/components/ChatInterface.tsx`)
5. Created SessionCard component (`frontend/src/components/SessionCard.tsx`)
6. Implemented `/chat/new` page
7. Implemented `/chat/[sessionId]` page
8. Implemented `/chats` grid view page
9. Updated home page (`/`) to redirect to `/chat/new`

### ⚠️ Important Notes:

1. **Initialization Logic**: The new route pages currently have placeholder initialization. The full chat initialization logic from the original `page.tsx` (which is ~3000 lines) needs to be integrated. This includes:
   - Message sending/receiving
   - Streaming responses
   - Markdown rendering
   - Feedback system
   - Suggested questions loading
   - Auto-scroll behavior
   - Character counting
   - And much more...

2. **Preserving Existing Functionality**: All existing features must work:
   - Microsoft SSO authentication
   - Session persistence (localStorage + backend sync)
   - Cross-profile chat viewing
   - Message editing
   - Feedback submission
   - Recommended questions
   - Thinking status
   - Streaming responses
   - etc.

3. **Next Steps**:
   - The original `page.tsx` logic needs to be extracted into a shared initialization module
   - This module should be imported and used by all chat pages
   - Alternatively, create a layout wrapper that handles all the initialization
   - Test all routes thoroughly to ensure no functionality is lost

## Backend Compatibility

The routing changes are frontend-only. The backend API endpoints remain unchanged:
- `POST /chat` - Send messages
- `GET /chat/sessions/user/{user_id}` - Get user sessions
- `GET /chat/sessions/all` - Get all users' chats
- `POST /chat/sessions/save` - Save session
- etc.

## Styling

All existing CSS classes and styles are preserved. The components use the same class names as the original implementation to ensure visual consistency.

## Browser History

With the new routing structure:
- Users can use browser back/forward buttons
- Each chat has a unique URL that can be bookmarked
- Sharing a chat URL will load that specific conversation (with proper auth)
- Browser refresh maintains the current chat view

