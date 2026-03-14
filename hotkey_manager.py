"""
Global Hotkey Manager
"""
from pynput import keyboard
from pynput.keyboard import Key, KeyCode
import pyperclip
import time


class HotkeyManager:
    """Hotkey Manager - 标准组合键实现"""

    def __init__(self, on_hotkey_press):
        """
        Initialize
        :param on_hotkey_press: Callback when hotkey is pressed
        """
        self.on_hotkey_press = on_hotkey_press
        self.hotkey_map = {}  # {hotkey_str: callback}
        self.pressed_keys = set()  # 当前按下的键
        self.triggered_hotkeys = set()  # 本次按键周期已触发的快捷键

    def register_hotkeys(self, hotkey_map: dict):
        """
        Register hotkeys
        :param hotkey_map: {hotkey_str: callback}
        """
        self.hotkey_map = hotkey_map
        print(f"[DEBUG] Registering {len(hotkey_map)} hotkeys...")

    def on_press(self, key):
        """Key press event handler"""
        try:
            # 规范化按键
            normalized = self._normalize_key(key)
            if normalized is None:
                return

            # 忽略已经按下的键(按键重复)
            if normalized in self.pressed_keys:
                return

            self.pressed_keys.add(normalized)

            # 检查所有已注册的快捷键
            for hotkey_str, callback in self.hotkey_map.items():
                if self._check_hotkey(hotkey_str):
                    # 检查是否已经触发过该快捷键
                    if hotkey_str not in self.triggered_hotkeys:
                        print(f"[TRIGGERED] Hotkey: {hotkey_str}")
                        self.triggered_hotkeys.add(hotkey_str)
                        callback()
                    break

        except Exception as e:
            print(f"[ERROR] on_press error: {e}")

    def on_release(self, key):
        """Key release event handler"""
        try:
            normalized = self._normalize_key(key)
            if normalized and normalized in self.pressed_keys:
                self.pressed_keys.remove(normalized)

            # 当所有键都释放时,清空已触发的快捷键记录
            if not self.pressed_keys:
                self.triggered_hotkeys.clear()

        except Exception as e:
            print(f"[ERROR] on_release error: {e}")

    def _normalize_key(self, key):
        """规范化键对象用于比较"""
        if isinstance(key, KeyCode):
            if hasattr(key, 'char') and key.char:
                return ('char', key.char.lower())
            elif hasattr(key, 'vk') and key.vk:
                # VK值映射
                vk_map = {
                    49: '1', 50: '2', 51: '3', 52: '4', 53: '5',
                    54: '6', 55: '7', 56: '8', 57: '9', 48: '0',
                    96: '0', 97: '1', 98: '2', 99: '3', 100: '4',
                    101: '5', 102: '6', 103: '7', 104: '8', 105: '9',
                    106: '*', 107: '+', 109: '-', 110: '.', 111: '/'
                }
                if key.vk in vk_map:
                    return ('char', vk_map[key.vk])
        elif isinstance(key, Key):
            if key in (Key.ctrl, Key.ctrl_l, Key.ctrl_r):
                return ('modifier', 'ctrl')
            elif key in (Key.alt, Key.alt_l, Key.alt_r, Key.alt_gr):
                return ('modifier', 'alt')
            elif key in (Key.shift, Key.shift_l, Key.shift_r):
                return ('modifier', 'shift')
            elif key in (Key.cmd, Key.cmd_l, Key.cmd_r):
                return ('modifier', 'cmd')
        return None

    def _check_hotkey(self, hotkey_str):
        """
        检查当前按下的键是否匹配快捷键组合
        """
        # 解析快捷键字符串
        parts = [p.strip().lower() for p in hotkey_str.split('+')]

        # 构建快捷键的目标键集合
        target_keys = []
        for part in parts:
            if part == 'ctrl':
                target_keys.append(('modifier', 'ctrl'))
            elif part == 'alt':
                target_keys.append(('modifier', 'alt'))
            elif part == 'shift':
                target_keys.append(('modifier', 'shift'))
            elif part == 'win' or part == 'cmd' or part == 'meta':
                target_keys.append(('modifier', 'cmd'))
            elif len(part) == 1:
                target_keys.append(('char', part.lower()))

        # 检查当前按键是否匹配目标快捷键
        return sorted(list(self.pressed_keys)) == sorted(target_keys)

    def start(self):
        """Start listening"""
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
        print(f"[OK] Hotkey listener started... {len(self.hotkey_map)} hotkeys registered")

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
        Paste text using keyboard simulation with backspace to clean up
        :param text: Text to paste
        """
        try:
            # Save current clipboard
            old_clipboard = pyperclip.paste()
        except:
            old_clipboard = None

        try:
            controller = keyboard.Controller()

            # First, release all modifier keys and digit keys to stop autorepeat
            controller.release(Key.ctrl)
            controller.release(Key.alt)
            controller.release(Key.shift)
            controller.release(Key.cmd)

            # Release digit keys to stop any autorepeat
            for digit in '0123456789':
                try:
                    controller.release(KeyCode.from_char(digit))
                except:
                    pass

            # 增加延迟,确保所有按键都完全释放
            time.sleep(0.1)

            # Press Backspace once to delete the digit that was typed
            controller.press(Key.backspace)
            controller.release(Key.backspace)

            # 增加延迟,确保 backspace 被正确处理
            time.sleep(0.1)

            # Now set new content to clipboard
            pyperclip.copy(text)

            # Wait for clipboard to update
            time.sleep(0.05)

            # Simulate Ctrl+V paste
            controller.press(Key.ctrl)
            controller.press(KeyCode.from_char('v'))
            controller.release(KeyCode.from_char('v'))
            controller.release(Key.ctrl)

            # Wait for paste to complete
            time.sleep(0.1)

            print(f"[OK] Pasted text: {text[:30]}...")

        except Exception as e:
            print(f"[ERROR] Paste failed: {e}")
            import traceback
            traceback.print_exc()
