import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from app.utils.api_key import APIKeyManager
from app.utils.error_handling import handle_gemini_error, handle_api_error
import httpx
import requests
from fastapi import HTTPException


class TestAPIKeyManager:
    """测试APIKeyManager类的各种功能"""

    @pytest.fixture
    def api_key_manager(self):
        """创建APIKeyManager实例用于测试"""
        # 模拟持久化对象
        mock_persistence = Mock()
        mock_persistence.save_settings = Mock()
        
        # 创建APIKeyManager实例
        manager = APIKeyManager(persistence=mock_persistence)
        # 设置测试用的API密钥
        manager.api_keys = ["AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", 
                           "AIzaSyBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                           "AIzaSyCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"]
        manager._reset_key_stack()
        return manager

    @pytest.mark.asyncio
    async def test_handle_permanent_failure(self, api_key_manager):
        """测试handle_permanent_failure方法能正确移除API Key并更新设置"""
        # 获取一个API密钥用于测试
        initial_key_count = len(api_key_manager.api_keys)
        test_key = api_key_manager.api_keys[0]
        
        # 调用handle_permanent_failure方法
        await api_key_manager.handle_permanent_failure(test_key)
        
        # 验证API密钥已被移除
        assert test_key not in api_key_manager.api_keys
        assert len(api_key_manager.api_keys) == initial_key_count - 1
        
        # 验证持久化方法被调用
        api_key_manager.persistence.save_settings.assert_called_once()
        
        # 验证密钥栈已重置
        # 由于密钥栈是随机排序的，我们验证栈中的密钥数量是否正确
        assert len(api_key_manager.key_stack) == len(api_key_manager.api_keys)

    @pytest.mark.asyncio
    async def test_handle_temporary_failure(self, api_key_manager):
        """测试handle_temporary_failure方法能正确暂时禁用API Key"""
        # 获取一个API密钥用于测试
        initial_key_count = len(api_key_manager.api_keys)
        initial_temp_failed_count = len(api_key_manager.temp_failed_keys)
        test_key = api_key_manager.api_keys[0]
        
        # 调用handle_temporary_failure方法
        await api_key_manager.handle_temporary_failure(test_key)
        
        # 验证API密钥已从可用密钥中移除
        assert test_key not in api_key_manager.api_keys
        assert len(api_key_manager.api_keys) == initial_key_count - 1
        
        # 验证API密钥已添加到临时失败密钥集合中
        assert test_key in api_key_manager.temp_failed_keys
        assert len(api_key_manager.temp_failed_keys) == initial_temp_failed_count + 1
        
        # 验证密钥栈已重置
        assert len(api_key_manager.key_stack) == len(api_key_manager.api_keys)

    @pytest.mark.asyncio
    async def test_reactivate_temp_failed_keys(self, api_key_manager):
        """测试reactivate_temp_failed_keys方法能正确重新激活临时禁用的API Key"""
        # 先添加一个临时失败的密钥
        test_key = "AIzaSyDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"
        api_key_manager.temp_failed_keys.add(test_key)
        
        # 记录初始状态
        initial_api_key_count = len(api_key_manager.api_keys)
        initial_temp_failed_count = len(api_key_manager.temp_failed_keys)
        
        # 调用重新激活方法
        await api_key_manager._reactivate_temp_failed_keys_async()
        
        # 验证临时失败密钥已被移除
        assert len(api_key_manager.temp_failed_keys) == 0
        
        # 验证API密钥已重新添加到可用密钥中
        assert test_key in api_key_manager.api_keys
        assert len(api_key_manager.api_keys) == initial_api_key_count + 1
        
        # 验证密钥栈已重置
        assert len(api_key_manager.key_stack) == len(api_key_manager.api_keys)

    @pytest.mark.asyncio
    async def test_get_available_key(self, api_key_manager):
        """测试get_available_key方法能正确获取API密钥"""
        # 获取一个API密钥
        key = await api_key_manager.get_available_key()
        
        # 验证返回的密钥不为None且在初始密钥列表中
        assert key is not None
        assert key in ["AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", 
                      "AIzaSyBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                      "AIzaSyCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"]
        
        # 验证密钥栈中的密钥数量减少
        assert len(api_key_manager.key_stack) == 2

    @pytest.mark.asyncio
    async def test_get_available_key_empty_stack(self, api_key_manager):
        """测试当密钥栈为空时，get_available_key方法能正确重新生成密钥栈"""
        # 清空密钥栈
        api_key_manager.key_stack = []
        
        # 获取一个API密钥
        key = await api_key_manager.get_available_key()
        
        # 验证返回的密钥不为None且在初始密钥列表中
        assert key is not None
        assert key in ["AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA", 
                      "AIzaSyBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
                      "AIzaSyCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"]
        
        # 验证密钥栈已被重新生成
        assert len(api_key_manager.key_stack) == 2


class TestErrorHandling:
    """测试错误处理函数"""

    @pytest.fixture
    def mock_key_manager(self):
        """创建模拟的APIKeyManager"""
        manager = Mock()
        manager.handle_permanent_failure = AsyncMock()
        manager.handle_temporary_failure = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_handle_gemini_error_400_invalid_key(self, mock_key_manager):
        """测试handle_gemini_error处理400错误（无效API密钥）"""
        # 创建模拟的400错误响应
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "error": {
                "code": "invalid_argument",
                "message": "API key not valid. Please pass a valid API key."
            }
        }
        
        mock_error = httpx.HTTPStatusError(
            "Invalid API key", 
            request=Mock(), 
            response=mock_response
        )
        
        test_api_key = "AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        
        # 调用错误处理函数
        result = await handle_gemini_error(mock_error, test_api_key, mock_key_manager)
        
        # 验证返回的错误消息
        assert result == "无效的 API 密钥"
        
        # 验证永久失败处理方法被调用
        mock_key_manager.handle_permanent_failure.assert_called_once_with(test_api_key)

    @pytest.mark.asyncio
    async def test_handle_gemini_error_403_forbidden(self, mock_key_manager):
        """测试handle_gemini_error处理403错误（权限被拒绝）"""
        # 创建模拟的403错误响应
        mock_response = Mock()
        mock_response.status_code = 403
        
        mock_error = httpx.HTTPStatusError(
            "Permission denied", 
            request=Mock(), 
            response=mock_response
        )
        
        test_api_key = "AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        
        # 调用错误处理函数
        result = await handle_gemini_error(mock_error, test_api_key, mock_key_manager)
        
        # 验证返回的错误消息
        assert result == "权限被拒绝"
        
        # 验证永久失败处理方法被调用
        mock_key_manager.handle_permanent_failure.assert_called_once_with(test_api_key)

    @pytest.mark.asyncio
    async def test_handle_gemini_error_429_quota_exceeded(self, mock_key_manager):
        """测试handle_gemini_error处理429错误（配额已用尽）"""
        # 创建模拟的429错误响应
        mock_response = Mock()
        mock_response.status_code = 429
        
        mock_error = httpx.HTTPStatusError(
            "Quota exceeded", 
            request=Mock(), 
            response=mock_response
        )
        
        test_api_key = "AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        
        # 调用错误处理函数
        result = await handle_gemini_error(mock_error, test_api_key, mock_key_manager)
        
        # 验证返回的错误消息
        assert result == "API 密钥配额已用尽或其他原因"
        
        # 验证临时失败处理方法被调用
        mock_key_manager.handle_temporary_failure.assert_called_once_with(test_api_key)

    @pytest.mark.asyncio
    async def test_handle_api_error_429_quota_exceeded(self):
        """测试handle_api_error处理429错误（配额已用尽）"""
        # 创建模拟的429错误响应
        mock_response = Mock()
        mock_response.status_code = 429
        
        mock_error = httpx.HTTPStatusError(
            "Quota exceeded", 
            request=Mock(), 
            response=mock_response
        )
        
        mock_key_manager = Mock()
        
        test_api_key = "AIzaSyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        
        # 调用错误处理函数
        result = await handle_api_error(
            mock_error, 
            test_api_key, 
            mock_key_manager, 
            "test_request", 
            "test_model"
        )
        
        # 验证返回的结果
        assert result == {
            'remove_cache': False,
            'error': 'API 密钥配额已用尽或其他原因', 
            'should_switch_key': True
        }


# 为异步方法创建一个AsyncMock类
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])