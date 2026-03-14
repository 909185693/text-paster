import subprocess
subprocess.run(['git', 'add', '-A'])
subprocess.run(['git', 'commit', '-m', 'fix: 修复粘贴时数字键被输入的问题'])
