/**
 * Authentication context provider.
 * Manages global authentication state and provides auth operations.
 */

import { createContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { AuthState, LoginCredentials, RegisterData } from '../types/user';
import authService from '../services/auth';
import { getErrorMessage } from '../utils/errors';

interface AuthContextType extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  error: string | null;
  clearError: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    tokens: null,
    isAuthenticated: false,
    isLoading: true,
  });
  const [error, setError] = useState<string | null>(null);

  // Initialize auth state from localStorage
  useEffect(() => {
    const initAuth = async () => {
      const tokens = authService.getTokens();
      const user = authService.getUser();

      if (tokens && user) {
        // Verify token is still valid by fetching current user
        try {
          const currentUser = await authService.getCurrentUser();
          setState({
            user: currentUser,
            tokens,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err) {
          // Token invalid, clear auth
          authService.clearAuth();
          setState({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
          });
        }
      } else {
        // No tokens or user found, ensure localStorage is also cleared
        authService.clearAuth();
        setState({
          user: null,
          tokens: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    };

    initAuth();
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      setError(null);
      const { tokens, user } = await authService.login(credentials);

      authService.saveTokens(tokens);
      authService.saveUser(user);

      setState({
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      throw err;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      setError(null);
      const { tokens, user } = await authService.register(data);

      authService.saveTokens(tokens);
      authService.saveUser(user);

      setState({
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
      throw err;
    }
  };

  const logout = async () => {
    try {
      setError(null);
      await authService.logout();

      setState({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
      });
    } catch (err) {
      const errorMessage = getErrorMessage(err);
      setError(errorMessage);
    }
  };

  const clearError = () => {
    setError(null);
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    error,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
