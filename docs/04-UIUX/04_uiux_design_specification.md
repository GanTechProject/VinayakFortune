---
title: UI/UX Design Specification
version: v1.0
date: 2026-07-20
author: VentureMiner AI Documentation Team
status: Approved
---

# UI/UX Design Specification

> **Document 04 — VentureMiner AI**
> The canonical design specification. Defines the design system, screen inventory, interaction patterns, and accessibility standards. Source of truth for every visual decision; deviations require a new revision.

## Table of Contents

1. Purpose & Scope
2. Design Principles
3. Brand & Voice
4. Information Architecture
5. Navigation Model
6. Design Tokens
7. Typography
8. Color System
9. Iconography
10. Spacing & Layout Grid
11. Components Library
12. Screen Inventory
13. Screen Specifications
14. Interaction Patterns
15. Empty / Loading / Error States
16. Motion & Microinteractions
17. Accessibility
18. Responsive Strategy
19. Internationalization
20. Dark Mode
21. Performance Budgets (visual)
22. Design Quality Checklist
23. Appendix

## 1. Purpose & Scope

This document is the design contract. It governs the look, feel, and behavior of every user-facing surface. Where this document disagrees with code, **this document wins** until the next revision.

### 1.1 In scope

- Design tokens (color, typography, spacing, motion).
- Component library contracts.
- Screen inventory + per-screen specs.
- Accessibility and responsive strategy.
- Visual states (empty, loading, error).

### 1.2 Out of scope

- Marketing site (handled by Web team outside this suite).
- Mobile native apps (v2+).
- Print design (handled inside reports via Document 09).

## 2. Design Principles

1. **Clarity over cleverness.** Every screen must answer "what is this and what do I do?" in < 5 seconds.
2. **Evidence, not assertion.** Visual hierarchy favors source citations and traces.
3. **Operator-grade density.** A senior researcher must be able to scan a portfolio in one screen.
4. **Calm by default.** The system is research-focused; visual noise is a defect.
5. **Bias to legibility.** Body text ≥ 14px; never sacrifice readability for compactness.

## 3. Brand & Voice

### 3.1 Voice

- **Authoritative but humble.** State conclusions with confidence; cite the evidence.
- **Specific over vague.** Prefer "12,400 monthly searches" to "lots of interest".
- **Operator's language.** Use domain terms (TAM, GTM, CAC) without dumbing them down.

### 3.2 Tone spectrum

| Context | Tone |
|---|---|
| Empty states | Encouraging, instructive |
| Error states | Apologetic, actionable |
| Success | Brief, factual |
| Reports | Analytical, neutral |

## 4. Information Architecture

```
Home (/)
├── Marketing (one-pager)
└── App (/app)
    ├── Onboarding (/app/onboarding)
    ├── Dashboard (/app/dashboard)
    ├── Discovery (/app/discovery)
    │   ├── Search (/app/discovery/search)
    │   ├── Trends (/app/discovery/trends)
    │   └── Pains (/app/discovery/pains)
    ├── Opportunities (/app/opportunities)
    │   ├── List (/app/opportunities)
    │   ├── Detail (/app/opportunities/:id)
    │   └── Compare (/app/opportunities/compare)
    ├── Validations (/app/validations)
    │   └── Detail (/app/validations/:id)
    ├── Reports (/app/reports)
    │   ├── Briefs (/app/reports/briefs)
    │   ├── Full (/app/reports/full)
    │   └── Compare (/app/reports/compare)
    ├── Portfolio (/app/portfolio)
    ├── Watchlists (/app/watchlists)
    └── Settings (/app/settings)
        ├── Workspace
        ├── Members
        ├── Rubric
        ├── Sources
        ├── Integrations
        ├── API tokens
        ├── Billing
        └── Audit log
```

## 5. Navigation Model

- **Top nav (persistent)**: logo · workspace switcher · global search (Cmd-K) · notifications · avatar.
- **Left rail (contextual)**: app sections.
- **Breadcrumb** (deep pages): workspace › section › page.
- **Quick action bar (bottom)**: floating "Run Discovery" / "Validate" / "Generate Brief".

### 5.1 Global search (Cmd-K)

- Indexes: opportunities, reports, sources, watchlists, members, settings pages.
- Keyboard-first; results in < 50ms p75.
- Recent + suggested surfaced above results.

## 6. Design Tokens

Tokens are stored in a JSON file (exported to CSS variables and JS).

### 6.1 Token structure

```json
{
  "color": { "primary": { "50": "...", "500": "...", "900": "..." } },
  "font":  { "size": { "xs": 12, "sm": 14, "base": 16, "lg": 18, "xl": 20, "2xl": 24, "3xl": 30, "4xl": 36 } },
  "space": { "0": 0, "1": 4, "2": 8, "3": 12, "4": 16, "5": 20, "6": 24, "8": 32, "10": 40, "12": 48, "16": 64 },
  "radius":{ "sm": 4, "md": 8, "lg": 12, "xl": 16, "full": 9999 },
  "shadow":{ "sm": "...", "md": "...", "lg": "..." }
}
```

## 7. Typography

| Role | Family | Size | Weight | Line-height |
|---|---|---|---|---|
| Display | Inter | 36 / 30 | 700 | 1.1 |
| H1 | Inter | 24 | 700 | 1.25 |
| H2 | Inter | 20 | 600 | 1.3 |
| H3 | Inter | 18 | 600 | 1.4 |
| Body | Inter | 16 | 400 | 1.5 |
| Small | Inter | 14 | 400 | 1.5 |
| Mono | JetBrains Mono | 14 | 400 | 1.5 |

- **Minimum body size:** 14px (small), 16px (body). Reports may use 11px for footnotes.
- **Long-form report body:** 16–17px, 1.6 line-height for reading.

## 8. Color System

### 8.1 Brand palette

| Token | Hex | Use |
|---|---|---|
| primary-500 | `#2563EB` | Primary actions, links |
| primary-600 | `#1D4ED8` | Hover |
| primary-700 | `#1E40AF` | Pressed |

### 8.2 Semantic palette

| Token | Light | Dark | Use |
|---|---|---|---|
| success | `#10B981` | `#34D399` | Pass, positive |
| warning | `#F59E0B` | `#FBBF24` | Caution |
| danger  | `#EF4444` | `#F87171` | Error, destructive |
| info    | `#3B82F6` | `#60A5FA` | Informational |

### 8.3 Neutral palette (slate)

| Token | Hex |
|---|---|
| slate-50 | `#F8FAFC` |
| slate-100 | `#F1F5F9` |
| slate-200 | `#E2E8F0` |
| slate-300 | `#CBD5E1` |
| slate-400 | `#94A3B8` |
| slate-500 | `#64748B` |
| slate-600 | `#475569` |
| slate-700 | `#334155` |
| slate-800 | `#1E293B` |
| slate-900 | `#0F172A` |

### 8.4 Score color scale (used in scoring UI)

| Range | Color |
|---|---|
| 0.0 – 3.0 | `#EF4444` (red) |
| 3.0 – 5.5 | `#F59E0B` (amber) |
| 5.5 – 7.5 | `#10B981` (green) |
| 7.5 – 10  | `#0EA5E9` (sky) |

## 9. Iconography

- **Set:** Phosphor (regular weight default; bold for emphasis).
- **Size:** 16px (inline), 20px (UI), 24px (feature), 32px (illustrations).
- **Color:** inherits from text by default; never rainbow-coded.

## 10. Spacing & Layout Grid

- **Base unit:** 4px.
- **Common spacing:** 4, 8, 12, 16, 20, 24, 32, 40, 48, 64.
- **Container max-width:** 1440px (app), 720px (read view).
- **Grid:** 12 columns, 24px gutter, 16px outer margin (≥ 768px viewport).
- **Breakpoints:** `sm 640 / md 768 / lg 1024 / xl 1280 / 2xl 1536`.

## 11. Components Library

The component library is implemented in React + Radix + Tailwind. Each component has:

- A **contract** (props, behavior, accessibility).
- **States** (default, hover, focus, active, disabled, loading, error).
- **Storybook** story.
- **Tests** (unit + visual).

### 11.1 Core components

| Component | Variants | Notes |
|---|---|---|
| `Button` | primary, secondary, ghost, danger; size sm/md/lg | Disabled / loading / icon-only |
| `Input` | text, number, password, search, url | Error state with inline help |
| `Textarea` | auto-resize | |
| `Select` | single, multi, async, combobox | Headless via Radix |
| `Combobox` | search + multi | Used for tags, sources |
| `DateRangePicker` | presets + custom | |
| `Tabs` | line, pill | |
| `Table` | sortable, filterable, paginated, virtualized | Sticky header |
| `Card` | default, outlined, elevated | |
| `Modal` | sm/md/lg/xl; destructive variant | Focus-trapped |
| `Drawer` | right, bottom (mobile) | |
| `Toast` | success, info, warning, error | Auto-dismiss 4s |
| `Tooltip` | light/dark; top/bottom/left/right | |
| `Popover` | | |
| `Dialog` | | Modal variant |
| `Accordion` | single, multi | |
| `Avatar` | with status dot | |
| `Badge` | tone variants | |
| `Breadcrumb` | | |
| `Pagination` | | |
| `EmptyState` | illustration + CTA | |
| `LoadingSkeleton` | line, block, table | |
| `ProgressBar` | determinate, indeterminate | |
| `ScoreBadge` | | Color by range |
| `CitationPopover` | | Shows source on hover |
| `EvidencePanel` | | Lists cited evidence |
| `RubricEditor` | | Drag-and-drop dimensions |
| `ReportPreview` | | Read-only render |
| `Alert` | banner | |

## 12. Screen Inventory

Screens are tagged with the ID format `SCR-<AREA>-NNN`.

| ID | Screen | Route | Auth |
|---|---|---|---|
| SCR-AUTH-001 | Sign in | `/app/signin` | Public |
| SCR-AUTH-002 | Sign up | `/app/signup` | Public |
| SCR-AUTH-003 | Email verification | `/app/verify` | Public |
| SCR-AUTH-004 | MFA challenge | `/app/mfa` | Partial |
| SCR-OB-001 | Onboarding tour | `/app/onboarding` | Auth |
| SCR-OB-002 | Sample opportunity | `/app/onboarding/sample` | Auth |
| SCR-DASH-001 | Dashboard | `/app/dashboard` | Auth |
| SCR-DISC-001 | Discovery search | `/app/discovery/search` | Auth |
| SCR-DISC-002 | Discovery results | `/app/discovery/search/:runId` | Auth |
| SCR-DISC-003 | Trends dashboard | `/app/discovery/trends` | Auth |
| SCR-DISC-004 | Pain feed | `/app/discovery/pains` | Auth |
| SCR-OPP-001 | Opportunity list | `/app/opportunities` | Auth |
| SCR-OPP-002 | Opportunity detail | `/app/opportunities/:id` | Auth |
| SCR-OPP-003 | Compare | `/app/opportunities/compare` | Auth |
| SCR-VAL-001 | Validation detail | `/app/validations/:id` | Auth |
| SCR-SCORE-001 | Rubric list | `/app/settings/rubric` | Admin |
| SCR-SCORE-002 | Rubric editor | `/app/settings/rubric/:id` | Admin |
| SCR-RPT-001 | Brief viewer | `/app/reports/briefs/:id` | Auth |
| SCR-RPT-002 | Full report viewer | `/app/reports/full/:id` | Auth |
| SCR-RPT-003 | Compare report | `/app/reports/compare/:id` | Auth |
| SCR-PORT-001 | Portfolio | `/app/portfolio` | Auth |
| SCR-WATCH-001 | Watchlists | `/app/watchlists` | Auth |
| SCR-WS-001 | Workspace settings | `/app/settings/workspace` | Admin |
| SCR-WS-002 | Members | `/app/settings/members` | Admin |
| SCR-INT-001 | Integrations | `/app/settings/integrations` | Admin |
| SCR-API-001 | API tokens | `/app/settings/api` | Admin |
| SCR-BILL-001 | Billing | `/app/settings/billing` | Admin |
| SCR-AUDIT-001 | Audit log | `/app/settings/audit` | Admin (Ent) |
| SCR-ERR-001 | 404 | `/app/404` | Public |
| SCR-ERR-002 | 500 | `/app/500` | Public |

## 13. Screen Specifications

A representative spec for the most important screen.

### 13.1 SCR-DASH-001 — Dashboard

**Purpose:** Give a returning user a 5-second read on what changed and what to do next.

**Layout:**

```
┌────────────────────────────────────────────────────────────┐
│ Top nav (logo · workspace · search · alerts · avatar)     │
├──────────────┬─────────────────────────────────────────────┤
│              │ Hello, {name} — {date}                      │
│  Left rail   │                                             │
│  (sections)  │ ┌─────────── KPI strip ───────────────────┐ │
│              │ │ Opportunities · Reports · Score avg.   │ │
│              │ └────────────────────────────────────────┘ │
│              │                                             │
│              │ ┌─── Watchlist feed ────┐ ┌─── Trends ──┐  │
│              │ │                        │ │              │  │
│              │ └────────────────────────┘ └──────────────┘ │
│              │                                             │
│              │ ┌─────────── Quick actions ──────────────┐ │
│              │ │ + New discovery · + Validate · + Report │ │
│              │ └────────────────────────────────────────┘ │
│              │                                             │
│              │ ┌─────────── Activity feed ──────────────┐  │
│              │ │ Recent runs, alerts, member actions     │  │
│              │ └─────────────────────────────────────────┘  │
└──────────────┴─────────────────────────────────────────────┘
```

**Behavior:**

- KPI strip links to filtered lists.
- Trends panel shows top 5 trends in user's watched categories.
- Activity feed paginates 20 per page; infinite scroll on mobile.

**States:**

- Empty (new user): 3 sample opportunities CTA.
- Loading: skeleton blocks.
- Error: retry banner + reload.

**Accessibility:**

- All sections have headings (`h2`).
- All KPIs are links with descriptive `aria-label`.
- Color is not the only signal for score color-coding — value always text.

### 13.2 SCR-OPP-002 — Opportunity detail

**Layout:**

```
┌─ Header ─────────────────────────────────────────────────┐
│ Title · Status · Score badge · Actions (Validate, Brief)  │
├─ Tabs ───────────────────────────────────────────────────┤
│ Overview · Validation · Report · Notes · History         │
├──────────────────────────────────────────────────────────┤
│ Overview tab                                              │
│ ┌─── Key facts ─────────┐ ┌─── Score breakdown ────────┐ │
│ │ Market size, growth,  │ │ Dimensions, weights,        │ │
│ │ demand, GTM, risks    │ │ sub-scores, rationale       │ │
│ └────────────────────────┘ └─────────────────────────────┘ │
│ ┌─── Evidence panel ─────────────────────────────────────┐│
│ │ Cited snippets, sources, freshness                     ││
│ └────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

**Behavior:**

- Tabs are deep-linkable (`?tab=validation`).
- Evidence panel shows citations as hover popovers and a clickable list.
- Score breakdown is expandable per dimension.

**Accessibility:**

- Tabs use ARIA tabs pattern.
- Each evidence item has a screen-reader-readable source.

### 13.3 SCR-OPP-003 — Compare

- A 2-up layout by default; up to 4 opportunities per screen.
- Sticky header with scores.
- Highlight differing cells in amber.
- "Generate comparison report" CTA.

## 14. Interaction Patterns

### 14.1 Destructive actions

- Always confirm via modal with explicit "Type the title to confirm" for hard deletes.
- Provide a 5-second "undo" toast where state allows.

### 14.2 Async runs (Discovery, Validation, Report)

- Inline progress with step list.
- SSE-driven; falls back to polling every 5s on error.
- User can navigate away; result delivered to in-app + email.
- User can cancel.

### 14.3 Long-form content

- Reports use a separate "read view" with serif option (toggle).
- Footnotes are inline (hover) and a sidebar list.

### 14.4 Bulk actions

- Selection state in lists; bulk bar appears at top.
- Confirm for bulk destructive.

### 14.5 Cmd-K

- Always available; index updated on view.

## 15. Empty / Loading / Error States

### 15.1 Empty state template

```
[Illustration]
Headline (1 line)
Subhead (1–2 lines, what to do)
Primary CTA
Secondary link
```

### 15.2 Loading

- Skeletons for predictable layouts.
- Spinner for actions.
- Progress for long-running tasks (with ETA when known).

### 15.3 Error

- Inline for field errors; banner for page errors; full-page for 500s.
- Always includes a "what to do next" — retry, contact support, return.

## 16. Motion & Microinteractions

- **Durations:** fast 120ms, default 200ms, slow 320ms.
- **Easing:** `cubic-bezier(0.2, 0.8, 0.2, 1)` (standard), `cubic-bezier(0.4, 0, 0.2, 1)` (decelerate).
- **Use motion for:** state transitions, focus changes, score updates.
- **Avoid motion for:** content shuffling during reading, distracting micro-loops.
- **Reduced motion:** respect `prefers-reduced-motion`.

## 17. Accessibility

- **WCAG 2.1 AA** is the minimum.
- All interactive elements keyboard-reachable.
- Focus order matches reading order.
- Visible focus ring (`2px solid primary-500`).
- Color contrast: ≥ 4.5:1 body, ≥ 3:1 large text, ≥ 3:1 UI components.
- Form fields have labels (no placeholder-only).
- Errors announced via `aria-live="polite"`.
- Tables use `<th scope>` and captions.
- Modals trap focus and restore on close.
- Charts have a text alternative (table or summary).

## 18. Responsive Strategy

- **Mobile-first.**
- **Breakpoints:** sm 640 / md 768 / lg 1024 / xl 1280.
- App is **desktop-first** (≥ 1024); below that, it is a **read + quick-action** view.
- Reports are **responsive** (single column on mobile, multi-column on desktop).
- Tables collapse to stacked cards on < 768.

## 19. Internationalization

- All strings externalized (`t('...')`).
- Date/number/currency via `Intl`.
- No hard-coded text in components.
- Right-to-left deferred to v3.

## 20. Dark Mode

- Default to system preference; user override in settings.
- Tokens designed to swap automatically.
- Charts re-palette for dark mode.
- Avoid pure black; use slate-900 background.

## 21. Performance Budgets (visual)

See TRD §8.3 for the page-level JS/CSS budgets. The visual budget is:

- No layout shift > 0.1 CLS.
- LCP < 2.5s p75.
- TTI < 3.0s p75 on dashboard.

## 22. Design Quality Checklist

Before merging UI code, designers + engineers confirm:

- [ ] Matches tokens (no hard-coded values).
- [ ] States (default, hover, focus, active, disabled, loading, error) implemented.
- [ ] Keyboard navigable.
- [ ] Screen reader tested.
- [ ] Color contrast verified.
- [ ] Reduced motion respected.
- [ ] Empty / loading / error states designed.
- [ ] Storybook story added.
- [ ] Visual regression test added.
- [ ] Responsive at sm/md/lg/xl verified.
- [ ] Dark mode verified (if supported).

## 23. Appendix

### 23.1 Component-to-screen matrix (excerpt)

| Component | Used on |
|---|---|
| `ScoreBadge` | Dashboard, Opportunity list, Compare, Report |
| `CitationPopover` | Opportunity detail, Report, Validation |
| `RubricEditor` | Settings |
| `ReportPreview` | Report viewer, Compare report |

### 23.2 Revision history

| Version | Date | Author | Summary |
|---|---|---|---|
| v0.5 | 2026-07-20 | Doc Team | All sections drafted |
| v1.0 | 2026-07-20 | Doc Team | First approved version |

### 23.3 Cross-references

- Application flows: Document 03.
- Accessibility policy: Document 21 (Security).
- Performance: Document 02 §8.

---

> *End of Document 04 — UI/UX Design Specification. Tokens are the source of truth; any new value must be added to the token system first.*
