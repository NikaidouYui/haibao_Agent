import requests
import re
from typing import List, Optional
from app.utils.logging import log
import app.config.settings as settings

def get_ghcr_token(repository: str) -> Optional[str]:
    """
    获取GHCR访问令牌
    
    Args:
        repository: 镜像仓库名，格式如 "nikaidouyui/haibao_agent"
    
    Returns:
        访问令牌，如果失败返回None
    """
    try:
        # 获取令牌的URL
        token_url = f"https://ghcr.io/token?service=ghcr.io&scope=repository:{repository}:pull"
        
        response = requests.get(token_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            return token
        else:
            log('warning', f"获取GHCR令牌失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        log('error', f"获取GHCR令牌异常: {str(e)}")
        return None

def get_ghcr_tags(repository: str) -> Optional[List[str]]:
    """
    从GHCR获取镜像标签列表
    
    Args:
        repository: 镜像仓库名，格式如 "nikaidouyui/haibao_agent"
    
    Returns:
        标签列表，如果失败返回None
    """
    try:
        # 先获取访问令牌
        token = get_ghcr_token(repository)
        if not token:
            log('warning', "无法获取GHCR访问令牌")
            return None
        
        # GHCR API端点
        url = f"https://ghcr.io/v2/{repository}/tags/list"
        
        # 设置认证头
        headers = {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
        }
        
        # 发送请求
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            tags = data.get('tags', [])
            return tags
        else:
            log('warning', f"获取GHCR标签失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        log('error', f"获取GHCR标签异常: {str(e)}")
        return None

def filter_version_tags(tags: List[str]) -> List[str]:
    """
    筛选出版本号标签（排除latest等）
    
    Args:
        tags: 所有标签列表
    
    Returns:
        版本号标签列表，按版本号降序排列
    """
    version_pattern = re.compile(r'^\d+\.\d+\.\d+$')
    version_tags = [tag for tag in tags if version_pattern.match(tag)]
    return sorted(version_tags, key=lambda x: [int(i) for i in x.split('.')], reverse=True)

def get_latest_docker_version(repository: str = "nikaidouyui/haibao_agent") -> Optional[str]:
    """
    获取最新的Docker镜像版本号
    
    Args:
        repository: 镜像仓库名
    
    Returns:
        最新版本号，如果失败返回None
    """
    tags = get_ghcr_tags(repository)
    if not tags:
        return None
    
    version_tags = filter_version_tags(tags)
    
    if version_tags:
        latest = version_tags[0]
        log('info', f"从GHCR获取到最新版本: {latest}")
        return latest
    
    log('warning', "未找到有效的版本标签")
    return None

async def check_version():
    """
    检查应用程序版本更新
    
    从本地和Docker镜像仓库获取版本信息，并比较版本号以确定是否有更新
    """
    try:
        # 读取本地版本
        with open("./version.txt", "r") as f:
            version_line = f.read().strip()
            settings.version['local_version'] = version_line.split("=")[1] if "=" in version_line else "0.0.0"
        
        # 获取远程版本（从Docker镜像仓库）
        remote_version = get_latest_docker_version()
        
        if remote_version:
            settings.version['remote_version'] = remote_version
            
            # 比较版本号
            local_parts = [int(x) for x in settings.version['local_version'].split(".")]
            remote_parts = [int(x) for x in remote_version.split(".")]
            
            # 确保两个列表长度相同
            while len(local_parts) < len(remote_parts):
                local_parts.append(0)
            while len(remote_parts) < len(local_parts):
                remote_parts.append(0)
                
            # 比较版本号
            settings.version['has_update'] = False
            for i in range(len(local_parts)):
                if remote_parts[i] > local_parts[i]:
                    settings.version['has_update'] = True
                    break
                elif remote_parts[i] < local_parts[i]:
                    break
            
            log('info', f"版本检查: 本地版本 {settings.version['local_version']}, 远程版本 {settings.version['remote_version']}, 有更新: {settings.version['has_update']}")
        else:
            # 如果无法获取Docker镜像版本，回退到GitHub方式
            log('warning', "无法从GHCR获取版本信息，回退到GitHub方式")
            github_url = "https://raw.githubusercontent.com/wyeeeee/hajimi/refs/heads/main/version.txt"
            response = requests.get(github_url, timeout=5)
            if response.status_code == 200:
                version_line = response.text.strip()
                settings.version['remote_version'] = version_line.split("=")[1] if "=" in version_line else "0.0.0"
                
                # 比较版本号
                local_parts = [int(x) for x in settings.version['local_version'].split(".")]
                remote_parts = [int(x) for x in settings.version['remote_version'].split(".")]
                
                # 确保两个列表长度相同
                while len(local_parts) < len(remote_parts):
                    local_parts.append(0)
                while len(remote_parts) < len(local_parts):
                    remote_parts.append(0)
                    
                # 比较版本号
                settings.version['has_update'] = False
                for i in range(len(local_parts)):
                    if remote_parts[i] > local_parts[i]:
                        settings.version['has_update'] = True
                        break
                    elif remote_parts[i] < local_parts[i]:
                        break
                
                log('info', f"版本检查(GitHub回退): 本地版本 {settings.version['local_version']}, 远程版本 {settings.version['remote_version']}, 有更新: {settings.version['has_update']}")
            else:
                log('warning', f"无法获取GitHub版本信息，HTTP状态码: {response.status_code}")
                
    except Exception as e:
        log('error', f"版本检查失败: {str(e)}")
        
    return settings.version['has_update']