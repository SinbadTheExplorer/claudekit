# add-d3-node

Add one or more planned nodes and their links to financial-map.html.

## When to invoke
After finance-planner has produced a structured node + link spec and you are ready to implement.

## Pre-flight Checks (do these FIRST)

1. Read the current end of the NODES array to find the insertion point
2. Read the current end of the LINKS array to find the insertion point
3. Confirm the node's `group` key exists in GROUP_COLOR — if not, run add-d3-layer first
4. Confirm no node with the same `id` already exists (grep for the id)

```bash
grep -n "id:'" ~/claude-projects/claudekit/financial-map.html | grep "YOUR_NEW_ID"
```

## Node Insertion

Find the end of the NODES array: look for `];` after the last node entry.

Add the new node BEFORE that `];`:
```js
  { id:'NEW_ID', label:'Display Name', group:'GROUP_KEY',
    beginner:'Plain English explanation.',
    expert:'Technical explanation with stats and sources.',
    breaks:'Specific failure cascade if this node is removed.' },
```

## Link Insertion

Find the end of the LINKS array (second `];` — after NODES).

Add new links BEFORE that `];`:
```js
  {s:'source_id', t:'target_id', w:2, sign:+1, why:'Mechanism explanation.'},
```

## Verification After Edit

Run these checks before marking done:
```bash
# Check for syntax errors — node count should be a number, not NaN
grep -c "{ id:'" ~/claude-projects/claudekit/financial-map.html

# Confirm new node ID appears exactly once
grep -c "id:'NEW_ID'" ~/claude-projects/claudekit/financial-map.html
```

Expected: node ID appears exactly 1 time in the file (in the NODES array).

## Common Mistakes to Avoid

- Missing trailing comma after `breaks` value closes the node object but before `},`
- Using double quotes inside a string that uses double quotes — use single quotes throughout JS
- Forgetting to escape apostrophes in strings: `it\'s` not `it's`
- Referencing a node ID in LINKS that doesn't exist in NODES yet
