import axios from 'axios';
import useAuthStore from '../stores/authStore';
import { message } from 'antd';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 1200000,
});

// 请求拦截器，添加认证令牌
api.interceptors.request.use(
  config => {
    const { token } = useAuthStore.getState();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// 错误处理
api.interceptors.response.use(
  response => {
    // 成功响应添加日志
    console.log(`API成功: ${response.config.url}`, response.data);
    return response;
  },
  error => {
    console.error(`API错误: ${error.config?.url || '未知URL'}`, error.response?.data || error.message);
    
    // 如果是401错误，说明令牌无效或已过期，需要重新登录
    if (error.response && error.response.status === 401) {
      console.log('认证失败，需要重新登录');
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    
    return Promise.reject(error);
  }
);

// 模板相关
export const fetchTemplates = () => api.get('/templates');

export const createTemplate = async (data) => {
  try {
    const response = await api.post('/templates/', data);
    return response.data;
  } catch (error) {
    console.error('Failed to create template:', error);
    throw error;
  }
};

export const updateTemplate = async (id, data) => {
  try {
    const response = await api.put(`/templates/${id}`, data);
    return response.data;
  } catch (error) {
    console.log('\n Update template error: ', error);
    throw error;
  }
};

export const deleteTemplate = async (id) => {
  try {
    const response = await api.delete(`/templates/${id}`);
    return response.data;
  } catch (error) {
    console.log('\n Delete template error: ', error);
    throw error;
  }
};

export const restoreTemplate = async (id) => {
  try {
    const response = await api.post(`/templates/${id}/restore`);
    return response.data;
  } catch (error) {
    console.log('\n Restore template error: ', error);
    throw error;
  }
};

// 模型相关
export const getModels = () => api.get('/models');

export const createModel = async (data) => {
  try {
    const response = await api.post('/models/', data);
    return response.data;
  } catch (error) {
    console.error('Failed to create model:', error);
    throw error;
  }
};

export const updateModel = async (id, data) => {
  try {
    const response = await api.put(`/models/${id}`, data);
    return response.data;
  } catch (error) {
    console.error('Failed to update model:', error);
    throw error;
  }
};

export const deleteModel = async (id) => {
  try {
    const response = await api.delete(`/models/${id}`);
    return response.data;
  } catch (error) {
    console.error('Failed to delete model:', error);
    throw error;
  }
};

export const restoreModel = async (id) => {
  try {
    const response = await api.post(`/models/${id}/restore`);
    return response.data;
  } catch (error) {
    console.error('Failed to restore model:', error);
    throw error;
  }
};

export const getModelTypes = async () => {
  try {
    const response = await api.get('/models/types');
    return response;
  } catch (error) {
    console.error('Failed to get model types:', error);
    // 返回一个模拟的成功响应，包含默认的模型类型列表
    return {
      data: {
        types: ['openai', 'anthropic', 'deepseek', 'qwen', 'doubao', 
          'chatglm', 'zhipu', 'wenxin', 'spark', 'modelscope', 'local']
      }
    };
  }
};

// 测试相关
export const testPrompt = async (data) => {
  try {
    console.log('发送测试请求:', data);
    const response = await api.post('/test/prompt', data);
    console.log('测试响应:', response.data);
    return response;
  } catch (error) {
    console.error('测试失败:', error.response?.data || error.message);
    throw error;
  }
};

// 历史记录
export const fetchHistory = () => api.get('/history');
export const exportHistory = () => api.get('/history/export', { responseType: 'blob' });

// 评估
export const evaluateResponse = data => api.post('/evaluate', data);
export const fetchEvaluations = historyId => api.get(`/evaluate/history/${historyId}`);

// 测试记录相关API
export const listTestRecords = async () => {
  try {
    const response = await api.get('/test/records');
    return response;
  } catch (error) {
    console.error('获取测试记录失败:', error.response?.data || error.message);
    throw error;
  }
};

export const deleteTestRecord = async (id) => {
  try {
    const response = await api.delete(`/test/records/${id}`);
    return response;
  } catch (error) {
    console.error(`删除测试记录失败: ${id}`, error.response?.data || error.message);
    throw error;
  }
};

export const exportTestRecords = async () => {
  try {
    console.log('导出测试记录');
    // 使用新的路由路径，但不在这里处理下载，而是返回response让调用者处理
    const response = await api.get('/test/records/export_csv', { responseType: 'blob' });
    return response;
  } catch (error) {
    console.error('导出测试记录失败:', error.response?.data || error.message);
    message.error('导出测试记录失败');
    throw error;
  }
};

// 提示词相关API
export const fetchPrompts = async () => {
  try {
    console.log('获取提示词列表');
    const response = await api.get('/prompts/');
    console.log('提示词列表响应:', response.data);
    return response;
  } catch (error) {
    console.error('获取提示词列表失败:', error.response?.data || error.message);
    throw error;
  }
};

export const getPrompt = async (id) => {
  try {
    console.log(`获取提示词: ${id}`);
    const response = await api.get(`/prompts/${id}`);
    return response;
  } catch (error) {
    console.error(`获取提示词失败: ${id}`, error.response?.data || error.message);
    throw error;
  }
};

export const createPrompt = async (data) => {
  try {
    console.log('创建提示词:', data);
    const response = await api.post('/prompts/', data);
    // 触发刷新提示词列表事件
    window.dispatchEvent(new CustomEvent('refreshPrompts'));
    return response;
  } catch (error) {
    console.error('创建提示词失败:', error.response?.data || error.message);
    throw error;
  }
};

export const updatePrompt = async (id, data) => {
  try {
    console.log(`更新提示词: ${id}`, data);
    const response = await api.put(`/prompts/${id}`, data);
    return response;
  } catch (error) {
    console.error(`更新提示词失败: ${id}`, error.response?.data || error.message);
    throw error;
  }
};

export const deletePrompt = async (id) => {
  try {
    console.log(`删除提示词: ${id}`);
    const response = await api.delete(`/prompts/${id}`);
    return response;
  } catch (error) {
    console.error(`删除提示词失败: ${id}`, error.response?.data || error.message);
    throw error;
  }
};

export const exportPrompts = async () => {
  try {
    console.log('导出提示词');
    const response = await api.post('/prompts/export', {}, { responseType: 'blob' });
    
    // 创建下载链接
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `提示词导出_${new Date().toLocaleDateString()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    message.success('导出成功');
    return response;
  } catch (error) {
    console.error('导出提示词失败:', error.response?.data || error.message);
    message.error('导出提示词失败');
    throw error;
  }
};

export default api; 