# infra/ — Infrastructure as Code

Terraform modules, environment configs, and the dependency stack manifests.
The actual provisioning ships in the operator-side work for issue #4 (AC-1.3
through AC-1.16). This directory is the home for that work.

## Source documents

- Document 02 (TRD) §3 (System Topology)
- Document 08-Engineering/23 (DevOps) — all sections, especially §3 IaC and §4 Environments
- Document 08-Engineering/24 (CI/CD)
- Document 08-Engineering/28 (Operations Guide)
- Document 00-Governance/branch_protection.json — canonical branch policy

## Status

**Stub.** The directory exists so the monorepo scaffold (AC-1.1) is complete.
The first Terraform commit will land in a follow-up PR after the human
operator provisions the AWS account and Secrets Manager.
