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

先看是否成功产生 `G:\YuzuVideoBridge\packets\AI中转站公寓\<视频ID>\manifest.json` 和 `images\sheet_001.jpg`。转录模型第一次会下载权重。视频处理仅在本地，**不会上传整段视频**。

确认后执行（会提交并推送到你的私有仓库）：
```powershell
python .\yuzu_bili_bridge.py "https://b23.tv/eSx4UL0" --repo "G:\YuzuVideoBridge" --asr --push
```

如无游客访问权限，可加 `--browser edge` 从你**本机**的 Edge 浏览器读取已有登录状态（不会上传 Cookie）；不要把 Cookie 贴给 ChatGPT。

## 4. 再向柚子发送

> 我准备好了私有仓库 `<owner>/YuzuVideoBridge`，请从 GitHub 读取 `packets/AI中转站公寓/<视频ID>/manifest.json`、`transcript.txt` 和所有 `images/sheet_*.jpg`，根据实际画面与对白分析视频，不要只读标题。

目前验证过：GitHub 插件能够读取 PNG/JPG 的 base64，柚子能将它送入视觉理解通道。完整视频管线尚待 Windows 实机测试。

## 5. 视频分系列存放

- `packets/MC/<video-id>/`：已完结的 MC 七集抽帧包，整体搬迁，不丢历史截图。
- `memory/MC/EPxx_标题.md`：MC 番各集笔记。
- `packets/AI中转站公寓/<video-id>/`：新的“AI中转站公寓”视频包目录。
- `memory/AI中转站公寓/`：对应的观影记忆。
- `memory/INDEX.md`：跨系列总索引。

现有 `传入视频.bat` 无须改输入方式：脚本已经默认将新生成的 packet 放在 `AI中转站公寓`。也可手动用 `--series "MC"` 或 `--series "AI中转站公寓"` 指定系列。用户应先 `git pull`，再生成并推送新素材。仓库设计为上传**抽帧和文字包**，不是整部视频原片。

## 6. 自动追番记忆 Skill（跨会话接续）

仓库已包含正式的操作规程：[`yuzu-video-memory/SKILL.md`](.agents/skills/yuzu-video-memory/SKILL.md)，以及供本地 agent 发现它的 [`AGENTS.md`](AGENTS.md)。**开始前先读 [`memory/INDEX.md`](memory/INDEX.md)**，它包含已看集数、人物关系、观看进度和可继续读取的 packet。

新会话直接对柚子说：

> 柚子，按 YuzuVideoBridge 仓库的 `.agents/skills/yuzu-video-memory/SKILL.md` 和 `memory/INDEX.md` 继续看我刚上传的视频，每两张图一段记忆，最后提交仓库。

**说明**：普通 ChatGPT 会话不保证自动加载 GitHub 中的 Skill；此文件提供一个确定可检索、可复用的入口。已归档的七集 Minecraft AI 群像故事是完整完结篇，新视频属于另一部作品时必须分开建系列记忆。

## 7. 已知限制

- **1 fps 是抽样观看，不是逐帧看完整 30/60 fps。** 想看快速动作可用 `--fps 2` 或 `--fps 3` 重采样；可根据具体片段再补更密的帧。
- Whisper 转写可能错误，尤其是多个角色配音；必要时需对照视觉字幕。
- B 站的反自动化限制可能导致 412 或下载失败；脚本不保证绕过这些限制。只能使用授权访问内容。
- `--push` 会执行 git commit/push；仓库应保持私有；请勿上传整部原片或登录凭据。
- 初次测试只需本地运行；GitHub 模式确认能工作后，未来可以增加 Issue 任务队列，让本地常驻程序自动领取需要解析的视频链接。
