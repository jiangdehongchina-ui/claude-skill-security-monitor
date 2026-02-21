"""配置加载器 — 带模块级缓存"""
import yaml
import json
from pathlib import Path

_config_cache = {}
_whitelist_cache = {}


def get_config_dir():
    return Path(__file__).parent.parent / "config"


def load_config():
    """加载 permissions.yaml 和 patterns.yaml（带缓存）"""
    if _config_cache:
        return _config_cache

    config_dir = get_config_dir()

    with open(config_dir / "permissions.yaml", "r", encoding="utf-8") as f:
        permissions = yaml.safe_load(f)

    with open(config_dir / "patterns.yaml", "r", encoding="utf-8") as f:
        patterns = yaml.safe_load(f)

    _config_cache["permissions"] = permissions.get("permissions", {})
    _config_cache["patterns"] = patterns
    return _config_cache


def load_whitelist():
    """加载白名单（带缓存）"""
    if _whitelist_cache:
        return _whitelist_cache

    whitelist_file = get_config_dir() / "whitelist.json"
    if whitelist_file.exists():
        with open(whitelist_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            _whitelist_cache.update(data)
            return _whitelist_cache

    _whitelist_cache["version"] = "1.0"
    _whitelist_cache["entries"] = []
    return _whitelist_cache
