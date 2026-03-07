# Docker Deployment Blueprints

## 1) Spring Boot service Dockerfile (multi-stage)

```dockerfile
# syntax=docker/dockerfile:1.7
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /workspace
COPY pom.xml ./
COPY src ./src
RUN --mount=type=cache,target=/root/.m2 mvn -q -DskipTests package

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=build /workspace/target/*.jar /app/app.jar
EXPOSE 8080
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75"
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
```

## 2) Vue 3 frontend Dockerfile (build + nginx)

```dockerfile
# syntax=docker/dockerfile:1.7
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 3) Local/staging compose baseline

```yaml
services:
  api:
    build:
      context: ./backend
    image: your-registry/your-app-api:dev
    environment:
      SPRING_PROFILES_ACTIVE: docker
    ports:
      - "8080:8080"
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started

  web:
    build:
      context: ./frontend
    image: your-registry/your-app-web:dev
    ports:
      - "8081:80"
    depends_on:
      - api

  mysql:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: app
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-proot"]
      interval: 10s
      timeout: 5s
      retries: 12

  redis:
    image: redis:7.4
```

## 4) Build acceleration baseline

- Enable BuildKit and buildx in CI.
- Use layer cache for Maven and pnpm.
- Export/import build cache for repeated CI jobs.

Example:

```bash
docker buildx build \
  --cache-from type=registry,ref=your-registry/your-app/cache:backend \
  --cache-to type=registry,mode=max,ref=your-registry/your-app/cache:backend \
  -t your-registry/your-app/api:commit-sha ./backend
```

## 5) Production hardening baseline

- Run container as non-root user.
- Pin base image major/minor versions and patch regularly.
- Add health endpoint and configure healthcheck policy.
- Set memory/cpu limits and JVM/container flags consistently.
- Use read-only root filesystem when service allows.
