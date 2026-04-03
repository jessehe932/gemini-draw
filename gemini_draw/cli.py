"""
gemini-draw 的独立 CLI 入口。
"""

from __future__ import annotations

import argparse

from .gemini_draw import draw


def main() -> int:
    parser = argparse.ArgumentParser(description="Gemini 后台生图 CLI")
    parser.add_argument("--prompt", required=True, help="图片提示词")
    parser.add_argument("--output-dir", default=None, help="输出目录")
    parser.add_argument("--timeout", type=int, default=400, help="超时秒数")
    args = parser.parse_args()

    result = draw(prompt=args.prompt, output_dir=args.output_dir, timeout=args.timeout)
    print(result["image_path"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
