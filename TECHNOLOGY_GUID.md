# Prompt Lab 技术说明文档

本文档详细描述了Prompt Lab项目的技术架构、组件关系和实现方法，帮助开发者理解系统的工作原理和扩展方式。

## 1. 系统架构

Prompt Lab采用前后端分离的架构设计，主要分为以下几个部分：

### 1.1 后端架构

- **Web框架**：FastAPI，提供高性能的API服务
- **数据库**：SQLite，用于存储用户、模板、提示词等数据
- **ORM**：SQLAlchemy，提供对象关系映射
- **数据迁移**：Alembic，管理数据库版本和结构变更
- **认证**：JWT (JSON Web Token)，实现用户认证和授权
- **模型适配器**：提供与各种AI模型API的统一接口

### 1.2 前端架构

- **框架**：React，构建用户界面
- **UI库**：Ant Design，提供美观的UI组件
- **状态管理**：Zustand，管理应用状态
- **HTTP客户端**：Axios，处理API请求
- **Markdown编辑器**：@uiw/react-md-editor，提供Markdown编辑功能

### 1.3 系统交互流程

```
用户 -> 前端UI -> API请求 -> 后端服务 -> 数据库/AI模型API -> 响应 -> 前端UI -> 用户
```

## 2. 核心模块详解

### 2.1 用户认证模块

#### 2.1.1 实现方式

用户认证基于JWT实现，主要包含以下流程：

1. **用户登录**：
   - 前端通过`authApi.js`中的`login`函数发送用户名和密码
   - 后端`auth.py`中的`login_for_access_token`函数验证用户凭据
   - 验证成功后生成JWT令牌并返回给前端

2. **令牌验证**：
   - 前端将JWT存储在本地，并在每次请求中通过Authorization头部发送
   - 后端使用`get_current_user`依赖函数验证令牌并获取当前用户

3. **权限控制**：
   - 前端使用`ProtectedRoute.js`组件保护需要登录的路由
   - 后端API端点使用`get_current_user`依赖确保只有已登录用户可以访问

#### 2.1.2 关键代码

**后端认证实现**：
```python
# app/routers/auth.py
@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(hours=JWT_EXPIRE_HOURS)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

**前端认证实现**：
```javascript
// src/services/authApi.js
export const login = async (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await axios.post('/api/v1/auth/token', formData);
  return response.data;
};
```

### 2.2 提示词模板管理模块

#### 2.2.1 数据模型

提示词模板使用`PromptTemplate`模型存储：

```python
# app/models.py
class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    content = Column(Text, nullable=False)
    variables = Column(JSON, default={})
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
```

#### 2.2.2 功能实现

1. **模板创建与编辑**：
   - 前端通过`TemplateEditor.js`组件提供模板编辑界面
   - 后端`templates.py`路由处理模板的CRUD操作

2. **模板变量识别**：
   - 系统会自动识别模板中的`{{变量名}}`格式的变量
   - 前端在使用模板时会提示用户填写这些变量

3. **模板组织**：
   - 模板可以按照类别和用途进行组织
   - 前端通过`TemplateTree.js`组件以树形结构展示模板

### 2.3 模型适配器模块

#### 2.3.1 设计思想

模型适配器采用适配器设计模式，为不同的AI模型API提供统一的接口，主要解决以下问题：

1. 不同AI模型API的调用方式和参数不同
2. 响应格式各异，需要统一处理
3. 认证方式和错误处理不同

#### 2.3.2 实现方式

`ModelAdapter`类是核心实现，主要包含以下部分：

1. **初始化与配置**：
   ```python
   def __init__(self, provider: str, api_key: str, base_url: str = ""):
       self.provider = provider
       self.api_key = api_key.strip() if api_key else ""
       self.base_url = base_url.strip() if base_url else ""
       self._validate_api_key()
   ```

2. **统一接口**：
   ```python
   def send_prompt(self, prompt: str, variables: dict = None):
       # 替换变量
       if variables:
           for var_name, var_value in variables.items():
               prompt = prompt.replace("{{" + var_name + "}}", str(var_value))

       # 根据提供商选择适当的调用方法
       if self.provider == "openai":
           return self._call_openai(prompt, variables)
       elif self.provider == "anthropic":
           return self._call_anthropic(prompt, variables)
       # ... 其他模型
   ```

3. **模型特定实现**：
   为每个支持的模型提供特定的调用方法，如：
   ```python
   def _call_openai(self, prompt, variables):
       # OpenAI特定的API调用实现
   ```

#### 2.3.3 支持的模型

目前适配器支持以下AI模型：

- OpenAI (GPT系列)
- Anthropic (Claude系列)
- ModelScope (通义千问等)
- 文心一言
- 讯飞星火
- ChatGLM
- 智谱AI
- DeepSeek

### 2.4 提示词优化模块

#### 2.4.1 工作原理

提示词优化模块使用AI模型自身的能力来优化提示词，主要流程：

1. 用户提供初始提示词和优化目标
2. 用户选择优化类型（通用优化、函数调用优化或图像生成优化）
3. 系统使用特定的元提示词(meta-prompt)指导AI模型分析和优化原始提示词
4. AI模型生成优化建议和改进版提示词
5. 用户可以比较原始和优化后的提示词效果

#### 2.4.2 优化类型

系统支持三种不同类型的提示词优化：

1. **通用优化**：适用于一般场景的提示词优化，注重清晰度、完整性和有效性
2. **函数调用优化**：专注于优化Function Calling场景的提示词，包含以下预定义要求：
   - 确保函数调用指令清晰明确
   - 参数说明详细准确
   - 返回值格式规范
   - 错误处理机制完善
   - 示例调用清晰易懂
3. **图像生成优化**：专注于优化图像生成场景的提示词，包含以下预定义要求：
   - 视觉元素描述详细具体
   - 艺术风格明确清晰
   - 构图和色彩指导准确
   - 技术参数设置合理
   - 避免模糊和歧义表达
   - 增强视觉冲击力

用户可以通过前端界面选择优化类型，系统会根据选择调用不同的API端点，并应用相应的预定义要求。用户输入的自定义要求会与预定义要求合并，共同指导优化过程。

#### 2.4.3 结果格式保障机制

系统实现了严格的结果格式保障机制，确保优化后返回的是正确的提示词文本而非评估结果：

1. **明确的指令提示**：在构建优化提示词时，系统明确指示模型返回优化后的提示词文本，并禁止返回评估结果。

2. **结果格式检测**：系统会检查返回内容是否为JSON格式的评估结果，如果检测到不符合预期的格式，会自动重新发送请求。

3. **自动重试机制**：当检测到返回格式不正确时，系统会添加强化指令并重新发送请求，确保获得正确格式的优化提示词。

这些机制共同确保了无论是通用优化、函数调用优化还是图像生成优化，系统都能返回正确格式的优化后提示词，提高了系统的稳定性和用户体验。

#### 2.4.4 实现方式

核心实现在`prompt_optimizer.py`服务中：

```python
def optimize_prompt(self, prompt: str, target: str, model_adapter: ModelAdapter) -> dict:
    """
    优化提示词
    
    Args:
        prompt: 原始提示词
        target: 优化目标
        model_adapter: 模型适配器
        
    Returns:
        包含优化结果的字典
    """
    # 构建元提示词
    meta_prompt = f"""作为一个提示词优化专家，请帮我优化以下提示词，使其更好地达成目标。

原始提示词:
{prompt}

优化目标:
{target}

请提供以下内容:
1. 对原始提示词的分析
2. 优化建议
3. 优化后的完整提示词

请确保优化后的提示词更清晰、更具体、更有效。
"""
    
    # 调用AI模型
    result = model_adapter.send_prompt(meta_prompt)
    
    # 解析响应
    # ...
    
    return {
        "original_prompt": prompt,
        "optimized_prompt": optimized_prompt,
        "analysis": analysis,
        "suggestions": suggestions
    }
```

前端通过`PromptOptimizer.js`组件提供用户界面，允许用户选择优化类型并查看预定义要求：

```javascript
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
```

根据用户选择的优化类型，前端会调用相应的API函数：

```javascript
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
```

### 2.5 响应评估模块

#### 2.5.1 评估指标

系统对AI模型的响应进行多维度评估：

1. **相关性**：响应与提示词的相关程度
2. **完整性**：响应是否完整回答了提示词中的问题
3. **准确性**：响应中的信息是否准确
4. **清晰度**：响应的表达是否清晰易懂
5. **创新性**：响应是否提供了新颖的见解或解决方案

#### 2.5.2 实现方式

评估可以通过两种方式实现：

1. **基于规则的评估**：使用预定义规则和启发式方法
2. **基于AI的评估**：使用另一个AI模型评估响应质量

核心实现在`response_evaluator.py`服务中：

```python
def evaluate_with_ai(self, prompt: str, response: str, model_adapter: ModelAdapter) -> Dict[str, Any]:
    """
    使用AI模型评估响应质量
    
    Args:
        prompt: 原始提示词
        response: 模型响应
        model_adapter: 用于评估的模型适配器
        
    Returns:
        包含评估结果的字典
    """
    evaluation_prompt = f"""作为一个AI响应质量评估专家，请评估以下AI响应的质量。

原始提示词:
{prompt}

AI响应:
{response}

请按照以下维度评估，给出1-10的分数和简短理由:
1. 相关性: 响应与提示词的相关程度
2. 完整性: 响应是否完整回答了提示词中的问题
3. 准确性: 响应中的信息是否准确
4. 清晰度: 响应的表达是否清晰易懂
5. 创新性: 响应是否提供了新颖的见解或解决方案

请以JSON格式返回评估结果，格式如下:
{{
  "scores": {{
    "relevance": 分数,
    "completeness": 分数,
    "accuracy": 分数,
    "clarity": 分数,
    "innovation": 分数,
    "overall": 总分
  }},
  "reasons": {{
    "relevance": "理由",
    "completeness": "理由",
    "accuracy": "理由",
    "clarity": "理由",
    "innovation": "理由"
  }},
  "suggestions": ["改进建议1", "改进建议2", ...]
}}
"""
    
    # 调用AI模型进行评估
    result = model_adapter.send_prompt(evaluation_prompt)
    
    # 解析JSON响应
    # ...
    
    return evaluation_result
```

### 2.6 WebSocket实时通信

#### 2.6.1 用途

WebSocket用于实现以下功能：

1. 实时推送模板更新通知
2. 长时间运行的任务进度通知
3. 协作编辑时的实时同步

#### 2.6.2 实现方式

后端使用FastAPI的WebSocket支持：

```python
# app/websocket.py
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
```

前端使用原生WebSocket API：

```javascript
// 在组件中初始化WebSocket连接
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws/templates');
  
  ws.onopen = () => {
    console.log('WebSocket连接已建立');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // 处理接收到的消息
    if (data.type === 'template_updated') {
      // 刷新模板列表
      loadTemplates();
    }
  };
  
  ws.onclose = () => {
    console.log('WebSocket连接已关闭');
  };
  
  return () => {
    ws.close();
  };
}, []);
```

## 3. 数据流与交互逻辑

### 3.1 提示词测试流程

1. **用户选择模板**：
   - 用户从`TemplateList.js`中选择一个模板
   - 前端加载模板详情和变量定义

2. **填写变量**：
   - 用户在`PromptEditor.js`中填写模板变量
   - 系统实时预览完整提示词

3. **选择模型**：
   - 用户从`ModelManagerModal.js`中选择要使用的AI模型
   - 前端加载模型配置

4. **发送请求**：
   - 用户点击测试按钮
   - 前端通过API发送提示词和模型信息
   - 后端`test.py`路由处理请求，调用适当的模型适配器

5. **处理响应**：
   - 后端接收AI模型的响应，记录到数据库
   - 前端在`ResponsePanel.js`中显示响应结果

6. **评估结果**：
   - 系统对响应进行评估
   - 前端显示评估结果和改进建议

### 3.2 提示词优化流程

1. **初始设置**：
   - 用户在`PromptOptimizer.js`中输入原始提示词和优化目标
   - 前端验证输入

2. **优化请求**：
   - 用户点击优化按钮
   - 前端通过API发送优化请求
   - 后端`prompt_optimize.py`路由处理请求

3. **优化过程**：
   - 后端构建元提示词
   - 调用AI模型进行优化
   - 解析AI模型的响应

4. **结果展示**：
   - 前端显示原始提示词和优化后的提示词对比
   - 显示分析和优化建议

5. **应用优化**：
   - 用户可以选择接受优化结果
   - 系统将优化后的提示词保存为新版本

### 3.3 用户管理流程

1. **用户注册**：
   - 新用户通过注册表单提交信息
   - 后端验证信息并创建用户账户
   - 系统发送确认邮件

2. **用户登录**：
   - 用户提交登录凭据
   - 后端验证凭据并生成JWT令牌
   - 前端存储令牌并重定向到主页

3. **用户权限**：
   - 系统根据用户角色控制功能访问
   - 管理员可以管理所有用户和内容
   - 普通用户只能访问自己的内容

## 4. 扩展与定制

### 4.1 添加新的AI模型

要添加新的AI模型支持，需要以下步骤：

1. 在`model_adapter.py`中添加新的调用方法：
   ```python
   def _call_new_model(self, prompt, variables):
       # 实现新模型的API调用
       # ...
       return {"model": "new_model", "output": response_content}
   ```

2. 在`send_prompt`方法中添加条件分支：
   ```python
   def send_prompt(self, prompt: str, variables: dict = None):
       # ...
       elif self.provider == "new_model":
           return self._call_new_model(prompt, variables)
       # ...
   ```

3. 在`get_model_types`方法中添加新模型类型：
   ```python
   @classmethod
   def get_model_types(cls):
       return [
           'openai', 'anthropic', 'deepseek', 'qwen', 'doubao', 
           'chatglm', 'zhipu', 'wenxin', 'spark', 'modelscope', 'new_model', 'local'
       ]
   ```

### 4.2 自定义评估指标

要添加新的评估指标，需要修改`response_evaluator.py`：

1. 在`evaluate`方法中添加新指标：
   ```python
   def evaluate(self, response: str) -> Dict[str, Any]:
       # ...
       evaluation = {
           # 现有指标
           "length": len(response),
           "word_count": len(response.split()),
           "has_content": bool(response.strip()),
           "quality_score": self._calculate_quality_score(response),
           # 新增指标
           "new_metric": self._calculate_new_metric(response)
       }
       # ...
   ```

2. 添加计算新指标的方法：
   ```python
   def _calculate_new_metric(self, response: str) -> float:
       # 实现新指标的计算逻辑
       # ...
       return score
   ```

3. 更新前端显示，在`TestResultPanel.js`中添加新指标的展示。

### 4.3 自定义UI主题

前端使用Ant Design，可以通过以下方式自定义主题：

1. 在`src/App.js`中配置主题：
   ```javascript
   import { ConfigProvider } from 'antd';

   function App() {
     return (
       <ConfigProvider
         theme={{
           token: {
             colorPrimary: '#00b96b',
             borderRadius: 6,
           },
         }}
       >
         {/* 应用内容 */}
       </ConfigProvider>
     );
   }
   ```

2. 创建自定义样式文件覆盖默认样式。

## 5. 部署指南

### 5.1 开发环境

开发环境使用以下配置：

1. **后端**：
   - 使用uvicorn开发服务器
   - 启用自动重载
   - 详细日志输出

2. **前端**：
   - 使用React开发服务器
   - 启用热模块替换
   - 代理API请求到后端

### 5.2 生产环境

生产环境部署建议：

1. **后端**：
   - 使用Gunicorn作为WSGI服务器
   - 使用Nginx作为反向代理
   - 关闭调试模式和详细日志

2. **前端**：
   - 构建静态文件
   - 使用Nginx提供静态文件服务
   - 配置适当的缓存策略

3. **数据库**：
   - 考虑使用PostgreSQL替代SQLite
   - 配置定期备份

4. **安全**：
   - 使用HTTPS
   - 配置适当的CORS策略
   - 使用环境变量存储敏感信息

### 5.3 Docker部署

提供Docker部署支持：

1. **Dockerfile**：构建应用容器
2. **docker-compose.yml**：编排多容器应用
3. **环境配置**：使用Docker环境变量

## 6. 性能优化

### 6.1 后端优化

1. **异步处理**：
   - 使用FastAPI的异步功能处理并发请求
   - 使用后台任务处理长时间运行的操作

2. **缓存**：
   - 缓存频繁访问的数据
   - 使用Redis作为缓存存储

3. **数据库优化**：
   - 创建适当的索引
   - 优化查询语句
   - 分页加载大量数据

### 6.2 前端优化

1. **代码分割**：
   - 使用React.lazy进行组件懒加载
   - 按路由分割代码

2. **资源优化**：
   - 压缩静态资源
   - 使用CDN加载第三方库

3. **渲染优化**：
   - 使用React.memo避免不必要的重渲染
   - 使用虚拟列表处理大量数据

## 7. 测试策略

### 7.1 后端测试

1. **单元测试**：
   - 测试各个服务和函数的独立功能
   - 使用pytest框架

2. **集成测试**：
   - 测试API端点
   - 使用TestClient模拟HTTP请求

3. **数据库测试**：
   - 使用测试数据库
   - 测试数据库操作和迁移

### 7.2 前端测试

1. **组件测试**：
   - 测试UI组件的渲染和交互
   - 使用React Testing Library

2. **集成测试**：
   - 测试组件之间的交互
   - 模拟API请求

3. **端到端测试**：
   - 测试完整的用户流程
   - 使用Cypress或Playwright

## 8. 故障排除

### 8.1 常见问题

1. **API连接问题**：
   - 检查API密钥是否有效
   - 验证网络连接
   - 查看API提供商状态

2. **数据库错误**：
   - 检查数据库连接
   - 验证数据库迁移是否完成
   - 检查SQL语法

3. **前端渲染问题**：
   - 检查控制台错误
   - 验证API响应格式
   - 检查组件props

### 8.2 日志和监控

1. **日志配置**：
   - 使用结构化日志
   - 配置适当的日志级别
   - 记录关键操作和错误

2. **监控**：
   - 监控API性能和错误率
   - 监控数据库性能
   - 监控用户活动

## 9. 未来规划

### 9.1 功能增强

1. **多语言支持**：
   - 添加国际化支持
   - 支持多语言提示词和响应

2. **高级分析**：
   - 提供提示词效果的统计分析
   - 可视化响应质量趋势

3. **协作功能**：
   - 团队共享和协作编辑
   - 评论和反馈系统

### 9.2 技术改进

1. **GraphQL API**：
   - 考虑使用GraphQL替代REST API
   - 减少过度获取和请求数量

2. **实时协作**：
   - 增强WebSocket功能
   - 实现文档协作编辑

3. **机器学习增强**：
   - 自动提示词分类
   - 智能提示词推荐系统 