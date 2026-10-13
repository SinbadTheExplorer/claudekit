// The only keys /e will store. Anything else is dropped, so a forged request
// can't create new rows or smuggle arbitrary text into the dashboard.
//
// NODES and SHOCKS mirror `const NODES` and `const SCENARIOS` in
// bullion-live-map/bullion_mkultra.html. test/worker.test.mjs fails if they
// drift, so add a node or scenario there and here in the same commit.

export const TABS = ['start', 'market', 'analysis', 'causal-link'];

export const NODES = [
  'sec', 'cftc', 'fdic', 'tsy', 'fed', 'fomc', 'ffr', 'banks', 'dealers', 'repo',
  'mmf', 'hf', 'gse', 'yield', 'credit', 'equit', 'mbs', 'tech', 'fins', 'defn',
  'cpi', 'nfp', 'vix', 'usd', 'dxy_fx', 'gold', 'oil', 'china', 'russia', 'geo',
  'deposits', 'm2', 'mortgage', 'privcredit', 'tbills', 'options', 'etf', 'energy',
  'house',
];

export const SHOCKS = [
  'rate_hike', 'vix_spike', 'cpi_rise', 'usd_shock', 'geo_conflict', 'bank_stress',
  'fiscal_stimulus', 'fiscal_tightening', 'trade_war', 'deregulation',
];

export const ALLOWED = {
  visit: new Set(['all']),
  tab: new Set(TABS),
  node: new Set(NODES),
  shock: new Set(SHOCKS),
};
