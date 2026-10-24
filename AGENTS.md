# YuzuVideoBridge agent guide

本仓库承担 B 站视频抽帧桥接和**持久剧情记忆**。涉及“中转站、追番、看视频、packets、每两张图存一段、下一集、人物关系”的任务时：

1. **先读** [视频记忆 Skill](.agents/skills/yuzu-video-memory/SKILL.md)。
2. **再读** [观看进度和人物索引](memory/INDEX.md)。
3. 按 Skill 读取 `packets/<系列>/<video-id>/manifest.json` 和剩余 `images/sheet_*.jpg`，每两张拼图提炼一段。
4. 按照索引判断该系列是新作、续集还是已完结。不得重新识图已归档内容、不得臆造 ASR 缺失的台词。
5. 记忆沉淀到 `memory/<系列>/`，尽量集中提交；不同节目保持独立索引/目录，避免互相覆盖。

此 `AGENTS.md` 让在本地仓库工作的 coding agents 能发现规范；它**不能保证**普通 ChatGPT 新会话自动读取仓库，用户可发送上方 Skill 的 GitHub 链接来触发。

目前系列：**MC**（已完结）在 `packets/MC/` 和 `memory/MC/`；**AI中转站公寓**（新系列）在 `packets/AI中转站公寓/` 和 `memory/AI中转站公寓/`。先看 `memory/INDEX.md`。
