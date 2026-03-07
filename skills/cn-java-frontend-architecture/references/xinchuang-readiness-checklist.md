# Xinchuang Readiness Checklist

Use this checklist when the project must align with domestic hardware/software ecosystem and procurement constraints.

## 1) Compatibility matrix (must be explicit)

Build and maintain a matrix across these dimensions:
- CPU architecture variants used by target environments.
- OS distribution and kernel baseline in target environments.
- JDK distribution and version baseline.
- Database engine and JDBC driver versions.
- Middleware stack (registry, MQ, cache, gateway).
- Container runtime and Kubernetes distribution (if used).

Output format should include: supported, conditionally supported, not supported, and mitigation plan.

## 2) Java backend hard requirements

- Freeze Java baseline (typically 17+) and verify JIT/GC behavior on target CPU/OS.
- Avoid native binding lock-in unless there is a fallback path.
- Verify encryption/signature libraries under domestic crypto compliance requirements.
- Test timezone/locale/encoding consistency end-to-end.
- Define SQL compatibility boundaries for non-ANSI behavior.

## 3) Frontend hard requirements

- Lock browser baseline and enterprise desktop runtime assumptions early.
- Validate upload, download, PDF preview, and printing across required browsers.
- Avoid relying on unsupported Web APIs without polyfill/fallback.
- Provide graceful degradation strategy for low-performance client devices.

## 4) Docker and runtime requirements

- Define allowed base image families and tag pinning rules.
- Build multi-arch images where needed and test startup parity.
- Verify image scanning and signature policy in CI.
- Validate container runtime parameters on target OS kernels.
- Predefine fallback deployment path when container runtime is restricted.

## 5) Delivery and acceptance

- Add compatibility test stage in CI/CD (env-labeled test matrix).
- Require compatibility sign-off before production cutover.
- Keep a vendor/cooperation issue register for blocked capabilities.
- Attach rollback and dual-run plan for migration windows.

## 6) Common failure patterns

- Starting certification and compatibility testing too late.
- Assuming x86 performance profile equals target production profile.
- Ignoring browser/runtime constraints in internal desktop environments.
- Shipping container image without validating runtime policy on target clusters.
