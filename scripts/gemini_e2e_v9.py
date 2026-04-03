#!/usr/bin/env python3
"""
gemini_e2e_v9.py - gemini-draw 最终 E2E 验收入口

要求：
1. 只走正式生产主线，不再维护第二套浏览器控制逻辑。
2. 默认后台静默执行，不碰系统 Chrome。
3. 成功标准是拿到真实下载文件，并输出 OS 文件审计。
"""

import argparse
import os
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))

from gemini_draw import draw


def main() -> int:
    parser = argparse.ArgumentParser(description="Gemini E2E V9（最终统一版）")
    parser.add_argument(
        "--prompt",
        default="A cyberpunk cat with neon lights, ultra detailed, 4K, cinematic lighting",
        help="图片生成 Prompt",
    )
    parser.add_argument("--output-dir", default=None, help="输出目录")
    parser.add_argument("--timeout", type=int, default=400, help="超时秒数")
    args = parser.parse_args()

    try:
        result = draw(prompt=args.prompt, output_dir=args.output_dir, timeout=args.timeout)
        size_bytes = os.path.getsize(result["image_path"])
        print("✅ Gemini E2E V9 验收通过")
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
