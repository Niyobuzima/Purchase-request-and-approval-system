/**
 * Testing utility for token refresh functionality.
 * This file is for development/testing only.
 */

/**
 * Sets an expired access token to test token refresh.
 * Call this from browser console after logging in:
 *
 * Example:
 * ```
 * import { setExpiredToken } from './utils/testTokenRefresh'
 * setExpiredToken()
 * ```
 */
export function setExpiredToken(): void {
  const tokens = localStorage.getItem('auth_tokens');

  if (!tokens) {
    console.error('No tokens found. Please login first.');
    return;
  }

  try {
    const parsed = JSON.parse(tokens);

    // Create an expired token (already expired)
    // This is a dummy token with exp set to past timestamp
    const expiredAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjAwMDAwMDAwLCJpYXQiOjE2MDAwMDAwMDAsImp0aSI6InRlc3QiLCJ1c2VyX2lkIjoidGVzdCJ9.test';

    const updatedTokens = {
      ...parsed,
      access: expiredAccessToken
    };

    localStorage.setItem('auth_tokens', JSON.stringify(updatedTokens));

    console.log('✅ Access token set to expired token');
    console.log('🔄 Next API request should trigger token refresh');
    console.log('📊 Open Network tab to see the refresh request');
  } catch (error) {
    console.error('Failed to set expired token:', error);
  }
}

/**
 * Logs current token info for debugging.
 */
export function checkTokenInfo(): void {
  const tokens = localStorage.getItem('auth_tokens');

  if (!tokens) {
    console.log('❌ No tokens found');
    return;
  }

  try {
    const parsed = JSON.parse(tokens);

    // Decode JWT payload (base64)
    const decodeToken = (token: string) => {
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
          return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
        return JSON.parse(jsonPayload);
      } catch {
        return null;
      }
    };

    const accessPayload = decodeToken(parsed.access);
    const refreshPayload = decodeToken(parsed.refresh);

    if (accessPayload) {
      const now = Math.floor(Date.now() / 1000);
      const accessExp = new Date(accessPayload.exp * 1000);
      const isAccessExpired = accessPayload.exp < now;

      console.log('🔑 Access Token Info:');
      console.log(`  Expires: ${accessExp.toLocaleString()}`);
      console.log(`  Status: ${isAccessExpired ? '❌ EXPIRED' : '✅ Valid'}`);
      console.log(`  Time left: ${Math.max(0, accessPayload.exp - now)} seconds`);
    }

    if (refreshPayload) {
      const now = Math.floor(Date.now() / 1000);
      const refreshExp = new Date(refreshPayload.exp * 1000);
      const isRefreshExpired = refreshPayload.exp < now;

      console.log('\n🔑 Refresh Token Info:');
      console.log(`  Expires: ${refreshExp.toLocaleString()}`);
      console.log(`  Status: ${isRefreshExpired ? '❌ EXPIRED' : '✅ Valid'}`);
      console.log(`  Time left: ${Math.max(0, refreshPayload.exp - now)} seconds`);
    }
  } catch (error) {
    console.error('Failed to check token info:', error);
  }
}

// Make functions available in browser console for testing
if (typeof window !== 'undefined') {
  (window as any).testTokenRefresh = {
    setExpiredToken,
    checkTokenInfo,
  };

  console.log('🧪 Token refresh testing utilities loaded!');
  console.log('📝 Available commands:');
  console.log('  - window.testTokenRefresh.setExpiredToken()');
  console.log('  - window.testTokenRefresh.checkTokenInfo()');
}
