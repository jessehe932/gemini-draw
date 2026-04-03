"""
gemini-draw 的独立登录初始化入口。
"""

from __future__ import annotations

import shutil
import subprocess
import time
import os
from pathlib import Path

PROFILE_DIR = Path(
    os.environ.get("GEMINI_DRAW_PROFILE_DIR", Path.home() / ".config/gemini-draw/template-profile")
)
LEGACY_PROFILE_DIR = Path.home() / ".config/openclaw_gemini_bot_profile"
GEMINI_URL = "https://gemini.google.com"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def ensure_template_profile() -> None:
    if PROFILE_DIR.exists():
        return
    if not LEGACY_PROFILE_DIR.exists():
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        return

    def ignore(_: str, names: list[str]) -> set[str]:
        ignored = {
            "SingletonCookie",
            "SingletonLock",
            "SingletonSocket",
            "RunningChromeVersion",
            "Crashpad",
            "ShaderCache",
            "GrShaderCache",
            "GraphiteDawnCache",
            "GPUCache",
            "Code Cache",
        }
        return {name for name in names if name in ignored}

    shutil.copytree(LEGACY_PROFILE_DIR, PROFILE_DIR, dirs_exist_ok=True, ignore=ignore)


def main() -> None:
    ensure_template_profile()
    print(f"Profile 目录：{PROFILE_DIR}")
    print("接下来会打开一个普通 Chrome 窗口，用于一次性 Gemini 登录。")
    input("按回车继续...")
    proxy = os.environ.get("GEMINI_DRAW_PROXY_SERVER", "").strip()
    cmd = [
        CHROME_BIN,
        f"--user-data-dir={PROFILE_DIR}",
        "--window-size=1280,900",
        "--no-first-run",
        "--no-default-browser-check",
        GEMINI_URL,
    ]
    if proxy:
        cmd.insert(2, f"--proxy-server={proxy}")
    proc = subprocess.Popen(
        cmd
    )
    print("请手动完成登录，然后关闭这个 Chrome 窗口。")
    while proc.poll() is None:
        time.sleep(1)


if __name__ == "__main__":
    main()
