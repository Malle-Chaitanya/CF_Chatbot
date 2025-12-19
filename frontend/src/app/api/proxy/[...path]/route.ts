/**
 * Next.js API Proxy Route
 * 
 * ✅ This proxy route is used for ALL backend API calls to ensure:
 * - Same-origin requests (no CORS issues)
 * - Cookies are automatically forwarded
 * - Consistent cookie handling across dev and prod
 * 
 * All frontend API calls should use `/api/proxy/*` paths via the `apiFetch()` helper.
 */

import { NextRequest, NextResponse } from 'next/server';
// ⚠️ CRITICAL: Use axios with proper configuration to access Set-Cookie headers
import axios from 'axios';

// Get backend URL from environment or default to localhost
// ⚠️ CRITICAL: Must use 'localhost' (not 127.0.0.1) for cookie domain matching
const BACKEND_BASE = (() => {
  const envUrl = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL;
  if (envUrl) {
    // Replace 127.0.0.1 with localhost to ensure cookie domain consistency
    return envUrl.replace('127.0.0.1', 'localhost');
  }
  return 'http://localhost:8002';
})();

async function proxyRequest(
  request: NextRequest,
  pathSegments: string[],
  method: string
) {
  try {
    const path = pathSegments.join('/');
    // ⚠️ CRITICAL: Ensure we use localhost (not 127.0.0.1) for cookie domain matching
    let backendUrl = BACKEND_BASE;
    if (backendUrl.includes('127.0.0.1')) {
      backendUrl = backendUrl.replace('127.0.0.1', 'localhost');
      console.log(`[PROXY] ⚠️ Replaced 127.0.0.1 with localhost for cookie compatibility`);
    }
    const url = `${backendUrl}/${path}${request.nextUrl.search}`;
    
    console.log(`[PROXY] ${method} ${url}`);
    
    // Get request body if present
    let body: string | undefined;
    if (method !== 'GET' && method !== 'HEAD') {
      try {
        body = await request.text();
      } catch {
        // No body, that's fine
      }
    }
    
    // Forward request to backend with cookies using axios
    // ⚠️ CRITICAL: Use axios instead of fetch to access Set-Cookie headers
    // Node.js fetch() strips Set-Cookie headers, but axios exposes them
    let axiosResponse;
    try {
      // ⭐ CRITICAL: Get cookies from browser request
      const browserCookies = request.headers.get('cookie') || '';
      
      // Use axios to make the request (exposes Set-Cookie headers)
      // ⚠️ CRITICAL: Configure axios to preserve all headers including Set-Cookie
      axiosResponse = await axios({
        method: method as 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS',
        url,
        headers: {
          'Content-Type': request.headers.get('content-type') || 'application/json',
          // ⭐ CRITICAL: Forward cookies from browser to backend
          cookie: browserCookies,
        },
        data: body,
        maxRedirects: 5,
        validateStatus: () => true, // Don't throw on any status code
        // ⚠️ CRITICAL: Don't use arraybuffer - use default to let axios parse headers correctly
        // Axios automatically exposes Set-Cookie in response.headers['set-cookie']
      });
    } catch (fetchError) {
      console.error('[PROXY] ❌ Axios error:', fetchError);
      const errorMessage = fetchError instanceof Error ? fetchError.message : 'Unknown error';
      const isConnectionRefused = errorMessage.includes('ECONNREFUSED') || errorMessage.includes('connect') || 
                                  errorMessage.includes('ECONNREFUSED');
      
      return NextResponse.json(
        { 
          error: 'Backend connection failed', 
          message: errorMessage,
          hint: isConnectionRefused 
            ? 'Backend server is not running. Please start it with: python server.py' 
            : undefined
        },
        { status: 502 }
      );
    }
    
    // 🔍 Check for Set-Cookie header (only log when found - missing is expected for most endpoints)
    const setCookieHeaders = axiosResponse.headers['set-cookie'] || 
                             axiosResponse.headers['Set-Cookie'] ||
                             axiosResponse.headers['SET-COOKIE'];
    
    // Get response body and content type
    let responseBody: string;
    if (typeof axiosResponse.data === 'string') {
      responseBody = axiosResponse.data;
    } else if (axiosResponse.data instanceof Buffer) {
      responseBody = axiosResponse.data.toString('utf-8');
    } else {
      // For JSON or other types, stringify
      responseBody = JSON.stringify(axiosResponse.data);
    }
    const contentType = axiosResponse.headers['content-type'] || 'application/json';
    
    // Create response with same status and content type
    const proxiedResponse = new NextResponse(responseBody, {
      status: axiosResponse.status,
      statusText: axiosResponse.statusText || '',
      headers: {
        'Content-Type': contentType,
      },
    });
    
    // 🔥 CRITICAL FIX: Forward Set-Cookie headers from backend to browser
    // Axios exposes Set-Cookie headers as an array in response.headers['set-cookie']
    try {
      let setCookieFound = false;
      
      // Axios stores Set-Cookie headers as an array
      if (setCookieHeaders) {
        const setCookies = Array.isArray(setCookieHeaders) ? setCookieHeaders : [setCookieHeaders];
        if (setCookies.length > 0) {
          console.log(`[PROXY] ✅ Found ${setCookies.length} Set-Cookie header(s) via axios - forwarding to browser`);
          setCookies.forEach((cookie, index) => {
            const cookiePreview = cookie.length > 60 ? cookie.substring(0, 60) + '...' : cookie;
            console.log(`[PROXY]   Set-Cookie ${index + 1}: ${cookiePreview}`);
            proxiedResponse.headers.append('Set-Cookie', cookie);
          });
          setCookieFound = true;
        }
      }
      
      // Only log when Set-Cookie is missing for endpoints that SHOULD set it (login/logout)
      // Most endpoints don't set cookies, so missing is expected and normal
      if (!setCookieFound && (path.includes('/auth/microsoft/callback') || path.includes('/auth/logout'))) {
        console.warn('[PROXY] ⚠️ Expected Set-Cookie header missing for auth endpoint:', path);
      }
    } catch (e) {
      console.error('[PROXY] ❌ Error handling Set-Cookie headers:', e);
      // Don't crash - just log the error and continue
    }
    
    // Forward other important headers (except content-type and set-cookie which we handled above)
    try {
      Object.entries(axiosResponse.headers).forEach(([key, value]) => {
        const lowerKey = key.toLowerCase();
        if (lowerKey !== 'set-cookie' && lowerKey !== 'content-type') {
          const headerValue = Array.isArray(value) ? value.join(', ') : String(value);
          proxiedResponse.headers.set(key, headerValue);
        }
      });
    } catch (headerError) {
      console.warn('[PROXY] ⚠️ Error forwarding headers (non-critical):', headerError);
      // Continue anyway - headers are not critical
    }
    
    return proxiedResponse;
  } catch (error) {
    console.error('[PROXY] ❌ Fatal error proxying request:', error);
    console.error('[PROXY] Error stack:', error instanceof Error ? error.stack : 'No stack trace');
    return NextResponse.json(
      { 
        error: 'Proxy error', 
        message: error instanceof Error ? error.message : 'Unknown error',
        details: process.env.NODE_ENV === 'development' ? (error instanceof Error ? error.stack : undefined) : undefined
      },
      { status: 500 }
    );
  }
}

// ✅ Next.js App Router: params might be a Promise, handle both cases
export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  const params = await Promise.resolve(context.params);
  return proxyRequest(request, params.path, 'GET');
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  const params = await Promise.resolve(context.params);
  return proxyRequest(request, params.path, 'POST');
}

export async function PUT(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  const params = await Promise.resolve(context.params);
  return proxyRequest(request, params.path, 'PUT');
}

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  const params = await Promise.resolve(context.params);
  return proxyRequest(request, params.path, 'DELETE');
}

export async function PATCH(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> | { path: string[] } }
) {
  const params = await Promise.resolve(context.params);
  return proxyRequest(request, params.path, 'PATCH');
}

