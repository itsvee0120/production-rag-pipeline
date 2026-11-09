# Deployment Runbook

## Scope
How to deploy a service to dev, staging, and production using our internal CLI `infractl` and the CI pipeline.

## Prerequisites
- You are a member of the `deployers` group in the identity provider.
- `infractl` version 4.2 or later is installed (`infractl version`).
- Your service has a Helm chart in the `charts/` directory of its repository.
- The container image is pushed to the internal ECR registry and tagged with the Git commit SHA.

## Standard Deployment Flow
1. Merge to `main`. CI builds the image and pushes it to ECR.
2. CI deploys automatically to **dev**.
3. Promote to **staging**:
   ```
   infractl deploy --env staging --service <name> --image-tag <sha>
   ```
4. Run the smoke tests in staging:
   ```
   infractl smoke --env staging --service <name>
   ```
5. Promote to **production** (requires an approved change ticket, format `CHG-XXXXX`):
   ```
   infractl deploy --env prod --service <name> --image-tag <sha> --change-id CHG-XXXXX
   ```

## Useful Flags
- `--dry-run`: renders the Helm manifests and shows the diff without applying.
- `--canary 10`: sends 10% of traffic to the new version for 15 minutes before full rollout. Required for production deploys of `orders-api` and `auth-service`.
- `--wait-timeout 600`: seconds to wait for pods to become Ready (default 300).
- `--skip-smoke`: skips smoke tests. Only allowed in dev.

## Deployment Windows
- Production deploys are allowed Monday to Thursday, 09:00 to 16:00 Pacific time.
- No production deploys on Fridays, weekends, or during a declared change freeze.
- Hotfixes outside the window need approval from the on-call engineering manager.

## Rollback
1. Find the previous release:
   ```
   infractl history --env prod --service <name>
   ```
2. Roll back to it:
   ```
   infractl rollback --env prod --service <name> --to-revision <n>
   ```
3. Post in the `#deployments` channel with the reason and the change ticket ID.

A rollback must finish within 10 minutes of detecting the issue. If it fails, page the platform on-call.

## Common Errors
- `ERR_IMAGE_NOT_FOUND`: the image tag does not exist in ECR. Check that CI finished.
- `ERR_CHANGE_ID_REQUIRED`: production deploy without `--change-id`.
- `ERR_DEPLOY_WINDOW_CLOSED`: deploy attempted outside the allowed window.
- `ERR_READINESS_TIMEOUT`: pods did not become Ready before `--wait-timeout`. Check pod logs with `kubectl logs`.
