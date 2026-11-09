# Platform Architecture Overview

## Purpose
This document describes the internal service architecture of our cloud infrastructure platform. It is the starting point for new engineers and the reference for design reviews.

## Environments
We run three isolated environments. Each lives in its own AWS account and its own VPC:

| Environment | AWS account alias | Region | VPC CIDR |
|---|---|---|---|
| dev | `plat-dev` | us-west-2 | 10.10.0.0/16 |
| staging | `plat-staging` | us-west-2 | 10.20.0.0/16 |
| production | `plat-prod` | us-west-2 (primary), us-east-2 (DR) | 10.30.0.0/16 |

Traffic between environments is not allowed. There is no VPC peering between staging and production.

## Core Services
- **edge-gateway**: Public entry point. Terminates TLS on an Application Load Balancer and routes requests to internal services.
- **auth-service**: Issues short-lived JWTs (15 minutes). Backed by a PostgreSQL database on Amazon RDS.
- **orders-api**: Main business API. Runs on Kubernetes (EKS) worker nodes.
- **billing-worker**: Consumes usage events from an SQS queue and writes invoices. See the Billing Policy document.
- **metrics-pipeline**: Ships logs and metrics to the central observability stack (Prometheus + Grafana, logs in OpenSearch).

## Compute
All stateless services run on Amazon EKS. Each environment has one EKS cluster:
- `eks-dev-01`
- `eks-staging-01`
- `eks-prod-01`

Worker node requirements and node pool sizing are described in the Kubernetes Worker Nodes document.

## Data Stores
- PostgreSQL 15 on RDS (Multi-AZ in production only).
- Redis 7 on ElastiCache for sessions and rate limiting.
- S3 for artifacts, backups, and invoice PDFs. All buckets enforce SSE-KMS encryption.

## Infrastructure as Code
All infrastructure is defined in Terraform. Manual changes in the AWS console are not allowed outside of a declared incident. Module versions and upgrade rules are in the Terraform Modules document.

## Ownership
- Platform team: VPCs, EKS clusters, Terraform modules.
- Service teams: their own Kubernetes deployments and Helm charts.
- FinOps team: billing policies, budgets, and cost alerts.
