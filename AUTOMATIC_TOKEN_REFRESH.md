# Automatic Token Refresh Implementation (Next.js Frontend)

## Overview
This implementation provides **seamless session management** that gives users a "never expire" experience while maintaining security best practices.

**Frontend Stack:** Next.js with TypeScript
**Implementation Location:** `frontend/src/lib/session-utils.ts`

## How It Works

### 1. Token Storage with Expiration Tracking
When users log in, we store:
```javascript
{
  access_token: "...",
  refresh_token: "...",
  expires_in: 3600,  // seconds (typically 1 hour)
  token_expires_at: Date.now() + 3600000  // timestamp
}
```

### 2. Automatic Token Refresh
**Before every API call**, the system:
1. Checks if the token expires in less than 5 minutes
2. If yes, automatically refreshes it in the background
3. Updates the stored tokens
4. Shows a brief notification to the user
5. Continues with the API call seamlessly

### 3. Background Token Monitor
- Runs every 2 minutes
- Proactively checks token expiration
- Refreshes tokens before they expire
- Users never experience session timeout during active use

### 4. Refresh Endpoint
Backend endpoint: `POST /auth/microsoft/refresh`
```javascript
// Request
{
  "refresh_token": "..."
}

// Response
{
  "access_token": "new_token",
  "refresh_token": "new_refresh_token",
  "expires_in": 3600
}
```

## User Experience

### ✅ Before (Old Behavior)
- User session expires after 1 hour
- User sees: "⚠️ Your session has expired. Please log in again."
- Must re-login manually

### ✅ After (New Behavior)
- Session automatically refreshes every ~55 minutes
- User sees brief notification: "Refreshing session..."
- No interruption to workflow
- Effectively "never expires" during active use

## Security Features

1. **Tokens Still Expire**: Each token expires after 1 hour (configurable)
2. **Refresh Tokens Rotate**: New refresh tokens are issued on each refresh
3. **Domain Validation**: Backend validates CloudFuze domain on every refresh
4. **Graceful Failures**: If refresh fails, user is prompted to re-login

## When Tokens Are Checked/Refreshed

### Automatic Checks Before:
- ✅ Sending chat messages (`sendMessage` in `chat-initialization.ts`)
- ✅ Fetching user sessions (`fetchAndMergeUserSessions`)
- ✅ Loading all users' chats (`fetchAllUsersChats`)
- ✅ Loading other users' sessions (`loadOthersSession`)
- All functions use `ensureValidToken()` from `session-utils.ts`

### Background Monitor:
- ✅ Every 2 minutes (even if user is idle)
- ✅ Runs via `TokenMonitor` component
- ✅ Starts automatically when user lands on chat page

## Implementation Details (Next.js)

### Key Files
1. **`frontend/src/lib/session-utils.ts`**
   - `refreshAccessToken()` - Refresh logic with single-flight mutex
   - `ensureValidToken()` - Check and refresh before API calls
   - `isTokenExpiringSoon()` - Check if token needs refresh (5 min threshold)
   - `startTokenMonitor()` - Background monitor
   - `showTokenRefreshNotification()` - Visual feedback

2. **`frontend/src/components/TokenMonitor.tsx`**
   - React component that starts background monitoring
   - Automatically included in all chat pages
   - Cleanup on unmount

3. **`frontend/src/lib/chat-initialization.ts`**
   - Updated `sendMessage` to call `ensureValidToken()` before API requests

4. **`frontend/src/app/globals.css`**
   - Animations: `slideInRight`, `slideOutRight` for notifications

### Architecture Features

1. **Single-Flight Mutex**
   - Prevents multiple simultaneous refresh attempts
   - Multiple API calls wait for single refresh operation
   - Thread-safe token refresh

2. **Proactive Refresh**
   - Tokens refreshed 5 minutes before expiration
   - No user interruption during active sessions

3. **Integration with Existing Code**
   - Already integrated with session fetching functions
   - Uses existing retry logic with token refresh

## Configuration

### Refresh Timing
```typescript
// Token is refreshed when it expires in less than:
const REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes (in isTokenExpiringSoon)
```

### Background Check Interval
```typescript
// Background token check runs every:
const CHECK_INTERVAL = 2 * 60 * 1000; // 2 minutes (in startTokenMonitor)
```

## Console Logs

The system logs detailed information for debugging:

```
[TOKEN_CHECK] Token expires in: 4 minutes
[TOKEN_CHECK] Token expiring soon, refreshing...
[TOKEN_REFRESH] Starting token refresh...
[TOKEN_REFRESH] ✅ Token refreshed successfully. Expires in: 3600 seconds
[TOKEN_MONITOR] Periodic token check...
```

## Visual Feedback

Users see a subtle notification when tokens are refreshed:
- Blue notification badge appears in top-right
- Shows "Refreshing session..." with spinner icon
- Fades out after 2 seconds
- Non-intrusive, informative

## Fallback Behavior

If token refresh fails:
1. System logs the failure reason
2. User continues until next API call
3. On next API call, redirects to login with error message
4. Preserves good UX even in failure scenarios

## How to Use in Your Code

### Before Making API Calls (TypeScript/Next.js)

```typescript
import { ensureValidToken, getCurrentUser } from '@/lib/session-utils';

async function makeAuthenticatedAPICall() {
  // Step 1: Ensure token is valid (auto-refreshes if needed)
  const tokenValid = await ensureValidToken();
  if (!tokenValid) {
    console.error('Token invalid or refresh failed');
    localStorage.removeItem('user');
    window.location.href = '/login?error=session_expired';
    return;
  }
  
  // Step 2: Get updated user (may have new token after refresh)
  const user = getCurrentUser();
  
  // Step 3: Make your API call
  const response = await fetch(`${API_BASE}/your-endpoint`, {
    headers: {
      'Authorization': `Bearer ${user.access_token}`
    }
  });
}
```

### Including the Token Monitor

Add to your main chat page:
```typescript
import TokenMonitor from '@/components/TokenMonitor';

export default function YourChatPage() {
  return (
    <>
      <TokenMonitor />
      {/* Your page content */}
    </>
  );
}
```

## Migration from Old System

### Old Code
```typescript
// Just checked if token exists
const currentUser = getCurrentUser();
if (!currentUser || !currentUser.access_token) {
  // redirect to login
}
```

### New Code
```typescript
// Check AND refresh if needed
const tokenValid = await ensureValidToken();
if (!tokenValid) {
  // redirect to login
}
// Get updated user (may have new token)
const currentUser = getCurrentUser();
// Token is now guaranteed fresh
```

## Benefits

1. **Better UX**: Users never interrupted during active sessions
2. **Security**: Tokens still expire, but are automatically renewed
3. **Transparency**: Users see when refresh happens
4. **Reliability**: Multiple layers of checks ensure tokens stay fresh
5. **Scalability**: Works for long editing sessions, long chats, etc.

## Testing

### Test Scenarios
1. **Active User**: Send messages continuously for 2+ hours
   - Expected: No login prompts, seamless experience
   
2. **Idle User**: Leave page open for 1+ hour without interaction
   - Expected: Token refreshed in background, next action works

3. **Network Failure**: Disconnect internet during refresh
   - Expected: Graceful error, prompt to re-login

4. **Invalid Refresh Token**: Manually corrupt refresh token
   - Expected: Redirect to login with appropriate error

## Future Enhancements

### Possible Improvements:
1. **Countdown Display**: Show "Session refreshes in: 3:45" in user menu
2. **Offline Detection**: Pause refresh attempts when offline
3. **Smart Timing**: Refresh based on user activity patterns
4. **Retry Logic**: Attempt refresh multiple times before failing
5. **Session Analytics**: Track refresh success rates

## Conclusion

This implementation provides a **professional, enterprise-grade session management system** that balances security with user experience. Users effectively never see session expiration during normal use, while maintaining all security best practices.




