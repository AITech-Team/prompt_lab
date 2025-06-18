import React, { useState, useRef, useEffect } from 'react';
import { Layout, Row, Col, Button, Space, Typography, Avatar, Dropdown, Tabs, message } from 'antd';
import { UserOutlined, LogoutOutlined, ThunderboltOutlined } from '@ant-design/icons';
import PromptEditor from './components/PromptEditor';
import TestRecordList from './components/TestRecordList';
import ProtectedRoute from './components/ProtectedRoute';
import PromptOptimizer from './components/PromptOptimizer';
import PromptList from './components/PromptList';
import useAuthStore from './stores/authStore';

const { Header, Content } = Layout;
const { Title } = Typography;

const App = () => {
  const { user, logout } = useAuthStore();
  const [optimizerVisible, setOptimizerVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('editor');
  const promptEditorRef = useRef(null);

  const handleLogout = () => {
    logout();
    window.location.reload();
  };

  // 添加事件监听，以便在保存提示词后自动切换到已保存的提示词标签页
  useEffect(() => {
    const handleSwitchToPromptsTab = (event) => {
      console.log("切换到已保存的提示词标签页");
      setActiveTab('prompts');
      console.log("当前活动标签页：", 'prompts');
    };

    console.log("设置switchToPromptsTab事件监听器");
    window.addEventListener('switchToPromptsTab', handleSwitchToPromptsTab);

    return () => {
      console.log("移除switchToPromptsTab事件监听器");
      window.removeEventListener('switchToPromptsTab', handleSwitchToPromptsTab);
    };
  }, []);

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <ProtectedRoute>
      <Layout style={{ minHeight: '100vh' }}>
        <Header style={{
          background: '#fff',
          padding: '0 24px',
          borderBottom: '1px solid #f0f0f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
            Prompt Lab
          </Title>

          <Space>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={() => setOptimizerVisible(true)}
            >
              智能优化
            </Button>

            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <span>{user?.displayName || user?.username}</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content style={{ padding: '24px' }}>
          <Tabs 
            activeKey={activeTab} 
            onChange={(key) => {
              console.log("手动切换标签页到:", key);
              setActiveTab(key);
            }}
            items={[
              {
                key: 'editor',
                label: '提示词编辑器',
                children: (
          <Row gutter={[16, 16]}>
            <Col span={24}>
                      <PromptEditor ref={promptEditorRef} />
            </Col>
            <Col span={24}>
              <TestRecordList />
            </Col>
          </Row>
                )
              },
              {
                key: 'prompts',
                label: '已保存的提示词',
                children: (
                  <PromptList 
                    onSelect={(prompt) => {
                      // 切换到编辑器Tab
                      setActiveTab('editor');
                      // 直接通过ref设置编辑器内容
                      if (promptEditorRef.current) {
                        promptEditorRef.current.setContent(prompt.content);
                        message.success('已应用提示词到编辑器');
                      }
                    }}
                  />
                )
              }
            ]}
          />
        </Content>

        <PromptOptimizer
          open={optimizerVisible}
          onCancel={() => setOptimizerVisible(false)}
          onOk={(result) => {
            // 切换到编辑器Tab
            setActiveTab('editor');
            // 直接通过ref设置编辑器内容
            if (promptEditorRef.current) {
              promptEditorRef.current.setContent(result.prompt);
              message.success('已应用优化后的提示词到编辑器');
            }
            setOptimizerVisible(false);
          }}
        />
      </Layout>
    </ProtectedRoute>
  );
};

export default App;