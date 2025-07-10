# HAJIMI Gemini API Proxy - AI协作说明文档

## 项目概述

HAJIMI是一个基于FastAPI构建的Gemini API代理服务，旨在提供简单、安全且可配置的方式来访问Google的Gemini模型。项目支持OpenAI API格式兼容，便于集成各种AI工具和服务。

### 核心特性
- 🔑 API密钥轮询和管理
- 📑 模型列表接口
- 💬 聊天补全接口（流式/非流式）
- 🔒 密码保护机制
- 🧩 OpenAI API格式兼容
- ⚡ 并发与缓存优化
- 🎭 假流式传输
- 🌐 联网搜索模式
- 🚦 速率限制和防滥用

## 项目架构

### 目录结构
```
haibao_Agent/
├── app/                    # 主应用目录
│   ├── main.py            # FastAPI应用入口
│   ├── api/               # API路由层
│   │   ├── routes.py      # 主要路由定义
│   │   ├── stream_handlers.py    # 流式请求处理
│   │   ├── nonstream_handlers.py # 非流式请求处理
│   │   └── dashboard.py   # 仪表盘API
│   ├── config/            # 配置管理
│   │   ├── settings.py    # 主配置文件
│   │   ├── persistence.py # 持久化配置
│   │   └── safety.py      # 安全设置
│   ├── services/          # 服务层
│   │   ├── gemini.py      # Gemini API客户端
│   │   └── OpenAI.py      # OpenAI兼容服务
│   ├── utils/             # 工具模块
│   │   ├── api_key.py     # API密钥管理
│   │   ├── auth.py        # 认证工具
│   │   ├── cache.py       # 缓存管理
│   │   ├── rate_limiting.py # 速率限制
│   │   └── response.py    # 响应处理
│   ├── vertex/            # Vertex AI集成
│   └── templates/         # 前端模板
├── hajimiUI/              # Vue.js前端界面
└── wiki/                  # 文档目录
```

### 核心组件

#### 1. API密钥管理 (`app/utils/api_key.py`)
- **APIKeyManager类**: 负载均衡的密钥管理
- **密钥栈机制**: 随机排序避免单点压力
- **异步安全**: 使用asyncio.Lock确保并发安全
- **密钥验证**: 自动检测和移除无效密钥

#### 2. Gemini服务客户端 (`app/services/gemini.py`)
- **GeminiClient类**: 核心API交互客户端
- **请求转换**: OpenAI格式到Gemini格式的转换
- **流式/非流式**: 支持两种响应模式
- **函数调用**: 支持工具和函数调用
- **响应包装**: GeminiResponseWrapper统一响应处理

#### 3. 路由系统 (`app/api/routes.py`)
- **多端点支持**: `/v1/chat/completions`, `/aistudio/`, `/vertex/`
- **缓存机制**: 智能缓存避免重复请求
- **并发控制**: 活跃请求池管理
- **错误处理**: 统一异常处理机制

#### 4. 配置管理 (`app/config/settings.py`)
- **环境变量**: 支持环境变量配置
- **持久化**: 配置持久化存储
- **动态更新**: 运行时配置更新
- **安全设置**: 内容安全和速率限制

## AI协作指南

### 开发环境设置

#### 1. 环境准备
```bash
# Python 3.12+
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 2. 配置文件
创建 `.env` 文件：
```env
GEMINI_API_KEYS=AIzaSy...  # 你的Gemini API密钥
PASSWORD=your_password     # 访问密码
FAKE_STREAMING=true        # 启用假流式
CONCURRENT_REQUESTS=1      # 并发请求数
```

#### 3. 启动服务
```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
python -m app.main
```

### 代码协作规范

#### 1. 代码结构原则
- **单一职责**: 每个模块专注单一功能
- **依赖注入**: 通过init_router等函数注入依赖
- **异步优先**: 所有IO操作使用async/await
- **错误处理**: 统一异常处理和日志记录

#### 2. 关键设计模式

##### 管理器模式
```python
# API密钥管理器
class APIKeyManager:
    async def get_available_key(self):
        # 负载均衡获取密钥
        
# 缓存管理器  
class ResponseCacheManager:
    async def get_and_remove(self, key):
        # 获取并移除缓存
```

##### 包装器模式
```python
class GeminiResponseWrapper:
    def __init__(self, data):
        # 统一响应格式包装
```

##### 工厂模式
```python
def init_router(dependencies...):
    # 路由器工厂函数
```

#### 3. 异步编程最佳实践

##### 并发控制
```python
# 活跃请求池管理
active_task = active_requests_manager.get(pool_key)
if active_task and not active_task.done():
    await asyncio.wait_for(active_task, timeout=240)
```

##### 资源管理
```python
async with httpx.AsyncClient() as client:
    response = await client.post(url, json=data)
```

##### 锁机制
```python
async with self.lock:
    # 临界区代码
```

### 功能扩展指南

#### 1. 添加新的API端点
```python
@router.post("/new/endpoint")
async def new_endpoint(
    request: CustomRequest,
    _ = Depends(custom_verify_password),
    _2 = Depends(verify_user_agent)
):
    # 实现逻辑
```

#### 2. 扩展Gemini客户端功能
```python
class GeminiClient:
    async def new_feature(self, request):
        # 新功能实现
        api_version, model, data = self._convert_request_data(...)
        # API调用逻辑
```

#### 3. 添加新的缓存策略
```python
def generate_custom_cache_key(request, **kwargs):
    # 自定义缓存键生成逻辑
```

### 测试策略

#### 1. 单元测试
```python
# 测试API密钥管理
async def test_api_key_manager():
    manager = APIKeyManager()
    key = await manager.get_available_key()
    assert key is not None
```

#### 2. 集成测试
```python
# 测试完整请求流程
async def test_chat_completions():
    # 模拟请求
    # 验证响应
```

#### 3. 性能测试
- 并发请求测试
- 缓存命中率测试
- 内存使用监控

### 部署指南

#### 1. Docker部署
```dockerfile
FROM python:3.12-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 环境变量配置
```env
# 基础配置
GEMINI_API_KEYS=key1,key2,key3
PASSWORD=secure_password
GEMINI_BASE_URL=https://generativelanguage.googleapis.com

# 性能配置
CONCURRENT_REQUESTS=3
CACHE_EXPIRY_TIME=21600
MAX_CACHE_ENTRIES=500

# 安全配置
MAX_REQUESTS_PER_MINUTE=30
MAX_REQUESTS_PER_DAY_PER_IP=600
```

#### 3. 监控和日志
- 使用结构化日志记录
- 监控API调用统计
- 错误率和响应时间监控

### 故障排除

#### 1. 常见问题

##### API密钥问题
```python
# 检查密钥有效性
async def test_api_key(api_key: str) -> bool:
    # 验证逻辑
```

##### 缓存问题
```python
# 清理过期缓存
await response_cache_manager.cleanup_expired()
```

##### 并发问题
```python
# 检查活跃请求
active_count = len(active_requests_manager.requests_pool)
```

#### 2. 调试技巧
- 启用详细日志记录
- 使用请求ID追踪
- 监控资源使用情况

### 安全考虑

#### 1. API密钥安全
- 环境变量存储
- 定期轮换密钥
- 访问日志记录

#### 2. 请求验证
- 密码认证
- User-Agent白名单
- 速率限制

#### 3. 数据保护
- 敏感信息脱敏
- 请求内容不记录
- 安全传输(HTTPS)

### 性能优化

#### 1. 缓存策略
- 智能缓存键生成
- LRU缓存淘汰
- 缓存预热

#### 2. 并发优化
- 连接池管理
- 异步IO优化
- 资源池化

#### 3. 内存管理
- 及时释放资源
- 避免内存泄漏
- 监控内存使用

## 贡献指南

### 1. 代码提交规范
- 使用有意义的提交信息
- 遵循代码风格规范
- 添加必要的测试

### 2. 文档更新
- 更新相关文档
- 添加使用示例
- 更新API文档

### 3. 版本管理
- 语义化版本控制
- 变更日志维护
- 向后兼容性考虑

## 联系方式

- 项目仓库: [GitHub链接]
- 问题反馈: [Issues链接]
- 文档更新: [Wiki链接]

---

本文档将随项目发展持续更新，建议定期查看最新版本。