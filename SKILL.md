# gemini-draw Skill — 调用契约

> 当前定位：这是可公开 GitHub 版本的本地克隆种子，后续会继续移除本地专有约束。

## 触发方式

用户在日常对话中，使用以下任意自然语言指令即可稳定触发：

```
帮我画一张 [描述]
用 Gemini 生成图片：[描述]
画一个 [描述]
生成一张 [描述] 的图
```

示例：
```
帮我画一张未来城市中霓虹灯下的赛博朋克猫咪
用 Gemini 生成图片：一只穿着宇航服的柴犬在月球上
画一个动漫风格的海底世界
```

## 工作流程

1. 使用独立模板 profile `~/.config/gemini-draw/template-profile/`
2. 启动 headless Chrome，在后台静默访问 `gemini.google.com`
3. 使用用户的 Gemini 登录态生成图片
4. 递归穿透 Shadow DOM，触发原图下载
5. 通过 OS 文件审计验证真实文件路径与大小
6. 交付到默认输出目录或调用方指定的输出目录

## 输出

- 图片文件路径：默认是 `~/Downloads/gemini-draw-output/`
- 典型规格：2816×1536 px，9-10 MB PNG

## 依赖条件

1. 独立 profile 已完成首次登录授权（仅需一次）
2. 如果本地网络环境需要代理，可通过环境变量 `GEMINI_DRAW_PROXY_SERVER` 提供
3. 正式入口：`scripts/gemini_draw.py`
4. E2E 验收入口：`tests/test_integration.py`

## 关键约束

- 不允许接管用户正在使用的系统 Chrome
- 不允许依赖 `localhost:9222` 的系统 CDP
- 不允许执行 `killall "Google Chrome"`
- 初始化登录仅允许通过 `scripts/init_login.py` 用普通系统 Chrome 一次性打开可见窗口
- 日常调用必须默认后台无头执行

## 调用示例

> **用户：** 画一张下雨的东京街头
> **猫猫：** 收到！正在生成图片，稍等约 30-60 秒...
> **（约 40s 后）**
> **猫猫：** 完成！📁 `~/Downloads/gemini-draw-output/2026-04-03_004930.png`（9.2 MB，2816×1536）
