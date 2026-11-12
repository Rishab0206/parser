import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

interface RequireAuthProps {
  children: React.ReactNode;
  adminOnly?: boolean;
}

export const RequireAuth: React.FC<RequireAuthProps> = ({ children, adminOnly = false }) => {
  const token = localStorage.getItem('auth_token');
  const userJson = localStorage.getItem('auth_user');
  const location = useLocation();

  if (!token || !userJson) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  try {
    const user = JSON.parse(userJson);
    if (adminOnly && user.role !== 'Admin') {
      return <Navigate to="/" replace />;
    }
  } catch {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};
