# 配置模块初始化文件
import app.config.settings as settings
from app.config.safety import *
from app.config.persistence import get_persistence

# 获取持久化实例
persistence_instance = get_persistence()

# 将实例的方法赋值给模块级别的变量
save_settings = persistence_instance.save_settings
load_settings = persistence_instance.load_settings