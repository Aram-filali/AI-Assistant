/**
 * API Client Module
 * 
 * Centralized HTTP client for backend communication with:
 * - Automatic JWT token injection from localStorage
 * - Default error handling and redirects
 * - Environment-based API URL configuration
 * - Request/response interceptors
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Centralized fetch wrapper with auth token injection.
 * 
 * Features:
 * - Automatically adds JWT token to Authorization header
 * - Handles 401 (Unauthorized) by clearing auth and redirecting to login
 * - Merges custom headers without overwriting defaults
 * - Safe for SSR (checks for window object)
 * 
 * @param endpoint - API endpoint path (e.g., "/chat/messages")
 * @param options - Fetch options (method, body, headers, etc.)
 * @returns Response object from fetch API
 */
export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  // Retrieve JWT token from localStorage (only in browser)
  const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;

  // Prepare headers with auth token and content type
  const headers = {
    "Content-Type": "application/json",
    // Add Authorization header if token exists
    ...(token && { "Authorization": `Bearer ${token}` }),
    ...options.headers,  // Allow custom headers to override
  };

  // Execute request
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized - clear session and redirect to login
  // This prevents stale tokens and ensures users re-authenticate
  if (response.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth-storage');  // Clear any other auth state
      window.location.href = '/login';  // Redirect to login page
    }
  }

  return response;
}
