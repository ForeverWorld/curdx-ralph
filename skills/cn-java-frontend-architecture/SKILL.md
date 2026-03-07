---
name: cn-java-frontend-architecture
description: Use this skill when the user asks for China-ready Java + frontend architecture selection, migration, or implementation (single-service, modular monolith, microservices, BFF, micro-frontend, SSR, Docker/Compose/Kubernetes deployment, Xinchuang readiness, admin platform, integration architecture).
license: MIT
compatibility: Claude Code
metadata:
  author: curdx
  version: 1.0.0
  category: architecture
  tags: china,java,spring-boot,mybatis-plus,dubbo,spring-cloud-alibaba,vue,vite,qiankun,docker,compose,kubernetes
---

# CN Java + Frontend Architecture

Use this skill to produce implementation-ready architecture decisions for China-focused teams, especially when projects need stable delivery under local network and ecosystem constraints.

## When to trigger

Trigger when user asks about:
- "国产化" or China-ready stack selection
- "信创适配" or domestic CPU/OS/database compatibility
- Java backend architecture choices (single app vs microservice vs RPC)
- Frontend architecture choices (SPA/SSR/micro-frontend/BFF)
- Migration from legacy Java monolith to scalable architecture
- Multi-team platform governance and engineering standards

## Workflow

1. Classify project profile: team size, domain complexity, traffic, release cadence, compliance.
2. Pick backend pattern from `references/architecture-matrix.md`.
3. Pick frontend pattern from `references/architecture-matrix.md`.
4. Apply delivery baseline from `references/implementation-checklist.md`.
5. If network instability exists, apply dependency/proxy guidance from `references/network-and-mirrors.md`.
6. Select Docker deployment blueprint from `references/docker-deployment-blueprints.md`.
7. If the project has Xinchuang/compliance requirements, apply `references/xinchuang-readiness-checklist.md`.
8. Output an ADR-style result: selected architecture, rejected options, migration steps, risk controls.

## Default baseline (if user gives no constraints)

- Backend: `Spring Boot 3.x + MyBatis-Plus + Redis + MySQL/PostgreSQL + OpenAPI`
- Auth: `Sa-Token` (session/JWT mode based on deployment)
- Frontend admin: `Vue 3 + Vite + Pinia + Vue Router + Element Plus`
- Container: multi-stage Docker build + Compose for local/staging + K8s-ready manifests
- Observability: `Micrometer + Prometheus + Grafana`
- Delivery: trunk-based + CI quality gates + staged rollout

## Escalation rules

- Need strong service governance and multi-language RPC: evaluate `Apache Dubbo`.
- Need Spring ecosystem microservices with registry/config/flow control/transaction: evaluate `Spring Cloud Alibaba` stack.
- Need independent multi-team frontend release: evaluate `qiankun` micro-frontend.
- Need SEO or edge rendering: choose SSR (`Nuxt` or `Next.js`) over plain SPA.
- Need higher deployment consistency across dev/staging/prod: standardize on Docker image contracts and runtime env templates.
- Need government/regulated procurement alignment: add Xinchuang compatibility baseline and certification plan (optional path, not default).

## Output contract

Always provide:
- One recommended architecture with explicit trade-offs.
- One fallback architecture (lower complexity path).
- Docker runtime topology (single-host compose vs cluster).
- 30/60/90 day migration plan.
- Risk list with concrete mitigations (performance, consistency, release risk, team skills).
