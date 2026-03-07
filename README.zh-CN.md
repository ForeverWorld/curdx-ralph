<div align="center">

<img src="./assets/logo/curdx-logo.svg" alt="CURDX" width="760" />

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

## 为什么用 CURDX

CURDX 适合希望 Claude Code 产出具备以下特性的团队：

- 一致性：统一 spec 工作流，减少随意提示词
- 可审计：状态文件与进度文件可追溯
- 更稳健：通过 hooks 做工具路由、安全提醒、循环控制
- 可扩展：commands + agents + skills 一体化沉淀

## 快速开始

### 1）安装并加载插件

```bash
git clone https://github.com/ForeverWorld/curdx-ralph.git
cd curdx-ralph
claude --plugin-dir /absolute/path/to/curdx-ralph
```

### 2）启动 spec

```text
/curdx:start my-feature 你的目标描述
```

### 3）推进完整流程

```text
/curdx:requirements
/curdx:design
/curdx:tasks
/curdx:implement
```

## 你能得到什么

### Spec 工作流

- 支持 spec 新建、恢复、切换
- 支持任务循环执行与进度追踪
- 支持 epic 拆解大需求

### Hook 守护

- `SessionStart`：上下文加载 + TDD 守护
- `PreToolUse`：安全提醒 + 工具重定向 + 快速模式约束
- `PostToolUse`：文件检查 + 上下文监控
- `Stop`/`PreCompact`：循环续跑与状态持久化

### 命令体系

- spec 主线命令（`/curdx:start`、`/curdx:tasks`、`/curdx:implement` 等）
- 交付命令（`/curdx:commit`、`/curdx:commit-push-pr`、`/curdx:review-pr`）
- hookify 命令（`/curdx:hookify`、`/curdx:hookify-configure` 等）

完整命令与参数见 [commands/help.md](./commands/help.md)。

### Skills

`skills/` 内置前后端与工程化技能包。

针对国内项目，`cn-java-frontend-architecture` 提供：
- Java + 前端架构选型矩阵
- Docker 部署蓝图与镜像/缓存建议
- 按需启用的信创适配清单（非默认必选）

## 中转过载自动重试

当中转站/上游错误出现（例如 `relay: 当前模型负载过高，请稍后重试`）：

```bash
bash scripts/claude-auto-retry.sh --stop-on-success
```

常用示例：

```bash
# 使用预设
bash scripts/claude-auto-retry.sh --preset relay-common --preset cn-relay-common

# 追加可重试错误
bash scripts/claude-auto-retry.sh --extra-transient "upstream timeout|provider overloaded"

# 追加不可重试错误
bash scripts/claude-auto-retry.sh --extra-non-retriable "insufficient quota|account suspended"
```

## 仓库结构

```text
curdx/
├── .claude-plugin/          # 插件元信息
├── commands/                # slash 命令
├── agents/                  # 子 agent 提示词
├── hooks/                   # hook 注册与脚本
├── scripts/                 # CI 与重试工具
├── skills/                  # 可复用技能包
├── references/              # 流程参考资料
├── templates/               # 各阶段模板
├── schemas/                 # 结构化 schema
└── assets/logo/             # README logo 资源
```

## 质量门禁

### CI 工作流

- [`.github/workflows/quality-gates.yml`](./.github/workflows/quality-gates.yml)
  - shell/python 语法检查
  - 插件契约检查
  - 策略检查
  - hook 行为测试（真实子进程执行，无 mock）
- [`.github/workflows/security-scan.yml`](./.github/workflows/security-scan.yml)
  - Trivy 漏洞与敏感信息扫描（`CRITICAL,HIGH`）

### 本地校验

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

## 常见问题

### `/curdx:start` 中途停了

先执行 `/curdx:status`，多数情况是等待你确认阶段或审批节点。

### 任务循环反复失败

执行 `/curdx:cancel` 清理状态，再用 `/curdx:start` 或 `/curdx:implement` 继续。

### Hook 太严格

优先通过环境变量调优，不建议直接删除 hooks。

## 贡献

贡献规范与校验要求见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 许可证

MIT，详见 [LICENSE](./LICENSE)。
