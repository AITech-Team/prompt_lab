import React, { useState } from 'react';
import { Layout, Menu, Button, Dropdown, Avatar, Space, Tooltip } from 'antd';
import { 
  AppstoreOutlined, 
  PlusOutlined, 
  KeyOutlined, 
  UserOutlined,
  LogoutOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import TemplateTree from '../components/TemplateTree';
import PromptEditor from '../components/PromptEditor';
import ResponsePanel from '../components/ResponsePanel';
import HistoryTable from '../components/HistoryTable';
import ModelManagerModal from '../components/ModelManagerModal';
import PromptOptimizer from '../components/PromptOptimizer';
import useAuthStore from '../stores/authStore';

const { Header, Sider, Content } = Layout;

const App = () => {
  // 状态管理
  const [modelModalOpen, setModelModalOpen] = useState(false);
  const [optimizerOpen, setOptimizerOpen] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const { user, logout } = useAuthStore();

  // 评分后刷新历史（可选）
  const handleScoreSubmit = async (historyId, score) => {
    try {
      await import('../services/api').then(({ evaluateResponse }) => evaluateResponse({ history_id: historyId, score }));
      window.message.success('评分成功');
    } catch {
      window.message.error('评分失败');
    }
  };

  // 处理优化后的提示词
  const handleOptimizedPrompt = (data) => {
    // 可以将优化后的提示词应用到编辑器
    console.log('优化后的提示词:', data.prompt);
    window.message.success('提示词已优化');
  };

  // 用户菜单项
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout();
        window.message.success('已退出登录');
      }
    }
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <AppstoreOutlined style={{ fontSize: 24, color: '#1677ff' }} />
          <span style={{ fontWeight: 'bold', fontSize: 20 }}>Prompt工程实验室</span>
          <Button icon={<KeyOutlined />} onClick={() => setModelModalOpen(true)}>模型管理</Button>
          <Button icon={<ThunderboltOutlined />} type="primary" onClick={() => setOptimizerOpen(true)}>
            提示词优化
          </Button>
        </div>
        
        {/* 用户信息 */}
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Space>
            <Avatar icon={<UserOutlined />} />
            <span>{user?.displayName || user?.username || '用户'}</span>
          </Space>
        </Dropdown>
      </Header>
      
      {/* 模型管理弹窗 */}
      <ModelManagerModal open={modelModalOpen} onClose={() => setModelModalOpen(false)} />
      
      {/* 提示词优化弹窗 */}
      <PromptOptimizer 
        open={optimizerOpen} 
        onCancel={() => setOptimizerOpen(false)}
        onOk={handleOptimizedPrompt}
      />
      
      <Layout>
        <Sider width={260} style={{ background: '#fff', borderRight: '1px solid #f0f0f0' }}>
          <TemplateTree />
        </Sider>
        <Content style={{ padding: 24, minHeight: 280, background: '#f5f7fa', display: 'flex', flexDirection: 'column' }}>
          <PromptEditor onTestResult={setTestResults} />
          <div style={{ marginTop: 24 }}>
            <HistoryTable />
          </div>
        </Content>
        <Sider width={360} style={{ background: '#fff', borderLeft: '1px solid #f0f0f0', padding: 16 }}>
          <ResponsePanel responses={testResults} onScoreSubmit={handleScoreSubmit} />
        </Sider>
      </Layout>
    </Layout>
  );
};

export default App; 