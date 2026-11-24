/**
 * ProtectedRoute.tsx
 *
 * Wraps any route that requires authentication.
 * - Redirects to /login if not authenticated.
 * - Optionally restricts by role ('admin' | 'customer').
 * - Shows a loading spinner while the session is being restored.
 */
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import type { UserRole } from '../../stores/authStore';

interface Props {
  children: React.ReactNode;
  /** If provided, only users with this role may access the route. */
  requiredRole?: UserRole;
}

export const ProtectedRoute: React.FC<Props> = ({ children, requiredRole }) => {
  const { user, loading } = useAuthStore();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0d1322]">
        <div className="flex flex-col items-center gap-4">
          <div
            className="w-12 h-12 rounded-full border-2 border-[#00f0ff]/20 border-t-[#00f0ff] animate-spin"
          />
          <span className="text-[#849495] text-sm font-mono">Restoring session…</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    // User is logged in but doesn't have the required role → back to home
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};
