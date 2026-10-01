# add-d3-layer

Add a new layer group (color + label + depth) to financial-map.html.

## When to invoke
Before adding nodes from a new layer that doesn't yet exist in GROUP_COLOR.

## The Three Objects to Update

All three must be updated atomically. If you update only one, nodes from that group will render incorrectly.

### 1. GROUP_COLOR
Find the closing `};` of the GROUP_COLOR object and insert before it:
```js
  NEW_KEY: '#hexcolor',  // Layer display name
```

### 2. LAYER_LABELS
Find the closing `};` of the LAYER_LABELS object and insert before it:
```js
  NEW_KEY: 'Layer Display Name',
```

### 3. GROUP_DEPTH
Find the closing `};` of the GROUP_DEPTH object and insert before it:
```js
  NEW_KEY: 2,
```
Depth values: 3=core (Fed, FFR), 2=important, 1=peripheral.

## New Layers for This Project

| Key | Color | Label | Depth |
|---|---|---|---|
| silver | #b8bcc8 | Regulators | 2 |
| cobalt | #7b9ed9 | Commercial Banking | 2 |
| violet | #9b8fd9 | Shadow Banking | 2 |
| iron | #8a9ba8 | Infrastructure | 2 |
| dkblue | #5a7fbf | Gov Institutional | 2 |
| indigo | #7b7fd9 | CB Institutional | 3 |

## Verification

After editing, check that all three appear:
```bash
grep -E "silver|cobalt|violet|iron|dkblue|indigo" ~/claude-projects/claudekit/financial-map.html | head -20
```

Each new key should appear exactly 3 times: once in GROUP_COLOR, once in LAYER_LABELS, once in GROUP_DEPTH.
