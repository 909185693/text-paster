import subprocess
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', 'fix: 优化粘贴逻辑,先释放按键并删除已输入的数字再粘贴'])
