'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import ChatSidebar from '@/components/ChatSidebar';
import ChatInterface from '@/components/ChatInterface';
import TokenMonitor from '@/components/TokenMonitor';
import { getCurrentUser, verifyToken, createNewSessionId, setCurrentSessionId } from '@/lib/session-utils';

export default function NewChatPage() {
  const router = useRouter();
  
  // Hydration guard to avoid SSR/client HTML mismatch
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => setHydrated(true), []);

  // Always start with loading state to match server/client initial render
  // This prevents hydration mismatches
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  // Load sidebar state from localStorage, default to true if not set
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sidebarOpen');
      return saved !== null ? saved === 'true' : true;
    }
    return true;
  });
  const authCheckRef = useRef<boolean>(false);

  // Save sidebar state to localStorage whenever it changes
  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebarOpen', String(isSidebarOpen));
    }
  }, [isSidebarOpen]);

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
        
        const currentUser = getCurrentUser();
        
        try {
          const navEntries = window.performance.getEntriesByType('navigation');
          if (navEntries.length > 0) {
            const navEntry = navEntries[0] as PerformanceNavigationTiming;
            isBackForwardNavigation = navEntry.type === 'back_forward';
            // If navigation type is 'navigate' but we have user in localStorage, it's likely client-side nav
            isClientSideNavigation = navEntry.type === 'navigate' && !!currentUser;
            if (isBackForwardNavigation) {
              console.log('[AUTH] Detected back/forward navigation, skipping token verification');
            }
            if (isClientSideNavigation) {
              console.log('[AUTH] Detected client-side navigation, skipping token verification');
            }
          }
        } catch (e) {
          // Performance API not available, check if user exists (likely client-side nav)
          isClientSideNavigation = !!currentUser;
        }
        
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

  // Initialize chat app ONLY after authentication is confirmed
  useEffect(() => {
    if (isAuthenticated) {
      // Wait for marked.js to load
      const checkMarked = setInterval(() => {
        if (typeof window.marked !== 'undefined') {
          clearInterval(checkMarked);
          // Import and initialize the chat app
          import('@/lib/chat-initialization').then(({ initializeChatApp }) => {
            console.log('[CHAT] Initializing new chat page');
            // Pass router and null session ID (will create on first message)
            initializeChatApp({ router, initialSessionId: null });
          });
        }
      }, 100);

      return () => clearInterval(checkMarked);
    }
  }, [isAuthenticated, router]);

  const handleNewChat = () => {
    // Already on new chat page - just clear the chat interface
    // The chat initialization will handle clearing messages
    if (typeof window !== 'undefined') {
      const messagesDiv = document.getElementById('messages');
      if (messagesDiv) {
        messagesDiv.innerHTML = '';
      }
      // Trigger updateEmptyState through the chat initialization
      const emptyState = document.getElementById('empty-state');
      const inputSection = document.querySelector('.chatgpt-input-section') as HTMLElement;
      if (emptyState && inputSection && messagesDiv) {
        emptyState.style.display = 'flex';
        messagesDiv.style.display = 'none';
        inputSection.classList.remove('show');
      }
    }
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
          Verifying authentication...
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

  return (
    <>
      <TokenMonitor />
      <div className="chatgpt-container">
        <ChatSidebar
          isOpen={isSidebarOpen}
          onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
          onNewChat={handleNewChat}
          activeSessionId={undefined}
        />
        <ChatInterface sessionId={undefined} />
      </div>
    </>
  );
}

