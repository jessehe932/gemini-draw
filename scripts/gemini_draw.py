#!/usr/bin/env python3
"""
gemini_draw.py - gemini-draw 正式入口

正式入口只走一条生产主线：
- 独立 profile
- headless 后台执行
- 不连接 localhost:9222
- 不接管系统 Chrome
"""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from gemini_draw.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
