# 柚子的 B 站视频桥接工具 (实验版 v0.1)

**目的**：让本地电脑获取 B 站视频，将有时间戳的画面九宫格/十二宫格和对白整理到你的**私有** GitHub 仓库，再由已经连接的 ChatGPT GitHub 工具读取。

这不需要 ChatGPT 自定义 MCP，也不需要 Work/Codex 额度。

## 1. 安装依赖（Windows PowerShell）

安装 FFmpeg（安装后重新打开 PowerShell）：
```powershell
winget install --id Gyan.FFmpeg -e
ffmpeg -version
```

使用你电脑现有 Python 3.12：
```powershell
python -m pip install --upgrade yt-dlp Pillow
# 建议加装离线转录，这样才能理解人物台词：
python -m pip install faster-whisper
```

## 2. 准备私有 GitHub 仓库

在 GitHub 网页创建一个 **Private** 仓库，例如 `YuzuVideoBridge`，克隆到本地 `G:\YuzuVideoBridge`，在 ChatGPT 中确保连接到**同一个 GitHub 帐号**。

不要把 Cookie / GitHub Token / 原始视频提交到仓库。

## 3. 运行（先本地试）

```powershell
python .\yuzu_bili_bridge.py "https://b23.tv/eSx4UL0" --repo "G:\YuzuVideoBridge" --asr
```

先看是否成功产生 `G:\YuzuVideoBridge\packets\...\manifest.json` 和 `images\sheet_001.jpg`。转录模型第一次会下载权重。视频处理仅在本地，**不会上传整段视频**。

确认后执行（会提交并推送到你的私有仓库）：
```powershell
python .\yuzu_bili_bridge.py "https://b23.tv/eSx4UL0" --repo "G:\YuzuVideoBridge" --asr --push
```

如无游客访问权限，可加 `--browser edge` 从你**本机**的 Edge 浏览器读取已有登录状态（不会上传 Cookie）；不要把 Cookie 贴给 ChatGPT。

## 4. 再向柚子发送

> 我准备好了私有仓库 `<owner>/YuzuVideoBridge`，请从 GitHub 读取 `packets/<视频ID>/manifest.json`、`transcript.txt` 和所有 `images/sheet_*.jpg`，根据实际画面与对白分析视频，不要只读标题。

目前验证过：GitHub 插件能够读取 PNG/JPG 的 base64，柚子能将它送入视觉理解通道。完整视频管线尚待 Windows 实机测试。

## 5. 已知限制

- **1 fps 是抽样观看，不是逐帧看完整 30/60 fps。** 想看快速动作可用 `--fps 2` 或 `--fps 3` 重采样；可根据具体片段再补更密的帧。
- Whisper 转写可能错误，尤其是多个角色配音；必要时需对照视觉字幕。
- B 站的反自动化限制可能导致 412 或下载失败；脚本不保证绕过这些限制。只能使用授权访问内容。
- `--push` 会执行 git commit/push；仓库应保持私有；请勿上传整部原片或登录凭据。
- 初次测试只需本地运行；GitHub 模式确认能工作后，未来可以增加 Issue 任务队列，让本地常驻程序自动领取需要解析的视频链接。
