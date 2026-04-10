"""
deep_paper 包初始化
提供 load_config() 工厂函数，统一读取 config.json
"""
from __future__ import annotations
import json
from pathlib import Path
from functools import lru_cache


# config.json 位于 deep_paper 包目录（即与 __init__.py 同级）
_CONFIG_PATH = Path(__file__).parent / "config.json"


@lru_cache(maxsize=1)
def load_config() -> dict:
    """读取并缓存 config.json，返回完整配置字典"""
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"config.json not found at {_CONFIG_PATH}. "
            "请确认当前目录已包含有效的 config.json"
        )
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


__all__ = ["load_config"]
