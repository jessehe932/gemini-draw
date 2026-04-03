# gemini-draw 经验教训

## 最终可用形态

`gemini-draw` 现在只保留一条正式生产主线：

1. Gemini 首次登录使用普通系统 `Google Chrome.app`
2. 日常生成使用隔离 profile
3. 正式执行使用私有 headless Chrome 实例
4. OpenClaw 在后台静默调用技能
5. 成功标准必须是真实下载文件加上 OS 级文件审计

## 之前为什么会出问题

### 1. 同时存在太多浏览器策略

早期实验混用了：

- 系统 Chrome
- `localhost:9222` 的 CDP
- Playwright `launch_persistent_context`
- Chrome for Testing
- 各种“藏窗口”补丁

这会直接造成冲突：

- 一个浏览器能打开 Gemini，但不能登录
- 一个浏览器能登录 Gemini，但不能登录 OpenClaw gateway
- 一个浏览器直接卡死
- 一个浏览器会关闭或干扰用户正在使用的 Chrome

### 2. 把“登录浏览器”和“生产浏览器”当成了同一个问题

Google 会把自动化拉起的浏览器视为不安全的登录环境。

这意味着：

- Gemini 登录初始化不能使用 Playwright 拉起的可见 Chrome
- 登录必须使用普通系统 Chrome 加隔离 profile
- 登录态落盘之后，生产自动化才可以使用后台 headless runtime

### 3. 实验脚本保留太久

同时保留多个 `gemini_e2e_v*` 分支，等于给 agent 留下了反复走旧路的机会。

正确做法是只保留：

- 一个登录入口
- 一个正式入口
- 一个最终 E2E 入口

### 4. 在强制物理审计之前，成功标准不够严格

这套技能真正稳定下来，是因为成功被重新定义为：

- Gemini 真的收到了提示词
- 页面上真的出现了生成图片
- 原图下载按钮真的被触发
- 文件真的落盘到了磁盘
- `os.path.getsize()` 真的验证了文件大小

## OpenClaw 必须保留的规则

1. 不要把 `localhost:9222` 再引回生产链路
2. 不要为这个技能执行 `killall "Google Chrome"`
3. 不要使用 Chrome for Testing 做 Gemini 登录初始化
4. 不要使用 Playwright 可见浏览器做 Gemini 账号登录
5. 正式入口只保留一条
6. E2E 入口只保留一条
7. 最终成功标准必须是 OS 文件审计
8. 下载失败时要暴露原始堆栈，不要编造成功结果

## 后续维护检查顺序

以后如果技能失效，按这个顺序排查：

1. Gemini 在隔离模板 profile 里的登录态是否还有效
2. Gemini 输入框 selector 是否变化
3. 发送按钮 selector 是否变化
4. 生成图片的判定规则是否变化
5. 下载按钮文案或 Shadow DOM 结构是否变化
6. 下载文件是否还高于预期的体积阈值

## 防回归建议

- 不要再加回旧实验脚本
- 不要在文档里保留过时浏览器路线
- 不要把登录逻辑和运行逻辑重新混在一起
- 不要把“页面看起来对了”当成成功，必须以文件审计为准
