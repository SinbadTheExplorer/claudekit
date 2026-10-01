# Bullion Mk1 — US Financial System Interactive Map

## Project Overview

This project builds a comprehensive interactive map of the US financial system as a personal learning and teaching tool. The map is a single HTML file (`financial-map.html`) using D3.js v7.

**Current state**: `financial-map.html` — force-directed network, dark gold theme, Beginner/Expert toggle, shock simulations, AI narrative via Claude API.

**Target**: ~100 nodes across all major US financial system layers (monetary policy, fiscal, regulators, commercial banking, shadow banking, markets, FX/commodities, infrastructure, geopolitics).

---

## Agent Pipeline: Planner → Builder → Tester

Every content addition session follows this exact flow:

```
finance-planner → finance-builder → finance-tester
      ↓                  ↓                ↓
  Plan nodes          Implement         Validate
  Plan links          Edit HTML         Report FAILs
  Output JSON         Verify JS         → back to builder
```

### Step 1: Invoke `finance-planner`
Use when: deciding what nodes to add next, or when you need structured node/link specs.

Skills available:
- `/plan-nodes` — apply the 4-question framework to a list of institutions
- `/plan-connections` — map transmission mechanisms between nodes

Output: JSON-formatted node specs + link specs ready for the builder.

### Step 2: Invoke `finance-builder`
Use when: implementing planned nodes/links into `financial-map.html`.

Skills available:
- `/add-d3-layer` — add a new group to GROUP_COLOR + LAYER_LABELS + GROUP_DEPTH
- `/add-d3-node` — append nodes and links to the NODES/LINKS arrays

Rules:
- Always add a new layer BEFORE adding nodes that use it
- Never modify existing 20 nodes or 46 original links
- Always verify no duplicate IDs before and after editing

### Step 3: Invoke `finance-tester`
Use when: after every builder session, before reporting completion.

Skills available:
- `/validate-plan` — cross-check implementation against the plan
- `/test-ui` — verify code features (API key, edge toggle, breaks panel)

Output: PASS/FAIL/WARNING report. FAILs go back to builder. WARNINGs are reported to user.

---

## The Implementation Plan

Full plan: `~/.claude/plans/20260629-rippling-honking-lark.md`

### Priority Order for Node Addition

| Session | Layer | Nodes | Status |
|---|---|---|---|
| A | Regulators | SEC, FDIC, OCC, CFPB, CFTC, NCUA, FHFA, FSOC, FSB, FINRA | ✓ Done |
| B | Commercial Banking | JPM, BofA, Wells, Citi, Regional Banks, Inv Banks, Fannie, Freddie, FHLBs, Primary Dealers, Interbank | ✓ Done |
| C | Shadow Banking | MMFs, Hedge Funds, PE, Insurance, Pension Funds, Broker-Dealers, Repo, Commercial Paper, MBS, CLOs | ✓ Done |
| D | Infrastructure | Fedwire, CHIPS, ACH, DTCC, CME Clearing, OCC Clearing, SWIFT, FedNow | ✓ Done |
| E | Gov + CB Institutional | Congress, ESF, OMB, Executive, NY Fed, Discount Window, QE/QT, OMO, Fed Facilities | ✓ Done |
| F | Monetary Plumbing + Asset Mgmt / Households / Ratings | SOFR, Bank Reserves+IORB, Reverse Repo (RRP), TGA; BlackRock, Vanguard, State Street, ETF Complex; Households, Consumer Credit; Credit Rating Agencies | ✓ Done |
| G | G-SIBs + Bond Complex + Macro Gauges + Exchanges | Citi, Wells, Goldman, Morgan Stanley, Ginnie Mae; IG Bonds, HY Bonds, Munis, TIPS; PCE, GDP, Unemployment, ISM/PMI; NYSE, Nasdaq, Cboe, ICE | ✓ Done |
| H | Crypto + Fintech + Real Estate + International + Derivatives | Stablecoins, Bitcoin, Crypto Exchanges; Card Networks, Wallets, Fintech Lenders; Residential RE, CRE, REITs; Foreign CBs, Foreign Holders, IMF/BIS, Eurodollar; IRS, CDS, OTC Derivatives | ✓ Done |

Update the Status column after each builder session.

**Map size:** 108 nodes / 251 links / 23 layers as of sessions A–H (target ~100 exceeded).

---

## File Structure

```
claudekit/
├── CLAUDE.md                          ← This file (workflow + project guide)
├── financial-map.html                 ← The interactive map (primary deliverable)
├── Interest Rates Presentation.pdf   ← Companion slide deck (interest rates node)
├── interest-rate-claude-ai.md         ← Source transcript for interest rate content
├── LICENSE                            ← All rights reserved (was Apache 2.0 before 2026-10-01)
└── .claude/
    ├── agents/
    │   ├── finance-planner.md         ← Planning agent
    │   ├── finance-builder.md         ← Implementation agent
    │   └── finance-tester.md          ← QA/validation agent
    └── skills/
        ├── finance-planner/
        │   ├── plan-nodes.md          ← 4-question framework skill
        │   └── plan-connections.md    ← Link mapping skill
        ├── finance-builder/
        │   ├── add-d3-node.md         ← Node/link insertion skill
        │   └── add-d3-layer.md        ← Layer group addition skill
        └── finance-tester/
            ├── validate-plan.md       ← Plan alignment check skill
            └── test-ui.md             ← Code feature verification skill
```

---

## Content Standards (enforced by finance-planner)

Every node MUST have:
- `beginner`: plain English, 1–2 sentences, analogy optional
- `expert`: technical explanation with at least one cited data source
- `breaks`: specific failure cascade — what concretely fails if this node is removed

Every link MUST have:
- `w` (1/2/3): transmission strength
- `sign` (+1/-1/0): direction when source rises
- `why`: the mechanism, not the correlation

---

## Background: User Context

- Business student, beginner finance level, strong accounting basics
- Goal: personal learning + future teaching use
- Explain the WHY behind structures
- End complex topics with a TLDR
- Back stats with sources (FRED, BLS, Fed, BIS, WGC, IIF, WTO)
- Be critical — flag flawed categorizations before mistakes are made
