import React, { useState, useEffect } from 'react';
import { Card, Table, Space, Button, Tooltip, Modal, message, Tabs, Empty, Spin } from 'antd';
import { DeleteOutlined, ExportOutlined, HistoryOutlined } from '@ant-design/icons';
import { listTestRecords, deleteTestRecord, exportTestRecords } from '../services/api';

const ResponsePanel = ({ responses }) => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);

  const loadRecords = async () => {
    setLoading(true);
    try {
      const response = await listTestRecords();
      
      if (response && response.data) {
        setRecords(response.data);
      } else {
        setRecords([]);
      }
    } catch (error) {
      message.error('加载测试记录失败');
      setRecords([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecords();
  }, []); // 组件加载时获取历史记录

  useEffect(() => {
    // 当有新的测试结果时，设置为当前结果并刷新历史记录
    if (responses) {
      setCurrentResult(responses);
      // 延迟一点再刷新记录，确保后端已经保存
      setTimeout(() => {
        loadRecords();
      }, 500);
    }
  }, [responses]);

  // 监听刷新事件
  useEffect(() => {
    const handleRefresh = () => {
      loadRecords();
    };
    window.addEventListener('refreshTestResults', handleRefresh);
    return () => {
      window.removeEventListener('refreshTestResults', handleRefresh);
    };
  }, []);

  const handleDelete = async (record) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这条测试记录吗？',
      onOk: async () => {
        try {
          await deleteTestRecord(record.id);
          message.success('删除成功');
          loadRecords();
        } catch (error) {
          console.error('Failed to delete record:', error);
          message.error('删除失败');
        }
      }
    });
  };

  const handleExport = async () => {
    try {
      const response = await exportTestRecords();
      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `test_records_${new Date().toISOString().slice(0,19).replace(/:/g, '-')}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Failed to export records:', error);
      message.error('导出失败');
    }
  };

  const columns = [
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
      render: (model) => model || '-',
    },
    {
      title: '提示词',
      dataIndex: 'prompt',
      key: 'prompt',
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <span>{text && text.length > 30 ? `${text.substring(0, 30)}...` : text || '-'}</span>
        </Tooltip>
      ),
    },
    {
      title: '评估分数',
      dataIndex: 'evaluation',
      key: 'evaluation',
      render: (evaluation) => {
        if (!evaluation || !evaluation.scores) return '-';
        const scores = evaluation.scores;
        const avg = Object.values(scores).reduce((a, b) => a + b, 0) / Object.values(scores).length;
        return (
          <Tooltip title={
            <div>
              {Object.entries(scores).map(([key, value]) => (
                <div key={key}>{key}: {value}/10</div>
              ))}
            </div>
          }>
            <span>{avg.toFixed(1)}</span>
          </Tooltip>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<HistoryOutlined />}
            onClick={() => {
              // 点击查看历史记录详情
              setCurrentResult({
                output: record.response,
                evaluation: record.evaluation
              });
            }}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record)}
          />
        </Space>
      ),
    },
  ];

  // 渲染评分卡片
  const renderScoreCard = (name, score, reason) => {
    if (!score) return null;
    
    let color = 'red';
    if (score >= 7) color = 'green';
    else if (score >= 4) color = 'orange';

    return (
      <Card
        size="small"
        title={
          <Space>
            <span>{name}:</span>
            <span style={{ color }}>{score}/10</span>
          </Space>
        }
        style={{ marginBottom: 8 }}
      >
        <div style={{ fontSize: '12px' }}>{reason || '无评估理由'}</div>
      </Card>
    );
  };

  // 渲染当前结果
  const renderCurrentResult = () => {
    if (!currentResult) {
      return (
        <Empty
          description="暂无测试结果"
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      );
    }

    const { output, evaluation } = currentResult;

    return (
      <div>
        <Card title="模型输出" size="small" style={{ marginBottom: 16 }}>
          <div style={{ 
            whiteSpace: 'pre-wrap',
            maxHeight: '300px',
            overflow: 'auto'
          }}>
            {output || '无输出'}
          </div>
        </Card>

        {evaluation && (
          <div>
            <h4>评估结果</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              {renderScoreCard('相关性', evaluation.scores?.relevance, evaluation.reasons?.relevance)}
              {renderScoreCard('准确性', evaluation.scores?.accuracy, evaluation.reasons?.accuracy)}
              {renderScoreCard('完整性', evaluation.scores?.completeness, evaluation.reasons?.completeness)}
              {renderScoreCard('清晰度', evaluation.scores?.clarity, evaluation.reasons?.clarity)}
            </div>
            {evaluation.suggestions && (
              <Card size="small" title="改进建议" style={{ marginTop: 16 }}>
                <div style={{ fontSize: '12px' }}>{evaluation.suggestions}</div>
              </Card>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <Tabs
      defaultActiveKey="current"
      items={[
        {
          key: 'current',
          label: '当前结果',
          children: renderCurrentResult()
        },
        {
          key: 'history',
          label: '历史记录',
          children: (
            <>
              <div style={{ marginBottom: 16, textAlign: 'right' }}>
                <Button
                  type="primary"
                  icon={<ExportOutlined />}
                  onClick={handleExport}
                  disabled={records.length === 0}
                >
                  导出CSV
                </Button>
              </div>
              {loading ? (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <Spin />
                </div>
              ) : (
                <Table
                  columns={columns}
                  dataSource={records}
                  rowKey="id"
                  pagination={{
                    defaultPageSize: 5,
                    showSizeChanger: true,
                    pageSizeOptions: ['5', '10', '20'],
                    showTotal: (total) => `共 ${total} 条记录`,
                  }}
                  size="small"
                />
              )}
            </>
          )
        }
      ]}
    />
  );
};

export default ResponsePanel; 