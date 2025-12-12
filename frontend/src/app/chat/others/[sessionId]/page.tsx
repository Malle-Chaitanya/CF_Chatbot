'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import ChatSidebar from '../../../../components/ChatSidebar';
import ChatInterface from '../../../../components/ChatInterface';
import { initializeChatApp } from '../../../../lib/chat-initialization';
import { User } from '../../../../types/chat';
import { getCurrentUser } from '../../../../lib/session-utils';

export default function OthersSessionChatPage() {
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

  const verifyToken = useCallback(async (accessToken: string): Promise<boolean> => {
    try {
      const response = await fetch('https://graph.microsoft.com/v1.0/me', {
        headers: { 'Authorization': `Bearer ${accessToken}` },
        signal: AbortSignal.timeout(10000)
      });
      return response.ok;
    } catch (error) {
      console.error('[AUTH] Token verification failed:', error);
      return false;
    }
  }, []);

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
            isClientSideNavigation = navEntry.type === 'navigate' && !!getCurrentUser();
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

        const userStr = localStorage.getItem('user');
        if (!userStr) {
          console.log('[AUTH] No user found, redirecting to login');
          setIsAuthenticated(false);
          setIsLoading(false);
          router.replace('/login');
          return;
        }

        const currentUser: User = JSON.parse(userStr);
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
          const isValid = await verifyToken(currentUser.access_token);
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
  }, [router, verifyToken]);

  useEffect(() => {
    if (isAuthenticated && sessionId) {
      const checkMarked = setInterval(() => {
        if (typeof window.marked !== 'undefined') {
          clearInterval(checkMarked);
          console.log('[CHAT] Initializing others chat page for session:', sessionId);
          initializeChatApp({ router, initialSessionId: sessionId }); // Pass sessionId for Others Chat
        }
      }, 100);
      return () => clearInterval(checkMarked);
    }
  }, [isAuthenticated, router, sessionId]);

  // Avoid rendering until after hydration to prevent mismatches
  if (!hydrated) return null;

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', background: 'white', fontFamily: 'Arial, sans-serif' }}>
        <div style={{ width: '50px', height: '50px', border: '4px solid #f3f3f3', borderTop: '4px solid #0129ac', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
        <p style={{ marginTop: '20px', color: '#666', fontSize: '16px' }}>Verifying authentication...</p>
        <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const handleNewChat = () => {
    router.push('/chat/new');
  };

  return (
    <div className="chatgpt-container">
      <ChatSidebar 
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onNewChat={handleNewChat}
        activeSessionId={sessionId}
      />
      <ChatInterface sessionId={sessionId} />
    </div>
  );
}

