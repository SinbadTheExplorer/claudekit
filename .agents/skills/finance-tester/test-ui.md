# test-ui

Verify that financial-map.html's code features are correctly implemented.

## When to invoke
After the finance-builder adds new code features (not just nodes/links). Also run as a final check before marking any session complete.

## Checks to Run (all via file reading — no browser needed)

### Check 1: API Key Integration
```bash
grep -n "getApiKey\|anthropic_key\|sessionStorage" ~/claude-projects/claudekit/financial-map.html
```
**Expected**: 
- `getApiKey` function defined
- `sessionStorage.getItem('anthropic_key')` present
- `sessionStorage.setItem('anthropic_key'` present
- `getApiKey()` used in the fetch headers

### Check 2: Expert Mode Edge Toggle
```bash
grep -n "graphLinkSel\|display.*expertMode\|expertMode.*display" ~/claude-projects/claudekit/financial-map.html
```
**Expected**: `_graphLinkSel.style('display'` inside `toggleExpertMode`

### Check 3: "What Breaks?" Panel
```bash
grep -n "dp-breaks\|breaks" ~/claude-projects/claudekit/financial-map.html | head -20
```
**Expected**:
- `id="dp-breaks"` in HTML section
- `d.breaks` read in `openDetail` function
- `dp-breaks` populated with text

### Check 4: All New Layer Groups Consistent
```bash
grep -n "silver\|cobalt\|violet\|iron\|dkblue\|indigo" ~/claude-projects/claudekit/financial-map.html | grep -v "^\s*//"
```
**Expected**: Each of the 6 new keys appears in GROUP_COLOR, LAYER_LABELS, AND GROUP_DEPTH (3 occurrences each minimum, plus however many nodes use them).

### Check 5: No Broken JS (syntax spot-check)
```bash
grep -c "{ id:'" ~/claude-projects/claudekit/financial-map.html
grep -c "{s:'" ~/claude-projects/claudekit/financial-map.html
```
**Expected**: Both return integer counts ≥ 20 (nodes) and 46 (links) respectively.

### Check 6: Anthropic CORS Header
```bash
grep -n "anthropic-dangerous-direct-browser-access" ~/claude-projects/claudekit/financial-map.html
```
**Expected**: This header must be present in the fetch call or the browser will block the API request.

## Report Format

```
UI FEATURE TEST REPORT
======================
Check 1 (API key):          PASS / FAIL — [detail]
Check 2 (edge toggle):      PASS / FAIL — [detail]
Check 3 (breaks panel):     PASS / FAIL — [detail]
Check 4 (layer groups):     PASS / FAIL — [detail]
Check 5 (JS syntax):        PASS / FAIL — [count: X nodes, Y links]
Check 6 (CORS header):      PASS / FAIL — [detail]

SUMMARY: X/6 checks passed
```

If any FAIL: hand back to finance-builder with exact line numbers to fix.
