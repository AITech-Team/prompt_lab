import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Select, message, Space } from 'antd';
import { getModels, createTemplate, testPrompt } from '../services/api';

const { TextArea } = Input;
const { Option } = Select;

const TemplateEditor = ({ onSave, initialValues = null }) => {
  const [form] = Form.useForm();
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    loadModels();
    if (initialValues) {
      form.setFieldsValue(initialValues);
    }
  }, [initialValues]);

  const loadModels = async () => {
    try {
      const data = await getModels();
      setModels(data.filter(model => !model.is_deleted));
    } catch (error) {
      console.error('Failed to load models:', error);
      message.error('加载模型列表失败');
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      await createTemplate(values);
      message.success('保存成功');
      if (onSave) {
        onSave(values);
      }
      if (!initialValues) {
        form.resetFields();
      }
    } catch (error) {
      if (error.name !== 'ValidationError') {
        message.error(error.message || '保存失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    try {
      const values = await form.validateFields();
      setTesting(true);
      
      const result = await testPrompt({
        model_id: values.model_id,
        content: values.content,
        variables: { user_input: "测试输入" }
      });
      
      message.info('测试结果: ' + result.response);
    } catch (error) {
      if (error.name !== 'ValidationError') {
        message.error(error.message || '测试失败');
      }
    } finally {
      setTesting(false);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
    >
      <Form.Item
        name="name"
        label="模板名称"
        rules={[{ required: true, message: '请输入模板名称' }]}
      >
        <Input placeholder="请输入模板名称" />
      </Form.Item>

      <Form.Item
        name="model_id"
        label="选择模型"
        rules={[{ required: true, message: '请选择模型' }]}
      >
        <Select placeholder="请选择模型">
          {models.map(model => (
            <Option key={model.id} value={model.id}>
              {model.name} ({model.provider})
            </Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        name="content"
        label="模板内容"
        rules={[{ required: true, message: '请输入模板内容' }]}
        extra="使用 {{user_input}} 表示用户输入变量"
      >
        <TextArea
          rows={6}
          placeholder="请输入模板内容，使用 {{user_input}} 表示用户输入变量"
        />
      </Form.Item>

      <Form.Item>
        <Space>
          <Button type="primary" onClick={handleSubmit} loading={loading}>
            {initialValues ? '更新' : '创建'}
          </Button>
          <Button onClick={handleTest} loading={testing}>
            测试
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};

export default TemplateEditor; 