from typing import Optional
from fastapi import HTTPException, Header, Query
import app.config.settings as settings

# 自定义密码校验依赖函数
async def custom_verify_password(
    authorization: Optional[str] = Header(None, description="OpenAI 格式请求 Key, 格式: Bearer sk-xxxx"),
    x_goog_api_key: Optional[str] = Header(None, description="Gemini 格式请求 Key, 从请求头 x-goog-api-key 获取"),
    key: Optional[str] = Query(None, description="Gemini 格式请求 Key, 从查询参数 key 获取"),
    alt: Optional[str] = None
):
    """
    自定义密码校验依赖函数
    1. 从请求中提取客户端提供的 Key（支持多种格式）。
    2. 根据类型，与项目配置的密钥进行比对。
    3. 如果 Key 无效、缺失或不匹配，则抛出 HTTPException。
    """
    from app.utils.logging import log
    
    client_provided_api_key: Optional[str] = None

    # 提取客户端提供的 Key
    if x_goog_api_key:
        client_provided_api_key = x_goog_api_key
        auth_method = "x-goog-api-key header"
    elif key:
        client_provided_api_key = key
        auth_method = "query parameter"
    elif authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        client_provided_api_key = token
        auth_method = "Bearer token"
    else:
        auth_method = "none"

    log('info', f"[DEBUG] 密码认证开始",
        extra={'auth_method': auth_method,
               'client_key_provided': bool(client_provided_api_key),
               'client_key_length': len(client_provided_api_key) if client_provided_api_key else 0,
               'expected_password': settings.PASSWORD,
               'authorization_header': authorization,
               'x_goog_api_key_header': x_goog_api_key,
               'key_query_param': key})

    # 进行校验和比对
    if not client_provided_api_key:
        log('error', f"[DEBUG] 密码认证失败：客户端未提供API密钥",
            extra={'auth_method': auth_method})
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")
    
    if client_provided_api_key != settings.PASSWORD:
        log('error', f"[DEBUG] 密码认证失败：API密钥不匹配",
            extra={'auth_method': auth_method,
                   'client_key': client_provided_api_key,
                   'expected_key': settings.PASSWORD,
                   'keys_match': client_provided_api_key == settings.PASSWORD})
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid token")
    
    log('info', f"[DEBUG] 密码认证成功",
        extra={'auth_method': auth_method})

def verify_web_password(password:str):
    if password != settings.WEB_PASSWORD:
        return False
    return True