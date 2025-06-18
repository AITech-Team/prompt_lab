import React, { useState } from 'react';
import { Button, Form, Input, Tabs, message, Card, Typography, Space } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons';
import { loginWithPassword, registerUser } from '../services/authApi';
import useAuthStore from '../stores/authStore';
import './Login.css';

const { Title, Text } = Typography;

const Login = ({ onLoginSuccess }) => {
  const { login } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('login');
  const [loginForm] = Form.useForm();
  const [registerForm] = Form.useForm();

  const handlePasswordLogin = async (values) => {
    try {
      setIsLoading(true);
      const response = await loginWithPassword(values);

      if (response.success && response.data) {
        login(response.data.token, response.data.user, 'password');
        message.success('登录成功！');
        onLoginSuccess?.();
      } else {
        message.error(response.message || '登录失败');
      }
    } catch (error) {
      message.error(error.message || '登录失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (values) => {
    try {
      setIsLoading(true);
      const response = await registerUser(values);

      if (response.success && response.data) {
        login(response.data.token, response.data.user, 'password');
        message.success('注册成功！');
        onLoginSuccess?.();
      } else {
        message.error(response.message || '注册失败');
      }
    } catch (error) {
      message.error(error.message || '注册失败，请稍后重试');
    } finally {
      setIsLoading(false);
    }
  };

  const tabItems = [
    {
      key: 'login',
      label: '登录',
      children: (
        <Form
          form={loginForm}
          onFinish={handlePasswordLogin}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入用户名"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading && activeTab === 'login'}
              block
              size="large"
            >
              登录
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'register',
      label: '注册',
      children: (
        <Form
          form={registerForm}
          onFinish={handleRegister}
          layout="vertical"
          size="large"
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, max: 50, message: '用户名长度必须在3-50个字符之间' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="请输入用户名"
            />
          </Form.Item>

          <Form.Item
            name="displayName"
            label="显示名称"
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="显示名称（可选）"
            />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { type: 'email', message: '请输入正确的邮箱格式' },
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="邮箱（可选）"
            />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码长度至少为6个字符' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入密码"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="确认密码"
            dependencies={['password']}
            rules={[
              { required: true, message: '请确认密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请再次输入密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading && activeTab === 'register'}
              block
              size="large"
            >
              注册账户
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ];

  return (
    <div className="login-container">
      <div className="login-content">
        <Card className="login-card">
          <div className="login-header">
            <Title level={2} className="login-title">
              欢迎使用 Prompt Lab
            </Title>
            <Text className="login-subtitle">
              智能提示词优化平台
            </Text>
          </div>

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            centered
            items={tabItems}
            size="large"
          />
        </Card>
      </div>
    </div>
  );
};

export default Login;
