import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import App from './pages/App';
import Login from './pages/Login';
import 'antd/dist/reset.css';
import { ConfigProvider, message } from 'antd';
import zhCN from 'antd/lib/locale/zh_CN';
import useAuthStore from './stores/authStore';

// 将message对象挂载到window上，便于全局调用
window.message = message;

const Root = () => {
  const { isAuthenticated, checkAuth, logout } = useAuthStore();
  const [loading, setLoading] = useState(true);
  
  // 验证用户认证状态
  useEffect(() => {
    const verifyAuth = async () => {
      try {
        // 检查本地存储中是否有有效令牌
        const isLoggedIn = checkAuth();
        setLoading(false);
        
        // 如果发现令牌无效，清除认证状态
        if (!isLoggedIn) {
          logout();
        }
      } catch (error) {
        console.error('认证验证失败:', error);
        logout();
        setLoading(false);
      }
    };
    
    verifyAuth();
  }, [checkAuth, logout]);
  
  // 处理登录成功
  const handleLoginSuccess = () => {
    message.success('登录成功');
  };
  
  // 加载状态
  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      正在加载中...
    </div>;
  }
  
  return (
    <ConfigProvider locale={zhCN}>
      {isAuthenticated ? (
        <App />
      ) : (
        <Login onLoginSuccess={handleLoginSuccess} />
      )}
    </ConfigProvider>
  );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
); 