# HAJIMI项目AI技术协作规范

## 项目技术栈概览

### 后端架构
- **框架**: FastAPI (Python 3.12+)
- **异步**: asyncio + httpx
- **依赖管理**: uv + pyproject.toml
- **API设计**: RESTful + OpenAI兼容格式

### 前端架构  
- **框架**: Vue.js 3 + Vite
- **状态管理**: Pinia
- **路由**: Vue Router
- **图表**: ECharts

### 核心依赖
```toml
fastapi>=0.115.12
google-genai==1.11.0
google-cloud-aiplatform==1.86.0
httpx>=0.28.1
pydantic==2.6.1
uvicorn>=0.34.2
```

## 代码协作规范

### 1. 文件修改权限矩阵

| 文件类型 | 可修改 | 需谨慎 | 禁止修改 |
|---------|--------|--------|----------|
| `app/config/settings.py` | ✅ 新增配置项 | ⚠️ 修改现有配置 | ❌ 删除配置项 |
| `app/services/*.py` | ✅ 新增方法 | ⚠️ 修改核心逻辑 | ❌ 删除现有方法 |
| `app/api/routes.py` | ✅ 新增路由 | ⚠️ 修改现有路由 | ❌ 删除路由 |
| `app/utils/*.py` | ✅ 工具函数 | ⚠️ 核心工具类 | ❌ 删除现有工具 |
| `app/main.py` | ❌ 启动逻辑 | ⚠️ 中间件配置 | ❌ 核心初始化 |

### 2. 代码修改最佳实践

#### 添加新功能
```python
# ✅ 推荐：扩展现有类
class GeminiClient:
    async def new_feature_method(self, request):
        """新功能的详细文档"""
        # 实现逻辑
        pass

# ✅ 推荐：新增工具函数
async def new_utility_function(param: str) -> dict:
    """工具函数文档"""
    return {"result": param}
```

#### 修改现有功能
```python
# ⚠️ 谨慎：修改现有方法时保持向后兼容
async def existing_method(self, param1, param2=None, new_param=None):
    # 保持原有参数
    # 新增可选参数
    pass
```

#### 配置管理
```python
# ✅ 推荐：添加新配置项
NEW_FEATURE_ENABLED = os.environ.get("NEW_FEATURE_ENABLED", "false").lower() in ["true", "1", "yes"]
NEW_FEATURE_TIMEOUT = int(os.environ.get("NEW_FEATURE_TIMEOUT", "30"))

# ✅ 推荐：配置验证
if NEW_FEATURE_ENABLED and NEW_FEATURE_TIMEOUT <= 0:
    raise ValueError("NEW_FEATURE_TIMEOUT must be positive when NEW_FEATURE_ENABLED is true")
```

### 3. 异步编程规范

#### 资源管理
```python
# ✅ 正确的异步资源管理
async def api_call_example():
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, timeout=600)
        return response.json()

# ❌ 错误：未正确管理资源
async def bad_example():
    client = httpx.AsyncClient()
    response = await client.post(url, json=data)  # 可能导致连接泄漏
    return response.json()
```

#### 并发控制
```python
# ✅ 正确的并发控制
async def concurrent_requests(requests_list):
    semaphore = asyncio.Semaphore(5)  # 限制并发数
    
    async def process_request(request):
        async with semaphore:
            return await make_api_call(request)
    
    tasks = [process_request(req) for req in requests_list]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

#### 错误处理
```python
# ✅ 推荐的错误处理模式
async def robust_api_call(api_key: str, data: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        log('warning', f"API调用超时: {api_key[:8]}...")
        raise HTTPException(status_code=408, detail="请求超时")
    except httpx.HTTPStatusError as e:
        log('error', f"API调用失败: {e.response.status_code}")
        raise HTTPException(status_code=e.response.status_code, detail="API调用失败")
    except Exception as e:
        log('error', f"未预期的错误: {str(e)}")
        raise HTTPException(status_code=500, detail="内部服务器错误")
```

### 4. 数据模型规范

#### Pydantic模型定义
```python
# ✅ 推荐的模型定义
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union

class NewFeatureRequest(BaseModel):
    """新功能请求模型"""
    feature_type: str = Field(..., description="功能类型")
    parameters: Optional[dict] = Field(None, description="功能参数")
    timeout: int = Field(30, ge=1, le=300, description="超时时间(秒)")
    
    @validator('feature_type')
    def validate_feature_type(cls, v):
        allowed_types = ['type1', 'type2', 'type3']
        if v not in allowed_types:
            raise ValueError(f'feature_type must be one of {allowed_types}')
        return v

class NewFeatureResponse(BaseModel):
    """新功能响应模型"""
    success: bool
    result: Optional[dict] = None
    error_message: Optional[str] = None
    processing_time: float
```

### 5. 日志记录规范

#### 结构化日志
```python
from app.utils.logging import log

# ✅ 推荐的日志记录方式
def log_api_call(api_key: str, model: str, request_type: str, status: str):
    extra_info = {
        'api_key': api_key[:8] + '...',
        'model': model,
        'request_type': request_type,
        'status': status,
        'timestamp': datetime.now().isoformat()
    }
    log('info', f"API调用 - {status}", extra=extra_info)

# ✅ 错误日志记录
def log_error(error: Exception, context: dict):
    extra_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context
    }
    log('error', f"发生错误: {type(error).__name__}", extra=extra_info)
```

### 6. 测试规范

#### 单元测试
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_new_feature():
    """测试新功能"""
    # 准备测试数据
    test_request = NewFeatureRequest(
        feature_type="type1",
        parameters={"param1": "value1"}
    )
    
    # 模拟依赖
    with patch('app.services.gemini.httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"result": "success"}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # 执行测试
        client = GeminiClient("test_key")
        result = await client.new_feature_method(test_request)
        
        # 验证结果
        assert result is not None
        assert "result" in result
```

#### 集成测试
```python
@pytest.mark.asyncio
async def test_full_request_flow():
    """测试完整请求流程"""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # 测试数据
    test_payload = {
        "model": "gemini-2.5-pro",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }
    
    # 发送请求
    response = client.post("/v1/chat/completions", json=test_payload)
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert len(data["choices"]) > 0
```

### 7. 性能优化指南

#### 缓存策略
```python
# ✅ 智能缓存实现
import hashlib
import json

def generate_smart_cache_key(request: dict, context: dict) -> str:
    """生成智能缓存键"""
    # 提取关键信息
    key_data = {
        'model': request.get('model'),
        'messages': request.get('messages', [])[-5:],  # 只取最后5条消息
        'temperature': request.get('temperature'),
        'max_tokens': request.get('max_tokens')
    }
    
    # 生成哈希
    key_string = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(key_string.encode()).hexdigest()[:16]

# ✅ 缓存管理
class SmartCacheManager:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache = {}
        self.access_times = {}
        self.max_size = max_size
        self.ttl = ttl
    
    async def get(self, key: str) -> Optional[dict]:
        if key in self.cache:
            # 检查过期
            if time.time() - self.access_times[key] > self.ttl:
                del self.cache[key]
                del self.access_times[key]
                return None
            
            # 更新访问时间
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    async def set(self, key: str, value: dict):
        # LRU淘汰
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = time.time()
```

#### 连接池优化
```python
# ✅ 连接池配置
import httpx

class OptimizedHTTPClient:
    def __init__(self):
        self.limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30
        )
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=10.0,
            pool=5.0
        )
    
    async def get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            limits=self.limits,
            timeout=self.timeout,
            http2=True  # 启用HTTP/2
        )
```

### 8. 安全编程规范

#### 输入验证
```python
# ✅ 严格的输入验证
def validate_api_key(api_key: str) -> bool:
    """验证API密钥格式"""
    import re
    pattern = r'^AIzaSy[a-zA-Z0-9_-]{33}$'
    return bool(re.match(pattern, api_key))

def sanitize_user_input(user_input: str) -> str:
    """清理用户输入"""
    # 移除潜在危险字符
    import html
    sanitized = html.escape(user_input)
    # 限制长度
    return sanitized[:10000]  # 限制最大长度
```

#### 敏感信息处理
```python
# ✅ 敏感信息脱敏
def mask_api_key(api_key: str) -> str:
    """脱敏API密钥"""
    if len(api_key) < 8:
        return "***"
    return f"{api_key[:8]}...{api_key[-3:]}"

def mask_sensitive_data(data: dict) -> dict:
    """脱敏敏感数据"""
    sensitive_keys = ['api_key', 'password', 'token', 'secret']
    masked_data = data.copy()
    
    for key in sensitive_keys:
        if key in masked_data:
            if isinstance(masked_data[key], str):
                masked_data[key] = mask_api_key(masked_data[key])
    
    return masked_data
```

### 9. 部署和运维规范

#### 健康检查
```python
# ✅ 健康检查端点
@router.get("/health")
async def health_check():
    """系统健康检查"""
    checks = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # 检查API密钥
    try:
        key = await key_manager.get_available_key()
        checks["checks"]["api_keys"] = "ok" if key else "error"
    except Exception:
        checks["checks"]["api_keys"] = "error"
    
    # 检查缓存
    try:
        cache_size = len(response_cache_manager.cache_dict)
        checks["checks"]["cache"] = f"ok ({cache_size} entries)"
    except Exception:
        checks["checks"]["cache"] = "error"
    
    # 整体状态
    if any(status == "error" for status in checks["checks"].values()):
        checks["status"] = "unhealthy"
    
    return checks
```

#### 监控指标
```python
# ✅ 监控指标收集
class MetricsCollector:
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_request(self, response_time: float, success: bool):
        self.request_count += 1
        self.response_times.append(response_time)
        if not success:
            self.error_count += 1
        
        # 保持最近1000条记录
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]
    
    def record_cache_hit(self):
        self.cache_hits += 1
    
    def record_cache_miss(self):
        self.cache_misses += 1
    
    def get_metrics(self) -> dict:
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        error_rate = self.error_count / self.request_count if self.request_count > 0 else 0
        cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "avg_response_time": avg_response_time,
            "cache_hit_rate": cache_hit_rate
        }
```

### 10. 代码审查清单

#### 提交前检查
- [ ] 代码符合项目风格规范
- [ ] 添加了必要的类型注解
- [ ] 包含适当的错误处理
- [ ] 添加了日志记录
- [ ] 编写了单元测试
- [ ] 更新了相关文档
- [ ] 检查了安全性问题
- [ ] 验证了性能影响
- [ ] 确保向后兼容性

#### 代码质量标准
```python
# ✅ 高质量代码示例
from typing import Optional, Dict, Any, List
import asyncio
import logging

class ExampleService:
    """示例服务类
    
    提供示例功能的服务实现
    """
    
    def __init__(self, config: Dict[str, Any]):
        """初始化服务
        
        Args:
            config: 服务配置字典
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._client: Optional[httpx.AsyncClient] = None
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理请求
        
        Args:
            request: 请求数据
            
        Returns:
            处理结果
            
        Raises:
            ValueError: 请求数据无效
            HTTPException: API调用失败
        """
        # 输入验证
        if not request or 'type' not in request:
            raise ValueError("请求数据无效")
        
        # 处理逻辑
        try:
            result = await self._make_api_call(request)
            self.logger.info(f"请求处理成功: {request['type']}")
            return result
        except Exception as e:
            self.logger.error(f"请求处理失败: {str(e)}")
            raise
    
    async def _make_api_call(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """内部API调用方法"""
        # 实现细节
        pass
```

这个技术规范文档为AI助手提供了详细的协作指南，确保代码质量和项目一致性。