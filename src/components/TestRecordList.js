import React, { useState, useEffect } from 'react';
import { Table, Card, Typography, Space, Button, Tooltip, Modal, message } from 'antd';
import { EyeOutlined, DeleteOutlined } from '@ant-design/icons';
import { getTestRecords, deleteTestRecord, exportTestRecords } from '../services/api';
import TestResultPanel from './TestResultPanel';

const { Text } = Typography;

const TestRecordList = () => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [previewRecord, setPreviewRecord] = useState(null);
  const [previewVisible, setPreviewVisible] = useState(false);

  useEffect(() => {
    loadRecords();
    
    // 监听测试结果更新事件
    const handleRefresh = () => {
      setTimeout(loadRecords, 500); // 添加延迟以确保数据已保存
    };
    window.addEventListener('refreshTestResults', handleRefresh);
    
    return () => {
      window.removeEventListener('refreshTestResults', handleRefresh);
    };
  }, []);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const response = await getTestRecords();
      setRecords(response.data);
    } catch (error) {
      console.error('Failed to load test records:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = (record) => {
    setPreviewRecord(record);
    setPreviewVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      await deleteTestRecord(id);
      await loadRecords();
    } catch (error) {
      console.error('Failed to delete test record:', error);
    }
  };

  // 导出记录
  const handleExport = async () => {
    try {
      const response = await exportTestRecords();
      
      // 创建下载链接
      const url = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `测试记录_${new Date().toLocaleDateString()}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      message.success('导出成功');
    } catch (error) {
      console.error('Failed to export records:', error);
      message.error('导出失败');
    }
  };

  const columns = [
    {
      title: '测试时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
      width: 180,
      sorter: (a, b) => new Date(b.created_at) - new Date(a.created_at),
      defaultSortOrder: 'descend'
    },
    {
      title: '提示词',
      dataIndex: 'prompt',
      key: 'prompt',
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Text ellipsis style={{ maxWidth: 200 }}>{text}</Text>
        </Tooltip>
      )
    },
    {
      title: '变量',
      dataIndex: 'variables',
      key: 'variables',
      width: 150,
      render: (variables) => {
        if (!variables) return '-';
        return Object.entries(variables).map(([key, value]) => (
          <div key={key}>{`${key}: ${value}`}</div>
        ));
      }
    },
    {
      title: '响应',
      dataIndex: 'response',
      key: 'response',
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <Text ellipsis style={{ maxWidth: 300 }}>{text}</Text>
        </Tooltip>
      )
    },
    {
      title: '评估结果',
      dataIndex: 'evaluation',
      key: 'evaluation',
      width: 120,
      render: (evaluation, record) => {
        if (!evaluation) return '-';
        if (evaluation.error) return <Text type="danger">评估失败</Text>;
        
        const scores = evaluation.scores || {};
        const avg = Object.values(scores).reduce((a, b) => a + b, 0) / Object.keys(scores).length;
        
        return (
          <Button type="link" onClick={() => handlePreview(record)}>
            {avg.toFixed(1)}/10
          </Button>
        );
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(record)}
          >
            查看
          </Button>
          <Button
            type="link"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          >
            删除
          </Button>
        </Space>
      )
    }
  ];

  return (
    <>
      <Card 
        title="测试记录" 
        style={{ marginTop: 16 }}
        extra={
          <Button 
            type="primary" 
            onClick={handleExport}
            disabled={records.length === 0}
          >
            导出记录
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
          scroll={{ x: 1200 }}
        />
      </Card>

      <Modal
        title="测试结果详情"
        visible={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={null}
        width={800}
      >
        {previewRecord && (
          <TestResultPanel
            result={{
              output: previewRecord.response,
              evaluation: previewRecord.evaluation
            }}
          />
        )}
      </Modal>
    </>
  );
};

export default TestRecordList; 