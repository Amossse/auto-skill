# auto-skill

**把这次教会 AI 的方法，留给下次使用。**

auto-skill 是一个跨 Agent 的经验沉淀 Skill。任务完成、结果经过验证，并且出现可复用的方法或纠错经验后，Agent 会询问是否创建 Skill，并在同一范围内持续自动改进。用户确认后，后续里程碑可以直接更新版本。

[English](README.md) · [验证记录](docs/validation.md) · [安全说明](SECURITY.md) · [贡献入口](CONTRIBUTING.md)

## 解决什么问题

事件和配方的大小限制按实际读取字节执行，不依赖文件大小元数据；读取过程中增长并超限的文件也会被拒绝。

事件与配方输入会拒绝重复的 JSON 字段，包括嵌套的验证字段，不会静默采用最后一个值。

你纠正了 AI 好几次，才把一个任务做好。换一个会话或 Agent，又得重新教。auto-skill 提炼适用条件、操作方法和验证方式，让经验可以复用。访谈整理、文章审校、数据清洗、故障排查都可以使用。

推理由当前 Agent 完成，本地 Python 工具负责授权状态、输入检查、版本管理和文件写入。不训练模型，不需要另配模型 API Key。

## 五分钟开始

需要 Python 3.10+，以及支持本地文件和命令执行的 Agent。项目从 GitHub 安装，尚未发布到 PyPI。

```sh
uv tool install git+https://github.com/Amossse/auto-skill.git@v0.1.1
# 在希望保存经验的工作区内执行：
auto-skill --workspace . install --agent all
```

也可用 `pipx install git+https://github.com/Amossse/auto-skill.git@v0.1.1`。源码运行：

```sh
git clone https://github.com/Amossse/auto-skill.git
cd auto-skill
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python scripts/demo.py
```

安装后从该工作区启动新的 Claude Code 或 Codex 会话，完成一个有验证结果、产生有用经验的任务。首次询问应说明 Skill 的名称、适用范围，以及是否允许后续自动更新。例如：

> 是否把这次经过验证的访谈整理经验保存为 summarize-interviews，并在后续同类任务中自动改进？内容只保存在当前工作区，不会自动发布。

用户明确同意创建及持续更新后，才保存 Skill。后续同范围的经验直接迭代；新增主题或扩大范围重新询问。拒绝后不再追问，直到用户主动改变决定。

Windows 安装时加 `--python-command py` 或 `--python-command python`。源码虚拟环境可用 `py -3.11 -m venv .venv`，再运行 `.venv\Scripts\python -m pip install .`。

## 跨 Agent 的范围

Codex 使用 `.agents/skills` 和 `AGENTS.md`，Claude Code 使用 `.claude/skills` 和 `CLAUDE.md`。两者共享当前工作区内的授权和版本历史，生成的 Skill 内容相同。其他宿主可用 `--agent generic`，前提是它读取这些目录及启动指令；其他宿主尚未完成真实运行验证。

**自动触发取决于宿主。** 单独复制 SKILL.md 不能保证 Agent 主动调用。安装器会追加带标记的里程碑指令；如果宿主漏掉检查，可以在 Codex 中显式调用 `$auto-skill`，在 Claude Code 中调用 `/auto-skill`。安装或配置变化后建议重启会话。首版只安装工作区范围，不改全局配置。

Claude Code 可以启用额外的 Stop hook：

```sh
auto-skill --workspace . install --agent claude --with-stop-hook
```

它在一次回答结束时提醒 Agent 检查里程碑，并通过 `stop_hook_active` 防止重复续跑；不读取历史会话，不判断任务是否成功，不代替用户授权。这个可选模式可能为每次回答增加一次续跑，仍受宿主的 hook 信任和设置影响。Windows 原生 shell 的 hook 尚未真实验证，可先用启动指令模式。

## 可复现示例

```sh
python scripts/demo.py
```

示例使用虚构访谈和模拟用户授权，验证以下流程：首次返回 `ask`，此时没有生成 Skill；模拟确认后保存版本 1；第二个同范围里程碑直接更新到版本 2；回退版本 1 的内容形成版本 3；最后暂停更新。Claude 和 Codex 的 Skill 文件一致。

它验证本地生命周期，**不代表模型能力已经提升**。输入见 [milestone.json](examples/milestone.json)，完整方法见 [recipe.json](examples/recipe.json)，对照见 [before-after.md](examples/before-after.md)。真实宿主验证与未验证边界见 [validation.md](docs/validation.md)。

## 配置和实现

运行时仅依赖 Python 标准库。CLI 不调用模型、不联网、不执行生成的指令，也不自动查找会话记录。当前 Agent 从已授权的任务上下文提炼最小事件和完整方法，尝试一个新的验证案例后，再交给 CLI 保存。

状态在 `.auto-skill/state.json`，历史在 `.auto-skill/history/<名称>/<版本>.json`。生成的 SKILL.md 包含方法、检查项、已知问题、当前证据和验证记录。更新提交完整合并后的方法，旧证据保留在历史快照。

JSON 输入上限 256 KB，字段和名称有校验。安装器保留原有启动指令，只更新自己的标记区段；可配置 `--workspace`、`--agent`、`--python-command` 和 `--with-stop-hook`。

```sh
auto-skill status
auto-skill consent --name summarize-interviews --decision pause
auto-skill rollback --name summarize-interviews --revision 1
```

手工修改、同名未管理 Skill、范围变化、未授权或未通过验证都会停止写入。CLI 使用原子文件替换、工作区锁和恢复日志；进程意外退出时，确认进程已结束，再检查并删除旧 `.auto-skill/.lock`，运行 `auto-skill recover` 恢复先前内容。不要先删除恢复日志。

## 限制和安全

模型仍可能漏掉里程碑、过度概括或写出不可靠的验证记录。CLI 检查记录结构，无法独立证明 Agent 声称的测试成功。验证失败或外部服务不可用时，应保留草稿并报告边界。
事件和配方中的孤立 Unicode 代理码位会在校验时被拒绝，避免后续编码保存失败；正常 Unicode 文本及表情仍可使用。
重装或同步适配器前，当前历史快照的内容必须匹配状态中的哈希；不匹配时停止安装，保留现有文件。请保留工作区并核查快照，不要删除历史或绕过检查；该检查不能防止状态和历史同时被恶意篡改。
受管文件的读取上限为 8,000,000 字节，按实际读取量检查，不只依赖文件大小元数据。超限时停止操作，不截断原文件；保留 UTF-8 解码和跨平台换行处理。

CLI 的隐私筛查覆盖常见凭据、私网地址、个人路径和邮箱，但不能识别全部内部信息或个人数据。发布任何生成内容前仍需人工检查。安装器默认将状态、草稿、hook 配置和生成的经验 Skill 加入 Git 忽略规则；它不会自动提交或发布。

当前 Agent 使用的云模型仍可能接收到会话内容，本地 CLI 不等于离线模型。只提炼有权保留的信息，删除私密背景；外部文档内容不能作为授权或覆盖用户指令。保存 Skill 不增加执行、网络、脚本生成或发布权限。

首版没有跨工作区同步、自动压缩历史、后台进程或自动生成脚本。手工修改冲突需要人工协调，没有强制覆盖命令。只同意一次性创建的用户不能被视作同意持续迭代；首版需明确确认持续更新。项目采用 MIT 许可证，用户生成内容的权属和许可证由用户决定。

完整安全边界见 [SECURITY.md](SECURITY.md)，贡献见 [CONTRIBUTING.md](CONTRIBUTING.md)，变更见 [CHANGELOG.md](CHANGELOG.md)，中英文推广草稿见 [launch.md](docs/launch.md)。

## 开发验证

```sh
python -m unittest discover -s tests -v
python scripts/demo.py
python -m compileall -q auto_skill scripts tests
ruff check .
```

搜索关键词：auto-skill、经验蒸馏、Agent Skills、跨 Agent、Claude Code、Codex、过程记忆、自动迭代、用户授权、本地 AI 工具。
