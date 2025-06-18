import React, { useState, useEffect, useCallback } from 'react';
import { List, Card, Button, Popconfirm, message, Tooltip, Space, Spin, Alert } from 'antd';
import { DeleteOutlined, EditOutlined, CopyOutlined, ReloadOutlined, LinkOutlined } from '@ant-design/icons';
import { fetchTemplates, deleteTemplate } from '../services/api';

const TemplateList = ({ onSelect, onDelete }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshCount, setRefreshCount] = useState(0);
  const [wsStatus, setWsStatus] = useState('disconnected'); // 'connected', 'disconnected', 'error'
  const [lastUpdateTime, setLastUpdateTime] = useState(null);

  const loadTemplates = useCallback(async (showLoading = true, isAutoRefresh = false) => {
    if (showLoading) {
      setLoading(true);
    }
    setError(null);
    try {
      const res = await fetchTemplates();
      console.log('Templates loaded:', res.data);
      setTemplates(res.data || []);
      setLastUpdateTime(new Date());
      if (!isAutoRefresh) {
        message.success('模板列表已更新');
      }
    } catch (error) {
      console.error('Failed to load templates:', error);
      setError('加载模板列表失败');
      if (!isAutoRefresh) {
        message.error('加载模板列表失败');
      }
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  }, []);

  // 强制刷新函数
  const forceRefresh = useCallback(() => {
    setRefreshCount(prev => prev + 1);
    loadTemplates(true, false);
  }, [loadTemplates]);

  // 初始加载和刷新计数变化时重新加载
  useEffect(() => {
    loadTemplates(true, false);
  }, [refreshCount, loadTemplates]);

  // WebSocket连接和自动刷新
  useEffect(() => {
    let ws = null;
    let reconnectTimer = null;
    let refreshInterval = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const baseReconnectDelay = 1000; // 1秒

    const connectWebSocket = () => {
      try {
        ws = new WebSocket('ws://localhost:8000/ws/templates');
        
        ws.onopen = () => {
          console.log('WebSocket connected');
          setWsStatus('connected');
          reconnectAttempts = 0; // 重置重连次数
          // 连接成功后立即刷新一次
          loadTemplates(false, true);
        };
        
        ws.onmessage = async (event) => {
          console.log('Received template update:', event.data);
          // 收到更新消息后执行多次刷新
          const delays = [0, 500, 1000];
          for (const delay of delays) {
            await new Promise(resolve => setTimeout(resolve, delay));
            await loadTemplates(false, true);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setWsStatus('error');
        };

        ws.onclose = () => {
          console.log('WebSocket disconnected');
          setWsStatus('disconnected');
          
          // 指数退避重连
          if (reconnectAttempts < maxReconnectAttempts) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
            console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts + 1}/${maxReconnectAttempts})`);
            reconnectTimer = setTimeout(() => {
              reconnectAttempts++;
              connectWebSocket();
            }, delay);
          } else {
            setError('WebSocket连接失败，请刷新页面重试');
            message.error('实时更新连接失败，将使用定时刷新');
          }
        };
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setWsStatus('error');
      }
    };

    // 启动WebSocket连接
    connectWebSocket();

    // 设置定期刷新（每5秒）
    refreshInterval = setInterval(() => {
      loadTemplates(false, true);
    }, 5000);

    // 监听刷新事件
    const handleRefresh = async () => {
      console.log('Manual refresh triggered');
      message.loading('正在刷新模板列表...', 0.5);
      await loadTemplates(true, false);
    };

    window.addEventListener('refreshTemplates', handleRefresh);
    
    return () => {
      window.removeEventListener('refreshTemplates', handleRefresh);
      clearInterval(refreshInterval);
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
      }
      if (ws) {
        ws.close();
      }
    };
  }, [loadTemplates]);

  const handleDelete = async (id) => {
    try {
      await deleteTemplate(id);
      message.success('删除成功');
      // 删除后立即刷新
      await loadTemplates(false, false);
      // 延迟再次刷新以确保数据同步
      setTimeout(() => loadTemplates(false, true), 500);
      if (onDelete) onDelete(id);
    } catch (error) {
      console.error('Failed to delete template:', error);
      message.error('删除失败');
    }
  };

  const handleCopy = (template) => {
    if (onSelect) onSelect(template);
    message.success('已复制到编辑器');
  };

  const renderStatus = () => {
    if (error) {
      return (
        <Alert
          message={error}
          type="error"
          showIcon
          action={
            <Button size="small" type="primary" onClick={forceRefresh}>
              重试
            </Button>
          }
          style={{ marginBottom: 16 }}
        />
      );
    }

    return (
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <LinkOutlined 
            style={{ 
              color: wsStatus === 'connected' ? '#52c41a' : 
                     wsStatus === 'error' ? '#ff4d4f' : '#faad14'
            }} 
          />
          <span>
            {wsStatus === 'connected' ? '实时更新已连接' :
             wsStatus === 'error' ? '实时更新连接失败' : '正在连接实时更新...'}
          </span>
        </Space>
        {lastUpdateTime && (
          <span style={{ color: '#8c8c8c', fontSize: '12px' }}>
            最后更新: {lastUpdateTime.toLocaleTimeString()}
          </span>
        )}
      </div>
    );
  };

  return (
    <Card 
      title="模板列表" 
      extra={
        <Space>
          <Tooltip title="刷新列表">
            <Button 
              type="link" 
              icon={<ReloadOutlined spin={loading} />} 
              onClick={forceRefresh}
              disabled={loading}
            />
          </Tooltip>
          <Spin spinning={loading} />
        </Space>
      }
    >
      {renderStatus()}
      <List
        dataSource={templates}
        locale={{ emptyText: '暂无模板' }}
        renderItem={item => (
          <List.Item
            key={item.id}
            actions={[
              <Tooltip title="使用此模板">
                <Button type="link" icon={<CopyOutlined />} onClick={() => handleCopy(item)} />
              </Tooltip>,
              <Tooltip title="编辑模板">
                <Button type="link" icon={<EditOutlined />} onClick={() => onSelect(item)} />
              </Tooltip>,
              <Popconfirm
                title="确定要删除这个模板吗？"
                onConfirm={() => handleDelete(item.id)}
                okText="确定"
                cancelText="取消"
              >
                <Button type="link" danger icon={<DeleteOutlined />} />
              </Popconfirm>
            ]}
          >
            <List.Item.Meta
              title={item.name}
              description={item.description || '暂无描述'}
            />
          </List.Item>
        )}
      />
    </Card>
  );
};

export default TemplateList; 