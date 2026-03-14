"""
Global Hotkey Manager
"""
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
import pyperclip
import time


class HotkeyManager:
    """Hotkey Manager - 手动实现快捷键检测"""

    def __init__(self, on_hotkey_press):
        """
        Initialize
        :param on_hotkey_press: Callback when hotkey is pressed
        """
        self.on_hotkey_press = on_hotkey_press
        self.listener = None
        self.hotkey_callbacks = {}  # {hotkey_str: callback}
        self.pressed_keys = set()  # 当前按下的键

    def parse_hotkey(self, hotkey_str: str) -> list:
        """
        Parse hotkey string to list of keys (支持左右Ctrl/Alt)
        :param hotkey_str: e.g., "ctrl+alt+1" or "ctrl+shift+a"
        :return: List of key values for comparison
        """
        parts = [p.strip().lower() for p in hotkey_str.split('+')]
        keys = []

        for part in parts:
            if part == 'ctrl':
                # 支持左Ctrl和右Ctrl
                keys.append(('modifier', 'ctrl'))
            elif part == 'alt':
                # 支持左Alt、右Alt和AltGr
                keys.append(('modifier', 'alt'))
            elif part == 'shift':
                keys.append(('modifier', 'shift'))
            elif part == 'win' or part == 'cmd' or part == 'meta':
                keys.append(('modifier', 'win'))
            elif len(part) == 1:
                # 字符键
                keys.append(('char', part))
            elif part.startswith('f') and part[1:].isdigit():
                # F1-F12
                keys.append(('key', f'f{part[1:]}'))

        return keys

    def normalize_key(self, key):
        """规范化键对象返回可比较的值"""
        if isinstance(key, KeyCode):
            # 检查是否是字符键
            if hasattr(key, 'char') and key.char:
                return ('char', key.char.lower())
            else:
                # 检查VK值
                vk_map = {
                    49: '1', 50: '2', 51: '3', 52: '4', 53: '5',
                    54: '6', 55: '7', 56: '8', 57: '9', 48: '0'
                }
                if key.vk in vk_map:
                    return ('char', vk_map[key.vk])
                return None
        elif isinstance(key, Key):
            # 检查修饰键
            if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
                return ('modifier', 'ctrl')
            elif key in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
                return ('modifier', 'alt')
            elif key in (Key.shift, Key.shift_l, Key.shift_r):
                return ('modifier', 'shift')
            elif key in (Key.cmd, Key.cmd_l, Key.cmd_r):
                return ('modifier', 'win')

        return None

    def register_hotkeys(self, hotkey_map: dict):
        """
        Register hotkeys
        :param hotkey_map: {hotkey_str: callback}
        """
        self.hotkey_callbacks = {}
        for hotkey_str, callback in hotkey_map.items():
            # 解析快捷键
            parsed = self.parse_hotkey(hotkey_str)
            if parsed:
                self.hotkey_callbacks[hotkey_str] = {'callback': callback, 'parsed': parsed}
                print(f"[DEBUG] Registered hotkey: {hotkey_str} -> {parsed}")

    def on_press(self, key):
        """Key press event"""
        try:
            # 规范化键对象
            normalized = self.normalize_key(key)
            if not normalized:
                return

            # 忽略已经按下的键（按键重复）
            if normalized in self.pressed_keys:
                return

            self.pressed_keys.add(normalized)
            print(f"[PRESS] {key} -> {normalized}")
            print(f"  Pressed keys: {self.pressed_keys}")

            # 检查是否有快捷键匹配
            for hotkey_str, hotkey_data in self.hotkey_callbacks.items():
                parsed_hotkey = hotkey_data['parsed']
                if self.pressed_keys == set(parsed_hotkey):
                    # 每次按下都触发，像 Ctrl+V 一样
                    print(f"[TRIGGERED] Hotkey: {hotkey_str}")
                    callback = hotkey_data['callback']
                    callback()
                    break

        except Exception as e:
            print(f"[ERROR] on_press error: {e}")
            import traceback
            traceback.print_exc()

    def on_release(self, key):
        """Key release事件"""
        try:
            normalized = self.normalize_key(key)
            if normalized and normalized in self.pressed_keys:
                self.pressed_keys.remove(normalized)

                print(f"[RELEASE] {key} -> {normalized}")
                print(f"  Pressed keys: {self.pressed_keys}")
        except Exception as e:
            print(f"[ERROR] on_release error: {e}")

    def start(self):
        """Start listening"""
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.start()
        print(f"[OK] Hotkey listener started... {len(self.hotkey_callbacks)} hotkeys registered")

    def stop(self):
        """Stop listening"""
        if self.listener:
            self.listener.stop()
            print("[OK] Hotkey listener stopped")


class ClipboardManager:
    """Clipboard Manager"""

    @staticmethod
    def paste_text(text: str):
        """
        Paste text
        :param text: Text to paste
        """
        try:
            # Save current clipboard
            old_clipboard = pyperclip.paste()
        except:
            old_clipboard = None

        try:
            # Set new content to clipboard
            pyperclip.copy(text)

            # Wait for clipboard to update
            time.sleep(0.05)

            # Simulate Ctrl+V paste
            controller = keyboard.Controller()

            # Release all modifier keys first to avoid interference
            controller.release(Key.ctrl)
            controller.release(Key.alt)
            controller.release(Key.shift)
            controller.release(Key.cmd)

            # Short delay
            time.sleep(0.02)

            # Press and release Ctrl+V
            controller.press(Key.ctrl)
            controller.press(KeyCode.from_char('v'))
            controller.release(KeyCode.from_char('v'))
            controller.release(Key.ctrl)

            # Wait for paste to complete
            time.sleep(0.1)

            print(f"[OK] Pasted text: {text[:30]}...")

        except Exception as e:
            print(f"[ERROR] Paste failed: {e}")
