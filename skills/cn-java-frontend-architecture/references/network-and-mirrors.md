# Network and Mirrors (China-focused)

Use this guide when dependency downloads are unstable or cross-region latency is high.

## Principles

- Prefer enterprise-internal artifact proxy first (Nexus/Artifactory).
- Use one controlled mirror policy per environment; avoid ad-hoc local overrides.
- Keep mirror config in onboarding docs and CI bootstrap scripts.

## Maven mirror template

```xml
<!-- ~/.m2/settings.xml -->
<settings>
  <mirrors>
    <mirror>
      <id>company-mirror</id>
      <name>Company Maven Proxy</name>
      <url>https://your-artifact-proxy.example.com/repository/maven-public/</url>
      <mirrorOf>*</mirrorOf>
    </mirror>
  </mirrors>
</settings>
```

## npm registry template

```bash
npm config set registry https://your-npm-proxy.example.com/
npm config get registry
```

## pnpm registry template

```bash
pnpm config set registry https://your-npm-proxy.example.com/
pnpm config get registry
```

## CI hardening tips

- Cache Maven local repository by lockfile hash or pom hash.
- Cache npm/pnpm store by lockfile hash.
- Add fallback retry for dependency install with bounded backoff.
- Record upstream incident patterns in runbook for quick triage.

## Docker daemon mirror template

```json
{
  "registry-mirrors": [
    "https://your-registry-mirror.example.com"
  ]
}
```

Apply with Docker daemon restart after updating `/etc/docker/daemon.json`.

## Docker build cache tips

- Enable BuildKit/buildx in CI by default.
- Use registry cache backend for cross-runner reuse.
- Keep one cache namespace per repo (or per language runtime) to avoid noisy eviction.

## Official references

- Maven mirror settings: https://maven.apache.org/guides/mini/guide-mirror-settings.html
- npm registry configuration: https://docs.npmjs.com/cli/v11/commands/npm-config
- Docker daemon configuration: https://docs.docker.com/engine/daemon/
- Docker build cache backends: https://docs.docker.com/build/cache/backends/
