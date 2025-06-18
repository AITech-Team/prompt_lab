import React, { useState } from 'react';
import { Table, Button, message, Popconfirm, Tag } from 'antd';
import { DeleteOutlined, UndoOutlined } from '@ant-design/icons';
import { Model } from '../types/model';

interface ModelTableProps {
  models: Model[];
  onDelete: (id: number) => void;
  onRestore: (id: number) => void;
  loading: boolean;
}

const ModelTable: React.FC<ModelTableProps> = ({ models, onDelete, onRestore, loading }) => {
  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Model) => (
        <span>
          {text}
          {record.is_deleted && (
            <Tag color="red" style={{ marginLeft: 8 }}>
              已删除
            </Tag>
          )}
        </span>
      ),
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
    },
    {
      title: '基础URL',
      dataIndex: 'base_url',
      key: 'base_url',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Model) => (
        <span>
          {record.is_deleted ? (
            <Popconfirm
              title="确定要恢复这个模型吗？"
              onConfirm={() => handleRestore(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" icon={<UndoOutlined />}>
                恢复
              </Button>
            </Popconfirm>
          ) : (
            <Popconfirm
              title="确定要删除这个模型吗？"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button type="link" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </span>
      ),
    },
  ];

  const handleDelete = async (id: number) => {
    try {
      await onDelete(id);
      message.success('模型删除成功');
    } catch (error) {
      message.error('删除模型失败');
    }
  };

  const handleRestore = async (id: number) => {
    try {
      await onRestore(id);
      message.success('模型恢复成功');
    } catch (error) {
      message.error('恢复模型失败');
    }
  };

  return (
    <Table
      columns={columns}
      dataSource={models}
      rowKey="id"
      loading={loading}
      pagination={false}
    />
  );
};

export default ModelTable; 