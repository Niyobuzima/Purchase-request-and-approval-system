/**
 * RootRedirect component.
 * Redirects root path based on authentication status.
 * Prevents redirect chain by checking auth before redirecting.
 */

import { Navigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { FullPageLoader } from '../common';

export function RootRedirect() {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading state while checking auth
  if (isLoading) {
    return <FullPageLoader />;
  }

  // Redirect based on auth status
  return <Navigate to={isAuthenticated ? '/dashboard' : '/login'} replace />;
}
