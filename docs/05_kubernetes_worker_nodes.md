# Kubernetes Worker Nodes

## Overview
Our EKS clusters (`eks-dev-01`, `eks-staging-01`, `eks-prod-01`) run application workloads on managed node groups. This document covers the system requirements for Kubernetes worker nodes, node pool layout, and maintenance.

## System Requirements
Every Kubernetes worker node must meet these requirements:
- **Kubernetes version**: 1.30 (control plane and nodes must stay within one minor version of each other).
- **AMI**: Amazon EKS-optimized Amazon Linux 2023 AMI. Custom AMIs need platform team approval.
- **Minimum size**: 4 vCPU and 16 GiB memory (`m6i.xlarge` or larger). Smaller nodes waste too much capacity on system daemons.
- **Root volume**: 100 GiB gp3, encrypted with the environment KMS key.
- **Container runtime**: containerd 1.7.
- **Networking**: Amazon VPC CNI with prefix delegation enabled. Nodes must run in the private app subnets.
- **IAM**: nodes use the instance role `eks-node-role-<env>`. Pods that need AWS access must use IRSA, not the node role.
- **Required DaemonSets**: `aws-node`, `kube-proxy`, `node-exporter`, `fluent-bit`.

## Node Pools
| Pool | Instance type | Min | Max | Purpose |
|---|---|---|---|---|
| `general` | m6i.xlarge | 3 | 30 | Default for stateless services |
| `compute` | c6i.2xlarge | 0 | 20 | CPU-heavy batch jobs |
| `memory` | r6i.2xlarge | 0 | 10 | Caches and in-memory processing |

Pods are placed on a pool with a node selector, for example `nodepool: compute`. The `compute` and `memory` pools have a taint, so pods also need a matching toleration.

## Autoscaling
- Cluster Autoscaler scales each pool between its min and max.
- Scale-down happens after a node is under 50% utilization for 10 minutes.
- Pods must set CPU and memory requests. Pods without requests are rejected by the admission controller with `ERR_MISSING_RESOURCE_REQUESTS`.

## Maintenance and Upgrades
- Node AMIs are rotated every 30 days, or within 72 hours of a critical CVE.
- Upgrades use rolling replacement: one node at a time per AZ, with `kubectl drain --ignore-daemonsets --delete-emptydir-data`.
- Every service with more than one replica must have a PodDisruptionBudget so drains do not take it fully down.
- Kubernetes minor version upgrades happen in dev first, then staging after 1 week, then production after 2 more weeks.

## Troubleshooting
- Node stuck `NotReady`: check the `aws-node` pod logs and whether the subnet has free IP addresses.
- Pods `Pending` with `Insufficient cpu`: the pool is at its max. Ask the platform team to raise it or move the workload to another pool.
- `ImagePullBackOff` in an isolated VPC: see the VPC and Networking Guide (missing ECR endpoints).
