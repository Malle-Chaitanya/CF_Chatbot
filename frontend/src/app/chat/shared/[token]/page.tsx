'use client';

import { useEffect, useState, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { getCurrentUser, checkSession } from '@/lib/session-utils';
import { apiFetch } from '@/lib/api';

export default function SharedChatPage() {
  const router = useRouter();
  const params = useParams();
  const shareToken = params.token as string;
  
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
  const authCheckRef = useRef<boolean>(false);

  // Authentication check BEFORE rendering
  useEffect(() => {
    if (authCheckRef.current) {
      console.log('[AUTH] Auth check already in progress, skipping');
      return;
    }
    
    authCheckRef.current = true;
    
    const checkAuth = async () => {
      try {
        const user = getCurrentUser();
        
        if (!user) {
          console.log('[AUTH] No user found!');
          const redirectUrl = `/login?redirect=/chat/shared/${shareToken}`;
          console.log('[AUTH] Redirecting to:', redirectUrl);
          router.replace(redirectUrl);
          return;
        }

        const sessionValid = await checkSession();
        if (!sessionValid) {
          console.log('[AUTH] Session invalid or expired, redirecting to login');
          localStorage.removeItem('user');
          router.replace(`/login?error=session_expired&redirect=/chat/shared/${shareToken}`);
          return;
        }

        if (!user.email || !user.email.endsWith('@cloudfuze.com')) {
          console.log('[AUTH] Non-CloudFuze email detected, redirecting to login');
          localStorage.removeItem('user');
          router.replace('/login?error=unauthorized_domain&email=' + encodeURIComponent(user.email || ''));
          return;
        }

        console.log('[AUTH] User authenticated successfully:', user.email);
        setIsAuthenticated(true);
        setIsLoading(false);
        
      } catch (error) {
        console.error('[AUTH] Authentication check failed:', error);
        localStorage.removeItem('user');
        setIsLoading(false);
        router.replace('/login?error=verification_failed');
      } finally {
        authCheckRef.current = false;
      }
    };

    checkAuth();
  }, [router, shareToken]);

  // Load shared chat after authentication
  useEffect(() => {
    console.log('[SHARED] Effect triggered - isAuthenticated:', isAuthenticated, 'shareToken:', shareToken);
    if (!isAuthenticated || !shareToken) {
      console.log('[SHARED] Skipping load - auth or token not ready');
      return;
    }

    const loadSharedChat = async () => {
      try {
        const user = getCurrentUser();
        if (!user) {
          throw new Error('User not authenticated');
        }

        console.log('[SHARED] Loading shared chat with token:', shareToken);

        const response = await apiFetch(`/chat/shared/${shareToken}`, {
          method: 'GET'
        });

        console.log('[SHARED] API response status:', response.status);

        if (!response.ok) {
          const errorText = await response.text();
          console.error('[SHARED] API error response:', response.status, errorText);
          console.error('[SHARED] Full error:', {
            status: response.status,
            statusText: response.statusText,
            body: errorText
          });
          
          let errorMessage = `Failed to load shared chat (${response.status})`;
          if (response.status === 404) {
            errorMessage = 'Shared chat not found or has expired';
          } else if (response.status === 403) {
            errorMessage = 'You do not have permission to access this shared chat';
          } else if (response.status === 401) {
            errorMessage = 'Your session has expired. Please log in again.';
          }
          
          setError(errorMessage);
          setIsLoading(false);
          return;
        }

        const data = await response.json();
        
        // Check if this is an existing copy or a new one
        if (data.is_existing) {
          console.log('[SHARED] Redirecting to existing copy:', data.session_id);
        } else {
          console.log('[SHARED] Chat copied successfully:', data.session_id);
        }
        
        console.log('[SHARED] Messages in response:', data.messages?.length || 0);
        console.log('[SHARED] Full response:', data);
        
        // CRITICAL: Store session in localStorage BEFORE redirecting
        // This ensures the session is immediately available when the chat page loads
        try {
          const user = getCurrentUser();
          if (user && user.id && data.messages) {
            const storageKeyBase = 'chat_sessions';
            const storageKey = `${storageKeyBase}_${user.id}`;
            
            const sessionToStore = {
              id: data.session_id,
              title: data.title || 'Shared Chat',
              timestamp: data.updated_at || Date.now(),
              createdAt: data.created_at || Date.now(),
              messages: data.messages || []
            };
            
            // Get existing sessions and prepend this one (or update if it exists)
            const existingSessions = JSON.parse(localStorage.getItem(storageKey) || '[]');
            const updatedSessions = [
              sessionToStore,
              ...existingSessions.filter((s: any) => s.id !== data.session_id)
            ];
            
            localStorage.setItem(storageKey, JSON.stringify(updatedSessions));
            console.log('[SHARED] Stored session in localStorage before redirect:', sessionToStore.id);
            console.log('[SHARED] Stored messages count:', sessionToStore.messages.length);
            console.log('[SHARED] Is existing copy:', data.is_existing || false);
          }
        } catch (e) {
          console.warn('[SHARED] Failed to store session in localStorage:', e);
          // Continue with redirect even if storage fails - backend fallback will handle it
        }
        
        console.log('[SHARED] Redirecting to /chat/', data.session_id);
        
        // Redirect to the session in user's own chats
        router.replace(`/chat/${data.session_id}`);
        
      } catch (error) {
        console.error('[SHARED] Failed to load shared chat:', error);
        setError('An error occurred while loading the shared chat');
        setIsLoading(false);
      }
    };

    loadSharedChat();
  }, [isAuthenticated, shareToken, router]);

  // Show loading state
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
          {!isAuthenticated ? 'Verifying authentication...' : 'Loading shared chat...'}
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

  // Show error state
  if (error) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        background: 'white',
        fontFamily: 'Arial, sans-serif',
        padding: '20px'
      }}>
        <div style={{
          padding: '32px',
          backgroundColor: '#fef2f2',
          borderRadius: '12px',
          border: '1px solid #fca5a5',
          maxWidth: '500px',
          textAlign: 'center'
        }}>
          <svg 
            width="48" 
            height="48" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="#ef4444" 
            strokeWidth="2"
            style={{ margin: '0 auto 16px' }}
          >
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
          <h2 style={{
            fontSize: '20px',
            fontWeight: '600',
            color: '#dc2626',
            marginBottom: '12px'
          }}>
            {error}
          </h2>
          <p style={{
            fontSize: '14px',
            color: '#7f1d1d',
            marginBottom: '24px'
          }}>
            The shared chat link may be invalid or the chat may have been deleted.
          </p>
          <button
            onClick={() => router.push('/chat/new')}
            style={{
              padding: '12px 24px',
              fontSize: '15px',
              fontWeight: '500',
              color: 'white',
              backgroundColor: '#0129ac',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#010f5e'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#0129ac'}
          >
            Go to Home
          </button>
        </div>
      </div>
    );
  }

  return null;
}

