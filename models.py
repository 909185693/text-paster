"""
数据模型定义
"""
import json
from dataclasses import dataclass, asdict
from typing import List, Optional
from pathlib import Path
import os
import sys


@dataclass
class TextItem:
    """文本条目"""
    name: str  # 名称
    text: str  # 文本内容
    hotkey: str  # 快捷键组合,如 "ctrl+alt+1"
    enabled: bool = True  # 是否启用

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # 使用用户目录保存配置,避免打包后路径问题
            if getattr(sys, 'frozen', False):
                # 打包后的 EXE
                config_dir = Path.home() / '.text-paster'
            else:
                # 开发环境
                config_dir = Path(__file__).parent

            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "config.json"

        self.config_path = Path(config_path)
        self.items: List[TextItem] = []
        self.load()

    def load(self):
        """加载配置"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.items = [TextItem.from_dict(item) for item in data.get('items', [])]
            except Exception as e:
                print(f"加载配置失败: {e}")
                self.items = []
        else:
            # 默认示例数据
            self.items = [
                TextItem(
                    name="邮箱地址",
                    text="myemail@example.com",
                    hotkey="ctrl+alt+1",
                    enabled=True
                ),
                TextItem(
                    name="自我介绍",
                    text="您好,我是一名全栈开发工程师,拥有5年开发经验。",
                    hotkey="ctrl+alt+2",
                    enabled=True
                ),
                TextItem(
                    name="项目经验",
                    text="我参与过多个大型项目开发,包括电商平台、管理系统等。",
                    hotkey="ctrl+alt+3",
                    enabled=True
                )
            ]
            self.save()

    def save(self):
        """保存配置"""
        data = {
            'items': [item.to_dict() for item in self.items]
        }
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_item(self, item: TextItem):
        """添加条目"""
        self.items.append(item)
        self.save()

    def remove_item(self, index: int):
        """删除条目"""
        if 0 <= index < len(self.items):
            self.items.pop(index)
            self.save()

    def update_item(self, index: int, item: TextItem):
        """更新条目"""
        if 0 <= index < len(self.items):
            self.items[index] = item
            self.save()

    def get_item_by_hotkey(self, hotkey: str) -> Optional[TextItem]:
        """根据快捷键获取条目"""
        for item in self.items:
            if item.enabled and item.hotkey.lower() == hotkey.lower():
                return item
        return None
