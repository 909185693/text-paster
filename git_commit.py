import subprocess
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', 'fix: 在粘贴前使用Backspace删除已输入的数字键'])
