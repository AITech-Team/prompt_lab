import React, { useState, useEffect } from 'react';
import { Table, Button, message, Space } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { fetchHistory, exportHistory } from '../services/api';

const HistoryTable = () => {
  const [loading, setLoading] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [data, setData] = useState([]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const res = await fetchHistory();
      if (res && res.data) {
        setData(res.data);
      } else {
        message.error('加载历史记录失败：返回数据格式错误');
      }
    } catch (error) {
      console.error('Load history failed:', error);
      message.error('加载历史记录失败：' + (error.message || '未知错误'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const handleExportCSV = async () => {
    if (data.length === 0) {
      message.warning('没有可导出的数据');
      return;
    }

    setExportLoading(true);
    try {
      const res = await exportHistory();
      if (res && res.data) {
        // 创建Blob对象
        const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8;' });
        // 创建下载链接
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', `prompt_history_${new Date().toISOString().slice(0,10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        message.success('导出成功');
      } else {
        throw new Error('导出数据格式错误');
      }
    } catch (error) {
      console.error('Export CSV failed:', error);
      message.error('导出失败：' + (error.message || '未知错误'));
    } finally {
      setExportLoading(false);
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '模板',
      dataIndex: ['template', 'name'],
      key: 'template',
    },
    {
      title: '变量',
      dataIndex: 'variables',
      key: 'variables',
      render: (variables) => JSON.stringify(variables),
    },
    {
      title: '模型',
      dataIndex: ['model', 'name'],
      key: 'model',
    },
    {
      title: '响应',
      dataIndex: 'response',
      key: 'response',
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <Button
          type="primary"
          icon={<DownloadOutlined />}
          onClick={handleExportCSV}
          loading={exportLoading}
          disabled={data.length === 0}
        >
          导出CSV
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        loading={loading}
        pagination={{
          defaultPageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
        }}
      />
    </div>
  );
};

export default HistoryTable; 