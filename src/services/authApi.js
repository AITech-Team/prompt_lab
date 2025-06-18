// 用户认证相关的 API 接口

const BASE_URL = 'http://localhost:8000/api/v1';

// 用户登录
export const loginWithPassword = async (loginData) => {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(loginData),
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('用户名或密码错误');
    } else if (response.status === 400) {
      const errorResponse = await response.json();
      throw new Error(errorResponse.detail || '请求参数错误');
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }

  return await response.json();
};

// 用户注册
export const registerUser = async (registerData) => {
  const response = await fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(registerData),
  });

  if (!response.ok) {
    if (response.status === 409) {
      const errorResponse = await response.json();
      throw new Error(errorResponse.detail || '用户名或邮箱已存在');
    } else if (response.status === 400) {
      const errorResponse = await response.json();
      throw new Error(errorResponse.detail || '请求参数错误');
    } else {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
  }

  return await response.json();
};

// 检查用户名是否可用
export const checkUsernameAvailable = async (username) => {
  const response = await fetch(`${BASE_URL}/auth/check-username/${encodeURIComponent(username)}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.json();
};

// 获取当前用户信息
export const getCurrentUser = async (token) => {
  const response = await fetch(`${BASE_URL}/auth/me`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error('未授权访问，请重新登录');
    }
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  return await response.json();
};
