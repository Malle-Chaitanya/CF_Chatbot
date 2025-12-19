/**
 * Centralized API Fetch Helper
 * 
 * All backend API calls should use this helper to ensure:
 * - Same-origin requests (via Next.js proxy)
 * - Cookies are automatically included
 * - Consistent error handling
 */

export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  // Remove leading slash if present (we add it in the proxy path)
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  
  return fetch(`/api/proxy${cleanPath}`, {
    ...options,
    credentials: 'include', // ⭐ CRITICAL: Always include cookies
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
}

