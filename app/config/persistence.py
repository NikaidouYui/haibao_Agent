import json
import os
import inspect
import pathlib
import mysql.connector
from abc import ABC, abstractmethod
from app.config import settings
from app.utils.logging import log

# 定义不应该被保存或加载的配置项
EXCLUDED_SETTINGS = [
    "STORAGE_DIR",
    "ENABLE_STORAGE",
    "BASE_DIR",
    "PASSWORD",
    "WEB_PASSWORD",
    "WHITELIST_MODELS",
    "BLOCKED_MODELS",
    "DEFAULT_BLOCKED_MODELS",
    "PUBLIC_MODE",
    "DASHBOARD_URL",
    "version",
    "PERSISTENCE_MODE",
    "MYSQL_HOST",
    "MYSQL_USER",
    "MYSQL_PASSWORD",
    "MYSQL_DATABASE",
]

class Persistence(ABC):
    @abstractmethod
    def save_settings(self):
        pass

    @abstractmethod
    def load_settings(self):
        pass

class FilePersistence(Persistence):
    def __init__(self):
        storage_dir = pathlib.Path(settings.STORAGE_DIR)
        storage_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = storage_dir / "settings.json"

    def save_settings(self):
        """
        将settings中所有的从os.environ.get获取的配置保存到JSON文件中，
        但排除特定的配置项
        """
        if settings.ENABLE_STORAGE:
            settings_dict = {}
            for name, value in inspect.getmembers(settings):
                if (not name.startswith('_') and
                    not inspect.isfunction(value) and
                    not inspect.ismodule(value) and
                    not inspect.isclass(value) and
                    name not in EXCLUDED_SETTINGS):
                    try:
                        json.dumps({name: value})
                        settings_dict[name] = value
                    except (TypeError, OverflowError):
                        continue
            log('info', f"保存设置到JSON文件: {self.settings_file}")
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, ensure_ascii=False, indent=4)
            return self.settings_file

    def load_settings(self):
        """
        从JSON文件中加载设置并更新settings模块，
        排除特定的配置项，并合并GEMINI_API_KEYS
        """
        if settings.ENABLE_STORAGE:
            if not self.settings_file.exists():
                return False
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                current_api_keys = []
                if hasattr(settings, 'GEMINI_API_KEYS') and settings.GEMINI_API_KEYS:
                    current_api_keys = settings.GEMINI_API_KEYS.split(',')
                    current_api_keys = [key.strip() for key in current_api_keys if key.strip()]
                
                current_google_credentials_json = settings.GOOGLE_CREDENTIALS_JSON if hasattr(settings, 'GOOGLE_CREDENTIALS_JSON') else ""
                current_vertex_express_api_key = settings.VERTEX_EXPRESS_API_KEY if hasattr(settings, 'VERTEX_EXPRESS_API_KEY') else ""
                
                for name, value in loaded_settings.items():
                    if hasattr(settings, name) and name not in EXCLUDED_SETTINGS:
                        if name == "GEMINI_API_KEYS":
                            loaded_api_keys = value.split(',') if value else []
                            loaded_api_keys = [key.strip() for key in loaded_api_keys if key.strip()]
                            all_keys = list(set(current_api_keys + loaded_api_keys))
                            setattr(settings, name, ','.join(all_keys))
                        elif name == "GOOGLE_CREDENTIALS_JSON":
                            is_empty = (not current_google_credentials_json or
                                       not current_google_credentials_json.strip() or
                                       current_google_credentials_json.strip() in ['""', "''"])
                            if is_empty:
                                setattr(settings, name, value)
                                if value:
                                    os.environ["GOOGLE_CREDENTIALS_JSON"] = value
                        elif name == "VERTEX_EXPRESS_API_KEY":
                            if not current_vertex_express_api_key or not current_vertex_express_api_key.strip():
                                setattr(settings, name, value)
                                if value:
                                    os.environ["VERTEX_EXPRESS_API_KEY"] = value
                        else:
                            setattr(settings, name, value)
                
                self._reload_vertex_config()
                log('info', f"从文件加载设置成功")
                return True
            except Exception as e:
                log('error', f"从文件加载设置时出错: {e}")
                return False

    def _reload_vertex_config(self):
        try:
            if (hasattr(settings, 'GOOGLE_CREDENTIALS_JSON') and settings.GOOGLE_CREDENTIALS_JSON) or \
               (hasattr(settings, 'VERTEX_EXPRESS_API_KEY') and settings.VERTEX_EXPRESS_API_KEY):
                log('info', "检测到Google Credentials JSON或Vertex Express API Key，准备更新配置")
                import app.vertex.config as app_config
                app_config.reload_config()
                if hasattr(settings, 'GOOGLE_CREDENTIALS_JSON') and settings.GOOGLE_CREDENTIALS_JSON:
                    app_config.GOOGLE_CREDENTIALS_JSON = settings.GOOGLE_CREDENTIALS_JSON
                    os.environ["GOOGLE_CREDENTIALS_JSON"] = settings.GOOGLE_CREDENTIALS_JSON
                    log('info', "已更新app_config和环境变量中的GOOGLE_CREDENTIALS_JSON")
                if hasattr(settings, 'VERTEX_EXPRESS_API_KEY') and settings.VERTEX_EXPRESS_API_KEY:
                    app_config.VERTEX_EXPRESS_API_KEY_VAL = [key.strip() for key in settings.VERTEX_EXPRESS_API_KEY.split(',') if key.strip()]
                    os.environ["VERTEX_EXPRESS_API_KEY"] = settings.VERTEX_EXPRESS_API_KEY
                    log('info', f"已更新app_config和环境变量中的VERTEX_EXPRESS_API_KEY_VAL")
                log('info', "配置更新完成，Vertex AI将在下次请求时重新初始化")
        except Exception as e:
            log('error', f"更新配置时出错: {str(e)}")


class MySQLPersistence(Persistence):
    def __init__(self):
        self.host = settings.MYSQL_HOST
        self.user = settings.MYSQL_USER
        self.password = settings.MYSQL_PASSWORD
        self.database = settings.MYSQL_DATABASE
        self.connection = None
        self._connect()
        self._create_table()

    def _connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            log('info', "成功连接到MySQL数据库")
        except mysql.connector.Error as err:
            log('error', f"连接MySQL失败: {err}")
            self.connection = None

    def _create_table(self):
        if not self.connection:
            return
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    `key` VARCHAR(255) PRIMARY KEY,
                    `value` TEXT
                )
            """)
            log('info', "设置表已存在或已成功创建")
        except mysql.connector.Error as err:
            log('error', f"创建表失败: {err}")

    def save_settings(self):
        if not self.connection:
            return
        try:
            cursor = self.connection.cursor()
            settings_dict = {}
            for name, value in inspect.getmembers(settings):
                if (not name.startswith('_') and
                    not inspect.isfunction(value) and
                    not inspect.ismodule(value) and
                    not inspect.isclass(value) and
                    name not in EXCLUDED_SETTINGS):
                    try:
                        # For simplicity, we'll store all values as strings.
                        # Complex objects would need serialization (e.g., to JSON).
                        settings_dict[name] = str(value)
                    except (TypeError, OverflowError):
                        continue
            
            for key, value in settings_dict.items():
                cursor.execute(
                    "INSERT INTO settings (`key`, `value`) VALUES (%s, %s) ON DUPLICATE KEY UPDATE `value` = %s",
                    (key, value, value)
                )
            self.connection.commit()
            log('info', "设置已成功保存到MySQL数据库")
        except mysql.connector.Error as err:
            log('error', f"保存设置到MySQL失败: {err}")
            self.connection.rollback()

    def load_settings(self):
        if not self.connection:
            return False
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT `key`, `value` FROM settings")
            loaded_settings = {row['key']: row['value'] for row in cursor.fetchall()}

            for name, value in loaded_settings.items():
                if hasattr(settings, name) and name not in EXCLUDED_SETTINGS:
                    # Here we assume the type conversion is not needed or handled elsewhere
                    # A more robust solution would handle type casting based on original type
                    setattr(settings, name, value)
            
            log('info', "从MySQL加载设置成功")
            return True
        except mysql.connector.Error as err:
            log('error', f"从MySQL加载设置失败: {err}")
            return False

def get_persistence():
    mode = settings.PERSISTENCE_MODE
    if mode == 'mysql':
        return MySQLPersistence()
    elif mode == 'file':
        return FilePersistence()
    else:
        log('warning', f"未知的持久化模式: {mode}. 回退到文件模式。")
        return FilePersistence()