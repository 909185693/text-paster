"""
测试简化模式的按键触发
模拟按键序列：
1. Ctrl+Alt+1（完整组合）
2. 保持 Ctrl+Alt，按 2（简化模式）
3. 保持 Ctrl+Alt，按 3（简化模式）
4. 释放所有键
5. Ctrl+Alt+1（重新需要完整组合）
"""
import time
from pynput import keyboard

def simulate_sequence():
    """模拟按键序列"""
    controller = keyboard.Controller()

    print("\n[TEST 1] 完整组合：Ctrl+Alt+1")
    controller.press(Key.ctrl)
    controller.press(Key.alt)
    controller.press('1')
    time.sleep(0.1)
    controller.release('1')
    controller.release(Key.alt)
    controller.release(Key.ctrl)
    time.sleep(0.5)

    print("\n[TEST 2] 简化模式：保持 Ctrl+Alt，按 2")
    controller.press(Key.ctrl)
    controller.press(Key.alt)
    time.sleep(0.1)
    controller.press('2')
    time.sleep(0.1)
    controller.release('2')
    controller.release(Key.alt)
    controller.release(Key.ctrl)
    time.sleep(0.5)

    print("\n[TEST 3] 简化模式：保持 Ctrl+Alt，按 3")
    controller.press(Key.ctrl)
    controller.press(Key.alt)
    time.sleep(0.1)
    controller.press('3')
    time.sleep(0.1)
    controller.release('3')
    controller.release(Key.alt)
    controller.release(Key.ctrl)
    time.sleep(0.5)

    print("\n[TEST 4] 只按 Ctrl+1（不应该触发）")
    controller.press(Key.ctrl)
    time.sleep(0.1)
    controller.press('1')
    time.sleep(0.1)
    controller.release('1')
    controller.release(Key.ctrl)
    time.sleep(0.5)

    print("\n[TEST 5] 只按 Alt+1（不应该触发）")
    controller.press(Key.alt)
    time.sleep(0.1)
    controller.press('1')
    time.sleep(0.1)
    controller.release('1')
    controller.release(Key.alt)
    time.sleep(0.5)

    print("\n测试完成！")

if __name__ == "__main__":
    print("5秒后开始测试...")
    time.sleep(5)
    simulate_sequence()
