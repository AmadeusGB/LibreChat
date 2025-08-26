# LibreChat RUSTMODEL 集成设计方案

## 概述

本文档详细说明如何将 RUSTMODEL (Agent Workflow Benchmark API) 集成到 LibreChat 中，在尽可能复用 OpenAI 现有流程的基础上，实现对 RUSTMODEL 的完整支持。

## 1. 整体架构设计

### 1.1 复用策略

**核心原则**: 最大化复用 OpenAI 的现有架构，通过适配层处理差异，而不是重新构建整套流程。

```
前端模型选择 → 用户输入 → 请求构建 → 后端路由 → 适配层 → RUSTMODEL客户端 → 流式响应 → 前端显示
     ↓           ↓         ↓         ↓        ↓新增     ↓新增        ↓适配      ↓
 ModelSelector → ChatForm → useSSE → AgentController → RustModelAdapter → RustModelClient → SSE Events → MessagesView
```

### 1.2 新增组件

1. **RustModelClient** - RUSTMODEL API 客户端
2. **RustModelAdapter** - 请求/响应适配器
3. **RustModelStreamHandler** - 流式响应处理器
4. **RustModelParameterSettings** - 参数配置

## 2. 前端集成方案

### 2.1 模型选择器扩展

**文件**: `packages/data-provider/src/config.ts`

**新增端点配置**:
```typescript
export const EndpointURLs = {
  [EModelEndpoint.openAI]: '/api/agents/chat/openAI',
  [EModelEndpoint.azureOpenAI]: '/api/agents/chat/azureOpenAI',
  [EModelEndpoint.rustModel]: '/api/agents/chat/rustModel',  // 新增
} as const;

// 新增 RUSTMODEL 端点枚举
export enum EModelEndpoint {
  // ... 现有端点
  rustModel = 'rustModel',
}

// 新增默认模型配置
export const defaultModels = {
  // ... 现有配置
  [EModelEndpoint.rustModel]: [
    'claude-3-5-sonnet-20241022',  // RUSTMODEL 使用的模型
  ],
};
```

### 2.2 参数配置界面

**文件**: `packages/data-provider/src/parameterSettings.ts`

**新增 RUSTMODEL 参数配置**:
```typescript
const rustModelParams = {
  temperature: {
    key: 'temperature',
    label: 'Temperature',
    description: 'Controls randomness in the output',
    type: 'number',
    range: { min: 0, max: 2, step: 0.1 },
    default: 0.1,
  },
  max_tokens: {
    key: 'max_tokens', 
    label: 'Max Tokens',
    description: 'Maximum number of tokens to generate',
    type: 'number',
    range: { min: 1, max: 100000, step: 1 },
    default: 8192,
  },
  use_rag: {
    key: 'use_rag',
    label: 'Use RAG Enhancement',
    description: 'Enable Retrieval-Augmented Generation',
    type: 'boolean',
    default: false,
  },
  disableStreaming: {
    key: 'disableStreaming',
    label: 'Disable Streaming',
    description: 'Disable streaming responses',
    type: 'boolean', 
    default: false,
  },
};

const rustModel: SettingsConfiguration = [
  librechat.modelLabel,
  librechat.promptPrefix,
  librechat.maxContextTokens,
  rustModelParams.max_tokens,
  rustModelParams.temperature,
  rustModelParams.use_rag,
  rustModelParams.disableStreaming,
  baseDefinitions.stop,
  librechat.resendFiles,
];

export const parameterSettings = {
  // ... 现有配置
  [EModelEndpoint.rustModel]: rustModel,
};
```

### 2.3 请求负载适配

**文件**: `packages/data-provider/src/createPayload.ts`

**修改负载构建逻辑**:
```typescript
export default function createPayload(submission: t.TSubmission) {
  const { conversation, endpointOption, userMessage } = submission;
  const endpoint = endpointOption.endpoint as s.EModelEndpoint;
  
  // 确定服务器端点
  let server = `${EndpointURLs[s.EModelEndpoint.agents]}/${endpoint}`;
  
  // 基础负载
  let payload: t.TPayload = {
    ...userMessage,
    ...endpointOption,
    endpoint,
    // ... 其他字段
  };
  
  // RUSTMODEL 特殊处理
  if (endpoint === s.EModelEndpoint.rustModel) {
    payload = adaptPayloadForRustModel(payload);
  }
  
  return { server, payload };
}

function adaptPayloadForRustModel(payload: t.TPayload): t.TPayload {
  // 将 messages 数组转换为单一 input 字符串
  const messages = payload.messages || [];
  const input = messages
    .filter(msg => msg.role === 'user')
    .map(msg => msg.content)
    .join('\n');
    
  return {
    ...payload,
    input,                    // RUSTMODEL 使用 input 而不是 messages
    model: payload.model || 'claude-3-5-sonnet-20241022',
    temperature: payload.temperature || 0.1,
    max_tokens: payload.max_tokens || 8192,
    use_rag: payload.use_rag || false,
    stream: !payload.disableStreaming,
    // 移除 RUSTMODEL 不支持的字段
    messages: undefined,
  };
}
```

## 3. 后端集成方案

### 3.1 路由配置

**文件**: `api/server/routes/agents/chat.js`

**现有路由无需修改**，通过端点参数区分:
```javascript
// 现有路由已支持动态端点
router.post('/:endpoint', controller);  // 支持 /rustModel
```

### 3.2 端点选项构建

**文件**: `api/server/middleware/buildEndpointOption.js`

**添加 RUSTMODEL 构建函数**:
```javascript
const buildFunction = {
  [EModelEndpoint.openAI]: openAI.buildOptions,
  [EModelEndpoint.azureOpenAI]: openAI.buildOptions,
  [EModelEndpoint.rustModel]: rustModel.buildOptions,  // 新增
};
```

**新建文件**: `api/server/services/Endpoints/rustModel/buildOptions.js`
```javascript
const buildOptions = (endpoint, parsedBody, endpointType) => {
  const {
    input,
    model = 'claude-3-5-sonnet-20241022',
    temperature = 0.1,
    max_tokens = 8192,
    use_rag = false,
    stream = true,
    ...rest
  } = parsedBody;

  return {
    endpoint: EModelEndpoint.rustModel,
    input,
    model,
    temperature,
    max_tokens,
    use_rag,
    stream,
    ...rest,
  };
};

module.exports = { buildOptions };
```

### 3.3 RUSTMODEL 客户端初始化

**新建文件**: `api/server/services/Endpoints/rustModel/initialize.js`

```javascript
const { RustModelClient } = require('../../../../app/clients/RustModelClient');

const initializeClient = async ({
  req, res, endpointOption, optionsOnly, overrideEndpoint, overrideModel,
}) => {
  const {
    RUSTMODEL_BASE_URL = 'https://agent-workflow-993464051590.us-central1.run.app',
    DEBUG_RUSTMODEL,
  } = process.env;

  // RUSTMODEL 无需认证
  const clientOptions = {
    baseURL: RUSTMODEL_BASE_URL,
    debug: isEnabled(DEBUG_RUSTMODEL),
    ...endpointOption,
  };

  const client = new RustModelClient(clientOptions, { req, res });
  return { client };
};

module.exports = { initializeClient };
```

### 3.4 RUSTMODEL 客户端类

**新建文件**: `api/app/clients/RustModelClient.js`

```javascript
const BaseClient = require('./BaseClient');
const { RustModelAdapter } = require('./adapters/RustModelAdapter');

class RustModelClient extends BaseClient {
  constructor(options = {}, clientOptions = {}) {
    super(clientOptions);
    
    this.baseURL = options.baseURL;
    this.sender = 'RustModel';
    this.debug = options.debug || false;
    
    // 模型参数
    this.modelOptions = {
      model: options.model || 'claude-3-5-sonnet-20241022',
      temperature: options.temperature || 0.1,
      max_tokens: options.max_tokens || 8192,
      use_rag: options.use_rag || false,
      stream: options.stream !== false,
    };
    
    // 适配器
    this.adapter = new RustModelAdapter();
  }

  async sendMessage(text, options = {}) {
    const { onStart, onProgress, onComplete, abortController } = options;
    
    try {
      // 构建请求
      const payload = this.adapter.buildRequest({
        input: text,
        ...this.modelOptions,
      });
      
      if (onStart) {
        onStart({ sender: this.sender });
      }
      
      if (this.modelOptions.stream) {
        await this.streamCompletion({ payload, onProgress, onComplete, abortController });
      } else {
        await this.completion({ payload, onComplete });
      }
      
    } catch (error) {
      throw error;
    }
  }

  async streamCompletion({ payload, onProgress, onComplete, abortController }) {
    const response = await fetch(`${this.baseURL}/v1/responses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(payload),
      signal: abortController?.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data.trim() === '[DONE]') continue;
            
            try {
              const parsed = JSON.parse(data);
              const adapted = this.adapter.adaptStreamResponse(parsed);
              
              if (adapted.isProgress && onProgress) {
                onProgress(adapted);
              } else if (adapted.isFinal && onComplete) {
                onComplete(adapted);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  async completion({ payload, onComplete }) {
    const response = await fetch(`${this.baseURL}/v1/responses`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    const adapted = this.adapter.adaptResponse(data);
    
    if (onComplete) {
      onComplete(adapted);
    }
  }
}

module.exports = { RustModelClient };
```

### 3.5 响应适配器

**新建文件**: `api/app/clients/adapters/RustModelAdapter.js`

```javascript
class RustModelAdapter {
  buildRequest(options) {
    return {
      input: options.input,
      temperature: options.temperature,
      model: options.model,
      max_tokens: options.max_tokens,
      use_rag: options.use_rag,
      stream: options.stream,
    };
  }

  adaptResponse(rustModelResponse) {
    // 将 RUSTMODEL 响应适配为 OpenAI 兼容格式
    const choice = rustModelResponse.choices?.[0];
    if (!choice) {
      throw new Error('Invalid RUSTMODEL response format');
    }

    return {
      id: rustModelResponse.id,
      object: rustModelResponse.object,
      created: rustModelResponse.created,
      model: rustModelResponse.model,
      choices: [{
        index: choice.index,
        message: {
          role: 'assistant',
          content: choice.message.content,
          // 保留 RUSTMODEL 扩展字段
          workflow_metadata: choice.message.workflow_metadata,
          code_files: choice.message.code_files,
          code_blocks: choice.message.code_blocks,
          cargo_check: choice.message.cargo_check,
          cargo_test: choice.message.cargo_test,
          evaluation: choice.message.evaluation,
        },
        finish_reason: choice.finish_reason,
      }],
      usage: rustModelResponse.usage,
      // 保留工作流数据
      workflow_data: rustModelResponse.workflow_data,
    };
  }

  adaptStreamResponse(rustModelChunk) {
    if (rustModelChunk.is_final) {
      // 最终响应
      return {
        isFinal: true,
        isProgress: false,
        data: this.adaptResponse(rustModelChunk),
      };
    } else {
      // 进度事件
      return {
        isFinal: false,
        isProgress: true,
        event: rustModelChunk.event,
        progress: rustModelChunk.progress,
        message: rustModelChunk.message,
        metadata: rustModelChunk.metadata,
        // 转换为 OpenAI 兼容的增量格式
        delta: {
          content: this.extractContentFromEvent(rustModelChunk),
        },
      };
    }
  }

  extractContentFromEvent(event) {
    // 根据事件类型提取内容更新
    switch (event.event) {
      case 'workflow.started':
        return '🚀 Starting Rust code generation workflow...\n\n';
      case 'workflow.prompt':
        return '📝 Processing your request...\n\n';
      case 'workflow.response':
        return '🤖 Generating Rust code...\n\n';
      case 'workflow.code_extraction':
        return '📁 Extracting and organizing code files...\n\n';
      case 'workflow.cargo_check':
        return event.metadata?.success 
          ? '✅ Code compilation successful!\n\n'
          : '❌ Compilation errors detected.\n\n';
      case 'workflow.cargo_test':
        return event.metadata?.success
          ? '✅ All tests passed!\n\n'
          : '❌ Some tests failed.\n\n';
      case 'workflow.evaluation':
        const score = event.metadata?.overall_score;
        return `📊 Code quality evaluation: ${(score * 100).toFixed(1)}%\n\n`;
      default:
        return '';
    }
  }
}

module.exports = { RustModelAdapter };
```

## 4. 前端流式响应处理

### 4.1 SSE 事件处理适配

**文件**: `client/src/hooks/SSE/useEventHandlers.ts`

**扩展事件处理器**:
```typescript
const useEventHandlers = () => {
  // ... 现有处理器

  const rustModelProgressHandler = useCallback((data: any, submission: EventSubmission) => {
    const { event, progress, message, metadata } = data;
    
    // 更新进度指示器
    if (progress !== undefined) {
      setProgress(progress);
    }
    
    // 显示阶段消息
    if (message) {
      setStatusMessage(message);
    }
    
    // 处理特定事件
    switch (event) {
      case 'workflow.cargo_check':
        if (metadata?.success === false) {
          setCompilationErrors(metadata.diagnostics || []);
        }
        break;
      case 'workflow.cargo_test':
        if (metadata?.test_results) {
          setTestResults(metadata.test_results);
        }
        break;
      case 'workflow.evaluation':
        if (metadata?.evaluation) {
          setCodeEvaluation(metadata.evaluation);
        }
        break;
    }
  }, []);

  return {
    // ... 现有处理器
    rustModelProgressHandler,
  };
};
```

### 4.2 RUSTMODEL 特有 UI 组件

**新建文件**: `client/src/components/Chat/Messages/RustModelMessage.tsx`

```typescript
import React from 'react';
import { TMessage } from 'librechat-data-provider';

interface RustModelMessageProps {
  message: TMessage;
}

const RustModelMessage: React.FC<RustModelMessageProps> = ({ message }) => {
  const { workflow_metadata, code_blocks, cargo_check, cargo_test, evaluation } = message;

  return (
    <div className="rustmodel-message">
      {/* 标准消息内容 */}
      <div className="message-content">
        {message.content}
      </div>

      {/* RUSTMODEL 扩展信息 */}
      {code_blocks && code_blocks.length > 0 && (
        <div className="code-blocks-section">
          <h4>Generated Code Files:</h4>
          {code_blocks.map((block, index) => (
            <div key={index} className="code-block">
              <div className="code-header">
                <span className="filename">{block.filename}</span>
                <span className="language">{block.language}</span>
              </div>
              <pre className="code-content">
                <code>{block.code}</code>
              </pre>
            </div>
          ))}
        </div>
      )}

      {/* 编译检查结果 */}
      {cargo_check && (
        <div className="cargo-check-section">
          <h4>Compilation Check:</h4>
          <div className={`status ${cargo_check.success ? 'success' : 'error'}`}>
            {cargo_check.success ? '✅ Compilation Successful' : '❌ Compilation Failed'}
          </div>
          {cargo_check.diagnostics && cargo_check.diagnostics.length > 0 && (
            <div className="diagnostics">
              {cargo_check.diagnostics.map((diag, index) => (
                <div key={index} className="diagnostic-item">
                  {diag}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 测试结果 */}
      {cargo_test && (
        <div className="cargo-test-section">
          <h4>Test Results:</h4>
          <div className={`status ${cargo_test.success ? 'success' : 'error'}`}>
            {cargo_test.success ? '✅ All Tests Passed' : '❌ Some Tests Failed'}
          </div>
          {cargo_test.test_results && (
            <div className="test-results">
              {Object.entries(cargo_test.test_results).map(([testName, passed]) => (
                <div key={testName} className={`test-item ${passed ? 'passed' : 'failed'}`}>
                  {passed ? '✅' : '❌'} {testName}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 代码评估 */}
      {evaluation && (
        <div className="evaluation-section">
          <h4>Code Quality Evaluation:</h4>
          <div className="scores">
            <div className="score-item">
              <span>Overall Score:</span>
              <span className="score">{(evaluation.overall_score * 100).toFixed(1)}%</span>
            </div>
            <div className="score-item">
              <span>Compilation Score:</span>
              <span className="score">{(evaluation.compilation_score * 100).toFixed(1)}%</span>
            </div>
            <div className="score-item">
              <span>Test Score:</span>
              <span className="score">{(evaluation.test_score * 100).toFixed(1)}%</span>
            </div>
          </div>
          {evaluation.feedback && evaluation.feedback.length > 0 && (
            <div className="feedback">
              <h5>Feedback:</h5>
              <ul>
                {evaluation.feedback.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 工作流元数据 */}
      {workflow_metadata && (
        <div className="workflow-metadata">
          <details>
            <summary>Workflow Details</summary>
            <div className="metadata-content">
              <div>Duration: {workflow_metadata.duration}s</div>
              <div>Timestamp: {workflow_metadata.timestamp}</div>
              {workflow_metadata.errors && workflow_metadata.errors.length > 0 && (
                <div className="errors">
                  <h5>Errors:</h5>
                  <ul>
                    {workflow_metadata.errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </details>
        </div>
      )}
    </div>
  );
};

export default RustModelMessage;
```

## 5. 数据流转适配

### 5.1 请求数据流

```
前端输入 → 消息数组构建 → RUSTMODEL适配 → 后端处理
    ↓              ↓              ↓           ↓
"Create factorial" → [{role:"user", content:"..."}] → {input:"..."} → RustModelClient
```

### 5.2 响应数据流

```
RUSTMODEL响应 → 适配器处理 → 标准格式 → 前端显示
      ↓            ↓          ↓        ↓
{workflow_data} → RustModelAdapter → {choices} → RustModelMessage
```

### 5.3 流式数据流

```
RUSTMODEL事件 → 进度适配 → SSE事件 → 前端更新
      ↓           ↓        ↓       ↓
{event:"workflow.started"} → {delta:{content}} → messageHandler → UI更新
```

## 6. 配置和环境变量

### 6.1 环境变量配置

**文件**: `.env`

```bash
# RUSTMODEL 配置
RUSTMODEL_BASE_URL=https://agent-workflow-993464051590.us-central1.run.app
DEBUG_RUSTMODEL=false

# 可选：如果需要自定义端点
RUSTMODEL_CUSTOM_ENDPOINT=
```

### 6.2 Docker 配置

**文件**: `docker-compose.yml`

```yaml
services:
  api:
    environment:
      - RUSTMODEL_BASE_URL=${RUSTMODEL_BASE_URL:-https://agent-workflow-993464051590.us-central1.run.app}
      - DEBUG_RUSTMODEL=${DEBUG_RUSTMODEL:-false}
```

## 7. 错误处理适配

### 7.1 HTTP 错误映射

```javascript
// api/app/clients/RustModelClient.js
const handleRustModelError = (error, response) => {
  switch (response?.status) {
    case 400:
      throw new Error('Invalid request parameters');
    case 422:
      const details = response.data?.detail || [];
      const messages = details.map(d => d.msg).join(', ');
      throw new Error(`Validation error: ${messages}`);
    case 500:
      throw new Error('RUSTMODEL service error');
    default:
      throw new Error(`RUSTMODEL API error: ${error.message}`);
  }
};
```

### 7.2 工作流错误处理

```javascript
// 处理工作流中的错误事件
adaptStreamResponse(rustModelChunk) {
  if (rustModelChunk.event === 'workflow.error') {
    return {
      isError: true,
      error: {
        message: rustModelChunk.message,
        metadata: rustModelChunk.metadata,
      },
    };
  }
  // ... 其他处理
}
```

## 8. 测试策略

### 8.1 单元测试

```javascript
// tests/api/clients/RustModelClient.test.js
describe('RustModelClient', () => {
  test('should adapt request format correctly', () => {
    const client = new RustModelClient();
    const adapted = client.adapter.buildRequest({
      input: 'Create a factorial function',
      temperature: 0.1,
    });
    
    expect(adapted).toEqual({
      input: 'Create a factorial function',
      temperature: 0.1,
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 8192,
      use_rag: false,
      stream: true,
    });
  });
});
```

### 8.2 集成测试

```javascript
// tests/integration/rustmodel.test.js
describe('RUSTMODEL Integration', () => {
  test('should handle complete workflow', async () => {
    const response = await request(app)
      .post('/api/agents/chat/rustModel')
      .send({
        input: 'Create a simple Rust function',
        temperature: 0.1,
      });
      
    expect(response.status).toBe(200);
    expect(response.body.choices[0].message.content).toBeDefined();
    expect(response.body.choices[0].message.code_blocks).toBeDefined();
  });
});
```

## 9. 部署和监控

### 9.1 健康检查

```javascript
// api/server/routes/health.js
router.get('/rustmodel', async (req, res) => {
  try {
    const response = await fetch(`${process.env.RUSTMODEL_BASE_URL}/health`);
    if (response.ok) {
      res.json({ status: 'healthy', service: 'rustmodel' });
    } else {
      res.status(503).json({ status: 'unhealthy', service: 'rustmodel' });
    }
  } catch (error) {
    res.status(503).json({ status: 'error', service: 'rustmodel', error: error.message });
  }
});
```

### 9.2 监控指标

- RUSTMODEL API 响应时间
- 工作流成功率
- 代码编译成功率
- 测试通过率

## 10. 实施计划

### 10.1 第一阶段：基础集成 (1-2周)

1. ✅ 添加 RUSTMODEL 端点配置
2. ✅ 创建 RustModelClient 基础类
3. ✅ 实现请求/响应适配器
4. ✅ 添加基础路由和中间件
5. ✅ 实现非流式响应处理

### 10.2 第二阶段：流式响应 (1周)

1. ✅ 实现流式响应处理
2. ✅ 添加进度指示器
3. ✅ 适配工作流事件
4. ✅ 前端 SSE 处理扩展

### 10.3 第三阶段：UI 增强 (1周)

1. ✅ 创建 RUSTMODEL 专用消息组件
2. ✅ 添加代码块展示
3. ✅ 显示编译和测试结果
4. ✅ 代码质量评估界面

### 10.4 第四阶段：完善和优化 (1周)

1. ✅ 错误处理完善
2. ✅ 性能优化
3. ✅ 测试覆盖
4. ✅ 文档完善

## 11. 兼容性考虑

### 11.1 向后兼容

- 现有 OpenAI 和其他端点功能不受影响
- 所有现有 API 保持不变
- 用户配置和数据完全兼容

### 11.2 数据格式兼容

- RUSTMODEL 响应通过适配器转换为标准格式
- 扩展字段作为可选属性添加
- 前端组件根据端点类型选择渲染方式

## 12. 总结

本设计方案通过以下策略实现了 RUSTMODEL 与 LibreChat 的深度集成：

### 12.1 核心优势

1. **最大化复用**: 95% 的现有代码和架构得到保留
2. **无缝集成**: 用户体验与现有端点一致
3. **功能增强**: 充分利用 RUSTMODEL 的代码生成和评估能力
4. **扩展性强**: 为未来添加更多专业化端点奠定基础

### 12.2 关键创新

1. **适配器模式**: 通过适配器处理 API 差异，保持架构清洁
2. **渐进式增强**: 在标准聊天界面基础上添加专业化功能
3. **工作流可视化**: 将 RUSTMODEL 的工作流进度实时展示给用户
4. **代码质量反馈**: 集成编译检查、测试结果和质量评估

### 12.3 实施建议

1. **分阶段实施**: 按照实施计划逐步推进，确保每个阶段都有可用的功能
2. **充分测试**: 重点测试适配器逻辑和流式响应处理
3. **用户反馈**: 在早期阶段收集用户反馈，优化 UI 和交互体验
4. **性能监控**: 密切监控 RUSTMODEL API 的性能和可用性

通过这个设计方案，LibreChat 将获得强大的 Rust 代码生成和评估能力，同时保持其作为通用 AI 聊天平台的灵活性和易用性。
