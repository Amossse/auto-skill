# Launch drafts (not posted)

## English

I built auto-skill: a portable Agent Skill that turns verified task experience into reusable procedures.
Your agent asks once before saving a new topic and enabling ongoing local updates. Later milestones
improve the same skill, with evidence, fresh validation records, version history and rollback.

It includes Codex/Claude workspace installers and an optional Claude Stop checkpoint. No separate model
API key, no CLI telemetry, and no automatic publication of your experience. Other hosts use the generic
protocol; automatic triggering depends on host support.

Try the fictional offline demo: `python scripts/demo.py`.
MIT toolkit: https://github.com/Amossse/auto-skill

## 中文

做了一个 auto-skill，把这次教会 AI 的方法留给下次使用。

任务完成并验证后，Agent 会询问是否把经验保存为 Skill，并允许后续同类任务自动改进。确认后，新的经验可以继续更新版本，保留证据和验证记录，也能回退。

首版支持 Codex 和 Claude 的工作区安装，Claude 可选 Stop 检查。CLI 不联网，不自动发布你的经验；自动触发仍取决于宿主。示例使用虚构访谈，运行 `python scripts/demo.py` 可验证本地流程。

项目采用 MIT 许可证：https://github.com/Amossse/auto-skill

## Suggested GitHub topics

`agent-skills`, `claude-code`, `codex`, `ai-agents`, `skill-distillation`, `procedural-memory`,
`human-in-the-loop`, `local-first`, `python`, `agentic-workflows`

Search phrases: experience to skill, learn from agent corrections, cross-agent skills, consented skill
iteration, portable procedural memory. Avoid claiming "every agent", "guaranteed automatic learning",
"perfect privacy", or a measured quality gain without comparative evidence.
