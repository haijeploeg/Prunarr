# Kubernetes Deployment Guide

This guide covers deploying PrunArr to Kubernetes using the official Helm chart.

## Prerequisites

- Kubernetes cluster (v1.19+)
- Helm 3.x installed
- kubectl configured for your cluster
- API credentials for Radarr, Sonarr, and Tautulli

## Quick Start

### Install with Helm

**Option 1: From OCI Registry (Recommended)**

```bash
# Install directly from GitHub Container Registry
helm install prunarr oci://ghcr.io/haijeploeg/charts/prunarr \
  --version 1.0.0 \
  --set config.radarr.apiKey="your-radarr-api-key" \
  --set config.radarr.url="https://radarr.example.com" \
  --set config.sonarr.apiKey="your-sonarr-api-key" \
  --set config.sonarr.url="https://sonarr.example.com" \
  --set config.tautulli.apiKey="your-tautulli-api-key" \
  --set config.tautulli.url="https://tautulli.example.com"
```

> **Note:** Chart versions are automatically generated from git tags in CI/CD. Browse available versions at [ghcr.io/hploeg/charts/prunarr](https://github.com/hploeg/prunarr/pkgs/container/charts%2Fprunarr)

**Option 2: From Local Chart**

```bash
# Clone the repository
git clone https://github.com/hploeg/prunarr.git
cd prunarr

# Install from local chart
helm install prunarr ./helm/prunarr \
  --set config.radarr.apiKey="your-radarr-api-key" \
  --set config.radarr.url="https://radarr.example.com" \
  --set config.sonarr.apiKey="your-sonarr-api-key" \
  --set config.sonarr.url="https://sonarr.example.com" \
  --set config.tautulli.apiKey="your-tautulli-api-key" \
  --set config.tautulli.url="https://tautulli.example.com"
```

## Deployment Modes

PrunArr supports two deployment modes:

### 1. CronJob Mode (Default - Recommended)

Automatically runs cleanup tasks on a schedule.

```bash
helm install prunarr ./helm/prunarr \
  --set mode=cronjob \
  --set config.radarr.apiKey="..." \
  --set config.sonarr.apiKey="..." \
  --set config.tautulli.apiKey="..." \
  # ... other config
```

**Default Schedules:**
- Movies cleanup: Daily at 2 AM (`0 2 * * *`)
- Series cleanup: Daily at 3 AM (`0 3 * * *`)
- Cache refresh: Disabled (enable with `cronjobs.cacheRefresh.enabled=true`)

### 2. Deployment Mode

Long-running pod for interactive kubectl exec commands.

```bash
helm install prunarr ./helm/prunarr \
  --set mode=deployment \
  --set config.radarr.apiKey="..." \
  # ... other config

# Run commands interactively
kubectl exec -it deployment/prunarr -- prunarr movies list --limit 10
```

## Configuration

### Using values.yaml

Create a `values.yaml` file:

```yaml
# values.yaml
mode: cronjob

image:
  repository: ghcr.io/haijeploeg/prunarr
  tag: "1.0.0"

config:
  radarr:
    apiKey: "your-radarr-api-key"
    url: "https://radarr.example.com"

  sonarr:
    apiKey: "your-sonarr-api-key"
    url: "https://sonarr.example.com"

  tautulli:
    apiKey: "your-tautulli-api-key"
    url: "https://tautulli.example.com"

  cache:
    enabled: true
    maxSizeMb: 100

  logging:
    level: ERROR

cronjobs:
  movies:
    enabled: true
    schedule: "0 2 * * *"  # 2 AM daily
    command: ["movies", "remove", "--watched", "--days-watched", "60", "--force"]

  series:
    enabled: true
    schedule: "0 3 * * *"  # 3 AM daily
    command: ["series", "remove", "--watched", "--days-watched", "60", "--force"]

persistence:
  enabled: true
  size: 1Gi

resources:
  limits:
    cpu: 1000m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 128Mi
```

Install with your values:

```bash
helm install prunarr ./helm/prunarr -f values.yaml
```

### Using External Secrets

For production, use external secret management:

```yaml
# values.yaml
externalSecrets:
  enabled: true
  secretName: "prunarr-api-keys"  # Pre-existing secret
  keys:
    radarrApiKey: "radarr-api-key"
    sonarrApiKey: "sonarr-api-key"
    tautulliApiKey: "tautulli-api-key"
```

Create the external secret:

```bash
kubectl create secret generic prunarr-api-keys \
  --from-literal=radarr-api-key="your-radarr-api-key" \
  --from-literal=sonarr-api-key="your-sonarr-api-key" \
  --from-literal=tautulli-api-key="your-tautulli-api-key"
```

Or use a secret operator like [External Secrets Operator](https://external-secrets.io):

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: prunarr-api-keys
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: SecretStore
  target:
    name: prunarr-api-keys
  data:
    - secretKey: radarr-api-key
      remoteRef:
        key: secret/radarr
        property: api_key
    - secretKey: sonarr-api-key
      remoteRef:
        key: secret/sonarr
        property: api_key
    - secretKey: tautulli-api-key
      remoteRef:
        key: secret/tautulli
        property: api_key
```

## Advanced Configuration

### Custom Schedules

Customize CronJob schedules:

```yaml
cronjobs:
  movies:
    schedule: "0 */6 * * *"  # Every 6 hours

  series:
    schedule: "30 2 * * 0"   # Sundays at 2:30 AM

  cacheRefresh:
    enabled: true
    schedule: "0 */4 * * *"  # Every 4 hours
```

### Resource Limits

Adjust based on your library size:

```yaml
resources:
  limits:
    cpu: 2000m      # 2 CPU cores
    memory: 1Gi     # 1 GB RAM
  requests:
    cpu: 500m       # 0.5 CPU cores
    memory: 256Mi   # 256 MB RAM
```

### Storage Configuration

Use specific storage class:

```yaml
persistence:
  enabled: true
  storageClass: "fast-ssd"  # Your storage class
  size: 5Gi
  accessMode: ReadWriteOnce
```

Or use existing PVC:

```yaml
persistence:
  enabled: true
  existingClaim: "prunarr-cache-pvc"
```

### Node Affinity

Run on specific nodes:

```yaml
nodeSelector:
  disktype: ssd

affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: node-role.kubernetes.io/worker
              operator: In
              values:
                - "true"
```

### Tolerations

Run on tainted nodes:

```yaml
tolerations:
  - key: "dedicated"
    operator: "Equal"
    value: "media"
    effect: "NoSchedule"
```

## Operations

### View CronJob Status

```bash
# List all CronJobs
kubectl get cronjobs -l app.kubernetes.io/instance=prunarr

# View specific CronJob
kubectl describe cronjob prunarr-movies

# View CronJob logs
kubectl logs -l app.kubernetes.io/instance=prunarr,prunarr.io/job-type=movies
```

### View Job History

```bash
# List recent jobs
kubectl get jobs -l app.kubernetes.io/instance=prunarr

# View specific job logs
kubectl logs job/prunarr-movies-28934567

# Get job status
kubectl describe job prunarr-movies-28934567
```

### Manual Job Execution

Trigger a job manually:

```bash
# Movies cleanup
kubectl create job --from=cronjob/prunarr-movies manual-movies-$(date +%s)

# Series cleanup
kubectl create job --from=cronjob/prunarr-series manual-series-$(date +%s)

# Cache refresh
kubectl create job --from=cronjob/prunarr-cache-refresh manual-cache-$(date +%s)
```

### Interactive Commands (Deployment Mode)

```bash
# List movies
kubectl exec -it deployment/prunarr -- prunarr movies list --limit 10

# Dry run removal
kubectl exec -it deployment/prunarr -- prunarr movies remove --watched --days-watched 60 --dry-run

# Cache status
kubectl exec -it deployment/prunarr -- prunarr cache status
```

### Debugging

Enable debug logging:

```bash
helm upgrade prunarr ./helm/prunarr \
  --reuse-values \
  --set config.logging.level=DEBUG
```

View logs:

```bash
# CronJob logs
kubectl logs -l prunarr.io/job-type=movies --tail=100

# Deployment logs
kubectl logs deployment/prunarr -f

# Specific pod
kubectl logs prunarr-movies-28934567-abcde
```

## Upgrades

### Upgrade Chart

```bash
# Update values
helm upgrade prunarr ./helm/prunarr -f values.yaml

# Upgrade with new image tag
helm upgrade prunarr ./helm/prunarr \
  --reuse-values \
  --set image.tag="1.1.0"
```

### Rollback

```bash
# View history
helm history prunarr

# Rollback to previous version
helm rollback prunarr

# Rollback to specific revision
helm rollback prunarr 3
```

## Uninstall

```bash
# Uninstall release
helm uninstall prunarr

# Also delete PVC (if needed)
kubectl delete pvc prunarr-cache
```

## Multi-Environment Deployment

Deploy to different namespaces:

```bash
# Production
helm install prunarr-prod ./helm/prunarr \
  --namespace production \
  --create-namespace \
  -f values-prod.yaml

# Staging
helm install prunarr-staging ./helm/prunarr \
  --namespace staging \
  --create-namespace \
  -f values-staging.yaml
```

## Monitoring & Alerts

### Prometheus Integration

Add ServiceMonitor for metrics (if using Prometheus Operator):

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: prunarr
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: prunarr
  endpoints:
    - port: metrics
      interval: 30s
```

### Alert Rules

Example PrometheusRule for failed jobs:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: prunarr-alerts
spec:
  groups:
    - name: prunarr
      interval: 5m
      rules:
        - alert: PrunArrJobFailed
          expr: kube_job_status_failed{job_name=~"prunarr-.*"} > 0
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "PrunArr job {{ $labels.job_name }} failed"
```

## Troubleshooting

### CronJob Not Running

**Check schedule:**
```bash
kubectl get cronjob prunarr-movies -o jsonpath='{.spec.schedule}'
```

**Check suspended status:**
```bash
kubectl get cronjob prunarr-movies -o jsonpath='{.spec.suspend}'
# Should be false
```

### Job Failures

**View failed job logs:**
```bash
kubectl logs -l job-name=prunarr-movies-28934567 --tail=100
```

**Check job events:**
```bash
kubectl describe job prunarr-movies-28934567
```

### API Connection Issues

**Test connectivity from pod:**
```bash
kubectl exec -it deployment/prunarr -- wget -O- https://radarr.example.com/api/v3/system/status
```

### Cache Issues

**Check PVC status:**
```bash
kubectl get pvc prunarr-cache
kubectl describe pvc prunarr-cache
```

**Verify cache directory:**
```bash
kubectl exec -it deployment/prunarr -- ls -la /home/prunarr/.prunarr/cache
```

## Best Practices

1. **Use External Secrets** - Don't store API keys in values.yaml
2. **Enable Persistence** - Cache improves performance significantly
3. **Set Resource Limits** - Prevent resource exhaustion
4. **Monitor Jobs** - Set up alerts for failed jobs
5. **Test with Dry Run** - Always test with `--dry-run` first
6. **Separate Environments** - Use different namespaces for prod/staging
7. **Version Lock** - Pin image tags, don't use `latest`
8. **Regular Backups** - Backup your configuration and secrets

## Examples

### Minimal Production Setup

```yaml
mode: cronjob

externalSecrets:
  enabled: true
  secretName: prunarr-secrets

config:
  radarr:
    url: "https://radarr.example.com"
  sonarr:
    url: "https://sonarr.example.com"
  tautulli:
    url: "https://tautulli.example.com"

cronjobs:
  movies:
    enabled: true
    schedule: "0 2 * * *"
  series:
    enabled: true
    schedule: "0 3 * * *"

persistence:
  enabled: true
  storageClass: "fast-ssd"
  size: 5Gi

resources:
  limits:
    cpu: 1000m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 128Mi
```

## Next Steps

- [Docker Guide](DOCKER.md) - Docker deployment options
- [Configuration Guide](CONFIGURATION.md) - Detailed configuration
- [Quick Start Guide](QUICK_START.md) - Common workflows
