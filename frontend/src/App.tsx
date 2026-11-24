import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { Dashboard } from './pages/Dashboard';
import { Analytics } from './pages/Analytics';
import { Studio } from './pages/Studio';
import { Profiles } from './pages/Profiles';
import { Escalations } from './pages/Escalations';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { OnboardingPage } from './pages/OnboardingPage';
import { useAuthStore } from './stores/authStore';

export const App: React.FC = () => {
  const { restoreSession } = useAuthStore();

  // Restore session token on app boot
  useEffect(() => {
    restoreSession();
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public auth routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected app shell — requires login */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route index element={<Dashboard />} />
          {/* Studio & Profiles require admin role */}
          <Route
            path="studio"
            element={
              <ProtectedRoute requiredRole="admin">
                <Studio />
              </ProtectedRoute>
            }
          />
          <Route
            path="profiles"
            element={
              <ProtectedRoute requiredRole="admin">
                <Profiles />
              </ProtectedRoute>
            }
          />
          <Route path="analytics" element={<Analytics />} />
          <Route path="escalations" element={<Escalations />} />
          <Route
            path="onboarding"
            element={
              <ProtectedRoute requiredRole="admin">
                <OnboardingPage />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
