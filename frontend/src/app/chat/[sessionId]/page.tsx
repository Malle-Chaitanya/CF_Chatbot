'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import ChatSidebar from '@/components/ChatSidebar';
import ChatInterface from '@/components/ChatInterface';
import { 
  getCurrentUser, 
  verifyToken, 
  getSessionById, 
  setCurrentSessionId,
  loadOthersSession
} from '@/lib/session-utils';
import { ChatSession } from '@/types/chat';

export default function ChatSessionPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.sessionId as string;
  
  // Hydration guard to avoid SSR/client HTML mismatch
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);

  // Always start with loading state to match server/client initial render
  // This prevents hydration mismatches
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoadingSession, setIsLoadingSession] = useState<boolean>(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [isReadOnly, setIsReadOnly] = useState<boolean>(false);
  const authCheckRef = useRef<boolean>(false);

  // Verify token with Microsoft Graph API
  const verifyTokenCallback = useCallback(async (accessToken: string): Promise<boolean> => {
    return await verifyToken(accessToken);
  }, []);

  // Authentication check BEFORE rendering
  useEffect(() => {
    if (authCheckRef.current) {
      console.log('[AUTH] Auth check already in progress, skipping');
      return;
    }
    
    authCheckRef.current = true;
    
    const checkAuth = async () => {
      try {
        // Check if this is client-side navigation (not a full page load)
        let isClientSideNavigation = false;
        let isBackForwardNavigation = false;
        
        try {
          const navEntries = window.performance.getEntriesByType('navigation');
          if (navEntries.length > 0) {
            const navEntry = navEntries[0] as PerformanceNavigationTiming;
            isBackForwardNavigation = navEntry.type === 'back_forward';
            // If navigation type is 'navigate' but we have user in localStorage, it's likely client-side nav
            const localUser = getCurrentUser();
            isClientSideNavigation = navEntry.type === 'navigate' && !!localUser;
            if (isBackForwardNavigation) {
              console.log('[AUTH] Detected back/forward navigation, skipping token verification');
            }
            if (isClientSideNavigation) {
              console.log('[AUTH] Detected client-side navigation, skipping token verification');
            }
          }
        } catch (e) {
          // Performance API not available, check if user exists (likely client-side nav)
          isClientSideNavigation = !!getCurrentUser();
        }
        
        const currentUser = getCurrentUser();
        
        if (!currentUser) {
          console.log('[AUTH] No user found, redirecting to login');
          setIsAuthenticated(false);
          setIsLoading(false);
          router.replace('/login');
          return;
        }

        if (!currentUser.access_token) {
          console.log('[AUTH] No access token found, redirecting to login');
          localStorage.removeItem('user');
          setIsAuthenticated(false);
          setIsLoading(false);
          router.replace('/login');
          return;
        }

        // Skip token verification for client-side navigation (already authenticated)
        if (!isBackForwardNavigation && !isClientSideNavigation) {
          console.log('[AUTH] Verifying access token...');
          const isValid = await verifyTokenCallback(currentUser.access_token);
          
          if (!isValid) {
            console.log('[AUTH] Token is invalid or expired, redirecting to login');
            localStorage.removeItem('user');
            setIsAuthenticated(false);
            setIsLoading(false);
            router.replace('/login?error=session_expired');
            return;
          }
        }

        if (!currentUser.email || !currentUser.email.endsWith('@cloudfuze.com')) {
          console.log('[AUTH] Non-CloudFuze email detected, redirecting to login');
          localStorage.removeItem('user');
          setIsAuthenticated(false);
          setIsLoading(false);
          router.replace('/login?error=unauthorized_domain&email=' + encodeURIComponent(currentUser.email || ''));
          return;
        }

        console.log('[AUTH] User authenticated successfully:', currentUser.email);
        setIsAuthenticated(true);
        setIsLoading(false);
        
      } catch (error) {
        console.error('[AUTH] Authentication check failed:', error);
        localStorage.removeItem('user');
        setIsAuthenticated(false);
        setIsLoading(false);
        router.replace('/login?error=verification_failed');
      } finally {
        authCheckRef.current = false;
      }
    };

    checkAuth();
  }, [router, verifyTokenCallback]);

  // Load session data after authentication
  useEffect(() => {
    if (!isAuthenticated || !sessionId) {
      setIsLoadingSession(false);
      return;
    }

    setIsLoadingSession(true);

    const loadSession = async () => {
      console.log('[SESSION] Loading own session from [sessionId] route:', sessionId);
      
      // This route should ONLY handle own chats
      // If user_chat_ format appears here, redirect to correct route
      if (sessionId.startsWith('user_chat_')) {
        console.log('[SESSION] Others chat detected, redirecting to /chat/others/', sessionId);
        setIsLoadingSession(false);
        router.replace(`/chat/others/${sessionId}`);
        return;
      }
      
      // Try to load own session from localStorage first
      let session = getSessionById(sessionId);
      
      if (session) {
        console.log('[SESSION] Loaded own session from localStorage:', session.title);
        setCurrentSession(session);
        setCurrentSessionId(sessionId);
        setIsReadOnly(false);
        setIsLoadingSession(false);
      } else {
        // Session not in localStorage - might be a recently shared chat that was just created
        // Try to fetch from backend
        console.log('[SESSION] Session not found in localStorage, trying backend:', sessionId);
        try {
          const user = getCurrentUser();
          if (!user || !user.access_token) {
            throw new Error('Not authenticated');
          }
          
          // Determine API base URL
          const hostname = typeof window !== 'undefined' ? window.location.hostname : '';
          let apiBase = '';
          
          if (hostname === 'localhost' || hostname === '127.0.0.1') {
            apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002';
          } else if (hostname === 'ai.cloudfuze.com') {
            apiBase = 'https://ai.cloudfuze.com';
          } else {
            const origin = typeof window !== 'undefined' ? window.location.origin : '';
            apiBase = origin.startsWith('http://') && hostname !== 'localhost' && hostname !== '127.0.0.1'
              ? origin.replace('http://', 'https://')
              : origin;
          }
          
          const response = await fetch(`${apiBase}/chat/sessions/${sessionId}?include_messages=true`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${user.access_token}`
            }
          });
          
          if (response.ok) {
            const data = await response.json();
            console.log('[SESSION] Loaded session from backend:', data);
            
            if (!data || !data.session_id) {
              console.error('[SESSION] Backend response missing session_id:', data);
              router.push('/chat/new');
              return;
            }
            
            // Store in localStorage for future access
            const sessionToStore = {
              id: data.session_id,
              title: data.title || '',
              timestamp: data.updated_at || Date.now(),
              createdAt: data.created_at || Date.now(),
              messages: data.messages || []
            };
            
            console.log('[SESSION] Storing session in localStorage:', sessionToStore);
            
            try {
              // Use the same storage key format as session-utils.ts
              const storageKeyBase = 'chat_sessions';
              const userId = user?.id || 'anonymous';
              const storageKey = `${storageKeyBase}_${userId}`;
              
              // Get existing sessions and add/update this one
              const existingSessions = JSON.parse(localStorage.getItem(storageKey) || '[]');
              const updatedSessions = [
                sessionToStore,
                ...existingSessions.filter((s: any) => s.id !== data.session_id)
              ];
              
              localStorage.setItem(storageKey, JSON.stringify(updatedSessions));
              console.log('[SESSION] Stored in localStorage with key:', storageKey);
            } catch (e) {
              console.warn('[SESSION] Failed to store in localStorage:', e);
            }
            
            setCurrentSession(sessionToStore);
            setCurrentSessionId(sessionId);
            setIsReadOnly(false);
            setIsLoadingSession(false);
          } else {
            const errorText = await response.text();
            console.log('[SESSION] Session not found on backend:', response.status, errorText);
            setIsLoadingSession(false);
            router.push('/chat/new');
          }
        } catch (error) {
          console.error('[SESSION] Error loading session from backend:', error);
          setIsLoadingSession(false);
          router.push('/chat/new');
        }
      }
    };

    loadSession();
  }, [isAuthenticated, sessionId, router]);

  // Initialize chat app ONLY after authentication AND session is loaded
  useEffect(() => {
    if (isAuthenticated && sessionId && currentSession) {
      // Wait for marked.js to load
      const checkMarked = setInterval(() => {
        if (typeof window.marked !== 'undefined') {
          clearInterval(checkMarked);
          // Import and initialize the chat app
          import('@/lib/chat-initialization').then(({ initializeChatApp }) => {
            console.log('[CHAT] Initializing chat with session:', sessionId);
            console.log('[CHAT] Current session loaded with messages:', currentSession?.messages?.length || 0);
            // Pass router, session ID, and the currently loaded session data
            initializeChatApp({ 
              router, 
              initialSessionId: sessionId,
              preloadedSession: currentSession
            });
          });
        }
      }, 100);

      return () => clearInterval(checkMarked);
    }
  }, [isAuthenticated, sessionId, router, currentSession]);

  const handleNewChat = () => {
    router.push('/chat/new');
  };

  const handleLoadSession = (session: ChatSession, readOnly: boolean) => {
    router.push(`/chat/${session.id}`);
  };

  // Avoid rendering until after hydration to prevent mismatches
  if (!hydrated) return null;

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'white',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #0129ac',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <p style={{ 
          marginTop: '20px', 
          color: '#666',
          fontSize: '16px'
        }}>
          Loading chat...
        </p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  // Show loading state while session is being fetched from backend
  if (isLoadingSession) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'white',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          width: '50px',
          height: '50px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #0129ac',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <p style={{ 
          marginTop: '20px', 
          color: '#666',
          fontSize: '16px'
        }}>
          Loading chat session...
        </p>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="chatgpt-container">
      <ChatSidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onNewChat={handleNewChat}
        onLoadSession={handleLoadSession}
        activeSessionId={sessionId}
      />
      <ChatInterface sessionId={sessionId} />
    </div>
  );
}

