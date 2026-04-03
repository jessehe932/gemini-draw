# gemini-draw

`gemini-draw` 是一个 Gemini 后台生图工具，可以作为两种形态使用：

- OpenClaw 技能
- 独立 Python CLI

它的核心约束很简单：

- 默认后台静默运行
- 不接管用户正在使用的 Chrome
- 通过隔离 profile 完成一次性 Gemini 登录初始化
- 下载的是原图，而不是截图
- 只有通过文件系统审计，才算真正成功

## 安装

### 方式一：作为 OpenClaw 技能使用

步骤 1：把仓库克隆到 OpenClaw 的 skills 目录

```bash
git clone <your-github-repo-url> ~/.openclaw/workspace/skills/gemini-draw
```

步骤 2：进入技能目录

```bash
cd ~/.openclaw/workspace/skills/gemini-draw
```

步骤 3：安装 Python 依赖

```bash
pip install -r requirements.txt
```

步骤 4：安装 Playwright 所需浏览器

```bash
playwright install chromium
```

步骤 5：在 OpenClaw 中根据 `SKILL.md` 调用该技能

### 方式二：作为独立 CLI 使用

步骤 1：把仓库克隆到本地任意目录

```bash
git clone <your-github-repo-url> gemini-draw
```

步骤 2：进入项目目录

```bash
cd gemini-draw
```

步骤 3：以可编辑模式安装 CLI

```bash
pip install -e .
```

步骤 4：安装 Playwright 所需浏览器

```bash
playwright install chromium
```

步骤 5：执行一次登录初始化

```bash
gemini-draw-login
```

步骤 6：开始生成图片

```bash
gemini-draw --prompt "一只穿宇航服的柴犬，电影感，高清"
```

## 首次登录初始化

步骤 1：初始化一个独立的 Gemini 登录 profile

```bash
python3 scripts/init_login.py
```

如果已经按 Python 包安装，也可以直接运行：

```bash
gemini-draw-login
```

步骤 2：在弹出的普通 Chrome 窗口里手动登录 Gemini

步骤 3：登录完成后，关闭这个窗口

说明：

- 这一步只需要做一次
- 登录态会保存在隔离 profile 中
- 后续正式生成默认走后台无头执行

## 生成图片

脚本入口：

```bash
python3 scripts/gemini_draw.py --prompt "一只穿宇航服的柴犬，电影感，高清"
```

包入口：

```bash
gemini-draw --prompt "一只穿宇航服的柴犬，电影感，高清"
```

也可以指定输出目录：

```bash
gemini-draw --prompt "一只穿宇航服的柴犬，电影感，高清" --output-dir ./output
```

## E2E 验收

步骤 1：确认已经完成过首次登录初始化

步骤 2：执行 E2E 测试

```bash
python3 tests/test_integration.py --prompt "一只穿宇航服的柴犬，电影感，高清"
```

步骤 3：检查终端输出中是否出现这类审计信息

```text
【OS 审计：文件路径: ..., 大小: ... bytes】
```

步骤 4：检查目标目录中是否真的出现了生成文件

## 运行设计

- 登录初始化
  - 使用普通系统 Chrome
  - 避免自动化浏览器触发 Google 的不安全浏览器拦截
- 正式执行
  - 使用隔离 profile
  - 启动私有 headless Chrome runtime
  - 不连接共享的系统 CDP 端口
- 下载验证
  - 穿透 Shadow DOM 触发真实下载按钮
  - 只有文件真正落盘并审计通过，才汇报成功

## 默认输出位置

默认输出到：

```text
~/Downloads/gemini-draw-output/
```

也可以通过 `--output-dir` 覆盖。

如果你的网络环境需要代理，也可以通过环境变量传入。例如 Gemini 在某些地区或网络环境下需要代理访问：

```bash
GEMINI_DRAW_PROXY_SERVER=http://your-proxy-host:port gemini-draw --prompt "一只穿宇航服的柴犬，电影感，高清"
```

## 关键文件

- `SKILL.md`：OpenClaw 调用契约
- `scripts/init_login.py`：一次性登录初始化
- `scripts/gemini_draw.py`：正式脚本入口
- `scripts/gemini_e2e_v9.py`：完整 E2E 验收入口
- `tests/test_integration.py`：集成测试包装入口
- `gemini_draw/gemini_draw.py`：共享运行时实现

## 成功输出

成功时会打印类似这样的审计信息：

```text
【OS 审计：文件路径: ..., 大小: ... bytes】
```
