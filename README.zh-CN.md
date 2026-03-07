<div align="center">

<img src="./assets/logo/curdx-logo-zh-cn.png" alt="CURDX" width="760" />

# CURDX

**面向 Claude Code 的 Spec 驱动工程化工作流插件**

[English](./README.md) | [简体中文](./README.zh-CN.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Claude Code Plugin](https://img.shields.io/badge/Platform-Claude%20Code-6f42c1)](https://code.claude.com/docs/en/plugins)
[![Quality Gates](https://img.shields.io/badge/CI-Quality%20Gates-2ea44f)](./.github/workflows/quality-gates.yml)
[![Security Scan](https://img.shields.io/badge/Security-Trivy%20Scan-blue)](./.github/workflows/security-scan.yml)

`research -> requirements -> design -> tasks -> implement`

</div>

---

## 项目简介

CURDX 是一个面向团队协作的 Claude Code 插件，目标是把“临时提示词驱动”升级为“可复用、可审计、可持续演进”的工程化交付流程。

它把以下能力合并在一起：
- 规范化的 Spec 生命周期（`research` 到 `implement`）
- 基于状态文件的自动执行闭环
- Hook 守护（安全提醒、工具路由、循环控制）
- 可扩展的命令、技能、Agent、模板与参考资料

## 适用场景

- 你希望多人协作时有统一流程，而不是各写各的提示词
- 你希望需求、设计、任务、执行记录可以追溯
- 你希望自动化执行时依然有质量和安全门禁
- 你希望在单仓或多仓（Monorepo）都能稳定使用

## 安装与加载

### 1. 克隆仓库

```bash
git clone https://github.com/ForeverWorld/curdx-ralph.git
cd curdx-ralph
```

### 2. 加载为 Claude Code 插件

```bash
claude --plugin-dir /absolute/path/to/curdx-ralph
```

### 3. 校验插件（推荐）

```bash
claude plugin validate .
```

## 快速上手

### 标准模式（建议用于正式需求）

```text
/curdx:start user-auth 增加 JWT 认证
/curdx:requirements
/curdx:design
/curdx:tasks
/curdx:implement
```

### 快速模式（减少交互、快速推进）

```text
/curdx:start user-auth 增加 JWT 认证 --quick
```

## 工作流说明

### 阶段链路

1. `research`：调研约束、方案和可行性
2. `requirements`：沉淀需求与验收标准
3. `design`：输出架构与实现策略
4. `tasks`：拆解为可执行任务
5. `implement`：进入自动执行循环并持续更新进度

### 执行循环特点

- 按任务逐个执行，每轮使用清晰上下文
- 可配置任务重试上限
- 可选恢复模式（失败时自动生成修复任务）
- 进度沉淀在 `.progress.md`

## 命令总览

### 主流程命令

| 命令 | 作用 |
|---|---|
| `/curdx:start [name] [goal]` | 智能入口：恢复已有 spec 或创建新 spec |
| `/curdx:new <name> [goal]` | 直接创建 spec |
| `/curdx:research` | 执行或重跑调研阶段 |
| `/curdx:requirements` | 生成需求文档 |
| `/curdx:design` | 生成技术设计 |
| `/curdx:tasks` | 生成实现任务 |
| `/curdx:implement` | 启动执行循环 |
| `/curdx:status` | 查看 spec 状态和进度 |
| `/curdx:switch <name-or-path>` | 切换当前 spec |
| `/curdx:cancel [name-or-path]` | 取消执行循环并清理状态 |

### 配套命令

| 命令 | 作用 |
|---|---|
| `/curdx:triage [epic-name] [goal]` | 把大需求拆成带依赖关系的多个 spec |
| `/curdx:index` | 索引代码与外部资源到 specs/.index |
| `/curdx:refactor` | 执行后按顺序更新 spec 文档 |
| `/curdx:review-pr [aspects]` | 多 Agent 进行 PR 审查 |
| `/curdx:mcp-doctor` | 检查/安装必需 MCP（context7、chrome-devtools） |
| `/curdx:commit` | 创建提交 |
| `/curdx:commit-push-pr` | 提交、推送并创建 PR |
| `/curdx:hookify` | 基于对话分析生成行为约束 hooks |
| `/curdx:hookify-list` | 查看 hookify 规则 |
| `/curdx:hookify-configure` | 启用/禁用 hookify 规则 |
| `/curdx:help` | 查看帮助 |

## 关键参数

- `/curdx:start`
  - `--fresh`：强制创建新 spec
  - `--quick`：跳过阶段交互，直接自动推进
  - `--commit-spec` / `--no-commit-spec`：控制 spec 文件是否自动提交
  - `--specs-dir <path>`：在指定 specs 目录创建
  - `--tasks-size fine|coarse`：任务颗粒度提示
- `/curdx:implement`
  - `--max-task-iterations <n>`：单任务最大重试次数
  - `--max-global-iterations <n>`：全局循环安全上限
  - `--recovery-mode`：失败时自动插入修复任务继续推进

## Spec 存储模型

默认目录结构：

```text
./specs/
├── .current-spec
└── <spec-name>/
    ├── .curdx-state.json
    ├── .progress.md
    ├── research.md
    ├── requirements.md
    ├── design.md
    └── tasks.md
```

支持多目录 specs，通过 `.claude/curdx.local.md` 配置：

```yaml
---
specs_dirs:
  - ./specs
  - ./packages/api/specs
  - ./packages/web/specs
---
```

## 守护与质量

## MCP 配置

检查 MCP 就绪状态：

```bash
bash scripts/mcp-doctor.sh
```

自动安装缺失的已知 MCP：

```bash
bash scripts/mcp-doctor.sh --install-missing
```

也可以通过命令使用：

```text
/curdx:mcp-doctor
/curdx:mcp-doctor --install-missing --scope project
```

默认必需 MCP：
- `context7`
- `chrome-devtools`

控制台自动化能力：
- 对 Nacos、RabbitMQ 这类带网页控制台的服务，CURDX 会规划 MCP 浏览器验证任务：
  - 通过 `chrome-devtools-mcp` 登录并配置
  - 再通过 API/CLI 回读验证（不只看 UI）

### Hook 守护

- `SessionStart`：上下文初始化与 TDD 守护
- `PreToolUse`：安全提醒、工具重定向、快速模式约束
- `PostToolUse`：文件检查与上下文监控
- `Stop`/`PreCompact`：循环连续性与状态持久化

### CI 工作流

- [`.github/workflows/quality-gates.yml`](./.github/workflows/quality-gates.yml)
  - 语法检查、插件契约检查、策略检查、Hook 行为测试
- [`.github/workflows/security-scan.yml`](./.github/workflows/security-scan.yml)
  - Trivy 漏洞与敏感信息扫描（`CRITICAL,HIGH`）

### 本地校验命令

```bash
bash -n hooks/scripts/*.sh scripts/*.sh
python3 -m py_compile hooks/scripts/*.py hooks/scripts/_checkers/*.py scripts/ci/*.py tests/hooks/*.py
python3 scripts/ci/check_plugin_manifest.py
python3 scripts/ci/check_claude_plugin_contract.py
python3 scripts/ci/check_skills_frontmatter.py
python3 scripts/ci/check_local_links.py
python3 scripts/ci/check_forbidden_files.py
python3 scripts/ci/check_workflow_hardening.py
python3 -m unittest discover -s tests/hooks -p 'test_*.py'
claude plugin validate .
```

## 中转过载自动重试

当中转/上游出现负载类错误时，可直接使用：

```bash
bash scripts/claude-auto-retry.sh --stop-on-success
```

常用示例：

```bash
bash scripts/claude-auto-retry.sh --preset relay-common --preset cn-relay-common
bash scripts/claude-auto-retry.sh --extra-transient "upstream timeout|provider overloaded"
bash scripts/claude-auto-retry.sh --extra-non-retriable "insufficient quota|account suspended"
```

## 仓库结构

```text
curdx/
├── .claude-plugin/          # 插件元信息
├── commands/                # slash 命令定义
├── agents/                  # 阶段与执行子 Agent 提示词
├── hooks/                   # hook 注册与脚本
├── scripts/                 # CI 与重试脚本
├── skills/                  # 可复用技能包
├── references/              # 工作流参考文档
├── templates/               # 产物模板
├── schemas/                 # 结构化 schema
└── assets/logo/             # README logo 资源
```

## 常见问题

- `/curdx:start` 中途停住：
  - 先执行 `/curdx:status`，大多数场景是等待阶段确认或审批节点。
- 任务循环反复失败：
  - 尝试 `/curdx:implement --recovery-mode`，或用 `/curdx:cancel` 清理后重新进入。
- 多目录下 spec 重名：
  - 在 `/curdx:switch` 中使用完整路径。

## 贡献

贡献流程与校验要求见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 许可证

MIT，详见 [LICENSE](./LICENSE)。
