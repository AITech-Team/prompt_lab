import React, { useState, useEffect } from 'react';
import { Layout, Button, message } from 'antd';
import ModelTable from '../components/ModelTable';
import ModelForm from '../components/ModelForm';
import { Model, ModelCreate } from '../types/model';

const { Content } = Layout;

export default function Home() {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const fetchModels = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/models');
      if (!response.ok) {
        throw new Error('获取模型列表失败');
      }
      const data = await response.json();
      setModels(data);
    } catch (error) {
      message.error('获取模型列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handleCreate = async (model: ModelCreate) => {
    try {
      const response = await fetch('/api/models', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(model),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '创建模型失败');
      }

      message.success('创建模型成功');
      setShowForm(false);
      fetchModels();
    } catch (error) {
      if (error instanceof Error) {
        message.error(error.message);
      } else {
        message.error('创建模型失败');
      }
    }
  };

  const handleDelete = async (id: number) => {
    try {
      const response = await fetch(`/api/models/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('删除模型失败');
      }

      fetchModels();
    } catch (error) {
      throw error;
    }
  };

  const handleRestore = async (id: number) => {
    try {
      const response = await fetch(`/api/models/${id}/restore`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('恢复模型失败');
      }

      fetchModels();
    } catch (error) {
      throw error;
    }
  };

  return (
    <Layout>
      <Content style={{ padding: '50px' }}>
        <div style={{ marginBottom: '20px' }}>
          <Button type="primary" onClick={() => setShowForm(true)}>
            添加模型
          </Button>
        </div>

        <ModelTable
          models={models}
          onDelete={handleDelete}
          onRestore={handleRestore}
          loading={loading}
        />

        <ModelForm
          visible={showForm}
          onCancel={() => setShowForm(false)}
          onSubmit={handleCreate}
        />
      </Content>
    </Layout>
  );
} 