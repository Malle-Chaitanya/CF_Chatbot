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
export async function fetchAndMergeUserSessions(): Promise<void> {
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
export async function fetchAllUsersChats(): Promise<OtherUserChat[]> {
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
export async function loadOthersSession(otherSessionId: string): Promise<ChatSession | null> {
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

