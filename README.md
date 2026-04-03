# gemini-draw

`gemini-draw` 是一个 Gemini 后台生图工具，可以作为两种形态使用：

- OpenClaw 技能
- 独立 Python CLI

你可以把它理解成：

- 用真实网页登录态使用 Gemini 生图
- 不依赖官方 API
- 默认后台静默运行
- 最终以真实文件下载和落盘审计作为成功标准

它的核心约束很简单：

- 默认后台静默运行
- 不接管用户正在使用的 Chrome
- 通过隔离 profile 完成一次性 Gemini 登录初始化
- 下载的是原图，而不是截图
- 只有通过文件系统审计，才算真正成功

## 仓库说明

这个仓库面向两类使用者：

- 想把它作为 OpenClaw 技能接入的人
- 想把它当成独立 Python CLI 使用的人

它适合这样的场景：

- 希望通过网页登录后的 Gemini 使用生图能力
- 不想依赖官方 API
- 希望在后台静默执行，而不是弹出生产浏览器窗口
- 希望最终以真实文件落盘作为成功标准

它不适合这样的场景：

- 想直接走官方 API
- 想在 Linux 或 Windows 上开箱即用
- 不愿意做第一次手动登录初始化

## 安装前提

开始前请先确认：

1. 你使用的是 macOS，并且本机安装了 `Google Chrome.app`
2. 你有可用的 Python 3.10+
3. 你可以安装 Python 依赖
4. 你允许第一次运行时手动登录 Gemini
5. 如果你所在网络环境访问 Gemini 需要代理，准备好代理地址

当前默认运行假设：

- 浏览器：`Google Chrome.app`
- 首次登录：手动完成
- 正式执行：后台 headless Chrome runtime
- 默认输出目录：`~/Downloads/gemini-draw-output/`

## 安装

### 方式一：作为 OpenClaw 技能使用

步骤 1：把仓库克隆到 OpenClaw 的 skills 目录

```bash
git clone https://github.com/jessehe932/gemini-draw.git ~/.openclaw/workspace/skills/gemini-draw
```

步骤 2：进入技能目录

```bash
cd ~/.openclaw/workspace/skills/gemini-draw
```

步骤 3：安装 Python 包

```bash
pip install -e .
```

步骤 4：安装 Playwright 所需浏览器

```bash
playwright install chromium
```

步骤 5：在 OpenClaw 中根据 `SKILL.md` 调用该技能

适合：

- 已经在使用 OpenClaw
- 想把 Gemini 生图接进自己的技能流

### 方式二：作为独立 CLI 使用

步骤 1：把仓库克隆到本地任意目录

```bash
git clone https://github.com/jessehe932/gemini-draw.git gemini-draw
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

适合：

- 不使用 OpenClaw
- 只想把它当作一个独立命令行工具使用

## 快速开始

如果你只想最快跑起来，推荐走独立 CLI：

1. `git clone https://github.com/jessehe932/gemini-draw.git gemini-draw`
2. `cd gemini-draw`
3. `pip install -e .`
4. `playwright install chromium`
5. `gemini-draw-login`
6. 登录 Gemini 后关闭窗口
7. `gemini-draw --prompt "一只穿宇航服的柴犬，电影感，高清"`

跑通之后，你通常会得到：

- 一张真实下载下来的 Gemini 原图
- 一个明确的输出文件路径
- 一条 `【OS 审计：文件路径: ..., 大小: ... bytes】` 作为成功依据

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

如果你要验证的是“以后能不能长期稳定用”，建议第一次配置完成后至少跑一次 E2E。

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

如果你不需要代理，就不要设置这个环境变量。

## 使用边界

这个项目当前默认面向：

- macOS
- 已安装 `Google Chrome.app`
- 可以手动完成一次 Gemini 登录初始化的环境

如果后续 Gemini 页面结构、登录流程或下载入口发生变化，通常需要调整：

- 输入框 selector
- 发送按钮 selector
- 生成完成判定
- 下载按钮 / Shadow DOM 穿透逻辑

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

## 发布说明

这个公开版仓库保留的是：

- 可安装的 skill / CLI 代码
- 登录、运行、验收说明

这个公开版仓库不包含：

- 你的本地 OpenClaw 记忆文件
- 你的本地工作区约束
- 私有配置、私有登录态、私有输出产物

## License

MIT
