# VPC and Networking Guide

## Overview
Every environment has its own VPC. Teams that need extra network isolation (for example, for load tests or security testing) can provision an **isolated VPC**. This guide explains the standard layout and how to request an isolated VPC in the staging environment.

## Standard VPC Layout
Each environment VPC spans three Availability Zones and has three subnet tiers:
- **Public subnets** (`/24` each): load balancers and NAT gateways only.
- **Private app subnets** (`/20` each): EKS worker nodes and application pods.
- **Private data subnets** (`/24` each): RDS and ElastiCache. No route to the internet.

Outbound internet access from private subnets goes through one NAT gateway per AZ.

## Provisioning an Isolated VPC in Staging
An isolated VPC has no internet gateway, no NAT gateway, and no peering. It reaches AWS services only through VPC endpoints.

### Steps
1. Open a ticket in the `NET` queue with the purpose, owner team, and expected lifetime (maximum 30 days).
2. Pick a free CIDR from the staging isolated range `10.21.0.0/16`. Isolated VPCs use `/20` blocks. Check the allocation sheet linked in the ticket template.
3. Create the VPC with the `isolated-vpc` Terraform module (version 3.x, see the Terraform Modules document):
   ```hcl
   module "isolated_vpc" {
     source      = "git::https://git.internal/platform/terraform-modules.git//isolated-vpc?ref=v3.4.0"
     name        = "stg-iso-<team>-<purpose>"
     cidr_block  = "10.21.16.0/20"
     environment = "staging"
     enable_vpc_endpoints = ["s3", "ecr.api", "ecr.dkr", "logs", "sts"]
   }
   ```
4. Run `terraform plan` and attach the plan output to the `NET` ticket.
5. A platform engineer approves the ticket. Then run `terraform apply` from the CI pipeline (never from a laptop).
6. Tag every resource with `owner`, `cost-center`, and `expires-on`. Resources without an `expires-on` tag are deleted by the nightly cleanup job.

Alternatively, `infractl` can do steps 3 to 5 in one command:
```
infractl vpc create --env staging --isolated --cidr 10.21.16.0/20 --ticket NET-1234
```
The `--isolated` flag removes the internet gateway and NAT gateway and adds the default VPC endpoints.

## Security Groups
- Default deny for all inbound traffic.
- Allow rules must reference other security groups, not CIDR blocks, except for the load balancer.
- Port 22 (SSH) is never opened. Use AWS Systems Manager Session Manager instead.

## DNS
- Internal zone: `svc.internal`. Each service gets `<service>.<env>.svc.internal`.
- Isolated VPCs get a private hosted zone `<vpc-name>.iso.internal` and do not resolve the shared zone.

## Troubleshooting
- Pods cannot pull images in an isolated VPC: check that both `ecr.api` and `ecr.dkr` endpoints exist, plus the `s3` gateway endpoint.
- `terraform apply` fails with `CIDR_OVERLAP`: the chosen block is already allocated. Pick another `/20`.
