import React, { useState, useRef, useEffect } from 'react';
import { 
  Modal, 
  Form, 
  Input, 
  Button, 
  Space, 
  Typography, 
  message, 
  Checkbox, 
  Select,
  Spin,
  Card,
  Table,
  Tooltip,
  Popconfirm,
  Radio
} from 'antd';
import { 
  BulbOutlined, 
  ThunderboltOutlined, 
  SaveOutlined, 
  ReloadOutlined, 
  CopyOutlined, 
  EyeOutlined,
  DeleteOutlined,
  ExportOutlined,
  CodeOutlined,
  PictureOutlined
} from '@ant-design/icons';
import { generatePrompt, generateFunctionCallingPrompt, generateImagePrompt } from '../services/promptApi';
import { getModels, createPrompt, fetchPrompts, deletePrompt, exportPrompts } from '../services/api';
import './PromptOptimizer.css';

const { TextArea } = Input;
const { Title, Paragraph, Text } = Typography;

const PromptOptimizer = ({ open, onCancel, onOk }) => {
  const [step, setStep] = useState(0); // 0: 输入, 1: 生成中, 2: 完成
  const [form] = Form.useForm();
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPrompt, setGeneratedPrompt] = useState('');
  const [deepReasoningContent, setDeepReasoningContent] = useState('');
  const [evaluationContent, setEvaluationContent] = useState('');
  const [isDeepReasoning, setIsDeepReasoning] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [modelList, setModelList] = useState([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [savedPrompts, setSavedPrompts] = useState([]);
  const [loadingPrompts, setLoadingPrompts] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [optimizationType, setOptimizationType] = useState('general');
  const abortControllerRef = useRef(null);

  // 加载模型列表和已保存提示词
  useEffect(() => {
    if (open) {
      fetchModels();
      loadSavedPrompts();
    }
  }, [open]);

  // 获取模型列表
  const fetchModels = async () => {
    try {
      setLoadingModels(true);
      const response = await getModels();
      if (response && response.data && Array.isArray(response.data)) {
        setModelList(response.data);
      }
    } catch (error) {
      console.error('获取模型列表失败:', error);
      message.error('获取模型列表失败');
    } finally {
      setLoadingModels(false);
    }
  };

  // 获取已保存的提示词列表
  const loadSavedPrompts = async () => {
    try {
      setLoadingPrompts(true);
      const response = await fetchPrompts();
      if (response && response.data) {
        // 过滤出名称中包含"优化提示词"的项目
        const optimizedPrompts = response.data.filter(prompt => 
          prompt.name.includes('优化提示词')
        );
        setSavedPrompts(optimizedPrompts);
      }
    } catch (error) {
      console.error('获取已保存提示词列表失败:', error);
      message.error('获取已保存提示词列表失败');
    } finally {
      setLoadingPrompts(false);
    }
  };

  // 重置状态
  const resetState = () => {
    setStep(0);
    setGeneratedPrompt('');
    setDeepReasoningContent('');
    setEvaluationContent('');
    setIsDeepReasoning(false);
    setIsEvaluating(false);
    setIsGenerating(false);
    form.resetFields();
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  // 处理关闭
  const handleCancel = () => {
    if (isGenerating) {
      message.warning('正在生成中，无法关闭');
      return;
    }
    resetState();
    onCancel();
  };

  // 处理生成取消
  const handleGenerationCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    resetState();
    onCancel();
  };

  // 处理提交
  const handleSubmit = async (values) => {
    if (!values.prompt?.trim()) {
      message.error('请输入要优化的提示词');
      return;
    }

    setStep(1);
    setIsGenerating(true);
    setGeneratedPrompt('');
    setDeepReasoningContent('');
    setEvaluationContent('');
    setIsDeepReasoning(false);
    setIsEvaluating(false);

    // 创建新的AbortController
    abortControllerRef.current = new AbortController();

    try {
      // 构建请求参数，如果选择了自定义模型，则不传递chatModel
      const requestParams = {
        prompt: values.prompt,
        requirements: values.requirements || '',
        enableDeepReasoning: values.enableDeepReasoning || false,
        language: 'zh-CN',
      };
      
      // 如果选择了自定义模型，则传递modelId
      if (values.modelId) {
        requestParams.modelId = values.modelId;
      } else if (values.chatModel) {
        // 否则，如果选择了OpenAI模型，则传递chatModel
        requestParams.chatModel = values.chatModel;
      }
      
      // 根据选择的优化类型调用不同的API函数
      let generateFunction;
      switch (values.optimizationType) {
        case 'function-calling':
          generateFunction = generateFunctionCallingPrompt;
          break;
        case 'image':
          generateFunction = generateImagePrompt;
          break;
        default:
          generateFunction = generatePrompt;
      }
      
      // 调用选定的API函数生成提示词
      for await (const event of generateFunction(requestParams)) {
        // 检查是否已被取消
        if (abortControllerRef.current?.signal.aborted) {
          break;
        }

        // 处理流式响应数据
        if (event.data) {
          try {
            const data = JSON.parse(event.data);

            if (data.type === "deep-reasoning-start") {
              setIsDeepReasoning(true);
            } else if (data.type === "deep-reasoning-end") {
              setIsDeepReasoning(false);
            } else if (data.type === "deep-reasoning") {
              if (data.message) {
                setDeepReasoningContent(prev => prev + data.message);
              }
            } else if (data.type === "evaluate-start") {
              setIsEvaluating(true);
            } else if (data.type === "evaluate-end") {
              setIsEvaluating(false);
            } else if (data.type === "evaluate") {
              if (data.message) {
                setEvaluationContent(prev => prev + data.message);
              }
            } else if (data.type === "error") {
              console.error('生成过程中发生错误:', data.message || data.error);
              message.error(data.message || data.error || '生成失败');
              setStep(0);
              setIsGenerating(false);
              break;
            } else if (data.type === "message") {
              if (data.message) {
                setGeneratedPrompt(prev => prev + data.message);
              }
            }

            // 检查是否完成
            if (data.done || event.event === 'done') {
              setStep(2);
              setIsGenerating(false);
              break;
            }
          } catch (e) {
            // 如果不是JSON格式，直接添加到结果中
            if (event.data !== '[DONE]') {
              if (isDeepReasoning) {
                setDeepReasoningContent(prev => prev + event.data);
              } else {
                setGeneratedPrompt(prev => prev + event.data);
              }
            } else {
              setStep(2);
              setIsGenerating(false);
              break;
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        // 请求被取消，不显示错误
        return;
      }
      console.error('生成提示词失败:', error);
      message.error('生成失败，请稍后重试');
      setStep(0);
      setIsGenerating(false);
    } finally {
      abortControllerRef.current = null;
    }
  };

  // 查看提示词详情
  const showPromptDetail = (prompt) => {
    setSelectedPrompt(prompt);
    setDetailModalVisible(true);
  };

  // 删除提示词
  const handleDelete = async (id) => {
    try {
      await deletePrompt(id);
      message.success('删除成功');
      loadSavedPrompts(); // 重新加载列表
    } catch (error) {
      console.error('删除提示词失败:', error);
      message.error('删除失败');
    }
  };

  // 导出提示词
  const handleExport = async () => {
    try {
      await exportPrompts();
      message.success('导出成功，请查看下载文件');
    } catch (error) {
      console.error('导出提示词失败:', error);
      message.error('导出失败');
    }
  };

  // 渲染不同步骤的内容
  const renderStepContent = () => {
    switch (step) {
      case 0:
        return (
          <>
            <Form
              form={form}
              onFinish={handleSubmit}
              layout="vertical"
              initialValues={{
                enableDeepReasoning: true,
                chatModel: 'gpt-4',
                optimizationType: 'general'
              }}
            >
              <Form.Item
                name="prompt"
                label="原始提示词"
                rules={[{ required: true, message: '请输入要优化的提示词' }]}
              >
                <TextArea
                  rows={6}
                  placeholder="请输入您想要优化的提示词..."
                />
              </Form.Item>

              <Form.Item
                name="optimizationType"
                label="优化类型"
                tooltip="选择不同类型的优化将应用不同的预定义要求"
              >
                <Radio.Group>
                  <Radio.Button value="general">
                    <Space>
                      <ThunderboltOutlined />
                      通用优化
                    </Space>
                  </Radio.Button>
                  <Radio.Button value="function-calling">
                    <Space>
                      <CodeOutlined />
                      函数调用优化
                    </Space>
                  </Radio.Button>
                  <Radio.Button value="image">
                    <Space>
                      <PictureOutlined />
                      图像生成优化
                    </Space>
                  </Radio.Button>
                </Radio.Group>
              </Form.Item>

              <Form.Item shouldUpdate={(prevValues, currentValues) => 
                prevValues.optimizationType !== currentValues.optimizationType
              }>
                {({ getFieldValue }) => {
                  const type = getFieldValue('optimizationType');
                  let predefineRequirements = '';
                  
                  switch (type) {
                    case 'function-calling':
                      predefineRequirements = (
                        <ul>
                          <li>确保函数调用指令清晰明确</li>
                          <li>参数说明详细准确</li>
                          <li>返回值格式规范</li>
                          <li>错误处理机制完善</li>
                          <li>示例调用清晰易懂</li>
                        </ul>
                      );
                      break;
                    case 'image':
                      predefineRequirements = (
                        <ul>
                          <li>视觉元素描述详细具体</li>
                          <li>艺术风格明确清晰</li>
                          <li>构图和色彩指导准确</li>
                          <li>技术参数设置合理</li>
                          <li>避免模糊和歧义表达</li>
                          <li>增强视觉冲击力</li>
                        </ul>
                      );
                      break;
                    default:
                      return null;
                  }
                  
                  return predefineRequirements ? (
                    <Card 
                      size="small" 
                      title={`${type === 'function-calling' ? '函数调用' : '图像生成'}优化的预定义要求`}
                      style={{ marginBottom: 16 }}
                    >
                      {predefineRequirements}
                      <Text type="secondary">这些预定义要求将与您输入的自定义要求一起应用</Text>
                    </Card>
                  ) : null;
                }}
              </Form.Item>

              <Form.Item
                name="requirements"
                label="自定义优化要求"
              >
                <TextArea
                  rows={4}
                  placeholder="请描述您的优化要求（可选）..."
                />
              </Form.Item>

              <Form.Item
                name="modelId"
                label="选择自定义模型"
                tooltip="选择自定义模型进行提示词优化，不选则使用默认模型"
              >
                <Select 
                  placeholder="选择自定义模型" 
                  allowClear 
                  loading={loadingModels}
                  optionFilterProp="label"
                  showSearch
                  onChange={(value) => {
                    // 当选择自定义模型时，清除chatModel字段
                    if (value) {
                      form.setFieldsValue({ chatModel: undefined });
                    }
                  }}
                >
                  {modelList.map(model => (
                    <Select.Option key={model.id} value={model.id} label={model.name}>
                      {model.name} ({model.provider})
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="chatModel"
                label="选择OpenAI模型"
                tooltip="如果选择了自定义模型，此选项将被忽略"
                shouldUpdate={(prevValues, currentValues) => prevValues.modelId !== currentValues.modelId}
              >
                {({ getFieldValue }) => {
                  // 如果选择了自定义模型，则隐藏OpenAI模型选择器
                  return getFieldValue('modelId') ? null : (
                <Select placeholder="选择AI模型">
                  <Select.Option value="gpt-4">GPT-4</Select.Option>
                  <Select.Option value="gpt-3.5-turbo">GPT-3.5 Turbo</Select.Option>
                </Select>
                  );
                }}
              </Form.Item>

              <Form.Item name="enableDeepReasoning" valuePropName="checked">
                <Checkbox>
                  <Space>
                    <BulbOutlined />
                    启用深度推理模式
                    <Text type="secondary">（提供详细的分析过程）</Text>
                  </Space>
                </Checkbox>
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button onClick={handleCancel}>
                    取消
                  </Button>
                  <Button 
                    type="primary" 
                    htmlType="submit"
                    icon={<ThunderboltOutlined />}
                  >
                    开始优化
                  </Button>
                </Space>
              </Form.Item>
            </Form>

            {/* 已保存的优化提示词列表 */}
            <Card 
              title="已保存的优化提示词" 
              size="small" 
              style={{ marginTop: 16 }}
              extra={
                <Space>
                  <Button 
                    icon={<ReloadOutlined />} 
                    size="small" 
                    onClick={loadSavedPrompts}
                    loading={loadingPrompts}
                  >
                    刷新
                  </Button>
                  <Button 
                    icon={<ExportOutlined />} 
                    size="small" 
                    onClick={handleExport}
                    disabled={savedPrompts.length === 0}
                  >
                    导出
                  </Button>
                </Space>
              }
            >
              <Table 
                dataSource={savedPrompts} 
                rowKey="id"
                size="small"
                pagination={{ pageSize: 5 }}
                loading={loadingPrompts}
                columns={[
                  {
                    title: '名称',
                    dataIndex: 'name',
                    ellipsis: true,
                    render: (text, record) => (
                      <Tooltip title={text}>
                        <a onClick={() => showPromptDetail(record)}>{text}</a>
                      </Tooltip>
                    )
                  },
                  {
                    title: '描述',
                    dataIndex: 'description',
                    ellipsis: true,
                    render: (text) => (
                      <Tooltip title={text}>
                        <span>{text}</span>
                      </Tooltip>
                    )
                  },
                  {
                    title: '创建时间',
                    dataIndex: 'created_at',
                    render: (text) => new Date(text).toLocaleString(),
                    width: 180
                  },
                  {
                    title: '操作',
                    key: 'action',
                    width: 180,
                    render: (_, record) => (
                      <Space>
                        <Button 
                          type="text" 
                          icon={<EyeOutlined />} 
                          onClick={() => showPromptDetail(record)}
                          title="查看详情"
                        />
                        <Button 
                          type="text" 
                          icon={<CopyOutlined />} 
                          onClick={() => {
                            navigator.clipboard.writeText(record.content);
                            message.success('已复制到剪贴板');
                          }}
                          title="复制内容"
                        />
                        <Popconfirm
                          title="确定要删除这个提示词吗？"
                          description="删除后将无法恢复"
                          onConfirm={() => handleDelete(record.id)}
                          okText="确定"
                          cancelText="取消"
                        >
                          <Button 
                            type="text" 
                            icon={<DeleteOutlined />} 
                            danger
                            title="删除"
                          />
                        </Popconfirm>
                        <Button
                          type="primary"
                          size="small"
                          onClick={() => {
                            // 将提示词内容填充到表单
                            form.setFieldsValue({
                              prompt: record.content
                            });
                            message.success('已应用提示词到编辑器');
                          }}
                        >
                          应用
                        </Button>
                      </Space>
                    )
                  }
                ]}
              />
            </Card>
          </>
        );

      case 1:
      case 2:
        return (
          <div className="optimization-result">
            <div className="result-header">
              <Title level={4}>
                {step === 1 ? (
                  isDeepReasoning ? '🧠 深度推理中...' :
                  isEvaluating ? '📊 评估中...' : '⚡ 优化中...'
                ) : '✅ 优化完成'}
              </Title>
            </div>

            <div className="result-panels">
              {/* 原始提示词 */}
              <Card title="📝 原始提示词" size="small" className="result-panel">
                <TextArea
                  value={form.getFieldValue('prompt')}
                  readOnly
                  rows={4}
                />
              </Card>

              {/* 深度推理过程 */}
              {deepReasoningContent && (
                <Card title="🧠 深度推理过程" size="small" className="result-panel">
                  <div className="reasoning-content">
                    {deepReasoningContent}
                    {isDeepReasoning && <Spin size="small" />}
                  </div>
                </Card>
              )}

              {/* 优化后的提示词 */}
              <Card title="⚡ 优化后的提示词" size="small" className="result-panel">
                <TextArea
                  value={generatedPrompt || (step === 1 ? '生成中...' : '')}
                  readOnly
                  rows={6}
                />
              </Card>

              {/* 评估结果 */}
              {evaluationContent && (
                <Card title="📊 评估结果" size="small" className="result-panel">
                  <div className="evaluation-content">
                    {evaluationContent}
                    {isEvaluating && <Spin size="small" />}
                  </div>
                </Card>
              )}
            </div>

            <div className="result-actions">
              {step === 1 ? (
                <Button onClick={handleGenerationCancel}>
                  取消生成
                </Button>
              ) : (
                <Space>
                  <Button onClick={() => setStep(0)}>
                    重新优化
                  </Button>
                  <Button 
                    onClick={() => {
                      navigator.clipboard.writeText(generatedPrompt);
                      message.success('已复制到剪贴板');
                    }}
                  >
                    复制结果
                  </Button>
                  <Button 
                    type="primary"
                    icon={<SaveOutlined />}
                    onClick={() => {
                      // 保存优化后的提示词
                      const currentDate = new Date();
                      const timestamp = currentDate.getTime(); // 添加毫秒级时间戳确保唯一性
                      const formattedDate = `${currentDate.getMonth() + 1}/${currentDate.getDate()} ${currentDate.getHours()}:${String(currentDate.getMinutes()).padStart(2, '0')}:${String(currentDate.getSeconds()).padStart(2, '0')}`;
                      
                      // 创建一个Modal来输入名称和描述
                      Modal.confirm({
                        title: '保存优化后的提示词',
                        content: (
                          <div>
                            <p>请输入提示词名称和描述：</p>
                            <Input 
                              placeholder="提示词名称" 
                              id="prompt-name-input" 
                              defaultValue={`优化提示词_${formattedDate}_${timestamp}`} 
                            />
                            <Input.TextArea 
                              placeholder="提示词描述" 
                              id="prompt-description-input" 
                              style={{ marginTop: 8 }}
                              defaultValue={`基于原始提示词优化生成，优化要求: ${form.getFieldValue('requirements') || '请优化这个提示词，使其更加清晰、具体，并减少歧义。保持专业性的同时提高可读性。'}`}
                            />
                          </div>
                        ),
                        onOk: async () => {
                          const nameInput = document.getElementById('prompt-name-input');
                          const descriptionInput = document.getElementById('prompt-description-input');
                          
                          const name = nameInput ? nameInput.value : `优化提示词_${formattedDate}_${timestamp}`;
                          const description = descriptionInput ? descriptionInput.value : '';
                          
                          try {
                            // 构建保存请求
                            const saveData = {
                              name,
                              description,
                              content: generatedPrompt,
                              variables: {
                                user_input: {
                                  type: 'string',
                                  description: '用户输入',
                                  required: true
                                }
                              }
                            };
                            
                            // 发送保存请求
                            await createPrompt(saveData);
                            message.success('提示词保存成功');
                            // 刷新已保存的提示词列表
                            loadSavedPrompts();
                            // 触发刷新提示词列表事件
                            console.log('触发刷新提示词列表事件');
                            window.dispatchEvent(new CustomEvent('refreshPrompts'));
                            // 触发切换到提示词列表标签页的事件
                            console.log('触发切换到提示词列表标签页的事件');
                            window.dispatchEvent(new CustomEvent('switchToPromptsTab'));
                            // 关闭优化器Modal
                            handleCancel();
                          } catch (error) {
                            console.error('保存提示词失败:', error);
                            message.error('保存提示词失败');
                          }
                        }
                      });
                    }}
                  >
                    保存提示词
                  </Button>
                </Space>
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <>
      <Modal
        title="智能提示词优化"
        open={open}
        onCancel={handleCancel}
        footer={null}
        width={step > 0 ? 1200 : 600}
        destroyOnClose
        maskClosable={!isGenerating}
      >
        {renderStepContent()}
      </Modal>

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
            onClick={() => {
              if (selectedPrompt) {
                navigator.clipboard.writeText(selectedPrompt.content);
                message.success('已复制到剪贴板');
              }
            }}
          >
            复制内容
          </Button>,
          <Button 
            key="use" 
            type="primary"
            onClick={() => {
              if (selectedPrompt) {
                form.setFieldsValue({
                  prompt: selectedPrompt.content
                });
                message.success('已应用提示词到编辑器');
                setDetailModalVisible(false);
              }
            }}
          >
            应用此提示词
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
    </>
  );
};

export default PromptOptimizer;
