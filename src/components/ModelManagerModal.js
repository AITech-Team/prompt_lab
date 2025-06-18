import React, { useEffect, useState } from 'react';
import { Modal, Table, Button, Form, Input, Select, Space, Popconfirm, message } from 'antd';
import { getModels, createModel, updateModel, deleteModel, restoreModel, getModelTypes } from '../services/api';

const ModelManagerModal = ({ open, onClose }) => {
  const [form] = Form.useForm();
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editing, setEditing] = useState(null);
  const [modelTypes, setModelTypes] = useState([]);

  const loadModels = async () => {
    try {
      setLoading(true);
      const response = await getModels();
      console.log('Models response:', response);
      
      if (!response.data || !Array.isArray(response.data)) {
        throw new Error('Invalid response format');
      }
      
      setModels(response.data);
    } catch (error) {
      console.error('Failed to load models:', error);
      message.error('加载模型列表失败');
    } finally {
      setLoading(false);
    }
  };

  const loadModelTypes = async () => {
    try {
      const response = await getModelTypes();
      if (response && response.data && response.data.types) {
        const types = response.data.types.map(type => ({
          label: type.charAt(0).toUpperCase() + type.slice(1),
          value: type
        }));
        setModelTypes(types);
      } else {
        // 如果响应格式不正确，使用硬编码的备用列表
        const defaultTypes = ['openai', 'anthropic', 'deepseek', 'qwen', 'doubao', 
          'chatglm', 'zhipu', 'wenxin', 'spark', 'modelscope', 'local'];
        const types = defaultTypes.map(type => ({
          label: type.charAt(0).toUpperCase() + type.slice(1),
          value: type
        }));
        setModelTypes(types);
        console.warn('使用默认模型类型列表，因为API返回格式不正确');
      }
    } catch (error) {
      console.error('Failed to load model types:', error);
      // 使用硬编码的备用列表
      const defaultTypes = ['openai', 'anthropic', 'deepseek', 'qwen', 'doubao', 
        'chatglm', 'zhipu', 'wenxin', 'spark', 'modelscope', 'local'];
      const types = defaultTypes.map(type => ({
        label: type.charAt(0).toUpperCase() + type.slice(1),
        value: type
      }));
      setModelTypes(types);
      console.warn('使用默认模型类型列表，因为API调用失败');
      message.warning('加载模型类型失败，使用默认列表');
    }
  };

  useEffect(() => {
    if (open) {
      loadModels();
      loadModelTypes();
    }
  }, [open]);

  const handleEdit = (record) => {
    setEditing(record);
    form.setFieldsValue({
      name: record.name,
      type: record.provider,
      base_url: record.base_url
    });
  };

  const handleFinish = async (values) => {
    try {
      setLoading(true);
      const data = {
        name: values.name.trim(),
        provider: values.type,
        api_key: values.api_key?.trim(),
        base_url: values.base_url?.trim() || null
      };

      if (editing) {
        await updateModel(editing.id, data);
        message.success('更新成功');
      } else {
        await createModel(data);
        message.success('添加成功');
      }
      
      await loadModels();
      setEditing(null);
      form.resetFields();
    } catch (error) {
      console.error('Failed to save model:', error);
      message.error(error.message || '保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      setLoading(true);
      await deleteModel(id);
      message.success('删除成功');
      await loadModels();
    } catch (error) {
      console.error('Failed to delete model:', error);
      message.error(error.message || '删除失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (id) => {
    try {
      setLoading(true);
      await restoreModel(id);
      message.success('恢复成功');
      await loadModels();
    } catch (error) {
      console.error('Failed to restore model:', error);
      message.error(error.message || '恢复失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { 
      title: '名称', 
      dataIndex: 'name', 
      key: 'name',
      render: (text, record) => (
        <Space>
          {text}
          {record.is_deleted && <span style={{ color: '#ff4d4f' }}>(已删除)</span>}
        </Space>
      )
    },
    { 
      title: '类型', 
      dataIndex: 'provider', 
      key: 'provider',
      render: (text) => modelTypes.find(t => t.value === text)?.label || text
    },
    { 
      title: 'API密钥', 
      dataIndex: 'api_key', 
      key: 'api_key', 
      render: v => v ? '已配置' : '未配置'
    },
    { 
      title: 'Base URL', 
      dataIndex: 'base_url', 
      key: 'base_url', 
      ellipsis: true 
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          {!record.is_deleted ? (
            <>
              <Button 
                size="small" 
                onClick={() => handleEdit(record)}
                disabled={loading}
              >
                编辑
              </Button>
              <Popconfirm
                title="确认删除？"
                onConfirm={() => handleDelete(record.id)}
                okText="确定"
                cancelText="取消"
                disabled={loading}
              >
                <Button size="small" danger disabled={loading}>
                  删除
                </Button>
              </Popconfirm>
            </>
          ) : (
            <Popconfirm
              title="确认恢复？"
              onConfirm={() => handleRestore(record.id)}
              okText="确定"
              cancelText="取消"
              disabled={loading}
            >
              <Button size="small" type="primary" disabled={loading}>
                恢复
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  return (
    <Modal 
      title="模型管理"
      open={open}
      onCancel={onClose}
      footer={null}
      width={800}
      maskClosable={false}
    >
      <Table 
        columns={columns}
        dataSource={models}
        rowKey="id"
        size="small"
        loading={loading}
        pagination={false}
        style={{ marginBottom: 16 }}
      />
      
      <Form
        form={form}
        onFinish={handleFinish}
        layout="vertical"
      >
        <Form.Item
          name="name"
          label="模型名称"
          rules={[{ required: true, message: '请输入模型名称' }]}
        >
          <Input 
            placeholder="请输入模型名称"
            disabled={loading}
          />
        </Form.Item>

        <Form.Item
          name="type"
          label="模型类型"
          rules={[{ required: true, message: '请选择模型类型' }]}
        >
          <Select
            options={modelTypes}
            placeholder="请选择模型类型"
            disabled={loading}
          />
        </Form.Item>

        <Form.Item
          name="api_key"
          label="API密钥"
          extra={editing ? "留空表示不修改" : "请输入模型的API密钥"}
          rules={[{ required: !editing, message: '请输入API密钥' }]}
        >
          <Input.Password
            placeholder={editing ? "留空则保持不变" : "请输入API密钥"}
            disabled={loading}
          />
        </Form.Item>

        <Form.Item
          name="base_url"
          label="Base URL"
          extra="可选，留空使用默认地址"
        >
          <Input
            placeholder="请输入Base URL（可选）"
            disabled={loading}
          />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
            >
              {editing ? '更新' : '添加'}
            </Button>
            {editing && (
              <Button
                onClick={() => {
                  setEditing(null);
                  form.resetFields();
                }}
                disabled={loading}
              >
                取消
              </Button>
            )}
          </Space>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ModelManagerModal; 