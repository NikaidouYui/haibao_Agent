import random
import re
import os
import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.logging import format_log_message
import app.config.settings as settings
logger = logging.getLogger("my_logger")

class APIKeyManager:
    def __init__(self, persistence=None):
        self.api_keys = re.findall(
            r"AIzaSy[a-zA-Z0-9_-]{33}", settings.GEMINI_API_KEYS)
        # 加载更多 GEMINI_API_KEYS
        for i in range(1, 99):
            if keys := os.environ.get(f"GEMINI_API_KEYS_{i}", ""):
                self.api_keys += re.findall(r"AIzaSy[a-zA-Z0-9_-]{33}", keys)
            else:
                break

        self.key_stack = [] # 初始化密钥栈
        self.temp_failed_keys = set()
        self.lock = asyncio.Lock()
        self.persistence = persistence
        self._reset_key_stack() # 初始化时创建随机密钥栈
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(self.reactivate_temp_failed_keys, 'cron', hour=8, minute=0, timezone='UTC')
        self.scheduler.start()

    def _reset_key_stack(self):
        """创建并随机化密钥栈"""
        shuffled_keys = self.api_keys[:]  # 创建 api_keys 的副本以避免直接修改原列表
        random.shuffle(shuffled_keys)
        self.key_stack = shuffled_keys

    async def get_available_key(self):
        """从栈顶获取密钥，若栈空则重新生成
        
        实现负载均衡：
        1. 维护一个随机排序的栈存储apikey
        2. 每次调用从栈顶取出一个key返回
        3. 栈空时重新随机生成栈
        4. 确保异步和并发安全
        """
        async with self.lock:
            # 如果栈为空，重新生成
            if not self.key_stack:
                self._reset_key_stack()
            
            # 从栈顶取出key
            if self.key_stack:
                return self.key_stack.pop()
            
            # 如果没有可用的API密钥，记录错误
            if not self.api_keys:
                log_msg = format_log_message('ERROR', "没有配置任何 API 密钥！")
                logger.error(log_msg)
            log_msg = format_log_message('ERROR', "没有可用的API密钥！")
            logger.error(log_msg)
            return None

    def show_all_keys(self):
        log_msg = format_log_message('INFO', f"当前可用API key个数: {len(self.api_keys)} ")
        logger.info(log_msg)
        for i, api_key in enumerate(self.api_keys):
            log_msg = format_log_message('INFO', f"API Key{i}: {api_key[:8]}...{api_key[-3:]}")
            logger.info(log_msg)

    async def handle_permanent_failure(self, api_key: str):
        async with self.lock:
            if api_key in self.api_keys:
                self.api_keys.remove(api_key)
                log_msg = format_log_message('WARNING', f"永久移除API Key: {api_key[:8]}...")
                logger.warning(log_msg)
                
                invalid_keys = set(settings.INVALID_API_KEYS.split(',')) if settings.INVALID_API_KEYS else set()
                invalid_keys.add(api_key)
                settings.INVALID_API_KEYS = ",".join(invalid_keys)
                
                if self.persistence:
                    self.persistence.save_settings()
                
                self._reset_key_stack()

    async def handle_temporary_failure(self, api_key: str):
        async with self.lock:
            if api_key in self.api_keys:
                self.api_keys.remove(api_key)
                self.temp_failed_keys.add(api_key)
                log_msg = format_log_message('WARNING', f"暂时禁用API Key: {api_key[:8]}...")
                logger.warning(log_msg)
                self._reset_key_stack()

    def reactivate_temp_failed_keys(self):
        asyncio.run(self._reactivate_temp_failed_keys_async())

    async def _reactivate_temp_failed_keys_async(self):
        async with self.lock:
            if self.temp_failed_keys:
                log_msg = format_log_message('INFO', f"重新激活 {len(self.temp_failed_keys)} 个临时失效的API Key")
                logger.info(log_msg)
                self.api_keys.extend(list(self.temp_failed_keys))
                self.temp_failed_keys.clear()
                self._reset_key_stack()

async def test_api_key(api_key: str) -> bool:
    """
    测试 API 密钥是否有效。
    """
    try:
        import httpx
        url = f"{settings.GEMINI_BASE_URL}/v1beta/models?key={api_key}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()
            return True
    except Exception:
        return False
