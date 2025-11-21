/**
 * Authentication service.
 * Handles login, logout, register, and token management.
 */

import api from '../lib/api';
import { LoginCredentials, RegisterData, AuthTokens, User } from '../types/user';

export const authService = {
  async login(credentials: LoginCredentials): Promise<{ tokens: AuthTokens; user: User }> {
    const response = await api.post('/auth/login/', credentials);
    return response.data;
  },

  async register(data: RegisterData): Promise<{ tokens: AuthTokens; user: User }> {
    const response = await api.post('/auth/register/', data);
    return response.data;
  },

  async logout(): Promise<void> {
    const tokens = localStorage.getItem('auth_tokens');
    if (tokens) {
      try {
        const parsed = JSON.parse(tokens);

        // Validate that parsed value is an object with refresh property
        if (parsed && typeof parsed === 'object' && typeof parsed.refresh === 'string' && parsed.refresh) {
          try {
            await api.post('/auth/logout/', { refresh: parsed.refresh });
          } catch (error) {
            // Ignore logout API errors
            console.error('Logout API error:', error);
          }
        } else {
          console.warn('Invalid token structure - missing refresh token');
        }
      } catch (error) {
        // JSON parse error
        console.warn('Failed to parse auth_tokens from localStorage:', error);
      }
    }

    // Always clear local storage regardless of API call success
    localStorage.removeItem('auth_tokens');
    localStorage.removeItem('user');
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/auth/me/');
    return response.data;
  },

  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await api.post('/auth/token/refresh/', {
      refresh: refreshToken,
    });
    return response.data;
  },

  saveTokens(tokens: AuthTokens): void {
    localStorage.setItem('auth_tokens', JSON.stringify(tokens));
  },

  saveUser(user: User): void {
    localStorage.setItem('user', JSON.stringify(user));
  },

  getTokens(): AuthTokens | null {
    const tokens = localStorage.getItem('auth_tokens');
    if (!tokens) return null;

    try {
      return JSON.parse(tokens);
    } catch (error) {
      console.warn('Failed to parse auth_tokens from localStorage:', error);
      // Remove corrupted data
      localStorage.removeItem('auth_tokens');
      return null;
    }
  },

  getUser(): User | null {
    const user = localStorage.getItem('user');
    if (!user) return null;

    try {
      return JSON.parse(user);
    } catch (error) {
      console.warn('Failed to parse user from localStorage:', error);
      // Remove corrupted data
      localStorage.removeItem('user');
      return null;
    }
  },

  clearAuth(): void {
    localStorage.removeItem('auth_tokens');
    localStorage.removeItem('user');
  },
};

export default authService;
