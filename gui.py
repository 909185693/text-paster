"""
图形界面
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from typing import Optional, TYPE_CHECKING
from models import ConfigManager, TextItem
from pynput import keyboard

if TYPE_CHECKING:
    from tray_manager import SystemTrayManager


class TextPasterGUI:
    """文本粘贴工具 GUI"""

    def __init__(self, root, config_manager=None):
        self.root = root
        self.root.title("文本快速粘贴工具 v1.0")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # 使用传入的 config_manager 或创建新的
        self.config_manager = config_manager if config_manager else ConfigManager()
        self.selected_index = None
        self.hotkey_callbacks = {}
        self.tray_manager = None
        self.capturing_hotkey = False
        self.on_data_changed = None  # 数据变更回调

        self.setup_ui()
        self.refresh_item_list()

        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """设置界面"""
        # 顶部框架 - 支持扩展以适应窗口最大化
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            top_frame,
            text="📝 文本快速粘贴工具",
            font=("Microsoft YaHei", 16, "bold")
        )
        title_label.pack(pady=(0, 10))

        # 添加/编辑区域
        add_frame = ttk.LabelFrame(top_frame, text="添加/编辑文本条目", padding="10")
        add_frame.pack(fill=tk.X, pady=(0, 10))

        # 名称输入
        ttk.Label(add_frame, text="分类:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.name_entry = ttk.Entry(add_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=(0, 10))

        # 快捷键输入
        ttk.Label(add_frame, text="快捷键:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        hotkey_input_frame = ttk.Frame(add_frame)
        hotkey_input_frame.grid(row=0, column=3, padx=(0, 10))
        self.hotkey_entry = ttk.Entry(hotkey_input_frame, width=20)
        self.hotkey_entry.pack(side=tk.LEFT)
        ttk.Button(hotkey_input_frame, text="拾取", width=6, command=self.start_hotkey_capture).pack(side=tk.LEFT, padx=(5, 0))

        # 文本内容
        ttk.Label(add_frame, text="文本内容:").grid(row=1, column=0, sticky=tk.NW, padx=(0, 5), pady=(10, 0))
        self.text_content = scrolledtext.ScrolledText(add_frame, width=70, height=5, wrap=tk.WORD)
        self.text_content.grid(row=1, column=1, columnspan=3, sticky=tk.EW, pady=(10, 0))

        # 按钮区域
        btn_frame = ttk.Frame(add_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=(10, 0))

        ttk.Button(btn_frame, text="添加", command=self.add_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="更新", command=self.update_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="删除", command=self.remove_item).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清空", command=self.clear_form).pack(side=tk.LEFT, padx=(0, 5))

        # 列表区域
        list_frame = ttk.LabelFrame(top_frame, text="文本条目列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 创建 Treeview
        columns = ("enabled", "hotkey", "name", "text_preview")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("enabled", text="启用")
        self.tree.heading("hotkey", text="快捷键")
        self.tree.heading("name", text="分类")
        self.tree.heading("text_preview", text="文本预览")

        self.tree.column("enabled", width=60, anchor=tk.CENTER, minwidth=60)
        self.tree.column("hotkey", width=120, anchor=tk.CENTER, minwidth=120)
        self.tree.column("name", width=150, anchor=tk.W, minwidth=100)
        self.tree.column("text_preview", width=300, anchor=tk.W, minwidth=200)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", self.on_double_click)

        # 底部按钮
        bottom_frame = ttk.Frame(self.root, padding="10")
        bottom_frame.pack(fill=tk.X)

        ttk.Button(bottom_frame, text="全部启用", command=self.enable_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bottom_frame, text="全部禁用", command=self.disable_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bottom_frame, text="刷新配置", command=self.refresh_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(bottom_frame, text=" | ").pack(side=tk.LEFT)
        ttk.Button(bottom_frame, text="最小化到托盘", command=self.minimize_to_tray).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bottom_frame, text="退出", command=self.root.quit).pack(side=tk.LEFT)

        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X)

    def refresh_item_list(self):
        """刷新条目列表"""
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 添加条目
        for idx, item in enumerate(self.config_manager.items):
            text_preview = item.text[:50] + "..." if len(item.text) > 50 else item.text
            enabled_str = "✓" if item.enabled else "✗"

            self.tree.insert("", tk.END, values=(
                enabled_str,
                item.hotkey,
                item.name,
                text_preview
            ), tags=(str(idx),))

    def on_select(self, event):
        """选择事件"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            item_tags = self.tree.item(item_id, "tags")
            if item_tags:
                index = int(item_tags[0])
                self.selected_index = index
                self.load_item_to_form(index)

    def on_double_click(self, event):
        """双击事件"""
        selection = self.tree.selection()
        if selection:
            item_id = selection[0]
            item_tags = self.tree.item(item_id, "tags")
            if item_tags:
                index = int(item_tags[0])
                # 切换启用状态
                self.config_manager.items[index].enabled = not self.config_manager.items[index].enabled
                self.config_manager.save()
                self.refresh_item_list()

                # 通知数据变更,重新加载快捷键
                if self.on_data_changed:
                    self.on_data_changed()

    def load_item_to_form(self, index: int):
        """加载条目到表单"""
        if 0 <= index < len(self.config_manager.items):
            item = self.config_manager.items[index]
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, item.name)

            self.hotkey_entry.delete(0, tk.END)
            self.hotkey_entry.insert(0, item.hotkey)

            self.text_content.delete(1.0, tk.END)
            self.text_content.insert(1.0, item.text)

    def clear_form(self):
        """清空表单"""
        self.name_entry.delete(0, tk.END)
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, "ctrl+alt+")
        self.text_content.delete(1.0, tk.END)
        self.selected_index = None

    def start_hotkey_capture(self):
        """开始快捷键捕获"""
        if self.capturing_hotkey:
            return

        self.capturing_hotkey = True
        self.captured_keys = []  # 记录捕获的键

        # 显示捕获提示
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, "按下快捷键...")
        self.hotkey_entry.config(state=tk.DISABLED)
        self.status_var.set("请按下快捷键组合(如 Ctrl+Alt+1)...")

        def on_press(key):
            if not self.capturing_hotkey:
                return False

            # 获取键的规范化名称
            key_name = None

            if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                key_name = 'ctrl'
            elif key in (keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r):
                key_name = 'alt'
            elif key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
                key_name = 'shift'
            elif hasattr(key, 'char') and key.char:
                # 移除 isprintable() 检查，直接使用所有字符键
                key_name = key.char.lower()
            elif hasattr(key, 'vk') and key.vk:
                # 处理数字键 (VK 48-57: 0-9)
                if 48 <= key.vk <= 57:
                    key_name = str(key.vk - 48)
                # 处理小键盘数字键 (VK 96-105: 0-9)
                elif 96 <= key.vk <= 105:
                    key_name = str(key.vk - 96)
                # 处理小键盘运算符
                elif key.vk == 106:
                    key_name = '*'
                elif key.vk == 107:
                    key_name = '+'
                elif key.vk == 108:
                    key_name = 'enter'
                elif key.vk == 109:
                    key_name = '-'
                elif key.vk == 110:
                    key_name = '.'
                elif key.vk == 111:
                    key_name = '/'

            if key_name and key_name not in self.captured_keys:
                self.captured_keys.append(key_name)

            # 显示当前捕获的键
            if self.captured_keys:
                display_text = '+'.join(self.captured_keys)
                self.hotkey_entry.config(state=tk.NORMAL)
                self.hotkey_entry.delete(0, tk.END)
                self.hotkey_entry.insert(0, display_text)
                self.hotkey_entry.config(state=tk.DISABLED)

            return True

        def on_release(key):
            if not self.capturing_hotkey:
                return False

            # 当所有键都释放时,完成捕获
            # 简单判断:如果捕获了多个键,假设是完整组合
            if len(self.captured_keys) >= 2:
                # 延迟一下再停止,确保捕获完整
                import threading
                def finish_capture():
                    import time
                    time.sleep(0.1)
                    if self.capturing_hotkey:
                        self.capturing_hotkey = False
                        hotkey_str = '+'.join(self.captured_keys)
                        self.hotkey_entry.config(state=tk.NORMAL)
                        self.hotkey_entry.delete(0, tk.END)
                        self.hotkey_entry.insert(0, hotkey_str)
                        self.status_var.set(f"已捕获快捷键: {hotkey_str}")

                thread = threading.Thread(target=finish_capture, daemon=True)
                thread.start()
                return False

            return True

        # 启动监听器
        self.listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self.listener.start()

    def add_item(self):
        """添加条目"""
        name = self.name_entry.get().strip()
        hotkey = self.hotkey_entry.get().strip()
        text = self.text_content.get(1.0, tk.END).strip()

        if not name or not hotkey or not text:
            messagebox.showwarning("警告", "请填写完整信息!")
            return

        # 检查快捷键是否重复
        for item in self.config_manager.items:
            if item.hotkey.lower() == hotkey.lower():
                messagebox.showerror("错误", f"快捷键 '{hotkey}' 已存在!")
                return

        item = TextItem(name=name, text=text, hotkey=hotkey, enabled=True)
        self.config_manager.add_item(item)
        self.refresh_item_list()
        self.clear_form()
        self.status_var.set(f"已添加: {name}")

        # 通知数据变更,重新加载快捷键
        if self.on_data_changed:
            self.on_data_changed()

    def update_item(self):
        """更新条目"""
        if self.selected_index is None:
            messagebox.showwarning("警告", "请先选择要更新的条目!")
            return

        name = self.name_entry.get().strip()
        hotkey = self.hotkey_entry.get().strip()
        text = self.text_content.get(1.0, tk.END).strip()

        if not name or not hotkey or not text:
            messagebox.showwarning("警告", "请填写完整信息!")
            return

        # 检查快捷键是否重复
        for idx, item in enumerate(self.config_manager.items):
            if idx != self.selected_index and item.hotkey.lower() == hotkey.lower():
                messagebox.showerror("错误", f"快捷键 '{hotkey}' 已存在!")
                return

        item = TextItem(name=name, text=text, hotkey=hotkey, enabled=True)
        self.config_manager.update_item(self.selected_index, item)
        self.refresh_item_list()
        self.status_var.set(f"已更新: {name}")

        # 通知数据变更,重新加载快捷键
        if self.on_data_changed:
            self.on_data_changed()

    def remove_item(self):
        """删除条目"""
        if self.selected_index is None:
            messagebox.showwarning("警告", "请先选择要删除的条目!")
            return

        item = self.config_manager.items[self.selected_index]
        if messagebox.askyesno("确认", f"确定要删除 '{item.name}' 吗?"):
            self.config_manager.remove_item(self.selected_index)
            self.refresh_item_list()
            self.clear_form()
            self.status_var.set(f"已删除: {item.name}")

            # 通知数据变更,重新加载快捷键
            if self.on_data_changed:
                self.on_data_changed()

    def enable_all(self):
        """全部启用"""
        for item in self.config_manager.items:
            item.enabled = True
        self.config_manager.save()
        self.refresh_item_list()
        self.status_var.set("已全部启用")

        # 通知数据变更,重新加载快捷键
        if self.on_data_changed:
            self.on_data_changed()

    def disable_all(self):
        """全部禁用"""
        for item in self.config_manager.items:
            item.enabled = False
        self.config_manager.save()
        self.refresh_item_list()
        self.status_var.set("已全部禁用")

        # 通知数据变更,重新加载快捷键
        if self.on_data_changed:
            self.on_data_changed()

    def refresh_config(self):
        """刷新配置 - 重新从文件加载配置"""
        try:
            # 重新加载配置文件
            self.config_manager.load()
            # 刷新界面列表
            self.refresh_item_list()
            # 清空表单
            self.clear_form()
            # 更新状态栏
            self.status_var.set("配置已刷新")

            # 通知数据变更,重新加载快捷键
            if self.on_data_changed:
                self.on_data_changed()

            messagebox.showinfo("成功", "配置已重新加载!")
        except Exception as e:
            messagebox.showerror("错误", f"刷新配置失败: {e}")
            print(f"[ERROR] Refresh config failed: {e}")

    def minimize_to_tray(self):
        """最小化到托盘"""
        self.root.withdraw()
        self.status_var.set("已最小化到托盘")

    def show_window(self):
        """显示窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def set_tray_manager(self, tray_manager: 'SystemTrayManager'):
        """设置托盘管理器"""
        self.tray_manager = tray_manager

    def on_closing(self):
        """窗口关闭事件"""
        # 最小化到托盘而不是关闭
        self.minimize_to_tray()

    def exit_app(self):
        """退出应用"""
        if self.tray_manager:
            self.tray_manager.stop()
        self.root.quit()


def main():
    """主函数"""
    root = tk.Tk()
    app = TextPasterGUI(root)  # 独立运行时创建自己的 config_manager
    root.mainloop()


if __name__ == "__main__":
    main()
