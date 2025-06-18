import React, { useState, useEffect } from 'react';
import MDEditor from '@uiw/react-md-editor';
import { Form, Input, Button, Card, message, Select, Tooltip, Space, Modal, Row, Col, Typography, Alert, Spin, Divider, Tag } from 'antd';
import { InfoCircleOutlined, SaveOutlined, RobotOutlined, PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import { getModels, testPrompt, createTemplate, fetchTemplates } from '../services/api';
import TestResultPanel from './TestResultPanel';

const { Text, Paragraph } = Typography;

const PromptEditor = React.forwardRef(({ onTestResult }, ref) => {
  const [content, setContent] = useState('');
  const [variables, setVariables] = useState({user_input: ''});
  const [variableNames, setVariableNames] = useState(['user_input']);
  const [newVariableName, setNewVariableName] = useState('');
  const [models, setModels] = useState([]);
  const [selectedModelId, setSelectedModelId] = useState(null);
  const [evaluatorModelId, setEvaluatorModelId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [saveModalVisible, setSaveModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    const handleTemplateSelected = (event) => {
      const template = event.detail;
      if (template) {
        setContent(template.content);
      }
    };

    const handleCreateTemplate = () => {
      setContent(`你是一个{{user_input}}专家，请回答以下问题：

1. 
2. 
3. `);
      form.resetFields();
      setSaveModalVisible(true);
    };

    const handleOptimizedPrompt = (event) => {
      const { prompt } = event.detail;
      if (prompt) {
        setContent(prompt);
        message.success('已成功应用优化后的提示词');
      }
    };

    const handleUsePrompt = (event) => {
      const prompt = event.detail;
      if (prompt && prompt.content) {
        setContent(prompt.content);
        message.success('已应用提示词到编辑器');
      }
    };

    window.addEventListener('templateSelected', handleTemplateSelected);
    window.addEventListener('createTemplate', handleCreateTemplate);
    window.addEventListener('optimizedPrompt', handleOptimizedPrompt);
    window.addEventListener('usePrompt', handleUsePrompt);

    return () => {
      window.removeEventListener('templateSelected', handleTemplateSelected);
      window.removeEventListener('createTemplate', handleCreateTemplate);
      window.removeEventListener('optimizedPrompt', handleOptimizedPrompt);
      window.removeEventListener('usePrompt', handleUsePrompt);
    };
  }, [form]);

  const loadModels = async () => {
    try {
      const response = await getModels();
      // 过滤掉已删除的模型
      const availableModels = response.data.filter(m => !m.is_deleted);
      setModels(availableModels);
    } catch (error) {
      console.error('Failed to load models:', error);
      message.error('加载模型列表失败');
    }
  };

  const handleInsertVariable = (variableName = 'user_input') => {
    setContent(prev => prev + `{{${variableName}}}`);
  };

  const addVariable = () => {
    if (!newVariableName.trim()) {
      message.warning('变量名不能为空');
      return;
    }
    
    if (variableNames.includes(newVariableName)) {
      message.warning('变量名已存在');
      return;
    }
    
    setVariableNames([...variableNames, newVariableName]);
    setVariables({...variables, [newVariableName]: ''});
    setNewVariableName('');
  };

  const removeVariable = (name) => {
    if (name === 'user_input') {
      message.warning('不能删除默认变量 user_input');
      return;
    }
    
    const newVariableNames = variableNames.filter(v => v !== name);
    const newVariables = {...variables};
    delete newVariables[name];
    
    setVariableNames(newVariableNames);
    setVariables(newVariables);
  };

  const handleTest = async () => {
    if (!content.trim()) {
      message.warning('请输入Prompt内容');
      return;
    }

    if (!selectedModelId) {
      message.warning('请选择模型');
      return;
    }

    setLoading(true);
    try {
      const result = await testPrompt({
        content,
        model_id: selectedModelId,
        evaluator_model_id: evaluatorModelId,
        variables: variables
      });

      // 处理响应结果
      if (result.error) {
        message.error(result.error);
        return;
      }

      // 确保结果格式正确
      const output = result.data?.output || result.output || '';
      const evaluation = result.data?.evaluation || result.evaluation || null;

      // 设置当前测试结果
      const resultData = {
        output,
        evaluation: evaluation ? JSON.parse(JSON.stringify(evaluation)) : null
      };
      
      setTestResults(resultData);
      
      // 调用父组件传入的回调，传递测试结果
      if (onTestResult) {
        onTestResult(resultData);
      }

      // 更新测试记录列表
      window.dispatchEvent(new CustomEvent('refreshTestResults'));

    } catch (error) {
      console.error('Test failed:', error);
      message.error('测试失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (values) => {
    if (!content.trim()) {
      message.warning('请输入模板内容');
      return;
    }

    // 创建变量定义对象
    const variablesObj = {};
    variableNames.forEach(name => {
      variablesObj[name] = {
        type: 'string',
        description: `${name}变量`,
        required: name === 'user_input' // 只有user_input是必填的
      };
    });

    try {
      await createTemplate({
        ...values,
        content,
        variables: variablesObj
      });
      message.success('保存成功');
      setSaveModalVisible(false);
      form.resetFields();
      window.dispatchEvent(new CustomEvent('refreshTemplates'));
    } catch (error) {
      console.error('Failed to save template:', error);
      message.error('保存失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const renderEvaluation = (evaluation) => {
    if (!evaluation) return null;

    // 检查是否有错误
    if (evaluation.error) {
      return (
        <Alert
          message="评估失败"
          description={evaluation.error}
          type="error"
          showIcon
        />
      );
    }

    // 渲染评分卡片
    const renderScoreCard = (name, score, reason) => {
      let color = 'red';
      if (score >= 7) color = 'green';
      else if (score >= 4) color = 'orange';

      return (
        <Card
          size="small"
          title={
            <Space>
              <span>{name}:</span>
              <Text style={{ color }}>{score}/10</Text>
            </Space>
          }
          style={{ marginBottom: 8 }}
        >
          <Text type="secondary">{reason || '评估失败'}</Text>
        </Card>
      );
    };

    return (
      <div>
        <Typography.Title level={4}>评估结果</Typography.Title>
        <Row gutter={[16, 16]}>
          <Col span={12}>
            {renderScoreCard('相关性', evaluation.scores?.relevance, evaluation.reasons?.relevance)}
          </Col>
          <Col span={12}>
            {renderScoreCard('准确性', evaluation.scores?.accuracy, evaluation.reasons?.accuracy)}
          </Col>
          <Col span={12}>
            {renderScoreCard('完整性', evaluation.scores?.completeness, evaluation.reasons?.completeness)}
          </Col>
          <Col span={12}>
            {renderScoreCard('清晰度', evaluation.scores?.clarity, evaluation.reasons?.clarity)}
          </Col>
        </Row>
        {evaluation.suggestions && (
          <Card title="改进建议" size="small" style={{ marginTop: 16 }}>
            <ul>
              {evaluation.suggestions.split('\n').map((suggestion, index) => (
                <li key={index}>{suggestion}</li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    );
  };

  const canTest = models.length > 0 && selectedModelId;

  // 暴露方法给父组件
  React.useImperativeHandle(ref, () => ({
    setContent: (newContent) => {
      setContent(newContent);
    },
    getContent: () => content
  }));

  return (
    <div style={{ padding: '20px' }}>
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card 
            title={
              <Space>
                Prompt编辑器
                <Tooltip title={`1. 在编辑器中编写Prompt模板\n2. 使用 {{变量名}} 作为变量占位符\n3. 在下方添加变量并填写变量值\n4. 选择模型进行测试`}>
                  <InfoCircleOutlined />
                </Tooltip>
              </Space>
            }
            extra={
              <Space>
                <Button 
                  type="primary" 
                  icon={<SaveOutlined />} 
                  onClick={() => setSaveModalVisible(true)}
                  disabled={!content.trim()}
                >
                  保存为模板
                </Button>
              </Space>
            }
            variant="outlined"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space wrap>
                <Button onClick={() => handleInsertVariable('user_input')}>插入变量 {`{{user_input}}`}</Button>
                {variableNames.filter(name => name !== 'user_input').map(name => (
                  <Button key={name} onClick={() => handleInsertVariable(name)}>
                    插入变量 {`{{${name}}}`}
                  </Button>
                ))}
              </Space>
              <MDEditor 
                height={180} 
                value={content} 
                onChange={setContent} 
                placeholder={`请输入Prompt模板，使用 {{变量名}} 作为变量占位符\n例如：你是一个笑话大王，给我讲一个关于{{user_input}}的笑话。`}
              />
            </Space>

            <Divider>变量设置</Divider>
            
            <Space style={{ marginBottom: 16 }}>
              <Input 
                placeholder="输入新变量名" 
                value={newVariableName} 
                onChange={e => setNewVariableName(e.target.value)} 
                style={{ width: 150 }}
              />
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={addVariable}
              >
                添加变量
              </Button>
            </Space>
            
            <Form layout="vertical">
              {variableNames.map(name => (
                <Form.Item
                  key={name}
                  label={
                    <Space>
                      <span>变量 {name}</span>
                      {name !== 'user_input' && (
                        <Button 
                          type="text" 
                          danger 
                          icon={<DeleteOutlined />} 
                          onClick={() => removeVariable(name)}
                          size="small"
                        />
                      )}
                    </Space>
                  }
                >
                  <Input
                    placeholder={`请输入${name}的值`}
                    value={variables[name]}
                    onChange={e => setVariables({...variables, [name]: e.target.value})}
                  />
                </Form.Item>
              ))}

              <Form.Item label="选择模型">
                <Select
                  placeholder="请选择模型"
                  value={selectedModelId}
                  onChange={setSelectedModelId}
                  style={{ width: '100%' }}
                >
                  {models.map(model => (
                    <Select.Option key={model.id} value={model.id}>
                      {model.name}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item label="评估模型（可选）">
                <Select
                  placeholder="请选择评估模型"
                  value={evaluatorModelId}
                  onChange={setEvaluatorModelId}
                  style={{ width: '100%' }}
                  allowClear
                >
                  {models.map(model => (
                    <Select.Option key={model.id} value={model.id}>
                      {model.name}
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item>
                <Button 
                  type="primary" 
                  onClick={handleTest}
                  disabled={!canTest}
                  loading={loading}
                >
                  测试Prompt
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>

      <Modal
        title="保存为模板"
        open={saveModalVisible}
        onCancel={() => {
          setSaveModalVisible(false);
          form.resetFields();
        }}
        footer={null}
      >
        <Form
          form={form}
          onFinish={handleSave}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="模板名称"
            rules={[{ required: true, message: '请输入模板名称' }]}
          >
            <Input placeholder="请输入模板名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="模板描述"
            rules={[{ required: true, message: '请输入模板描述' }]}
          >
            <Input.TextArea placeholder="请输入模板描述" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">
              保存
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
});

export default PromptEditor; 