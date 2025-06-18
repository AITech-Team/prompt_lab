import React, { useState, useEffect } from 'react';
import { Table, Button, Space, message, Modal, Typography, Card, Input } from 'antd';
import { ExportOutlined, DeleteOutlined, CopyOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons';
import { fetchPrompts, deletePrompt, exportPrompts } from '../services/api';

const { Text, Paragraph } = Typography;
const { Search } = Input;

const PromptList = ({ onSelect }) => {
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);

  // 加载提示词列表
  const loadPrompts = async () => {
    try {
      setLoading(true);
      console.log('开始加载提示词列表');
      const response = await fetchPrompts();
      console.log('提示词列表加载结果:', response);
      if (response && response.data) {
        console.log('设置提示词列表:', response.data);
        setPrompts(response.data);
      } else {
        console.error('提示词列表响应无效:', response);
      }
    } catch (error) {
      console.error('获取提示词列表失败:', error);
      message.error('获取提示词列表失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载
  useEffect(() => {
    console.log("PromptList组件初始化，加载提示词列表");
    loadPrompts();
    
    // 监听刷新提示词列表的事件
    const handleRefreshPrompts = () => {
      console.log("接收到refreshPrompts事件，刷新提示词列表");
      loadPrompts();
    };
    
    console.log("设置refreshPrompts事件监听器");
    window.addEventListener('refreshPrompts', handleRefreshPrompts);
    
    return () => {
      console.log("移除refreshPrompts事件监听器");
      window.removeEventListener('refreshPrompts', handleRefreshPrompts);
    };
  }, []);

  // 处理删除
  const handleDelete = async (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除这个提示词吗？此操作不可恢复。',
      okText: '确认',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deletePrompt(id);
          message.success('删除成功');
          loadPrompts(); // 重新加载列表
        } catch (error) {
          message.error('删除失败');
        }
      }
    });
  };

  // 处理导出
  const handleExport = async () => {
    try {
      await exportPrompts();
      // 导出处理已经在exportPrompts函数内完成，这里不需要重复处理
    } catch (error) {
      message.error('导出失败');
    }
  };

  // 处理复制
  const handleCopy = (content) => {
    navigator.clipboard.writeText(content);
    message.success('已复制到剪贴板');
  };

  // 查看详情
  const showDetail = (prompt) => {
    setSelectedPrompt(prompt);
    setDetailModalVisible(true);
  };

  // 使用提示词
  const handleUse = (prompt) => {
    if (onSelect) {
      onSelect(prompt);
    } else {
      // 如果没有提供onSelect回调，则尝试通过事件分发
      const event = new CustomEvent('usePrompt', { detail: prompt });
      window.dispatchEvent(event);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <a onClick={() => showDetail(record)}>{text}</a>
      )
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="text" 
            icon={<CopyOutlined />} 
            onClick={() => handleCopy(record.content)}
            title="复制内容"
          />
          <Button 
            type="text" 
            icon={<DeleteOutlined />} 
            danger
            onClick={() => handleDelete(record.id)}
            title="删除"
          />
          <Button 
            type="primary" 
            size="small"
            onClick={() => handleUse(record)}
          >
            使用
          </Button>
        </Space>
      )
    }
  ];

  // 过滤提示词
  const filteredPrompts = prompts.filter(
    prompt => 
      prompt.name.toLowerCase().includes(searchText.toLowerCase()) ||
      prompt.description.toLowerCase().includes(searchText.toLowerCase())
  );

  return (
    <Card
      title="已保存的提示词"
      extra={
        <Space>
          <Button 
            icon={<ReloadOutlined />}
            onClick={loadPrompts}
            loading={loading}
          >
            刷新列表
          </Button>
          <Button 
            type="primary" 
            icon={<ExportOutlined />} 
            onClick={handleExport}
            disabled={prompts.length === 0}
          >
            导出提示词
          </Button>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        <Search
          placeholder="搜索提示词"
          allowClear
          enterButton
          value={searchText}
          onChange={e => setSearchText(e.target.value)}
        />
        
        <Table
          columns={columns}
          dataSource={filteredPrompts}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Space>

      {/* 提示词详情模态框 */}
      <Modal
        title="提示词详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="copy" 
            type="default" 
            icon={<CopyOutlined />}
            onClick={() => selectedPrompt && handleCopy(selectedPrompt.content)}
          >
            复制内容
          </Button>,
          <Button 
            key="use" 
            type="primary"
            onClick={() => {
              selectedPrompt && handleUse(selectedPrompt);
              setDetailModalVisible(false);
            }}
          >
            使用此提示词
          </Button>
        ]}
        width={700}
      >
        {selectedPrompt && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text strong>名称：</Text>
              <Text>{selectedPrompt.name}</Text>
            </div>
            <div>
              <Text strong>描述：</Text>
              <Text>{selectedPrompt.description}</Text>
            </div>
            <div>
              <Text strong>创建时间：</Text>
              <Text>{new Date(selectedPrompt.created_at).toLocaleString()}</Text>
            </div>
            <div>
              <Text strong>内容：</Text>
              <Paragraph 
                style={{ 
                  background: '#f5f5f5', 
                  padding: 16, 
                  borderRadius: 4,
                  maxHeight: 300,
                  overflow: 'auto'
                }}
              >
                {selectedPrompt.content}
              </Paragraph>
            </div>
          </Space>
        )}
      </Modal>
    </Card>
  );
};

export default PromptList; 