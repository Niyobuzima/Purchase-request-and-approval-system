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
      const { refresh } = JSON.parse(tokens);
      try {
        await api.post('/auth/logout/', { refresh });
      } catch (error) {
        // Ignore logout errors
        console.error('Logout error:', error);
      }
    }
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
    return tokens ? JSON.parse(tokens) : null;
  },

  getUser(): User | null {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  clearAuth(): void {
    localStorage.removeItem('auth_tokens');
    localStorage.removeItem('user');
  },
};

export default authService;
