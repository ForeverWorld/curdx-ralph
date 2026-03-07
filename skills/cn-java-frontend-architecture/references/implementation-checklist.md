# Implementation Checklist

## 1) Backend baseline

- Use Java 17+ and Spring Boot 3.x baseline.
- Enforce API contracts first: OpenAPI spec + error model + pagination standards.
- Separate domain modules before introducing microservices.
- Use `MyBatis-Plus` for CRUD-heavy modules, keep SQL review for critical paths.
- Define idempotency strategy for write APIs (token/table/unique constraint).
- Add distributed tracing and metrics before pressure testing.

## 2) Service governance baseline

- Service registry/config center standardization.
- Circuit-breaker and rate-limit strategy per critical endpoint.
- Cross-service transaction policy: prioritize eventual consistency + compensation.
- Async event conventions: schema versioning, retry, dead-letter queue, replay procedure.

## 3) Frontend baseline

- Use unified design system tokens and component library policy.
- Define routing/menu/permission model once and version it.
- Build state boundaries: page-local, module-shared, global-shared.
- Set performance budgets: JS bundle, route chunk size, first screen SLA.
- Add API client layer with retry, timeout, and error normalization.

## 4) Delivery baseline

- Branch policy: short-lived branches + mandatory review.
- CI gates: lint, type check, unit tests, contract tests, security scan.
- Deploy strategy: canary or blue-green for high-risk modules.
- Rollback drills: verify rollback in staging before production launch.

## 5) Migration roadmap template

- Day 0-30: define target architecture, baseline standards, pilot module.
- Day 31-60: split 1-2 high-value modules, stabilize CI/CD and observability.
- Day 61-90: expand module/service boundaries, formalize governance playbook.

## 6) Anti-patterns to avoid

- Microservices before modular boundaries are clear.
- Shared database between services as a long-term default.
- Frontend micro-frontend without shared design/system governance.
- Missing contract/version governance for internal APIs and events.

## 7) Xinchuang adaptation baseline (only when required)

- Create a compatibility matrix before architecture freeze.
- Reserve explicit budget/time for compatibility testing and issue fixing.
- Establish a separate acceptance gate for CPU/OS/JDK/DB compatibility.
- Keep environment-specific configuration externalized and versioned.
- Validate Docker runtime policies in target environments, not only in generic cloud VMs.
