import React, { useState, useEffect } from 'react';
import { Tree, Button, message, Popconfirm, Space } from 'antd';
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons';
import { fetchTemplates, deleteTemplate } from '../services/api';

const TemplateTree = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedKey, setSelectedKey] = useState(null);

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const res = await fetchTemplates();
      if (res && res.data) {
        const treeData = res.data.map(template => ({
          key: template.id,
          title: (
            <Space>
              <span>{template.name}</span>
              <Popconfirm
                title="确定要删除这个模板吗？"
                onConfirm={() => handleDelete(template.id)}
                okText="确定"
                cancelText="取消"
              >
                <DeleteOutlined style={{ color: '#ff4d4f' }} />
              </Popconfirm>
            </Space>
          ),
          children: [],
          template: template
        }));
        setTemplates(treeData);
      } else {
        message.error('加载模板失败：返回数据格式错误');
      }
    } catch (error) {
      console.error('Load templates failed:', error);
      message.error('加载模板失败：' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTemplates();
  }, []);

  const handleDelete = async (templateId) => {
    try {
      await deleteTemplate(templateId);
      message.success('删除成功');
      await loadTemplates();
    } catch (error) {
      console.error('Delete template failed:', error);
      message.error('删除失败：' + (error.message || '未知错误'));
    }
  };

  const handleSelect = (selectedKeys) => {
    if (selectedKeys.length > 0) {
      setSelectedKey(selectedKeys[0]);
      const template = templates.find(t => t.key === selectedKeys[0])?.template;
      if (template) {
        // 触发模板选择事件
        if (window.dispatchEvent) {
          window.dispatchEvent(new CustomEvent('templateSelected', { 
            detail: template 
          }));
        }
      }
    }
  };

  return (
    <div style={{ padding: '16px' }}>
      <div style={{ marginBottom: '16px' }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => {
            if (window.dispatchEvent) {
              window.dispatchEvent(new CustomEvent('createTemplate'));
            }
          }}
        >
          新建模板
        </Button>
      </div>
      <Tree
        treeData={templates}
        onSelect={handleSelect}
        selectedKeys={selectedKey ? [selectedKey] : []}
        loading={loading}
      />
    </div>
  );
};

export default TemplateTree; 