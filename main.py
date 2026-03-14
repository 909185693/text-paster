"""
文本快速粘贴工具 - 主程序
"""
import tkinter as tk
from tkinter import messagebox
import threading
import time
from models import ConfigManager
from hotkey_manager import HotkeyManager, ClipboardManager
from gui import TextPasterGUI
from tray_manager import SystemTrayManager


class TextPasterApp:
    """文本粘贴工具应用"""

    def __init__(self):
        self.config_manager = ConfigManager()
        self.hotkey_manager = None
        self.clipboard_manager = ClipboardManager()

        # 创建 GUI，传入共享的 config_manager
        self.root = tk.Tk()
        self.gui = TextPasterGUI(self.root, config_manager=self.config_manager)
        # 设置数据变更回调,重新加载快捷键
        self.gui.on_data_changed = self.reload_hotkeys

        # 创建并启动系统托盘
        self.tray_manager = SystemTrayManager(
            show_window_callback=self.show_window,
            exit_callback=self.exit_app
        )
        self.gui.set_tray_manager(self.tray_manager)
        self.tray_manager.start()

        # 启动快捷键监听
        self.start_hotkey_listener()

    def start_hotkey_listener(self):
        """启动快捷键监听"""
        # 创建热键映射
        hotkey_map = {}
        for item in self.config_manager.items:
            if item.enabled:
                # 使用闭包捕获变量
                def make_callback(text, hotkey):
                    return lambda: self.paste_text(hotkey, text)

                hotkey_map[item.hotkey] = make_callback(item.text, item.hotkey)

        # 初始化快捷键管理器
        self.hotkey_manager = HotkeyManager(None)
        self.hotkey_manager.register_hotkeys(hotkey_map)

        # 在单独的线程中启动监听
        thread = threading.Thread(target=self.hotkey_manager.start, daemon=True)
        thread.start()

        print(f"[OK] Registered {len(hotkey_map)} hotkeys")

        # 显示快捷键列表
        for item in self.config_manager.items:
            if item.enabled:
                print(f"[{item.hotkey:20s}] -> {item.name}")

    def reload_hotkeys(self):
        """重新加载快捷键"""
        print("\n[RELOAD] Reloading hotkeys...")

        # 重新加载配置文件
        self.config_manager.load()
        print(f"[RELOAD] Loaded {len(self.config_manager.items)} items from config")

        # 停止旧的监听器
        if self.hotkey_manager:
            self.hotkey_manager.stop()

        # 重新启动监听器
        self.start_hotkey_listener()

        print("[OK] Hotkeys reloaded\n")

    def paste_text(self, hotkey: str, text: str):
        """粘贴文本"""
        # 更新 GUI 状态
        self.gui.status_var.set(f"Pasted: {text[:30]}...")

        try:
            # 获取当前激活窗口
            import win32gui
            foreground_window = win32gui.GetForegroundWindow()

            # 将窗口提到前台
            try:
                win32gui.SetForegroundWindow(foreground_window)
            except:
                pass

            # 短暂延迟确保窗口获得焦点
            time.sleep(0.05)

            # 粘贴文本
            self.clipboard_manager.paste_text(text)

            # 更新 GUI 状态为成功
            self.root.after(100, lambda: self.gui.status_var.set(f"OK: Pasted {text[:20]}..."))

        except Exception as e:
            error_msg = f"Paste failed: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.gui.status_var.set(error_msg)

            # 在 GUI 中显示错误
            self.root.after(100, lambda: messagebox.showerror("Error", error_msg))

    def show_window(self):
        """显示窗口"""
        self.gui.show_window()

    def exit_app(self):
        """退出应用"""
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        if self.tray_manager:
            self.tray_manager.stop()
        self.gui.exit_app()

    def run(self):
        """运行应用"""
        try:
            print("\n" + "="*50)
            print("Text Paster Tool Started")
            print("="*50)
            print("Tips:")
            print("  - Click any text box")
            print("  - Press hotkey to paste")
            print("  - Double-click list item to enable/disable")
            print("="*50 + "\n")

            self.root.mainloop()
        finally:
            if self.hotkey_manager:
                self.hotkey_manager.stop()
            print("\nText Paster Tool Exited")


def main():
    """主函数"""
    try:
        app = TextPasterApp()
        app.run()
    except KeyboardInterrupt:
        print("\nProgram interrupted")
    except Exception as e:
        print(f"Program error: {e}")
        import traceback
        traceback.print_exc()
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Error", f"Program error:\n\n{str(e)}")
        root.destroy()


if __name__ == "__main__":
    main()
