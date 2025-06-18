import React from 'react';
import { Card, Typography, Tabs, Row, Col, Divider, Alert } from 'antd';
import MDEditor from '@uiw/react-md-editor';

const { Text, Title } = Typography;
const { TabPane } = Tabs;

const TestResultPanel = ({ result }) => {
  if (!result) {
    return null;
  }

  const { output, evaluation, thinking } = result;

  // 检查输出是否包含错误信息
  const isErrorOutput = output && output.toLowerCase().includes('调用失败');

  // 分数评估卡片
  const renderScoreCard = (name, score, reason) => {
    let color = 'red';
    if (score >= 7) color = 'green';
    else if (score >= 4) color = 'orange';

    return (
      <Card
        size="small"
        title={
          <div>
            <span>{name}: </span>
            <Text style={{ color }}>{score}/10</Text>
          </div>
        }
        style={{ marginBottom: 8 }}
      >
        <Text type="secondary">{reason || '无评估信息'}</Text>
      </Card>
    );
  };

  // 评估部分
  const renderEvaluation = () => {
    if (!evaluation) return null;

    // 检查是否有错误
    if (evaluation.error) {
      return <Alert message="评估失败" description={evaluation.error} type="error" showIcon />;
    }

    return (
      <div>
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

  const renderThinking = () => {
    if (!thinking) return null;
    
    return (
      <div>
        <Title level={4}>模型思考过程</Title>
        <Card>
          <div data-color-mode="light">
            <MDEditor.Markdown 
              source={thinking} 
              style={{ padding: '10px', backgroundColor: '#f5f5f5' }}
            />
          </div>
        </Card>
      </div>
    );
  };

  // 主要输出部分
  const renderOutput = () => {
    if (!output) return <Alert message="没有获取到输出结果" type="warning" showIcon />;
    
    if (isErrorOutput) {
      return <Alert message="API调用失败" description={output} type="error" showIcon />;
    }
    
    return (
      <div data-color-mode="light">
        <MDEditor.Markdown 
          source={output} 
          style={{ padding: '10px', backgroundColor: '#f5f5f5', marginBottom: '20px' }}
        />
      </div>
    );
  };

  return (
    <div>
      <Title level={4}>响应结果</Title>
      {renderOutput()}
      
      {thinking && (
        <>
          <Divider style={{ margin: '24px 0' }} />
          {renderThinking()}
        </>
      )}
      
      {evaluation && (
        <>
          <Divider style={{ margin: '24px 0' }} />
          <Title level={4}>评估结果</Title>
          {renderEvaluation()}
        </>
      )}
    </div>
  );
};

export default TestResultPanel; 