---
title: VentureMiner AI — AI Venture Intelligence Platform
version: v1.2
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# VentureMiner AI

> **Project name:** VentureMiner AI — AI Venture Intelligence Platform
> **Repository name:** `VinayakFortune` (the GitHub URL slug — a legacy / umbrella identifier; the project itself is **VentureMiner AI**)
> **Suite version:** v1.0
> **Last updated:** 2026-07-20

> **AI Venture Intelligence Platform** — turn market signals into validated, monetizable SaaS opportunities in hours, not quarters.

This repository contains the **complete documentation suite** for **VentureMiner AI**, hosted under the GitHub repository name **`VinayakFortune`**. The two names refer to the same project: `VinayakFortune` is the URL / repo slug, and **VentureMiner AI** is the product. Every document, code module, and artifact in this repo identifies the project as **VentureMiner AI**.

## Quick links

- 📚 **Documentation suite:** [`docs/README.md`](docs/README.md) — full index, reading paths by role, and statistics
- 📄 **PDF bundle:** [`docs/pdfs/`](docs/pdfs/) — 38 generated PDFs, ready to share
- 📋 **Manifest:** [`docs/manifest.json`](docs/manifest.json) — machine-readable metadata for every document
- 💬 **Project history:** [`ChatHistory.txt`](ChatHistory.txt) — the source conversation that defined this project

## Repository naming

- **Repository URL:** `github.com/GanTechProject/VinayakFortune`
- **Project / product name:** **VentureMiner AI**
- **Rationale:** the GitHub repository is named after the host organization / umbrella; the project itself is **VentureMiner AI**. All internal artifacts — every document, code module, and report — refer to the project as **VentureMiner AI**. When in doubt: the project name is the source of truth, the repository name is the URL slug.

## What is VentureMiner AI?

VentureMiner AI is a SaaS platform that helps operators (indie founders, corporate innovators, early-stage investors, and consultants) discover, validate, and act on market opportunities. The product is built on a multi-agent AI architecture with retrieval-augmented generation (RAG), per-tenant memory, and an evidence-disciplined verifier — every claim in every report is bound to a citable source.

The full product vision, requirements, and architecture are specified in the 38-document suite under `docs/`.

## Document counts

| Bucket | Count | Range |
|---|---|---|
| Foundation | 7 | Docs 00–06 |
| AI Architecture | 12 | Docs 07–18 |
| Engineering | 12 | Docs 19–30 |
| Supplementary | 7 | Docs 31–37 |
| **Total** | **38** | Docs 00–37 |

## Repository layout

```
ProjectSAAS/
├── README.md                       # This file
├── ChatHistory.txt                 # Source conversation
├── Makefile                        # top-level targets (make smoke, make lint, ...)
├── docker-compose.yml              # local dev stack
├── services/
│   └── hello-world/                # sample FastAPI service (AC-1.1)
│       ├── app/                    # main.py + test_main.py
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── requirements.txt
│       └── README.md
├── web/                            # Next.js app (lands in #16)
├── ai-plane/                       # AI services (lands in #6-#10)
├── infra/                          # Terraform / IaC (operator-side, #4)
├── .github/workflows/
│   ├── ci-hello-world.yml          # required status check
│   └── docs-lint.yml               # docs structure lint
└── docs/
    ├── README.md                   # Documentation index
    ├── 00-Governance/              # Document 00
    ├── 01-PRD/                     # Document 01
    ├── 02-TRD/                     # Document 02
    ├── 03-ApplicationFlow/         # Document 03
    ├── 04-UIUX/                    # Document 04
    ├── 05-Backend/                 # Document 05
    ├── 06-Roadmap/                 # Document 06
    ├── 07-AI-Architecture/         # Documents 07–18
    ├── 08-Engineering/             # Documents 19–30
    ├── 09-Supplementary/           # Documents 31–37
    ├── pdfs/                       # Generated PDFs
    ├── generate_pdfs.py            # PDF generator (reportlab)
    ├── build_manifest.py           # Manifest builder
    └── manifest.json               # Machine-readable document metadata
```

## Working with the docs

To regenerate PDFs after editing any `.md` file:

```bash
cd docs
python generate_pdfs.py                       # all docs
python generate_pdfs.py --only 01-PRD         # one folder
python generate_pdfs.py --skip-existing       # incremental
```

To rebuild the manifest after adding a new document:

```bash
cd docs
python build_manifest.py
```

Dependencies: `reportlab>=5.0`, `markdown>=3.5`.

## Status

This repository is currently in the **pre-implementation → foundations** transition. The 38-document spec suite (v1.2) is the contract; the **foundations monorepo** (services/hello-world, web/, ai-plane/, infra/, .github/workflows/) is now scaffolded as the entry point for the [issue ledger](https://github.com/GanTechProject/VinayakFortune/issues) (17 issues filed, 115/115 REQ-* IDs cited downstream per the corrected PRD §15.3 traceability matrix). The implementation roadmap in `docs/06-Roadmap/06_implementation_roadmap.md` defines the work that follows.

### Quick start

```bash
make hello-world-test    # RED-first unit tests for the sample service
make lint                # ruff on services/hello-world
make smoke               # test + lint + Docker build
make hello-world-run     # local on :8000
```

## Compliance

All documents in this suite conform to the rules in `docs/00-Governance/00_documentation_governance.md`. See `docs/README.md` for the compliance checklist.

## Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v1.0 | 2026-07-20 | Doc Team | Initial 38-doc suite (Markdown + PDF), pushed to `GanTechProject/VinayakFortune`. |
| v1.1 | 2026-07-20 | Doc Team | Clarified repository vs. project naming: repo is `VinayakFortune`, project is **VentureMiner AI**. |
| v1.2 | 2026-07-20 | Doc Team | Foundations monorepo scaffold: `services/hello-world/` (FastAPI sample, AC-1.1), `web/`, `ai-plane/`, `infra/` placeholders, `Makefile`, `docker-compose.yml`, GitHub Actions workflows (`ci-hello-world`, `docs-lint`). Closes the local-buildable portion of [issue #4](https://github.com/GanTechProject/VinayakFortune/issues/4); the AWS-side ACs (1.3-1.16) remain for the operator-side follow-up. |
