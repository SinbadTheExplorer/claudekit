# validate-plan

Check that the builder's implementation matches the finance-planner's specification.

## When to invoke
After the finance-builder completes a session of adding nodes/links.

## Step 1: Read the Plan

Read the plan file:
```
~/.claude/plans/rippling-honking-lark.md
```

Extract the list of required nodes from the "Missing layers" section.

## Step 2: Read the Implementation

Read the HTML file:
```
~/claude-projects/claudekit/financial-map.html
```

## Step 3: Cross-Reference Checks

### Node presence check
For each required institution in the plan, verify a node with a matching label/id exists:

Required per plan:
**Regulators**: SEC, FDIC, OCC, CFPB, CFTC, NCUA, FHFA, FSOC, FSB, FINRA
**Commercial Banking**: JPMorgan Chase, Bank of America, Wells Fargo, Citigroup, Regional Banks, Community Banks, Investment Banks, Fannie Mae, Freddie Mac, FHLBs, Primary Dealers, Interbank Lending
**Shadow Banking**: Money Market Funds, Hedge Funds, Private Equity, Insurance Companies, Pension Funds, Broker-Dealers, Repo Market, Commercial Paper, MBS Market, CLOs
**Infrastructure**: Fedwire, CHIPS, ACH Network, DTCC, CME Clearing, Options Clearing Corp, SWIFT, FedNow
**Gov Institutional**: Congress, ESF, OMB, Executive Branch
**CB Institutional**: NY Federal Reserve, Discount Window, QE/QT / Fed Balance Sheet, Open Market Operations, Fed Lending Facilities

### Field completeness check
For each node added in this session, verify:
- `beginner` field is non-empty and plain-language
- `expert` field cites at least one real data source
- `breaks` field describes a specific failure cascade

### Link integrity check
For each new link, verify:
- Source node ID exists in NODES
- Target node ID exists in NODES
- `why` field is non-empty

## Step 4: Report

Produce a table:

```
REQUIRED NODES CHECK
Node                  | Status
----------------------|---------
SEC                   | ✓ FOUND (id: sec)
FDIC                  | ✓ FOUND (id: fdic)
DTCC                  | ✗ MISSING
...

FIELD COMPLETENESS
Node ID   | beginner | expert | breaks
----------|----------|--------|--------
sec       | ✓        | ✓      | ✓
fdic      | ✓        | ✗      | ✓  ← missing data source

LINK INTEGRITY
All X new links: valid sources and targets ✓
OR
FAIL: Link s='dtcc_bad' — no such node

OVERALL: X/Y required nodes present
```
