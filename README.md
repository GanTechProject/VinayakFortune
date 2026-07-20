---
title: VentureMiner AI — AI Venture Intelligence Platform
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# VentureMiner AI

> **AI Venture Intelligence Platform** — turn market signals into validated, monetizable SaaS opportunities in hours, not quarters.

This repository contains the **complete documentation suite** for VentureMiner AI. Every document is versioned, cross-referenced, and conformant with the governance rules in `docs/00-Governance/00_documentation_governance.md`.

## Quick links

- 📚 **Documentation suite:** [`docs/README.md`](docs/README.md) — full index, reading paths by role, and statistics
- 📄 **PDF bundle:** [`docs/pdfs/`](docs/pdfs/) — 38 generated PDFs, ready to share
- 📋 **Manifest:** [`docs/manifest.json`](docs/manifest.json) — machine-readable metadata for every document
- 💬 **Project history:** [`ChatHistory.txt`](ChatHistory.txt) — the source conversation that defined this project

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

This repository is currently the **specification phase** of the project. No application code has been committed yet. The implementation roadmap in `docs/06-Roadmap/06_implementation_roadmap.md` defines the work that will follow.

## Compliance

All documents in this suite conform to the rules in `docs/00-Governance/00_documentation_governance.md`. See `docs/README.md` for the compliance checklist.
