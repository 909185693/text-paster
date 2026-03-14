"""
系统托盘管理器
"""
import threading
import pystray
from PIL import Image, ImageDraw, ImageFont
from typing import Callable, Optional


class SystemTrayManager:
    """系统托盘管理器"""

    def __init__(self, show_window_callback: Callable, exit_callback: Callable):
        """
        初始化托盘管理器

        Args:
            show_window_callback: 显示窗口的回调函数
            exit_callback: 退出应用的回调函数
        """
        self.show_window_callback = show_window_callback
        self.exit_callback = exit_callback
        self.icon: Optional[pystray.Icon] = None
        self.icon_thread = None

    def create_icon_image(self) -> Image.Image:
        """创建托盘图标"""
        # 创建一个简单的图标
        width = 64
        height = 64
        image = Image.new('RGB', (width, height), color='white')

        # 绘制边框
        draw = ImageDraw.Draw(image)
        draw.rectangle([(0, 0), (width-1, height-1)], outline='#0078d7', width=3)

        # 绘制一个简单的 "T" 字母
        draw.rectangle([(20, 10), (44, 25)], fill='#0078d7')  # 顶部横线
        draw.rectangle([(28, 10), (36, 54)], fill='#0078d7')  # 竖线

        return image

    def on_clicked(self, icon, item):
        """托盘图标点击事件"""
        self.show_window_callback()

    def on_exit(self, icon, item):
        """退出事件"""
        self.exit_callback()
        icon.stop()

    def create_tray_icon(self):
        """创建托盘图标"""
        # 创建图标图片
        icon_image = self.create_icon_image()

        # 创建菜单
        menu = pystray.Menu(
            pystray.MenuItem('显示窗口', self.on_clicked),
            pystray.MenuItem('退出', self.on_exit)
        )

        # 创建托盘图标
        self.icon = pystray.Icon(
            'text_paster',
            icon_image,
            '文本快速粘贴工具',
            menu
        )

        # 运行托盘图标
        self.icon.run()

    def start(self):
        """启动托盘图标"""
        # 在单独的线程中运行托盘图标
        self.icon_thread = threading.Thread(target=self.create_tray_icon, daemon=True)
        self.icon_thread.start()

    def stop(self):
        """停止托盘图标"""
        if self.icon:
            self.icon.stop()
