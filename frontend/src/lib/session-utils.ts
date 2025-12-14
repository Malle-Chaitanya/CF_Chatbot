import { ChatSession, User, OtherUserChat } from '@/types/chat';

// API Base URL configuration
export function getApiBase(): string {
  if (typeof window === 'undefined') return '';
  
  const hostname = window.location.hostname;
  
  // Development environment
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002';
  }
  
  // Production environments - always use HTTPS
  if (hostname === 'ai.cloudfuze.com') {
    return 'https://ai.cloudfuze.com';
  }
  
  // Other domains (fallback to relative URL)
  return window.location.origin;
}

// Get user-specific localStorage key
export function getUserStorageKey(key: string): string {
  if (typeof window === 'undefined') return key;
  
  const user = JSON.parse(localStorage.getItem('user') || 'null');
  const userId = user?.id || 'anonymous';
  return `${key}_${userId}`;
}

// Create a new session ID
export function createNewSessionId(): string {
  const date = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const randomId = Math.random().toString(36).substr(2, 9);
  return `cf.conversation.${date}.${randomId}`;
}

// Get current session ID from localStorage
export function getCurrentSessionId(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(getUserStorageKey('chatbot_session_id'));
}

// Set current session ID to localStorage
export function setCurrentSessionId(sessionId: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(getUserStorageKey('chatbot_session_id'), sessionId);
}

// Get all sessions from localStorage (filter out empty sessions)
export function getAllSessions(): ChatSession[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const storageKey = getUserStorageKey('chat_sessions');
    const sessionsStr = localStorage.getItem(storageKey);
    const sessions = sessionsStr ? JSON.parse(sessionsStr) : [];
    // Filter out sessions with no messages (empty chats)
    return sessions.filter((s: ChatSession) => s.messages && s.messages.length > 0);
  } catch (e) {
    console.error('[SESSIONS] Failed to load sessions:', e);
    return [];
  }
}

// Save all sessions to localStorage
export function saveAllSessions(sessions: ChatSession[]): void {
  if (typeof window === 'undefined') return;
  
  try {
    const storageKey = getUserStorageKey('chat_sessions');
    localStorage.setItem(storageKey, JSON.stringify(sessions));
  } catch (e) {
    console.error('[SESSIONS] Failed to save sessions:', e);
  }
}

// Get a specific session by ID
export function getSessionById(sessionId: string): ChatSession | null {
  const sessions = getAllSessions();
  return sessions.find(s => s.id === sessionId) || null;
}

// Get all deleted sessions from localStorage
export function getDeletedSessions(): ChatSession[] {
  if (typeof window === 'undefined') return [];
  
  try {
    const storageKey = getUserStorageKey('deleted_chat_sessions');
    const deletedStr = localStorage.getItem(storageKey);
    return deletedStr ? JSON.parse(deletedStr) : [];
  } catch (e) {
    console.error('[DELETED_SESSIONS] Failed to load deleted sessions:', e);
    return [];
  }
}

// Save deleted sessions to localStorage
export function saveDeletedSessions(sessions: ChatSession[]): void {
  if (typeof window === 'undefined') return;
  
  try {
    const storageKey = getUserStorageKey('deleted_chat_sessions');
    localStorage.setItem(storageKey, JSON.stringify(sessions));
    console.log('[DELETED_SESSIONS] Saved', sessions.length, 'deleted sessions');
  } catch (e) {
    console.error('[DELETED_SESSIONS] Failed to save deleted sessions:', e);
  }
}

// Delete a session (soft delete - move to deleted_chat_sessions)
export function deleteSession(sessionId: string): void {
  const sessions = getAllSessions();
  const sessionIndex = sessions.findIndex(s => s.id === sessionId);
  
  if (sessionIndex >= 0) {
    const [deletedSession] = sessions.splice(sessionIndex, 1);
    deletedSession.deletedAt = Date.now();
    
    // Save to deleted sessions
    const deletedSessions = getDeletedSessions();
    deletedSessions.unshift(deletedSession);
    saveDeletedSessions(deletedSessions);
    
    // Save updated active sessions
    saveAllSessions(sessions);
    
    console.log('[SESSION] Soft deleted session:', sessionId);
  }
}

// Sync session with messages to backend
export async function syncSessionToBackend(sessionData: ChatSession): Promise<void> {
  try {
    if (typeof window === 'undefined') return;
    
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (!user || !user.access_token) return;
    
    await fetch(`${getApiBase()}/chat/sessions/save`, {
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
        message_count: sessionData.messages.length,
        messages: sessionData.messages
      })
    });
  } catch (error) {
    console.error('[SESSION] Failed to sync session to backend:', error);
  }
}

// Fetch user sessions from backend and merge with localStorage
// Phase 2.2: Non-recursive retry with explicit flag
export async function fetchAndMergeUserSessions(options = { retryAttempted: false }): Promise<void> {
  try {
    if (typeof window === 'undefined') return;
    
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (!user || !user.access_token || !user.id) {
      console.log('[SESSIONS] No authenticated user, skipping backend fetch');
      return;
    }
    
    console.log('[SESSIONS] Fetching sessions from backend for user:', user.id);
    
    const response = await fetch(`${getApiBase()}/chat/sessions/user/${user.id}?include_messages=true`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${user.access_token}`
      }
    });
    
    // Phase 2.2: Handle 401 with single retry after token refresh
    if (response.status === 401 && !options.retryAttempted) {
      console.warn('[SESSIONS] Got 401, attempting token refresh (retry 1/1)...');
      
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        console.log('[SESSIONS] Token refreshed, retrying request...');
        // Non-recursive call with retry flag
        return await fetchAndMergeUserSessions({ retryAttempted: true });
      }
      
      // Refresh failed, logout
      console.warn('[SESSIONS] Token refresh failed, logging out');
      localStorage.removeItem('user');
      window.location.href = '/login?error=session_expired';
      return;
    }
    
    // If we already retried and got 401 again, immediate logout
    if (response.status === 401 && options.retryAttempted) {
      console.error('[SESSIONS] Got 401 after retry, logging out immediately');
      localStorage.removeItem('user');
      window.location.href = '/login?error=session_expired';
      return;
    }
    
    if (!response.ok) {
      console.error('[SESSIONS] Failed to fetch sessions:', response.status);
      return;
    }
    
    const data = await response.json();
    const backendSessions = data.sessions || [];
    
    console.log(`[SESSIONS] Fetched ${backendSessions.length} sessions from backend`);
    
    if (backendSessions.length === 0) {
      return;
    }
    
    // Get local sessions
    const localSessions = getAllSessions();
    const localSessionIds = new Set(localSessions.map((s: ChatSession) => s.id));
    
    // Merge backend sessions with local sessions
    const mergedSessions = [...localSessions];
    let addedCount = 0;
    
    for (const backendSession of backendSessions) {
      if (!localSessionIds.has(backendSession.session_id)) {
        // Convert backend session format to frontend format
        mergedSessions.push({
          id: backendSession.session_id,
          title: backendSession.title,
          timestamp: backendSession.updated_at,
          createdAt: backendSession.created_at,
          messages: backendSession.messages || []
        });
        addedCount++;
      }
    }
    
    if (addedCount > 0) {
      console.log(`[SESSIONS] Added ${addedCount} sessions from backend`);
      // Sort by timestamp (most recent first)
      mergedSessions.sort((a, b) => b.timestamp - a.timestamp);
      saveAllSessions(mergedSessions);
    }
  } catch (error) {
    console.error('[SESSIONS] Failed to fetch and merge sessions:', error);
  }
}

// Fetch all users' chats (one recent chat per user)
// Phase 2.2: Non-recursive retry with explicit flag
export async function fetchAllUsersChats(options = { retryAttempted: false }): Promise<OtherUserChat[]> {
  try {
    if (typeof window === 'undefined') return [];
    
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (!user || !user.access_token) return [];
    
    const response = await fetch(`${getApiBase()}/chat/sessions/all?limit=15`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${user.access_token}`
      }
    });
    
    // Phase 2.2: Handle 401 with single retry after token refresh
    if (response.status === 401 && !options.retryAttempted) {
      console.warn('[SESSIONS] Got 401, attempting token refresh (retry 1/1)...');
      
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        console.log('[SESSIONS] Token refreshed, retrying request...');
        // Non-recursive call with retry flag
        return await fetchAllUsersChats({ retryAttempted: true });
      }
      
      // Refresh failed, logout
      console.warn('[SESSIONS] Token refresh failed, logging out');
      localStorage.removeItem('user');
      window.location.href = '/login?error=session_expired';
      return [];
    }
    
    // If we already retried and got 401 again, immediate logout
    if (response.status === 401 && options.retryAttempted) {
      console.error('[SESSIONS] Got 401 after retry, logging out immediately');
      localStorage.removeItem('user');
      window.location.href = '/login?error=session_expired';
      return [];
    }
    
    if (response.ok) {
      const data = await response.json();
      return data.sessions || [];
    }
    
    return [];
  } catch (error) {
    console.error('[SESSION] Failed to fetch all users chats:', error);
    return [];
  }
}

// Load another user's chat session (read-only)
// Phase 2.2: Non-recursive retry with explicit flag
export async function loadOthersSession(
  otherSessionId: string, 
  options = { retryAttempted: false }
): Promise<ChatSession | null> {
  try {
    if (typeof window === 'undefined') return null;
    
    const user = JSON.parse(localStorage.getItem('user') || 'null');
    if (!user || !user.access_token) {
      console.error('[SESSION] User not authenticated for loading others session');
      return null;
    }
    
    console.log('[SESSION] Attempting to load others session:', otherSessionId);
    
    // Check if this is a user_chat_ format (legacy others chat)
    if (otherSessionId.startsWith('user_chat_')) {
      const userId = otherSessionId.replace('user_chat_', '');
      console.log('[SESSION] Loading others session with userId:', userId);
      
      // Fetch actual messages from backend
      const response = await fetch(`${getApiBase()}/chat/sessions/user/${userId}?include_messages=true`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${user.access_token}`
        }
      });
      
      // Phase 2.2: Handle 401 with single retry after token refresh
      if (response.status === 401 && !options.retryAttempted) {
        console.warn('[SESSION] Got 401, attempting token refresh (retry 1/1)...');
        
        const refreshed = await refreshAccessToken();
        if (refreshed) {
          console.log('[SESSION] Token refreshed, retrying request...');
          // Non-recursive call with retry flag
          return await loadOthersSession(otherSessionId, { retryAttempted: true });
        }
        
        // Refresh failed, logout
        console.warn('[SESSION] Token refresh failed, logging out');
        localStorage.removeItem('user');
        window.location.href = '/login?error=session_expired';
        return null;
      }
      
      // If we already retried and got 401 again, immediate logout
      if (response.status === 401 && options.retryAttempted) {
        console.error('[SESSION] Got 401 after retry, logging out immediately');
        localStorage.removeItem('user');
        window.location.href = '/login?error=session_expired';
        return null;
      }
      
      if (response.status === 403) {
        console.error('[SESSION] Access denied (403) - user does not have permission to view this chat');
        console.error('[SESSION] This chat may be from another user that you no longer have access to');
        return null;
      }
      
      if (response.status === 404) {
        console.error('[SESSION] Chat not found (404) - this chat may have been deleted');
        return null;
      }
      
      if (!response.ok) {
        console.error('[SESSION] Failed to load other user session: HTTP', response.status);
        const errorText = await response.text();
        console.error('[SESSION] Error details:', errorText);
        return null;
      }
      
      const data = await response.json();
      const sessions = data.sessions || [];
      
      if (sessions.length === 0) {
        console.log('[SESSION] No sessions found for user');
        return null;
      }
      
      // Get the most recent session
      const mostRecentSession = sessions[0];
      
      console.log('[SESSION] Successfully loaded others session:', mostRecentSession.title);
      
      return {
        id: mostRecentSession.session_id,
        title: mostRecentSession.title,
        timestamp: mostRecentSession.updated_at,
        createdAt: mostRecentSession.created_at,
        messages: mostRecentSession.messages || []
      };
    } else {
      // Not a user_chat_ format - might be a regular session ID used incorrectly
      console.error('[SESSION] Invalid others session format:', otherSessionId);
      console.error('[SESSION] Expected format: user_chat_* for others sessions');
      return null;
    }
  } catch (error) {
    console.error('[SESSION] Failed to load other user session:', error);
    return null;
  }
}

// Get current user from localStorage
export function getCurrentUser(): User | null {
  if (typeof window === 'undefined') return null;
  
  try {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    return JSON.parse(userStr);
  } catch (e) {
    console.error('[USER] Failed to parse user:', e);
    return null;
  }
}

// Verify token with Microsoft Graph API
export async function verifyToken(accessToken: string): Promise<boolean> {
  try {
    const response = await fetch('https://graph.microsoft.com/v1.0/me', {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      },
      signal: AbortSignal.timeout(10000) // 10 second timeout
    });
    return response.ok;
  } catch (error) {
    console.error('[AUTH] Token verification failed:', error);
    return false;
  }
}

// ============================================================================
// PHASE 2.1: Token Refresh with Single-Flight Mutex
// ============================================================================

// Module-level mutex to prevent parallel refresh attempts
let refreshPromise: Promise<boolean> | null = null;

/**
 * Show token refresh notification
 */
function showTokenRefreshNotification(): void {
  if (typeof window === 'undefined') return;
  
  // Remove any existing notification
  const existing = document.getElementById('token-refresh-notification');
  if (existing) existing.remove();
  
  const notification = document.createElement('div');
  notification.id = 'token-refresh-notification';
  notification.style.cssText = `
    position: fixed;
    top: 70px;
    right: 20px;
    background: rgba(1, 41, 172, 0.95);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    z-index: 9999;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 10px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    animation: slideInRight 0.3s ease-out;
  `;
  notification.innerHTML = `
    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
      <path d="M8 3a5 5 0 1 0 0 10 5 5 0 0 0 0-10zM4 8a4 4 0 1 1 8 0 4 4 0 0 1-8 0z"/>
      <path d="M7.5 5.5a.5.5 0 0 1 1 0v2.293l1.354 1.353a.5.5 0 0 1-.708.708l-1.5-1.5A.5.5 0 0 1 7.5 8V5.5z"/>
    </svg>
    Refreshing session...
  `;
  document.body.appendChild(notification);
  
  // Remove after 2 seconds
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease-in';
    setTimeout(() => notification.remove(), 300);
  }, 2000);
}

/**
 * Refresh access token with single-flight guarantee.
 * Multiple simultaneous calls will wait for the same refresh operation.
 * 
 * SECURITY: Only sends refresh_token to backend.
 * Backend owns all OAuth secrets (client_id, client_secret).
 * 
 * @returns true if refresh succeeded, false if failed (requires re-login)
 */
export async function refreshAccessToken(): Promise<boolean> {
  // If refresh already in progress, wait for it
  if (refreshPromise) {
    console.log('[AUTH] Refresh already in progress, waiting...');
    return refreshPromise;
  }
  
  // Start new refresh and store promise
  refreshPromise = (async () => {
    try {
      if (typeof window === 'undefined') return false;
      
      const user = getCurrentUser();
      if (!user || !user.refresh_token) {
        console.error('[AUTH] No refresh token available');
        return false;
      }
      
      console.log('[AUTH] Refreshing access token...');
      
      // Show notification
      showTokenRefreshNotification();
      
      // SECURITY: Only send refresh_token, backend handles OAuth secrets
      const response = await fetch(`${getApiBase()}/auth/microsoft/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          refresh_token: user.refresh_token,
        })
      });
      
      if (!response.ok) {
        console.error('[AUTH] Token refresh failed:', response.status);
        return false;
      }
      
      const data = await response.json();
      
      // Update user with new tokens and expiration
      const updatedUser = {
        ...user,
        access_token: data.access_token,
        refresh_token: data.refresh_token || user.refresh_token,
        token_expires_at: Date.now() + (data.expires_in * 1000),
        token_issued_at: Date.now(),
      };
      
      localStorage.setItem('user', JSON.stringify(updatedUser));
      console.log('[AUTH] Token refreshed successfully. Expires in:', data.expires_in, 'seconds');
      return true;
      
    } catch (error) {
      console.error('[AUTH] Token refresh error:', error);
      return false;
    } finally {
      // Always clear mutex when done
      refreshPromise = null;
    }
  })();
  
  return refreshPromise;
}

/**
 * Check if access token is expired or expiring soon.
 * @param marginMinutes - Refresh if token expires in less than this many minutes (default: 5)
 * @returns true if token needs refresh
 */
export function isTokenExpiringSoon(marginMinutes: number = 5): boolean {
  if (typeof window === 'undefined') return false;
  
  const user = getCurrentUser();
  if (!user || !user.token_expires_at) {
    return false;
  }
  
  const now = Date.now();
  const expiresAt = user.token_expires_at;
  const marginMs = marginMinutes * 60 * 1000;
  
  // Return true if token expires in less than margin
  return (expiresAt - now) < marginMs;
}

/**
 * Ensure we have a valid access token, refreshing if necessary.
 * Call this before API requests that require authentication.
 * 
 * @returns true if token is valid or was successfully refreshed, false if auth failed
 */
export async function ensureValidToken(): Promise<boolean> {
  if (typeof window === 'undefined') return false;
  
  const user = getCurrentUser();
  if (!user) return false;
  
  // If token is expiring soon, refresh it proactively
  if (isTokenExpiringSoon(5)) {
    console.log('[AUTH] Token expiring soon, refreshing proactively...');
    const refreshed = await refreshAccessToken();
    
    if (!refreshed) {
      console.error('[AUTH] Proactive token refresh failed');
      return false;
    }
  }
  
  return true;
}

// ============================================================================
// PHASE 3: Background Token Monitor
// ============================================================================

let tokenMonitorInterval: NodeJS.Timeout | null = null;

/**
 * Start background token monitoring.
 * Checks token expiration every 2 minutes and refreshes proactively.
 */
export function startTokenMonitor(): void {
  if (typeof window === 'undefined') return;
  
  // Don't start multiple monitors
  if (tokenMonitorInterval) {
    console.log('[TOKEN_MONITOR] Already running');
    return;
  }
  
  console.log('[TOKEN_MONITOR] Starting background token monitor (checks every 2 minutes)');
  
  tokenMonitorInterval = setInterval(async () => {
    const user = getCurrentUser();
    if (!user || !user.access_token) {
      console.log('[TOKEN_MONITOR] No authenticated user, skipping check');
      return;
    }
    
    console.log('[TOKEN_MONITOR] Periodic token check...');
    const tokenValid = await ensureValidToken();
    if (!tokenValid) {
      console.warn('[TOKEN_MONITOR] Token invalid, user will need to re-login on next action');
    }
  }, 2 * 60 * 1000); // Every 2 minutes
}

/**
 * Stop background token monitoring.
 */
export function stopTokenMonitor(): void {
  if (tokenMonitorInterval) {
    clearInterval(tokenMonitorInterval);
    tokenMonitorInterval = null;
    console.log('[TOKEN_MONITOR] Stopped background token monitor');
  }
}

