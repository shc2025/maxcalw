#!/usr/bin/env python3
"""安装 yfinance"""
import subprocess, sys
# 用 bootstrap pip
p = subprocess.run([
    sys.executable, "/tmp/pip.pyz", "install", "yfinance", "--quiet"
], capture_output=True, text=True, timeout=60)
print("stdout:", p.stdout[:200])
print("stderr:", p.stderr[:200])
print("returncode:", p.returncode)
# 测试
p2 = subprocess.run([sys.executable, "-c", "import yfinance; print('yfinance', yfinance.__version__)"],
                    capture_output=True, text=True, timeout=15)
print("import test:", p2.stdout, p2.stderr[:100])
