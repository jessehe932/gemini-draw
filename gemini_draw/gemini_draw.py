"""
gemini_draw.py - gemini-draw 统一生产主线

目标：
1. 默认后台静默运行，不碰用户正在使用的系统 Chrome。
2. 正式入口与 E2E 共用同一套独立 profile + headless 浏览器策略。
3. 只有拿到真实下载文件并通过 OS 文件审计，才算成功。
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .exceptions import ChromeConnectionError, GeminiDrawError, ImageDownloadError, ImageGenerationTimeout
from .utils import ensure_output_dir, get_logger, sanitize_filename

logger = get_logger(__name__)

PROFILE_DIR = Path(
    os.environ.get("GEMINI_DRAW_PROFILE_DIR", Path.home() / ".config/gemini-draw/template-profile")
)
LEGACY_PROFILE_DIR = Path.home() / ".config/openclaw_gemini_bot_profile"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
GEMINI_URL = "https://gemini.google.com/app"
OUTPUT_DIR = Path(os.environ.get("GEMINI_DRAW_OUTPUT_DIR", Path.home() / "Downloads/gemini-draw-output"))
DEFAULT_TIMEOUT_SECONDS = 400
MIN_ORIGINAL_BYTES = 8 * 1024 * 1024
DEBUG_DIR = Path("/tmp/gemini-draw-debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOAD_BUTTON_SCRIPT = """() => {
  function findAndClickDownload(root) {
    const visited = new Set();
    function walk(node) {
      if (!node || visited.has(node)) return null;
      visited.add(node);

      const list = node.querySelectorAll ? node.querySelectorAll('*') : [];
      for (const el of list) {
        const tag = el.tagName ? el.tagName.toLowerCase() : '';
        const aria = el.getAttribute ? (el.getAttribute('aria-label') || '') : '';
        if (tag === 'button' && /下载|download/i.test(aria)) {
          el.click();
          return aria || 'download';
        }
        if (el.shadowRoot) {
          const nested = walk(el.shadowRoot);
          if (nested) return nested;
        }
      }
      return null;
    }
    return walk(root);
  }
  return findAndClickDownload(document);
}"""


async def _launch_context() -> BrowserContext:
    try:
        _ensure_template_profile()
        runtime_profile = _prepare_runtime_profile()
        profile_dir = str(runtime_profile)
        debug_port = _reserve_debug_port()
        chrome_proc = _launch_runtime_chrome(profile_dir, debug_port)
        ws_url = await asyncio.to_thread(_wait_for_cdp_websocket_url, debug_port, chrome_proc)
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(ws_url)
        contexts = browser.contexts
        if contexts:
            ctx = contexts[0]
        else:
            ctx = await browser.new_context(accept_downloads=True)
        setattr(ctx, "_gemini_playwright", playwright)
        setattr(ctx, "_gemini_browser", browser)
        setattr(ctx, "_gemini_chrome_proc", chrome_proc)
        setattr(ctx, "_gemini_runtime_profile", profile_dir)
        return ctx
    except Exception as exc:  # pragma: no cover - real browser launch path
        raise ChromeConnectionError(f"独立 headless Chrome 启动失败：{exc}") from exc


async def _close_context(ctx: BrowserContext) -> None:
    playwright = getattr(ctx, "_gemini_playwright", None)
    browser = getattr(ctx, "_gemini_browser", None)
    chrome_proc = getattr(ctx, "_gemini_chrome_proc", None)
    runtime_profile = getattr(ctx, "_gemini_runtime_profile", None)
    try:
        if browser is not None:
            await browser.close()
        else:
            await ctx.close()
    except Exception:
        pass
    if playwright is not None:
        await playwright.stop()
    _terminate_runtime_chrome(chrome_proc)
    if runtime_profile:
        shutil.rmtree(runtime_profile, ignore_errors=True)


def _prepare_runtime_profile() -> Path:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    runtime_dir = Path(tempfile.mkdtemp(prefix="openclaw-gemini-runtime-"))

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

    logger.info(f"复制 Gemini 模板 profile → 运行副本: {runtime_dir}")
    shutil.copytree(PROFILE_DIR, runtime_dir, dirs_exist_ok=True, ignore=ignore)
    return runtime_dir


def _ensure_template_profile() -> None:
    if PROFILE_DIR.exists():
        return
    if not LEGACY_PROFILE_DIR.exists():
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        return

    logger.info(f"迁移旧 Gemini profile → 模板 profile: {LEGACY_PROFILE_DIR} -> {PROFILE_DIR}")
    shutil.copytree(
        LEGACY_PROFILE_DIR,
        PROFILE_DIR,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
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
        ),
    )


def _reserve_debug_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _optional_proxy_args() -> list[str]:
    proxy = os.environ.get("GEMINI_DRAW_PROXY_SERVER", "").strip()
    if not proxy:
        return []
    return [f"--proxy-server={proxy}"]


def _launch_runtime_chrome(profile_dir: str, debug_port: int) -> subprocess.Popen[str]:
    cmd = [
        CHROME_BIN,
        "--headless=new",
        f"--user-data-dir={profile_dir}",
        f"--remote-debugging-port={debug_port}",
        "--window-size=1600,1200",
        "--disable-gpu",
        "--disable-software-rasterizer",
        "--no-first-run",
        "--no-default-browser-check",
        "--no-sandbox",
        "about:blank",
    ]
    cmd[4:4] = _optional_proxy_args()
    logger.info(f"启动隔离 Chrome Runtime: port={debug_port} profile={profile_dir}")
    return subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def _wait_for_cdp_websocket_url(debug_port: int, chrome_proc: subprocess.Popen[str], timeout_s: int = 30) -> str:
    url = f"http://127.0.0.1:{debug_port}/json/version"
    deadline = time.time() + timeout_s
    last_error: Exception | None = None
    while time.time() < deadline:
        if chrome_proc.poll() is not None:
            raise ChromeConnectionError(f"隔离 Chrome 提前退出，exit={chrome_proc.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                payload = json.load(response)
            ws_url = payload.get("webSocketDebuggerUrl")
            if ws_url:
                return ws_url
        except Exception as exc:
            last_error = exc
        time.sleep(0.5)
    raise ChromeConnectionError(f"等待 CDP 端口超时: {last_error}")


def _terminate_runtime_chrome(chrome_proc: subprocess.Popen[str] | None) -> None:
    if chrome_proc is None:
        return
    if chrome_proc.poll() is not None:
        return
    try:
        chrome_proc.terminate()
        chrome_proc.wait(timeout=5)
    except Exception:
        try:
            chrome_proc.kill()
        except Exception:
            pass


async def _find_or_open_gemini_tab(ctx: BrowserContext) -> Page:
    for page in ctx.pages:
        if "gemini.google.com" in page.url and "signin" not in page.url:
            logger.info(f"复用已有 Gemini 标签页: {page.url}")
            return page
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
    logger.info("未找到 Gemini 标签页，正在导航到 Gemini...")
    await page.goto(GEMINI_URL, wait_until="domcontentloaded", timeout=60_000)
    logger.info(f"导航完成: {page.url}")
    return page


async def _dismiss_popups(page: Page) -> None:
    for sel in [
        '[aria-label*="Got it"]',
        '[aria-label*="我知道了"]',
        '[aria-label*="Accept"]',
        '[aria-label*="关闭"]',
        '[aria-label*="Skip"]',
    ]:
        try:
            btn = page.locator(sel).first
            if await btn.count() > 0:
                await btn.click(force=True, timeout=3_000)
        except Exception:
            continue


async def _assert_logged_in(page: Page) -> None:
    await asyncio.sleep(1)

    login_button_selectors = [
        'button:has-text("登录")',
        'a:has-text("登录")',
        'button:has-text("Sign in")',
        'a:has-text("Sign in")',
    ]
    for sel in login_button_selectors:
        try:
            if await page.locator(sel).count() > 0:
                raise ChromeConnectionError(
                    "独立 profile 当前未登录 Gemini。请先运行 scripts/init_login.py 完成一次性登录初始化。"
                )
        except ChromeConnectionError:
            raise
        except Exception:
            continue

    try:
        body = await page.locator("body").inner_text(timeout=5_000)
    except Exception as exc:
        raise ChromeConnectionError(f"无法读取 Gemini 页面状态：{exc}") from exc

    login_signals = [
        "登录",
        "您登录了吗",
        "登录即可关联到 Google 应用",
        "Sign in",
    ]
    if any(signal in body for signal in login_signals):
        raise ChromeConnectionError(
            "独立 profile 当前未登录 Gemini。请先运行 scripts/init_login.py 完成一次性登录初始化。"
        )


async def _fill_prompt(page: Page, prompt: str) -> None:
    logger.info("开始填写 Prompt...")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(1)
    await _dismiss_popups(page)

    inp = page.locator('[aria-label="为 Gemini 输入提示"]').first
    if await inp.count() == 0:
        inp = page.locator('div[contenteditable="true"]').first
    if await inp.count() == 0:
        raise GeminiDrawError("找不到 Gemini 输入框")

    await inp.click(force=True, timeout=5_000)
    await inp.fill(prompt)
    logger.info("Prompt 已写入输入框")

    btn = page.locator('[aria-label="发送"]').first
    if await btn.count() == 0:
        btn = page.locator('[aria-label="Send"]').first
    if await btn.count() == 0:
        raise GeminiDrawError("找不到 Gemini 发送按钮")
    if not await btn.is_enabled(timeout=3_000):
        raise GeminiDrawError("Gemini 发送按钮不可点击")
    await btn.click(force=True, timeout=5_000)
    logger.info("Prompt 已发送")


async def _wait_for_image(page: Page, timeout_s: int) -> Page:
    logger.info(f"开始等待 Gemini 出图，最长 {timeout_s}s")
    start = time.time()
    while time.time() - start < timeout_s:
        for sel in ['img[alt*="AI 生成"]', 'img[src*="blob:"]']:
            imgs = await page.query_selector_all(sel)
            for img in imgs:
                src = await img.get_attribute("src") or ""
                alt = await img.get_attribute("alt") or ""
                if "blob:" in src or "AI 生成" in alt:
                    logger.info(f"检测到生成图片: alt={alt[:40]} src={src[:60]}")
                    return img
        await asyncio.sleep(5)
        elapsed = int(time.time() - start)
        if elapsed and elapsed % 30 == 0:
            logger.info(f"等待出图中... {elapsed}s")
    raise ImageGenerationTimeout(f"在 {timeout_s}s 内未检测到 Gemini 生成图片")


async def _download_original(page: Page, img_el: Page, output_dir: Path, prompt: str) -> dict[str, Any]:
    logger.info("开始执行原图下载...")
    await img_el.hover()
    await asyncio.sleep(2)

    try:
        async with page.expect_download(timeout=60_000) as dl_info:
            js_result = await page.evaluate(DOWNLOAD_BUTTON_SCRIPT)
            if not js_result:
                raise ImageDownloadError("递归 Shadow DOM 没找到下载按钮")
            logger.info(f"Shadow DOM 下载按钮命中: {js_result}")
        download = await dl_info.value
        logger.info(f"Download 事件已触发: {download.suggested_filename}")
    except Exception as exc:  # pragma: no cover - real browser download path
        if isinstance(exc, ImageDownloadError):
            raise
        raise ImageDownloadError(f"未能触发 Gemini 原图下载：{exc}") from exc

    suggested = download.suggested_filename or "gemini-download.png"
    temp_path = Path("/tmp") / suggested
    await download.save_as(str(temp_path))

    if not temp_path.exists():
        raise ImageDownloadError(f"下载事件已触发，但文件不存在：{temp_path}")

    size_bytes = os.path.getsize(temp_path)
    logger.info(f"【OS 审计：文件路径: {temp_path}, 大小: {size_bytes} bytes】")
    if size_bytes < MIN_ORIGINAL_BYTES:
        raise ImageDownloadError(
            f"下载文件过小，未达到高清原图标准：{size_bytes} bytes (< {MIN_ORIGINAL_BYTES})"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(prompt)
    ext = temp_path.suffix or ".png"
    dst = output_dir / f"{safe_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}{ext}"
    shutil.copy2(temp_path, dst)
    return {"image_path": str(dst), "size_bytes": size_bytes, "download_path": str(temp_path)}


async def draw_async(
    prompt: str,
    output_dir: str | None = None,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    logger.info("=" * 60)
    logger.info("开始 Gemini 图片生成任务（后台静默模式）")
    logger.info(f"Prompt: {prompt[:120]}")
    logger.info("=" * 60)

    ctx = await _launch_context()
    try:
        logger.info("独立 headless Chrome 已启动")
        page = await _find_or_open_gemini_tab(ctx)
        logger.info(f"当前页面: {page.url}")
        await page.screenshot(path=str(DEBUG_DIR / "after-open.png"))
        if "signin" in page.url:
            raise ChromeConnectionError("独立 profile 尚未登录 Gemini，请先执行 scripts/init_login.py")
        await _assert_logged_in(page)

        await _dismiss_popups(page)
        await _fill_prompt(page, prompt)
        img_el = await _wait_for_image(page, timeout)
        result = await _download_original(page, img_el, ensure_output_dir(output_dir or str(OUTPUT_DIR)), prompt)
        result["prompt"] = prompt
        return result
    except Exception:
        try:
            if "page" in locals():
                await page.screenshot(path=str(DEBUG_DIR / "failure.png"))
        except Exception:
            pass
        raise
    finally:
        await _close_context(ctx)


def draw(
    prompt: str,
    output_dir: str | None = None,
    port: int = 9222,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """
    兼容旧调用签名。`port` 仅为历史参数，当前实现不会再连接系统 Chrome 的 CDP 端口。
    """
    if port != 9222:
        logger.info(f"忽略 legacy CDP 端口参数: {port}（已切换为独立 headless profile）")
    return asyncio.run(draw_async(prompt=prompt, output_dir=output_dir, timeout=timeout))
