# Terraform Modules

## Overview
All infrastructure is built from shared modules in the `platform/terraform-modules` repository. Modules are versioned with Git tags and referenced with `?ref=<tag>`. Never reference a branch.

## Current Module Versions
| Module | Current version | Previous (legacy) version | Legacy end of support |
|---|---|---|---|
| `vpc` | v3.4.0 | v2.9.1 | 2026-12-31 |
| `isolated-vpc` | v3.4.0 | v2.9.1 | 2026-12-31 |
| `eks-cluster` | v5.1.2 | v4.6.0 | 2026-11-30 |
| `eks-node-group` | v5.1.2 | v4.6.0 | 2026-11-30 |
| `rds-postgres` | v2.3.0 | v1.8.4 | 2027-03-31 |
| `s3-bucket` | v1.7.0 | none | n/a |

The v2.x network modules and v4.x EKS modules were the standard until last month's platform release (October 2026). They are now **legacy**: they still work but receive only security fixes until their end-of-support date.

## What Changed in v3.x Network Modules
- **Isolated VPCs are only supported in v3.x.** The legacy `vpc` v2.9.1 module has no `isolated` option and always creates an internet gateway. Provisioning an isolated VPC with v2.x modules is not supported. You must upgrade to `isolated-vpc` v3.x.
- VPC endpoints are configured with the list variable `enable_vpc_endpoints` instead of one boolean per endpoint (`enable_s3_endpoint`, `enable_ecr_endpoint` in v2.x).
- Subnet sizes are computed from `cidr_block` automatically. The v2.x variables `public_subnets` and `private_subnets` were removed.

## What Changed in v5.x EKS Modules
- Default Kubernetes version is 1.30 (v4.x defaulted to 1.28).
- Node groups use Amazon Linux 2023 AMIs. v4.x used Amazon Linux 2, which is not allowed for new node groups.
- IRSA is enabled by default.

## Upgrading from Legacy Modules
1. Change the `?ref=` tag to the current version.
2. Rename removed variables (see the changelog in the module's `CHANGELOG.md`).
3. Run `terraform plan` and check for resource **replacements**. A VPC replacement destroys everything inside it.
4. If the plan replaces a VPC or cluster, use `terraform state mv` or `moved` blocks to keep the existing resources. Ask in `#platform-help` if unsure.
5. Apply in dev, then staging, then production.

## State and Locking
- Remote state is stored in the S3 bucket `plat-tfstate-<env>` with DynamoDB table `plat-tf-locks` for locking.
- Never run `terraform apply` from a laptop against staging or production. Use the CI pipeline.
- If a lock is stuck, use `terraform force-unlock <lock-id>` only after confirming in `#platform-help` that no apply is running.

## Module Usage Rules
- Pin exact versions (`?ref=v3.4.0`), not ranges.
- Do not fork modules into service repositories. Propose changes as pull requests to `platform/terraform-modules`.
- Every module call must pass `environment` and `tags` (including `owner` and `cost-center`).
