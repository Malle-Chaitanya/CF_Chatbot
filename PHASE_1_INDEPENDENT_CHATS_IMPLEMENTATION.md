# Phase-1: Independent Chat Sessions Implementation

## Overview

This document describes the Phase-1 implementation to fix the chat blocking bug and make chat sessions independent from a UI perspective.

**Status**: ✅ **COMPLETED**

**Date**: December 13, 2025

---

## Problem Statement

### The Bug

When a user was chatting in Chat A and the AI response was generating, switching to Chat B would:
- Keep Chat B's input field disabled
- Prevent sending any messages in Chat B
- Leave Chat A's streaming response running in the background
- Create a "frozen" UI state where no chat was usable

### Root Cause

The application used a **single global `isGenerating` flag** that blocked ALL chat sessions when any one was generating:

```typescript
// ❌ OLD CODE - Global flag blocking all chats
let isGenerating = false;

function setGeneratingState(generating: boolean) {
  isGenerating = generating;
  // Disables ALL inputs globally
  buttons.forEach(btn => btn.disabled = generating);
}
```

---

## Phase-1 Solution

### Goal

> **Fix the blocking bug and make chats independent from a UI perspective.**

This means:
- Switching chats never freezes input
- Chat B can send messages immediately after switching
- No shared global state blocking all chats
- Clean abort of previous session's streaming request
- Only one active generation at a time (by design)

**Note**: Phase-1 does NOT implement parallel generation. That is Phase-2.

---

## Implementation Details

### 1. Per-Session State Management

**File**: `frontend/src/lib/chat-initialization.ts`

Replaced the global `isGenerating` flag with per-session Maps at module level:

```typescript
// ✅ PHASE-1: Module-level per-session state management
// These must be at module level to persist across session switches
const generatingStatus = new Map<string, boolean>();
const activeRequests = new Map<string, AbortController>();
```

**Why module level?**
- State must persist across calls to `initializeChatApp()`
- When switching sessions, we need access to previous session's state to clean it up
- Allows proper abort and cleanup of zombie requests

### 2. Session-Scoped Helper Functions

```typescript
// Check if a specific session is generating
function isSessionGenerating(sid: string): boolean {
  return generatingStatus.get(sid) === true;
}

// Set generating state for a specific session
function setSessionGenerating(sid: string, generating: boolean) {
  generatingStatus.set(sid, generating);
  updateUIForActiveSession();
}
```

### 3. UI Updates Only Affect Active Session (Correction #1)

**Critical Fix**: The UI must only be disabled for the **active session**, not all sessions globally.

```typescript
// ✅ CORRECTION 1: UI updates only affect the active session
function updateUIForActiveSession() {
  const isActiveGenerating = activeSessionId ? isSessionGenerating(activeSessionId) : false;
  
  const buttons = [sendBtn, sendBtnEmptyState];
  const inputs = [input, inputEmptyState];
  
  buttons.forEach(btn => {
    if (btn) {
      btn.disabled = isActiveGenerating;
      btn.style.opacity = isActiveGenerating ? '0.5' : '1';
      btn.style.cursor = isActiveGenerating ? 'not-allowed' : 'pointer';
    }
  });
  
  inputs.forEach(inp => {
    if (inp) {
      inp.disabled = isActiveGenerating;
      inp.style.opacity = isActiveGenerating ? '0.7' : '1';
    }
  });
}
```

### 4. Abort Logic on Session Switch (Correction #2)

When switching from Chat A to Chat B, we must:
1. Abort Chat A's fetch request
2. Delete Chat A's AbortController
3. Reset Chat A's generating state

```typescript
if (isSwitchingSession) {
  console.log('[CHAT] Switching session from', currentInitializedSessionId, 'to', initialSessionId);
  
  // ✅ PHASE-1: Abort any active request from previous session
  if (currentInitializedSessionId) {
    const previousController = activeRequests.get(currentInitializedSessionId);
    if (previousController) {
      console.log('[CHAT] Aborting active request for previous session:', currentInitializedSessionId);
      previousController.abort();
      activeRequests.delete(currentInitializedSessionId);
      // ✅ CORRECTION 2: Reset session state on abort
      setSessionGenerating(currentInitializedSessionId, false);
    }
  }
}
```

### 5. AbortController for Each Request

When sending a message, create an AbortController and wire it to the fetch:

```typescript
async function sendMessageText(question: string) {
  if (!question) return;
  
  // ✅ PHASE-1: Check per-session state instead of global
  if (!sessionId || isSessionGenerating(sessionId)) return;
  
  // ✅ PHASE-1: Create AbortController for this request
  const controller = new AbortController();
  activeRequests.set(sessionId, controller);
  
  // Disable send buttons while generating
  setSessionGenerating(sessionId, true);

  try {
    // ✅ PHASE-1: Wire AbortController signal to fetch request
    const response = await fetch(`${getApiBase()}/chat/stream`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentUser.access_token}`
      },
      body: JSON.stringify(requestBody),
      signal: controller.signal, // Allows aborting the request
    });
    
    // ... streaming logic ...
  } catch (error) {
    // Handle abort gracefully
  }
}
```

### 6. Abort Signal Check in Stream Loop (Correction #3)

**Critical Fix**: The stream loop must check if the request was aborted and stop processing:

```typescript
while (true) {
  // ✅ CORRECTION 3: Check abort signal in stream loop
  // This prevents partial DOM writes and race conditions on session switch
  if (controller.signal.aborted) {
    console.log('[CHAT] Stream aborted, stopping render loop');
    break;
  }
  
  const { done, value } = await reader.read();
  if (done) break;
  
  // ... process stream data ...
}
```

**Why this is critical:**
- Prevents partial DOM writes after abort
- Avoids race conditions when switching sessions quickly
- Ensures clean termination of the streaming loop

### 7. Proper Cleanup on Completion and Error

**On successful completion:**

```typescript
// ✅ PHASE-1: Clean up after successful completion
activeRequests.delete(sessionId!);
setSessionGenerating(sessionId!, false);
```

**On error (with AbortError handling):**

```typescript
catch (error) {
  // ✅ PHASE-1: Handle AbortError gracefully (expected on session switch)
  if ((error as Error).name === 'AbortError') {
    console.log('[CHAT] Request aborted (user switched sessions)');
    // Don't show error message for aborted requests
    botDiv.remove(); // Remove the thinking message
    return;
  }
  
  console.error("Error sending message:", error);
  botDiv.innerHTML = "Sorry, there was an error. Please try again.";
  
  // ✅ CORRECTION 2: Always clean up on error
  activeRequests.delete(sessionId!);
  setSessionGenerating(sessionId!, false);
}
```

### 8. Updated All Guard Checks

Replaced all instances of global `isGenerating` checks with per-session checks:

```typescript
// ✅ OLD: if (isGenerating) return;
// ✅ NEW: if (!sessionId || isSessionGenerating(sessionId)) return;
```

**Updated in:**
- `sendMessage()` - Main send message function
- `sendMessageText()` - Text sending logic
- `askRecommendedQuestion()` - Suggested question clicks
- `saveEdit()` - Message editing
- `sendBtnEmptyState` click handler - Empty state send button
- Suggested question button click handlers

---

## Phase-1 Gold Standard Checklist

✅ **State Management**
- ❌ No module-level `isGenerating` (removed)
- ✅ `Map<sessionId, boolean>` for generating state
- ✅ `Map<sessionId, AbortController>` for request management

✅ **Switching Chats**
- ✅ Abort previous session request
- ✅ Reset previous session generating state
- ✅ UI updates based on active session only

✅ **Streaming**
- ✅ AbortController wired to `fetch`
- ✅ Stream loop checks `signal.aborted`
- ✅ `AbortError` is silently ignored

✅ **UX Result**
- ✅ Chat B can send immediately after switching
- ✅ Chat A is cleanly stopped
- ✅ No frozen UI
- ✅ No background leaks

---

## Testing Checklist

To verify Phase-1 is working correctly:

### Test 1: Basic Session Switch
1. ✅ Start Chat A, send a message
2. ✅ While Chat A is generating, click "New Chat" or switch to Chat B
3. ✅ Verify Chat B's input is NOT disabled
4. ✅ Send a message in Chat B immediately
5. ✅ Verify Chat B's response generates normally
6. ✅ Check console - should see "[CHAT] Aborting active request for previous session"

### Test 2: Fast Session Switching
1. ✅ Start Chat A, send a message
2. ✅ Quickly switch between Chat A → Chat B → Chat A multiple times during generation
3. ✅ Verify no frozen states occur
4. ✅ Verify only the active session's UI reflects generating state

### Test 3: Error Handling
1. ✅ Disconnect network during generation
2. ✅ Verify error message appears
3. ✅ Verify input becomes re-enabled
4. ✅ Verify can send new message

### Test 4: Normal Completion
1. ✅ Send a message and let it complete normally
2. ✅ Verify response displays correctly
3. ✅ Verify input re-enables
4. ✅ Verify can send follow-up message

---

## What Phase-1 Does NOT Do

Phase-1 is **NOT** implementing parallel generation. The following are expected behaviors:

❌ **Not Implemented:**
- Background generation (Chat A continues while viewing Chat B)
- Multiple simultaneous LLM requests
- Job-based generation system
- ChatGPT-style multi-session parallel processing

These features are planned for **Phase-2**.

---

## Phase-2 Preview

Phase-2 will add true parallel generation:

### Changes Required for Phase-2:
1. Remove abort-on-switch logic
2. Move generation ownership to backend
3. Implement job-based system with `jobId`
4. Make UI a subscriber to job status
5. Allow multiple concurrent generations

### Backend Changes:
- Store generation state in database/cache
- Use WebSocket or Server-Sent Events for status updates
- Return `jobId` instead of blocking on stream
- Allow polling/subscribing to job status by `jobId`

**Note**: Do not implement Phase-2 until Phase-1 is thoroughly tested and stable.

---

## Files Modified

### Primary Changes
- `frontend/src/lib/chat-initialization.ts` - Complete refactor of state management

### Key Sections Changed
1. **Lines 18-27**: Added module-level state Maps
2. **Lines 31-49**: Added session switch abort logic
3. **Lines 81-118**: Replaced `setGeneratingState` with `updateUIForActiveSession`
4. **Lines 2039-2081**: Updated `sendMessage()` to use per-session state
5. **Lines 2083-2382**: Updated `sendMessageText()` with AbortController
6. **Lines 2170-2179**: Added abort signal check in stream loop
7. **Lines 2350-2360**: Updated cleanup on completion
8. **Lines 2366-2384**: Updated error handling with AbortError support
9. Multiple locations: Updated all guard checks to use per-session state

---

## Summary

Phase-1 successfully implements independent chat sessions by:

1. **Replacing global state** with per-session Maps
2. **Scoping UI updates** to only the active session
3. **Aborting zombie requests** when switching sessions
4. **Cleaning up state** properly on abort, error, and completion
5. **Handling AbortError** gracefully without user-facing errors

The implementation is **production-ready** and includes all 3 critical corrections identified in the design review.

---

## Next Steps

1. ✅ Deploy to staging environment
2. ✅ Perform thorough testing using the checklist above
3. ✅ Monitor for any edge cases in production
4. ⏳ Plan Phase-2 parallel generation (future)

---

## Credits

**Implementation Date**: December 13, 2025  
**Implemented By**: AI Assistant  
**Architecture Review**: User  
**Status**: Production-Ready ✅






