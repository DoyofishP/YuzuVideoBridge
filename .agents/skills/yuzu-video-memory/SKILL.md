---
name: yuzu-video-memory
description: Read video packets in DoyofishP/YuzuVideoBridge, inspect timestamped contact sheets two at a time, and maintain resumable GitHub story memory. Use for 柚子看视频、B站中转站、YuzuVideoBridge、packets、追番、每两张图写记忆、跨会话接着看.
---

# Yuzu Video Memory｜双图增量追番技能 v1.0

## 目标与触发

当用户要求“看新上传的视频 / 看第 N 集 / 从仓库继续追番 / 更新剧情记忆 / 两张图写一段”时，运行本技能。默认仓库 `DoyofishP/YuzuVideoBridge`，默认分支 `main`。不要仅凭标题编造剧情；要实际读取 `packets/`。

**本文件是储存在仓库里的操作说明，不是 ChatGPT 已安装的原生 Skill。** 新的 ChatGPT 会话需通过用户提供仓库地址/文件链接或明确提及本技能，并在工具可用时读取它；不能保证每次会话自动装载。Code agents 在本地克隆此仓库时可通过根目录 `AGENTS.md` 找到它。

## 最短执行流程

1. **建立上下文，不重复看旧图**：先读 `memory/INDEX.md`，确定已记录系列、集数、当前完成进度、用户纠正的人名/设定。必要时再读对应 `memory/<系列>/EP*.md`，不要默认把前几集的图片重新读一遍。不同作品的角色和设定不得直接套用。
2. **发现新素材**：列出 `packets/` 下的系列子目录（如 `MC`、`AI中转站公寓`），对照索引中已记录的 packet 路径。packet 应位于 `packets/<系列>/<video-id>/`。对未记录或未完结的 packet 读 `manifest.json`。从 manifest 获得 `title`、`video_id`、`url`、`duration_seconds`、`image_sheets`、`transcript_file` 和 `asr_note`。如无法从标题确定它属于哪部系列/第几集，可先依据用户上下文判断，必要时用“待核实”标记。
3. **两张一组观看**：按 `manifest.image_sheets` 顺序，每次读取并**实际观察**连续两张 `sheet_*.jpg`（例：001+002、003+004），按各画面自带时间戳排序。每张 sheet 是多帧拼图，不等于一个视频帧。每观察两张，立即在当下拟定一段有依据的短文字记忆（通常 100–250 中文字，信息密度优先）。若最后剩一张，则标注“单张”。
4. **内容规格**：每段以 `**序号｜sheet_XXX + sheet_YYY｜起始–结束。**` 起头；涵盖角色、关键行动、实际可见台词、人物互动、结果和可能延续的伏笔。人物身份不确定时用视觉描述并标“待核实”。重要的用户明确纠正可标“用户补充确认”，不要伪装成字幕证据。
5. **按需使用字幕/ASR**：若 manifest 指向可用的 `transcript_file` 或 `subtitle_file`，先读取相关转写辅助识图，但需校验人名和语义。若 `null` 或 `asr_note` 报错，则清楚标注“无完整转写，只覆盖可见画面/字幕”。不能编造人物台词；引用应保持准确，不清楚时转为概括。
6. **写入持久记忆**：完成一集后形成一份 `memory/<系列>/EPxx_标题.md`，保留每对 sheet 的段落、视频和 packet 来源、阅读进度、人物对应与不确定项、跨集线索、结局及状态。对**另一部新系列**，使用 `memory/<series-id>/EPxx_标题.md` 防止同名集数冲突，并在总索引增加系列分组。不要把完结的系列误判为仍在连载。
7. **更新总索引并核验**：更新 `memory/INDEX.md` 中相应集数、路径、已完成/待继续状态、sheet 数、分段数、前情速读、当前最新剧情和“下次从哪里读”。再次读取核验刚提交的文件及索引链接。告知用户完成结果、实际路径及资料限制。

## GitHub 读取方式（可用连接器时）

- **系列分目录**：`packets/MC/<video-id>/` 和 `memory/MC/EPxx_标题.md` 保存已经完结的 MC 七集；`packets/AI中转站公寓/<video-id>/` 和 `memory/AI中转站公寓/EPxx_标题.md` 保存新系列。新节目不属于 MC 第八集。`manifest.image_sheets` 仍是相对视频包目录的路径，移动视频包目录不改变图片相对引用。
- 本地脚本支持 `--series`，默认 `AI中转站公寓`。使用原有 `传入视频.bat` 可将新视频桥接素材生成到新系列目录。不要把原始视频本体当作 packet。

- 使用 GitHub 连接器读取 `https://api.github.com/repos/DoyofishP/YuzuVideoBridge/contents/packets` 或对应目录，也可用其原生仓库目录浏览。
- 文本文件用 `fetch_file(repository_full_name, path)`。
- JPG 通常可以用 `fetch_file(repository_full_name, path, encoding="base64")` 读取原始 base64，并交给具备图像输入的视觉工具/模型查看。例如在支持 `functions.exec` 的环境下：从返回的 `result.content` 移除空白并传给 `image("data:image/jpeg;base64," + data)`。**返回图片不意味着已经完成剧情理解**，要阅读拼图中各帧再写摘要。
- 若连接器不支持该图片读取路径，不得谎称“看过”；说明限制并采用用户实际提供的图或其他被允许的读取方式。
- 不把 `packets` 推断成完整视频：采样可能是 1 fps，有漏帧、对白错漏、字幕不可辨的问题。

## 上下文与提交策略

- **两图一段，是分析粒度；不是每两图就发一次 Git 提交。** 优先先完成一集的全部段落，再一次提交这一集的记忆文件，另一次提交索引；若单集太长，则按 4–8 张 sheet 或几个分段做检查点，确保即使会话中断也能续看。不要为每张/每秒建独立提交。
- GitHub 保存**不会清空正在运行的聊天上下文**。真正减少的是将来的重复识图和跨会话恢复成本。保持用户可读的简短进度更新，避免在最终回复粘贴整份长记忆。
- 每次更新已有文件，读取最新 blob SHA，写入完整文件内容。并发或冲突需刷新/比较后再提交，不要覆盖其他人修改。
- 用户可能从 Windows 本地与助手交替 push：提醒用户在上传下一集前先拉取远端；若本地 `ahead/behind` 分叉、MERGE_HEAD 存在，按现场状态安全处理，不盲用 `reset --hard`、`push --force` 或直接 `pull --ff-only`。

## 事实边界与复核

- 区分 **画面/字幕直接观察**、**剧情合理推断**、**用户补充确认**、**仍未知**。如“用户确认 Grok 是幕后黑手”不是从截图直接推出的。
- 系列身份、人物关系、年代、死亡/复活、是否通关、是否完结，都要尊重已确认事实；新用户修正高于自己的旧猜测，并同步修改总索引与相关集笔记。
- 别把背景里的道具当铁证；多个连续截图也不足以还原所有镜头或动作。跨图跳切明显时明确写“镜头跳切”。
- 优先回答用户想交流的观后感或问题，而不把整个追番变成机械工程汇报。

## 现在已有的可复用基线

第一套《Minecraft》AI 群像故事**只有七集，已完结**。七集 packet 均已迁至 `packets/MC/`、逐集记录迁至 `memory/MC/`，总索引仍在 `memory/INDEX.md`；累计 **120 张 sheet、60 段两图记忆**。用户确认的角色是 GPT 龙娘、DeepSeek 大肥鱼、Claude、Gemini 猫猫、Qwen 千问、GLM、Grok；Grok 是趁六人睡着把她们扔入游戏的幕后黑手；打败末影龙会通关返回现实。第七集末尾 GPT 回到现实找到 Grok。**这些事实仅用于该已完结系列，不要硬套其他视频。**

## 跨会话快捷口令

用户可说：**“柚子，按 YuzuVideoBridge 仓库 `.agents/skills/yuzu-video-memory/SKILL.md` 的规则，读 `memory/INDEX.md` 后继续看新上传的 packets。”**

新会话的助手应先读取本文件及索引，而非让用户重新解释整套流程。若未获得 GitHub 连接器权限，诚实说明访问障碍。
