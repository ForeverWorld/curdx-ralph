# Web Control Panel Automation (MCP-Only)

> Used by: research-analyst, task-planner

## Purpose

Some backend infrastructure is configured primarily through a web control panel (for example, Nacos and RabbitMQ Management UI).  
For these cases, the workflow must include browser automation through MCP `chrome-devtools`.

## Official Baselines (validate during research)

### Nacos

- Console default URL is typically `http://<host>:8848/nacos`.
- Community quick-start docs commonly show default account/password as `nacos` / `nacos`.
- Treat defaults as bootstrap only. Production must rotate credentials.

### RabbitMQ Management UI

- Management plugin: `rabbitmq_management`.
- Management HTTP API/UI default port: `15672`.
- Default `guest` user access is localhost-only unless explicitly reconfigured.

## Required Research Output

When a spec mentions Nacos/RabbitMQ (or any control-panel service), `research.md` must include:

```markdown
## Control Panel Targets

| Service | URL | Auth Source | Bootstrap Creds | Config Goal | Verify Method |
|---------|-----|-------------|-----------------|-------------|---------------|
| Nacos | http://127.0.0.1:8848/nacos | docker-compose/.env | nacos / nacos | Create namespace + config entry | API readback + UI check |
| RabbitMQ | http://127.0.0.1:15672 | docker-compose/.env | guest / guest (localhost only) | Create exchange/queue/binding | rabbitmqctl or HTTP API |
```

Minimum fields:
- URL (explicit host + port)
- Auth source (where username/password/token comes from)
- Target configuration action
- Non-UI verification method (API/CLI)

## Task Generation Rules

For each control-panel service, generate explicit tasks:

1. **CP1 Startup [VERIFY]**
- Start dependency stack and wait for panel readiness (HTTP 200 or expected login page marker).

2. **CP2 Browser Config [VERIFY]**
- Use `chrome-devtools-mcp` to:
  - open panel URL
  - login with credentials from env/config
  - perform required config actions
  - capture evidence (screenshot or visible value check)

3. **CP3 API/CLI Verify [VERIFY]**
- Verify resulting configuration via service API/CLI (not UI-only proof).

4. **CP4 Cleanup [VERIFY]**
- Stop background services and clean temporary state.

## Guardrails

- Never rely on manual verification text ("manually click/check").
- Never hardcode production credentials in task files.
- If MCP `chrome-devtools` is unavailable, mark as blocked and instruct:
  - `/curdx:mcp-doctor --install-missing`

## Source Links (official docs)

- Nacos quick start (console URL and bootstrap creds examples): https://nacos.io/en/docs/quick-start/
- Nacos auth API examples (default local address `127.0.0.1:8848`): https://nacos.io/en/docs/auth/
- RabbitMQ management plugin guide (`rabbitmq-plugins enable rabbitmq_management`): https://www.rabbitmq.com/docs/management
- RabbitMQ monitoring guide (management HTTP API on `15672`): https://www.rabbitmq.com/docs/monitoring
- RabbitMQ access control (default `guest` user semantics): https://www.rabbitmq.com/docs/access-control
