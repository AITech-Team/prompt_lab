import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Select, message } from 'antd';
import { ModelCreate } from '../types/model';

interface ModelFormProps {
  visible: boolean;
  onCancel: () => void;
  onSubmit: (values: ModelCreate) => void;
}

const ModelForm: React.FC<ModelFormProps> = ({ visible, onCancel, onSubmit }) => {
  const [form] = Form.useForm();
  const [modelTypes, setModelTypes] = useState<{label: string, value: string}[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  // 获取模型类型
  useEffect(() => {
    const fetchModelTypes = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/models/types');
        const data = await response.json();
        
        if (data && data.types) {
          const types = data.types.map((type: string) => ({
            label: type.charAt(0).toUpperCase() + type.slice(1),
            value: type
          }));
          setModelTypes(types);
        }
      } catch (error) {
        console.error('Failed to fetch model types:', error);
        message.error('无法获取模型类型列表');
      } finally {
        setLoading(false);
      }
    };

    if (visible) {
      fetchModelTypes();
    }
  }, [visible]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await onSubmit(values);
      form.resetFields();
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message);
      }
    }
  };

  return (
    <Modal
      title="添加模型"
      open={visible}
      onCancel={() => {
        form.resetFields();
        onCancel();
      }}
      onOk={handleSubmit}
      okText="确定"
      cancelText="取消"
    >
      <Form form={form} layout="vertical">
        <Form.Item
          name="name"
          label="模型名称"
          rules={[{ required: true, message: '请输入模型名称' }]}
        >
          <Input placeholder="请输入模型名称" />
        </Form.Item>

        <Form.Item
          name="provider"
          label="提供商"
          rules={[{ required: true, message: '请选择提供商' }]}
        >
          <Select 
            placeholder="请选择提供商" 
            loading={loading}
            options={modelTypes}
          />
        </Form.Item>

        <Form.Item
          name="api_key"
          label="API密钥"
          rules={[{ required: true, message: '请输入API密钥' }]}
        >
          <Input.Password placeholder="请输入API密钥" />
        </Form.Item>

        <Form.Item name="base_url" label="基础URL">
          <Input placeholder="请输入基础URL（可选）" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ModelForm; 