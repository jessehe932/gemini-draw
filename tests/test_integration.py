"""
tests/test_integration.py - gemini-draw E2E 验收入口

运行方式：
    cd /path/to/gemini-draw
    python3 -m tests.test_integration --prompt "一只橘猫"

说明：
1. 不再要求 killall "Google Chrome"
2. 不再要求手动启动 localhost:9222
3. 只验证正式生产主线：独立 profile + headless + OS 文件审计
"""

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from gemini_draw import draw


def main() -> int:
    parser = argparse.ArgumentParser(description="gemini-draw E2E 验收入口")
    parser.add_argument("--prompt", default="一只可爱的橘猫", help="图片生成 Prompt")
    parser.add_argument("--output-dir", default=None, help="输出目录")
    parser.add_argument("--timeout", type=int, default=400, help="超时秒数")
    args = parser.parse_args()

    try:
        result = draw(prompt=args.prompt, output_dir=args.output_dir, timeout=args.timeout)
        size_bytes = os.path.getsize(result["image_path"])
        print("✅ E2E 验收通过")
        print(f"Prompt: {result['prompt']}")
        print(f"结果: {result['image_path']}")
        print(f"【OS 审计：文件路径: {result['image_path']}, 大小: {size_bytes} bytes】")
        return 0
    except Exception:
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
