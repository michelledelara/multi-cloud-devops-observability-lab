# AWS × Azure × OCI

These are functional mappings; scope and semantics are not identical across providers.

| Capability | AWS | Microsoft Azure | OCI |
|---|---|---|---|
| Main account boundary | AWS account | Subscription within a tenant | Tenancy |
| Resource organization | Accounts, tags, resource groups | Resource Group | Compartments |
| Private network | VPC | VNet | VCN |
| Virtual machine | EC2 instance | Azure Virtual Machine | Compute instance |
| Object storage | S3 | Blob Storage | Object Storage |
| Managed Kubernetes | EKS | AKS | OKE |
| Container registry | ECR | ACR | OCIR |
| Identity/access | IAM | Entra ID and Azure RBAC | OCI IAM and policies |
| Workload identity | IAM roles | Managed identities | Instance/resource principals |
| Monitoring | CloudWatch | Azure Monitor | OCI Monitoring |
| Logs | CloudWatch Logs | Log Analytics | OCI Logging |
| Network filtering | Security Groups and network ACLs | NSGs | Security Lists and NSGs |
| Native/managed IaC route | CloudFormation | ARM/Bicep | Resource Manager running Terraform |
| Terraform provider | hashicorp/aws | hashicorp/azurerm | oracle/oci |

An Azure Resource Group is a lifecycle/management container, not a direct equivalent of an AWS account. An OCI compartment is an organizational and policy scope within a tenancy. OCI Resource Manager manages Terraform workflows rather than introducing a separate native declarative language.

In this repository, Terraform manages Azure and OCI and CloudFormation manages AWS. EKS, AKS, OKE, cloud registries and cloud VMs are mappings for architectural context, not resources provisioned by these definitions.
