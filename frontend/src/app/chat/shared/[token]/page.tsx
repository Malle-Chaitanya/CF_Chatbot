'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { getCurrentUser, verifyToken } from '@/lib/session-utils';

export default function SharedChatPage() {
  const router = useRouter();
  const params = useParams();
  const shareToken = params.token as string;
  
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>('');
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
        const user = getCurrentUser();
        
        if (!user) {
          console.log('[AUTH] No user found, redirecting to login');
          router.replace(`/login?redirect=/chat/shared/${shareToken}`);
          return;
        }

        if (!user.access_token) {
          console.log('[AUTH] No access token found, redirecting to login');
          localStorage.removeItem('user');
          router.replace(`/login?redirect=/chat/shared/${shareToken}`);
          return;
        }

        console.log('[AUTH] Verifying access token...');
        const isValid = await verifyTokenCallback(user.access_token);
        
        if (!isValid) {
          console.log('[AUTH] Token is invalid or expired, redirecting to login');
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
        
      } catch (error) {
        console.error('[AUTH] Authentication check failed:', error);
        localStorage.removeItem('user');
        router.replace('/login?error=verification_failed');
      } finally {
        authCheckRef.current = false;
      }
    };

    checkAuth();
  }, [router, shareToken, verifyTokenCallback]);

  // Load shared chat after authentication
  useEffect(() => {
    if (!isAuthenticated || !shareToken) return;

    const loadSharedChat = async () => {
      try {
        const user = getCurrentUser();
        if (!user || !user.access_token) {
          throw new Error('User not authenticated');
        }

        console.log('[SHARED] Loading shared chat with token:', shareToken);

        // Determine API base URL
        const hostname = window.location.hostname;
        let apiBase = '';
        
        if (hostname === 'localhost' || hostname === '127.0.0.1') {
          apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8002';
        } else if (hostname === 'ai.cloudfuze.com') {
          apiBase = 'https://ai.cloudfuze.com';
        } else {
          const origin = window.location.origin;
          apiBase = origin.startsWith('http://') && hostname !== 'localhost' && hostname !== '127.0.0.1'
            ? origin.replace('http://', 'https://')
            : origin;
        }

        // Call backend API to retrieve and copy shared chat
        const response = await fetch(`${apiBase}/chat/shared/${shareToken}`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${user.access_token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          if (response.status === 404) {
            setError('Shared chat not found or has expired');
          } else {
            setError('Failed to load shared chat');
          }
          setIsLoading(false);
          return;
        }

        const data = await response.json();
        
        console.log('[SHARED] Chat copied successfully:', data.session_id);
        
        // Redirect to the new session in user's own chats
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

