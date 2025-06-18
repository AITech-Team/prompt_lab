import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useAuthStore = create(
  persist(
    (set, get) => ({
      // 状态
      token: null,
      isAuthenticated: false,
      user: null,
      loginType: null, // 'password' | 'thor'
      
      // 登录
      login: (token, user, loginType = 'password') => {
        set({
          token,
          user,
          isAuthenticated: true,
          loginType
        });
      },
      
      // 登出
      logout: () => {
        set({
          token: null,
          user: null,
          isAuthenticated: false,
          loginType: null
        });
      },
      
      // 更新用户信息
      updateUser: (user) => {
        set({ user });
      },
      
      // 检查是否已登录
      checkAuth: () => {
        const state = get();
        return state.isAuthenticated && state.token;
      },
      
      // 获取认证头
      getAuthHeader: () => {
        const state = get();
        if (state.token) {
          return { Authorization: `Bearer ${state.token}` };
        }
        return {};
      }
    }),
    {
      name: 'auth-storage',
      // 只持久化必要的状态
      partialize: (state) => ({
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        loginType: state.loginType,
      }),
    }
  )
);

export default useAuthStore;
