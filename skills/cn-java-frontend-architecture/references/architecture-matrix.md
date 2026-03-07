# Architecture Matrix (China-ready)

## TOC
- Backend patterns
- Frontend patterns
- Combined reference architectures

## Backend patterns

| Scenario | Recommended pattern | Core stack | Why this works | Main risks |
| --- | --- | --- | --- | --- |
| New business, 3-8 engineers | Modular monolith | Spring Boot, MyBatis-Plus, Redis | Fast delivery, low ops burden, easy refactor to services later | Poor module boundaries can become big ball of mud |
| Legacy monolith modernization | Layered modularization first | Spring Boot 3, domain modules, event outbox | Lowest migration risk, keeps release continuity | Mixed old/new style during transition |
| Multi-team medium scale | Microservices (Spring ecosystem) | Spring Cloud Alibaba: Nacos, Sentinel, Seata, RocketMQ | Strong ecosystem fit for Spring teams; service governance + resilience | Higher platform complexity and ops cost |
| High-throughput RPC-heavy domain | Service mesh + RPC style | Dubbo, registry/config center, gateway | High performance RPC and mature governance patterns | RPC contract evolution discipline is required |
| Transaction-heavy cross-service business | Microservices + compensation | SCA + Seata/TCC + idempotency | Better control over eventual consistency | Business compensation complexity |
| Strong integration requirements | Event-driven integration | RocketMQ/Kafka + outbox + CDC | Decouples systems and stabilizes peak traffic | Debugging async chains is harder |
| Xinchuang/regulated projects | Compatibility-first layered architecture | Spring Boot, JDBC compatibility layer, vendor-certified middleware | Reduces procurement/compliance risk and late-stage rework | Certification and performance testing cycles are longer |

## Frontend patterns

| Scenario | Recommended pattern | Core stack | Why this works | Main risks |
| --- | --- | --- | --- | --- |
| Admin/back-office platform | SPA | Vue 3, Vite, Pinia, Element Plus | Fast iteration, rich ecosystem, strong team adoption in CN | SEO weak, first screen depends on optimization |
| Public content/product pages with SEO | SSR/Hybrid | Nuxt or Next.js | Better SEO and first contentful paint | Full-stack complexity and infra overhead |
| Multi-team independent frontend releases | Micro-frontend | qiankun + Vue/React subapps | Team autonomy and independent deployment | Shared deps/version governance complexity |
| API orchestration + multi-end consistency | BFF | Node/Nest or Spring gateway BFF | Reduces frontend coupling to microservice topology | BFF can become bottleneck without ownership |

## Combined reference architectures

1. `Default enterprise`:
- Backend: modular monolith (Spring Boot + MyBatis-Plus + Redis)
- Frontend: Vue 3 SPA
- Fit: most internal systems and SaaS admin portals

2. `Scalable platform`:
- Backend: Spring Cloud Alibaba microservices + event bus
- Frontend: Vue 3 SPA + optional BFF
- Fit: multi-team, high release frequency

3. `Large organization frontend platform`:
- Backend: microservices (SCA or Dubbo based on team skill)
- Frontend: qiankun micro-frontend + design system governance
- Fit: many squads with independent product lines

4. `SEO + transaction platform`:
- Backend: modular monolith or microservices based on complexity
- Frontend: SSR (Nuxt/Next) + BFF
- Fit: search-heavy user acquisition + complex domain transactions

5. `Xinchuang enterprise`:
- Backend: modular architecture with strict compatibility boundaries
- Frontend: Vue 3 SPA with controlled browser/runtime baseline
- Deployment: Docker image standards with domestic OS/CPU validation matrix
- Fit: projects requiring domestic hardware/software ecosystem alignment
