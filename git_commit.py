import subprocess
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', 'fix: 使用Windows API WM_PASTE消息粘贴,完全避免数字键输入干扰'])
