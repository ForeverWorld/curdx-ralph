# Control Panel Service Catalog (Generic)

> Used by: research-analyst

Use this catalog to recognize common infrastructure services that expose web control panels.
Treat URLs/ports as environment-specific unless explicitly confirmed in the target deployment.

| Service | Detection Keywords | Typical Dev URL (docs examples) | Notes | Official Docs |
|---|---|---|---|---|
| Nacos | `nacos`, `8848` | `http://localhost:8848/nacos` | Bootstrap creds often `nacos/nacos` in quick-start examples | https://nacos.io/en/docs/quick-start/ |
| RabbitMQ Management | `rabbitmq`, `rabbitmq_management`, `15672` | `http://localhost:15672` | `guest` semantics depend on access-control config | https://www.rabbitmq.com/docs/management |
| Grafana | `grafana`, `3000` | `http://localhost:3000` | Sign-in docs show default `admin/admin` for first login | https://grafana.com/docs/grafana/latest/setup-grafana/sign-in-to-grafana/ |
| Keycloak Admin Console | `keycloak`, `kc.sh`, `8080` | `http://localhost:8080/admin/` | Admin bootstrap via env vars is supported | https://www.keycloak.org/docs/latest/server_admin/index.html |
| Jenkins | `jenkins`, `8080`, `jenkins/jenkins` | `http://localhost:8080` | Unlock/setup wizard required on first start | https://www.jenkins.io/doc/book/installing/docker/ |
| Argo CD | `argocd`, `argocd-server` | `https://localhost:8080` (via port-forward in docs) | URL depends on ingress/route in cluster | https://argo-cd.readthedocs.io/en/latest/getting_started/ |
| MinIO Console | `minio`, `console-address`, `9001` | deployment-specific | Console port is explicitly configurable (`--console-address`) | https://min.io/docs/minio/linux/reference/minio-server/minio-server.html |
| Kibana | `kibana`, `5601` | `http://localhost:5601` | Host/port configurable in `kibana.yml` | https://www.elastic.co/docs/deploy-manage/deploy/self-managed/configure-kibana |
| Prometheus Expression Browser | `prometheus`, `9090` | `http://localhost:9090/graph` | Primarily for ad-hoc query/debug | https://prometheus.io/docs/visualization/ |

## Usage Rules

1. Detect service candidates from compose/k8s/env/source.
2. Confirm panel URL/auth source from project config (do not assume defaults blindly).
3. Write `## Control Panel Targets` in `research.md` for each confirmed target.
4. Require dual-proof verification:
   - UI action via MCP `chrome-devtools`
   - API/CLI readback of resulting state
