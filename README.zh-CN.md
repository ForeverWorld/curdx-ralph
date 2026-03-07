# CURDX

[English](./README.md) | [简体中文](./README.zh-CN.md)

CURDX 是一个面向 **Claude Code** 的插件仓库，目标是把“从想法到交付”的开发链路标准化：

- 用 spec 驱动调研、需求、设计、任务拆解
- 用 hooks 在会话期间做质量守护（TDD、安全、上下文、工具使用）
- 用命令把常见工程动作沉淀成可复用流程（实现、重构、评审、PR）
- 用 skills 注入可复用的领域知识

如果你希望在 Claude Code 里落地一套可复用、可审计、可持续迭代的工程流程，这个仓库就是为这个目的设计的。

## 适用场景

- 你希望团队稳定执行 spec-driven 开发。
- 你希望 AI 编码过程自带质量约束，而不是只做事后检查。
- 你需要可扩展的命令、agent、skill 组合。
- 你希望把团队实践固化成插件能力。

## 核心能力

### 1) Spec 工作流（CURDX 主线）

完整流程：`research -> requirements -> design -> tasks -> implement`

- 支持新建 spec、恢复执行、切换 spec、多目录 specs
- 支持任务循环执行与进度追踪
- 支持 Epic 拆解（triage）

### 2) Hook 质量守护

CURDX 内置多种会话生命周期钩子（见 `hooks/hooks.json`）：

- `SessionStart`：加载上下文并执行 TDD 守护
- `PreToolUse`：安全提醒、工具路由、快速模式约束
- `PostToolUse`：文件检查与上下文监控
- `UserPromptSubmit`：TDD 守护与 hookify 规则
- `PreCompact` / `Stop`：状态持久化与收尾检查

### 3) 命令体系

仓库提供面向日常开发的 slash commands：

- spec 主线命令
- Git/PR 辅助命令
- hookify 规则管理命令
- 评审与重构命令

### 4) Skills 库

`skills/` 提供可复用技能包，覆盖前后端和工程化主题（如 `nextjs`、`spring-boot`、`vitest`、`vue`、`typescript-core`）。

## 快速开始

### 前置要求

- 已安装 Claude Code
- 可用的 `bash` 与 `python3`（hooks 和校验脚本依赖）
- 建议在 Git 仓库内使用

### 安装与加载

```bash
git clone https://github.com/ForeverWorld/curdx-ralph.git
cd curdx-ralph

claude --plugin-dir /absolute/path/to/curdx-ralph
```

### 首次运行

在 Claude 会话中执行：

```text
/curdx:start my-feature 你的目标描述
```

然后按流程推进：

```text
/curdx:requirements
/curdx:design
/curdx:tasks
/curdx:implement
```

## 命令参考

### Spec 工作流

| Command | 说明 |
| --- | --- |
| `/curdx:start [name] [goal]` | 智能入口（新建或恢复） |
| `/curdx:new <name> [goal]` | 新建 spec |
| `/curdx:research` | 调研阶段 |
| `/curdx:requirements` | 需求阶段 |
| `/curdx:design` | 设计阶段 |
| `/curdx:tasks` | 任务拆解阶段 |
| `/curdx:implement` | 执行循环 |
| `/curdx:status` | 查看当前状态 |
| `/curdx:switch <name>` | 切换活动 spec |
| `/curdx:cancel` | 取消并清理状态 |
| `/curdx:triage` | 大需求拆分为多个 spec |
| `/curdx:refactor` | 执行后回写 spec 文档 |
| `/curdx:index` | 建立索引提示 |
| `/curdx:feedback` | 提交反馈 |
| `/curdx:help` | 帮助 |

### 交付与评审

| Command | 说明 |
| --- | --- |
| `/curdx:commit` | 创建提交 |
| `/curdx:commit-push-pr` | 提交 + 推送 + 创建 PR |
| `/curdx:review-pr` | PR 评审流程 |
| `/curdx:clean-gone` | 清理远端已删的本地分支 |

### Hookify

| Command | 说明 |
| --- | --- |
| `/curdx:hookify` | 创建 hook 规则 |
| `/curdx:hookify-list` | 查看已配置规则 |
| `/curdx:hookify-configure` | 交互式配置规则 |
| `/curdx:hookify-help` | Hookify 帮助 |

详细参数与示例可见 [commands/help.md](./commands/help.md)。

## 仓库结构

```text
curdx/
├── .claude-plugin/         # 插件元信息（plugin.json）
├── commands/               # slash command 定义
├── agents/                 # 子 Agent 提示词
├── hooks/
│   ├── hooks.json          # hook 事件注册
│   └── scripts/            # hook 脚本实现
├── skills/                 # 可复用技能包
├── references/             # 流程参考资料
├── templates/              # 生成模板
└── scripts/ci/             # CI 校验脚本
```

## Hook 日志与调试

默认日志位置：

- `~/.curdx/logs/hooks.log`
- `~/.curdx/logs/hooks.jsonl`
- `~/.curdx/logs/hooks.<hook_name>.log`
- `~/.curdx/logs/hooks.<hook_name>.jsonl`
- `~/.curdx/logs/sessions/<session>/...`

常用环境变量：

- `CURDX_HOOK_LOG=0`：关闭 hook 日志
- `CURDX_HOOK_LOG_LEVEL=DEBUG|INFO|WARN|ERROR`：设置最低日志级别
- `CURDX_HOOK_LOG_SPLIT=0`：关闭按 hook 分文件
- `CURDX_HOOK_LOG_JSONL=0`：关闭 JSONL 输出
- `CURDX_HOOK_LOG_SESSION_SPLIT=0`：关闭按会话分目录

实时查看：

```bash
tail -f ~/.curdx/logs/hooks.log
tail -f ~/.curdx/logs/hooks.tool_redirect.log
```

日志摘要分析：

```bash
python3 hooks/scripts/analyze_hook_logs.py --since-minutes 60
python3 hooks/scripts/analyze_hook_logs.py --session <session-id> --since-minutes 180
```

## CI 与本地校验

GitHub Actions（`.github/workflows/quality-gates.yml`）会检查：

- hooks 脚本 shell/python 语法
- 插件清单元数据
- skills frontmatter
- markdown 本地链接

本地可直接执行：

```bash
bash -n hooks/scripts/*.sh
python3 -m py_compile hooks/scripts/*.py hooks/scripts/_checkers/*.py scripts/ci/*.py
python3 scripts/ci/check_plugin_manifest.py
python3 scripts/ci/check_skills_frontmatter.py
python3 scripts/ci/check_local_links.py
```

## 开发说明

### 新增命令

1. 在 `commands/` 下新增 `*.md`
2. 填写 frontmatter（至少 `description`）
3. 在 README/帮助文档补充说明

### 新增 Hook

1. 在 `hooks/hooks.json` 注册事件和 matcher
2. 在 `hooks/scripts/` 新增实现脚本
3. 本地跑语法检查
4. 验证日志与行为符合预期

### 新增 Skill

1. 新建 `skills/<skill-name>/SKILL.md`
2. 保持 frontmatter 完整
3. 用 `scripts/ci/check_skills_frontmatter.py` 校验

## 常见问题

### `/curdx:start` 停住不继续

先执行 `/curdx:status` 查看 phase，通常是等待你确认后再进入下一阶段。

### 任务循环反复失败

先用 `/curdx:cancel` 清理状态，再通过 `/curdx:start` 或 `/curdx:implement` 恢复。

### Hook 太严格，影响探索速度

建议先通过环境变量调低约束，再逐步恢复，不建议直接删 hooks。

## 贡献

欢迎提交 Issue / PR。PR 描述建议包含：

- 改动动机
- 影响范围（`commands` / `hooks` / `skills`）
- 验证方式（本地命令或截图）

## License

`.claude-plugin/plugin.json` 当前声明为 `MIT`。
如果对外分发，建议补充根目录 `LICENSE` 文件以避免歧义。
