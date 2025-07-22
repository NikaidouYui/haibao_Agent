# Gemini Base URL 配置说明

## 概述

本项目现在支持通过环境变量 `GEMINI_BASE_URL` 来自定义 Gemini API 的基础 URL，这对于使用反向代理或自定义 API 端点的用户非常有用。

## 配置方法

### 1. 环境变量配置

在 `.env` 文件中添加或修改以下配置：

```bash
# Gemini API 基础URL (可选，默认为官方API地址)
GEMINI_BASE_URL=https://your-custom-api-endpoint.com
```

### 2. 默认值

如果不设置 `GEMINI_BASE_URL` 环境变量，系统将使用默认的官方 Gemini API 地址：
```
https://generativelanguage.googleapis.com
```

## 使用场景

### 1. 反向代理
如果你通过反向代理访问 Gemini API：
```bash
GEMINI_BASE_URL=https://your-proxy.example.com
```

### 2. 自定义端点
如果你有自己的 Gemini API 兼容服务：
```bash
GEMINI_BASE_URL=https://api.yourservice.com
```

### 3. 本地开发
如果你在本地运行 Gemini API 兼容服务：
```bash
GEMINI_BASE_URL=http://localhost:8080
```

## 影响的 API 端点

配置 `GEMINI_BASE_URL` 会影响以下 API 端点：

1. **生成内容 API**
   - 原始: `https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`
   - 自定义: `{GEMINI_BASE_URL}/v1beta/models/{model}:generateContent`

2. **流式生成 API**
   - 原始: `https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent`
   - 自定义: `{GEMINI_BASE_URL}/v1beta/models/{model}:streamGenerateContent`

3. **模型列表 API**
   - 原始: `https://generativelanguage.googleapis.com/v1beta/models`
   - 自定义: `{GEMINI_BASE_URL}/v1beta/models`

4. **OpenAI 兼容 API**
   - 原始: `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`
   - 自定义: `{GEMINI_BASE_URL}/v1beta/openai/chat/completions`

## 注意事项

1. **URL 格式**: 确保 URL 以 `http://` 或 `https://` 开头
2. **末尾斜杠**: 系统会自动处理 URL 末尾的斜杠，无需担心
3. **兼容性**: 自定义端点必须与 Gemini API 完全兼容
4. **安全性**: 使用 HTTPS 以确保数据传输安全

## 测试配置

你可以使用项目中的测试脚本来验证配置：

```bash
python simple_test.py
```

## 配置示例

### 示例 1: 使用 Cloudflare Workers 代理
```bash
GEMINI_BASE_URL=https://your-worker.your-subdomain.workers.dev
```

### 示例 2: 使用 Nginx 反向代理
```bash
GEMINI_BASE_URL=https://gemini-proxy.yourdomain.com
```

### 示例 3: 使用自建服务
```bash
GEMINI_BASE_URL=https://api.yourcompany.com/gemini
```

## 故障排除

### 1. 连接失败
- 检查 URL 是否正确
- 确认网络连接正常
- 验证代理服务是否正常运行

### 2. API 响应错误
- 确认自定义端点与 Gemini API 兼容
- 检查 API 密钥是否正确配置
- 查看服务日志获取详细错误信息

### 3. 配置不生效
- 重启应用程序以加载新的环境变量
- 检查 `.env` 文件格式是否正确
- 确认环境变量名称拼写正确

## 相关文件

本功能涉及以下文件的修改：

- `.env` - 环境变量配置
- `app/config/settings.py` - 配置加载
- `app/services/gemini.py` - Gemini 服务客户端
- `app/services/OpenAI.py` - OpenAI 兼容服务
- `app/utils/api_key.py` - API 密钥管理

## 版本信息

此功能在当前版本中添加，向后兼容，不会影响现有配置。