#!/usr/bin/env python3
"""
init_login.py - 初始化登录（一次性）

使用普通系统 Google Chrome 打开隔离 profile，
避免 Playwright/自动化参数触发 Google 的不安全浏览器拦截。

用户只需运行一次：手动在 Chrome 里登录 Google 账号，
然后关闭这个专属窗口。登录态会永久保存在专属目录中。

以后 gemini_draw.py 运行时直接复用这个登录态。
"""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from gemini_draw.login_init import main

if __name__ == "__main__":
    main()
