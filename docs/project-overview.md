# Bullion Mk1 — Project Overview

**Type:** Personal learning and teaching tool  
**Owner:** SinbadTheExplorer (Business student, strong accounting background)  
**Status:** V1 complete as of June 2026  

---

## What It Is

An interactive map of the entire US financial system — built as a single HTML file using D3.js v7. The map lets you click any institution to see how it connects to every other node, what would break if it disappeared, and how shocks (rate hikes, VIX spikes) cascade through the system.

Designed for two audiences: a **Beginner** learning the system top-down, and an **Expert** who wants transmission mechanisms and data sources.

---

## The Problem It Solves

Most financial education presents institutions in isolation (what is the Fed? what is the SEC?). This map shows the *relationships* — what each entity controls, what controls it, and what fails if it disappears. It makes systemic risk visible.

---

## Current Scope (V1)

| Layer | Node Count | Examples |
|---|---|---|
| Monetary Policy | 3 | Federal Reserve, FOMC, Fed Funds Rate |
| Fiscal / Sovereign | 1 | US Treasury |
| Domestic Markets | 3 | Yield Curve, Credit Markets, Equity Markets |
| Equity Sectors | 3 | Tech, Financials, Defensive |
| Sentiment / Vol | 1 | VIX |
| Economic Indicators | 2 | Core CPI, Non-Farm Payrolls |
| FX / Currency | 2 | US Dollar (DXY), EM FX |
| Commodities | 2 | Gold, Oil (WTI) |
| Geopolitics | 3 | China Economy, Russia/Sanctions, Global Trade |
| Regulators | 10 | SEC, FDIC, OCC, CFPB, CFTC, NCUA, FHFA, FSOC, FSB, FINRA |
| Commercial Banking | 12 | JPM, BofA, Wells, Citi, Regional Banks, GSEs, FHLBs, etc. |
| Shadow Banking | 10 | MMFs, Hedge Funds, PE, Insurance, Pension, Repo, MBS, CLOs |
| Infrastructure | 8 | Fedwire, CHIPS, ACH, DTCC, CME Clearing, OCC, SWIFT, FedNow |
| Gov Institutional | 4 | Congress, ESF, OMB, Executive Branch |
| CB Institutional | 5 | NY Fed, Discount Window, QE/QT, OMO, Fed Lending Facilities |
| **Total** | **69 nodes, ~130 links** | |

---

## Key Features

- **Force-directed network** — nodes repel/attract based on relationship strength
- **Beginner / Expert toggle** — switches descriptions AND hides low-weight edges in Beginner mode
- **"What Breaks?" panel** — every node has a failure cascade description
- **Shock simulations** — Rate Hike, VIX Spike, CPI Rise, USD Shock animate how shocks propagate
- **Live market metrics** — US2Y, US10Y, VIX, SPX, CPI displayed in panel
- **AI narrative** — connects to Claude API at runtime (API key prompted, stored in sessionStorage only, never to disk)
- **Mobile responsive** — works on phones and tablets

---

## Technology

- **Visualization:** D3.js v7 (force-directed graph)
- **AI:** Anthropic Claude API (claude-sonnet) via browser-side fetch
- **Format:** Single-file HTML — no build step, no dependencies to install
- **Security:** API key stored in sessionStorage only; `anthropic-dangerous-direct-browser-access` header required for browser-side Anthropic API calls

---

## Agent Pipeline (for future extensions)

Every new node/link session follows:

```
finance-planner → finance-builder → finance-tester
```

Agents live in `.claude/agents/`, skills in `.claude/skills/`. See `CLAUDE.md` for the full workflow.

---

## File Structure

```
claudekit/
├── CLAUDE.md                          ← Workflow guide for agents
├── financial-map.html                 ← The map (primary deliverable)
├── docs/
│   ├── project-overview.md            ← This file
│   └── chrome-mcp-setup.md            ← Claude in Chrome setup guide
├── Interest Rates Presentation.pdf    ← Companion slide deck
├── interest-rate-claude-ai.md         ← Interest rate content transcript
└── LICENSE                            ← Apache 2.0
```

---

## Next Steps (V2 Ideas)

- Add international central banks (ECB, BOJ, PBOC, BOE)
- Add crypto layer (BTC, stablecoins, DeFi protocols, crypto exchanges)
- Add real estate finance layer (mortgage REITs, servicers, GSE pipeline)
- Animated shock traces — highlight path of contagion step by step
- Export to PDF / shareable link
