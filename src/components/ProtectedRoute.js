import React from 'react';
import useAuthStore from '../stores/authStore';
import Login from '../pages/Login';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, checkAuth } = useAuthStore();

  // 检查认证状态
  if (!checkAuth()) {
    return <Login onLoginSuccess={() => window.location.reload()} />;
  }

  return children;
};

export default ProtectedRoute;
