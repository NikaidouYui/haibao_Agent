#!/usr/bin/env python3
"""
简单测试 GEMINI_BASE_URL 环境变量配置
"""
import os

def test_gemini_base_url():
    """测试 GEMINI_BASE_URL 配置"""
    print("=== Gemini Base URL 配置测试 ===")
    
    # 直接读取环境变量
    gemini_base_url = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com").rstrip('/')
    
    print(f"当前配置的 GEMINI_BASE_URL: {gemini_base_url}")
    
    # 测试默认值
    if not os.environ.get("GEMINI_BASE_URL"):
        print("✓ 使用默认的官方 API 地址")
    else:
        print("✓ 使用自定义的 API 地址")
    
    # 验证URL格式
    if gemini_base_url.startswith(('http://', 'https://')):
        print("✓ URL 格式正确")
    else:
        print("✗ URL 格式错误，应该以 http:// 或 https:// 开头")
        return False
    
    # 验证URL末尾没有斜杠
    if not gemini_base_url.endswith('/'):
        print("✓ URL 末尾正确处理（无多余斜杠）")
    else:
        print("✗ URL 末尾处理错误")
        return False
    
    print("\n=== 生成的 API URL 示例 ===")
    api_key = "AIzaSyExample_API_Key_Here"
    model = "gemini-1.5-pro"
    api_version = "v1beta"
    
    # 模拟生成的URL
    generate_url = f"{gemini_base_url}/{api_version}/models/{model}:generateContent?key={api_key}"
    stream_url = f"{gemini_base_url}/{api_version}/models/{model}:streamGenerateContent?key={api_key}&alt=sse"
    models_url = f"{gemini_base_url}/v1beta/models?key={api_key}"
    openai_url = f"{gemini_base_url}/v1beta/openai/chat/completions"
    
    print(f"生成内容 URL: {generate_url}")
    print(f"流式生成 URL: {stream_url}")
    print(f"模型列表 URL: {models_url}")
    print(f"OpenAI 兼容 URL: {openai_url}")
    
    print("\n=== 测试自定义 URL ===")
    # 测试自定义URL
    custom_url = "https://api.example.com"
    os.environ["GEMINI_BASE_URL"] = custom_url
    
    new_base_url = os.environ.get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com").rstrip('/')
    custom_generate_url = f"{new_base_url}/{api_version}/models/{model}:generateContent?key={api_key}"
    
    print(f"自定义基础 URL: {custom_url}")
    print(f"生成的 API URL: {custom_generate_url}")
    
    # 清理环境变量
    if "GEMINI_BASE_URL" in os.environ:
        del os.environ["GEMINI_BASE_URL"]
    
    return True

if __name__ == "__main__":
    success = test_gemini_base_url()
    if success:
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 测试失败！")