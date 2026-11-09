# Billing and Cost Policy

## Scope
How cloud costs are tracked, charged back to teams, and controlled. Owned by the FinOps team.

## Cost Allocation
Every billable resource must have these tags:
- `cost-center`: a 4-digit code, for example `CC-4120`.
- `owner`: the owning team's name.
- `environment`: `dev`, `staging`, or `prod`.

Untagged resources are reported daily in the `#finops-alerts` channel. After 7 days untagged, they are stopped (compute) or flagged for deletion (storage).

## Chargeback
- Costs are charged back to each cost center monthly, on the 5th business day.
- Shared platform costs (EKS control planes, NAT gateways, observability stack) are split by each team's share of vCPU-hours on the shared clusters.
- Data transfer between AZs is charged to the team whose pods send the traffic.

## Budgets and Alerts
- Each team has a monthly budget per environment.
- Alerts fire at 50%, 80%, and 100% of the budget.
- At 120% of a **dev** or **staging** budget, non-essential workloads in that environment are scaled to zero until the FinOps team approves more budget.
- Production is never scaled down automatically for budget reasons.

## Environment Cost Rules
- **dev**: workloads are scaled to zero from 20:00 to 07:00 Pacific and on weekends.
- **staging**: isolated VPCs expire after 30 days (see the VPC and Networking Guide). Each isolated VPC costs at least the price of its VPC endpoints, about USD 7.50 per endpoint per AZ per month.
- **prod**: Reserved Instances and Savings Plans cover the baseline. On-demand capacity is for autoscaling only.

## Approved Instance Families
Only these EC2 families may be used without a FinOps exception: `m6i`, `m7i`, `c6i`, `c7i`, `r6i`, `t3` (dev only). GPU instances (`g5`, `p4d`) need an approved exception ticket in the `FIN` queue.

## Invoices
The `billing-worker` service generates customer invoices from usage events. Invoices are stored as PDFs in the S3 bucket `plat-prod-invoices` and kept for 7 years. Invoice IDs use the format `INV-YYYY-NNNNNN`, for example `INV-2026-004213`.

## Refunds and Credits
- Customer credits up to USD 500 can be issued by support.
- Credits above USD 500 need approval from the finance lead.
- Refunds are processed within 10 business days.
