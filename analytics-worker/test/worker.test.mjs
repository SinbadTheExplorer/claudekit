// Run: node --test analytics-worker/test/   (Node 22.5+ for node:sqlite)
// D1 is stood in for by an in-memory SQLite with the real schema.sql. The
// real-D1 check is `wrangler dev --local` (see README "Verify locally").

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import worker, { purge, today, dashboardCsp } from '../src/index.js';
import { NODES, SHOCKS, TABS } from '../src/allowlist.js';

const here = new URL('.', import.meta.url);
const ORIGIN = 'https://sinbadtheexplorer.github.io';
const TOKEN = 'x'.repeat(40);

function d1() {
  const db = new DatabaseSync(':memory:');
  db.exec(readFileSync(new URL('../schema.sql', here), 'utf8'));
  const stmt = (sql, args = []) => ({
    bind: (...a) => stmt(sql, a),
    run: async () => ({ meta: { changes: Number(db.prepare(sql).run(...args).changes) } }),
    all: async () => ({ results: db.prepare(sql).all(...args) }),
    _exec: () => db.prepare(sql).run(...args),
  });
  return {
    raw: db,
    prepare: sql => stmt(sql),
    batch: async list => { db.exec('BEGIN'); try { list.forEach(s => s._exec()); db.exec('COMMIT'); } catch (e) { db.exec('ROLLBACK'); throw e; } },
  };
}

function env(over = {}) {
  return { DB: d1(), ALLOWED_ORIGIN: ORIGIN, SALT_SECRET: 's'.repeat(32), STATS_TOKEN: TOKEN, ...over };
}

function beacon(body, headers = {}) {
  const text = typeof body === 'string' ? body : JSON.stringify(body);
  return new Request('https://w.example/e', {
    method: 'POST', body: text,
    headers: { Origin: ORIGIN, 'Content-Type': 'text/plain;charset=UTF-8', 'CF-Connecting-IP': '203.0.113.7', 'User-Agent': 'UA/1', ...headers },
  });
}
const rows = (e, sql = 'SELECT kind, key, hits, ms FROM agg ORDER BY kind, key') => e.DB.raw.prepare(sql).all();
const statsReq = (auth) => new Request('https://w.example/stats?days=7', { headers: auth ? { Authorization: auth } : {} });

test('allowlist matches the live page (NODES, SCENARIOS, tabs)', () => {
  const html = readFileSync(new URL('../../bullion-live-map/bullion_mkultra.html', here), 'utf8');
  const nodesBlock = html.slice(html.indexOf('const NODES = ['), html.indexOf('\n];', html.indexOf('const NODES = [')));
  const pageNodes = [...nodesBlock.matchAll(/\{\s*id:\s*'([^']+)'/g)].map(m => m[1]);
  assert.deepEqual([...NODES].sort(), [...pageNodes].sort());
  const sStart = html.indexOf('const SCENARIOS = {');
  const scen = html.slice(sStart, html.indexOf('\n};', sStart));
  const pageShocks = [...scen.matchAll(/^\s{2}([a-z_]+):\s*\{/gm)].map(m => m[1]);
  assert.deepEqual([...SHOCKS].sort(), [...pageShocks].sort());
  for (const t of TABS.filter(t => t !== 'start')) assert.ok(html.includes(`id="tab-${t}"`), t);
});

test('valid beacon is stored, merged and capped', async () => {
  const e = env();
  const r = await worker.fetch(beacon({ first: true, ev: [
    { kind: 'visit', key: 'all', hits: 1, ms: 0 },
    { kind: 'node', key: 'fed', hits: 1, ms: 3000 },
    { kind: 'node', key: 'fed', hits: 1, ms: 2000 },
    { kind: 'shock', key: 'rate_hike', hits: 999, ms: 1e12 },
  ] }), e);
  assert.equal(r.status, 204);
  assert.equal(r.headers.get('X-Content-Type-Options'), 'nosniff');
  assert.deepEqual(rows(e).map(x => ({ ...x })), [
    { kind: 'node', key: 'fed', hits: 2, ms: 5000 },
    { kind: 'shock', key: 'rate_hike', hits: 50, ms: 30 * 60 * 1000 },
    { kind: 'visit', key: 'all', hits: 1, ms: 0 },
    { kind: 'visitor', key: 'all', hits: 1, ms: 0 },
  ]);
});

test('duplicates in one batch cannot exceed the per-item cap', async () => {
  const e = env();
  const ev = Array.from({ length: 60 }, () => ({ kind: 'node', key: 'fed', hits: 50, ms: 30 * 60 * 1000 }));
  await worker.fetch(beacon({ ev }), e);
  assert.deepEqual({ ...rows(e)[0] }, { kind: 'node', key: 'fed', hits: 50, ms: 30 * 60 * 1000 });
});

test('keys outside the allowlist, odd kinds and prototype names are dropped', async () => {
  const e = env();
  await worker.fetch(beacon({ ev: [
    { kind: 'node', key: '<img src=x onerror=alert(1)>', hits: 1 },
    { kind: 'node', key: 'not_a_node', hits: 1 },
    { kind: 'tab', key: 'admin', hits: 1 },
    { kind: 'visitor', key: 'all', hits: 50 },
    { kind: '__proto__', key: 'x', hits: 1 },
    { kind: 'constructor', key: 'x', hits: 1 },
    { kind: 'node', key: { toString: 1 }, hits: 1 },
  ] }), e);
  assert.equal(rows(e).length, 0);
});

test('foreign or missing Origin → 403, nothing written', async () => {
  const e = env();
  assert.equal((await worker.fetch(beacon({ ev: [{ kind: 'node', key: 'fed', hits: 1 }] }, { Origin: 'https://evil.example' }), e)).status, 403);
  assert.equal((await worker.fetch(beacon({ ev: [{ kind: 'node', key: 'fed', hits: 1 }] }, { Origin: '' }), e)).status, 403);
  assert.equal((await worker.fetch(beacon({ ev: [] }), env({ ALLOWED_ORIGIN: '' }))).status, 403);
  assert.equal(rows(e).length, 0);
});

test('DNT and GPC are honored server-side', async () => {
  for (const h of [{ DNT: '1' }, { 'Sec-GPC': '1' }]) {
    const e = env();
    assert.equal((await worker.fetch(beacon({ first: true, ev: [{ kind: 'node', key: 'fed', hits: 1 }] }, h), e)).status, 204);
    assert.equal(rows(e).length, 0);
    assert.equal(e.DB.raw.prepare('SELECT COUNT(*) c FROM seen').get().c, 0);
  }
});

test('oversized and malformed bodies are rejected', async () => {
  const e = env();
  assert.equal((await worker.fetch(beacon('x'.repeat(9000)), e)).status, 413);
  assert.equal((await worker.fetch(beacon('{not json'), e)).status, 400);
  assert.equal((await worker.fetch(beacon({ ev: 'nope' }), e)).status, 400);
  assert.equal((await worker.fetch(beacon('null'), e)).status, 400);
});

test('same visitor counted once a day; seen holds a hash, never the IP', async () => {
  const e = env();
  await worker.fetch(beacon({ first: true, ev: [] }), e);
  await worker.fetch(beacon({ first: true, ev: [] }), e);
  await worker.fetch(beacon({ first: true, ev: [] }, { 'CF-Connecting-IP': '198.51.100.9' }), e);
  assert.equal(e.DB.raw.prepare("SELECT hits FROM agg WHERE kind='visitor'").get().hits, 2);
  for (const s of e.DB.raw.prepare('SELECT h FROM seen').all()) {
    assert.match(s.h, /^[0-9a-f]{32}$/);
    assert.ok(!s.h.includes('203.0.113.7'));
  }
});

test('without SALT_SECRET, visitors are not counted (and nothing breaks)', async () => {
  const e = env({ SALT_SECRET: '' });
  assert.equal((await worker.fetch(beacon({ first: true, ev: [{ kind: 'tab', key: 'market', hits: 1 }] }), e)).status, 204);
  assert.equal(e.DB.raw.prepare('SELECT COUNT(*) c FROM seen').get().c, 0);
  assert.equal(rows(e).length, 1);
});

test('purge deletes earlier seen rows and totals past retention', async () => {
  const e = env();
  const db = e.DB.raw;
  db.prepare('INSERT INTO seen VALUES (?, ?)').run('2026-10-11', 'a'.repeat(32));
  db.prepare('INSERT INTO seen VALUES (?, ?)').run('2026-10-12', 'b'.repeat(32));
  db.prepare("INSERT INTO agg VALUES ('2025-01-01','visit','all',1,0)").run();
  db.prepare("INSERT INTO agg VALUES ('2026-10-01','visit','all',1,0)").run();
  await purge(e, '2026-10-12');
  assert.deepEqual(db.prepare('SELECT day FROM seen').all().map(r => r.day), ['2026-10-12']);
  assert.deepEqual(db.prepare('SELECT day FROM agg').all().map(r => r.day), ['2026-10-01']);
});

test('scheduled handler purges with today’s date', async () => {
  const e = env();
  e.DB.raw.prepare('INSERT INTO seen VALUES (?, ?)').run('2000-01-01', 'c'.repeat(32));
  await worker.scheduled({}, e);
  assert.equal(e.DB.raw.prepare('SELECT COUNT(*) c FROM seen').get().c, 0);
});

test('/stats: no, wrong, or non-Bearer token → 401', async () => {
  const e = env();
  for (const a of [null, 'Bearer nope', TOKEN, 'Basic ' + TOKEN, 'Bearer ' + TOKEN + 'x']) {
    const r = await worker.fetch(statsReq(a), e);
    assert.equal(r.status, 401, String(a));
    assert.equal(r.headers.get('Access-Control-Allow-Origin'), null);
  }
});

test('/stats fails closed when STATS_TOKEN is missing or short', async () => {
  for (const t of [undefined, '', 'short-token']) {
    const e = env({ STATS_TOKEN: t });
    assert.equal((await worker.fetch(statsReq('Bearer ' + (t || '')), e)).status, 401);
  }
});

test('/stats with the right token returns totals, no-store', async () => {
  const e = env();
  await worker.fetch(beacon({ first: true, ev: [{ kind: 'visit', key: 'all', hits: 1, ms: 4000 }, { kind: 'node', key: 'gold', hits: 1, ms: 1000 }] }), e);
  const r = await worker.fetch(statsReq('Bearer ' + TOKEN), e);
  assert.equal(r.status, 200);
  assert.equal(r.headers.get('Cache-Control'), 'no-store');
  const j = await r.json();
  assert.equal(j.daily[0].day, today());
  assert.equal(j.daily[0].visitors, 1);
  assert.equal(j.daily[0].visits, 1);
  assert.deepEqual(j.items.map(x => x.key), ['gold']);
});

test('rate limiters: 429 when a limiter refuses, and a missing binding allows', async () => {
  const no = { limit: async () => ({ success: false }) };
  assert.equal((await worker.fetch(beacon({ ev: [] }), env({ RL_COLLECT: no }))).status, 429);
  assert.equal((await worker.fetch(beacon({ ev: [] }), env({ RL_COLLECT_GLOBAL: no }))).status, 429);
  assert.equal((await worker.fetch(statsReq('Bearer ' + TOKEN), env({ RL_AUTH: no }))).status, 429);
  const keys = [];
  const spy = { limit: async ({ key }) => { keys.push(key); return { success: true }; } };
  await worker.fetch(beacon({ ev: [] }), env({ RL_COLLECT: spy }));
  assert.match(keys[0], /^[0-9a-f]{32}$/, 'limiter key is the hash, not the IP');
});

test('dashboard: hash-based CSP with no unsafe-inline, and hashes match the served page', async () => {
  const r = await worker.fetch(new Request('https://w.example/dashboard'), env());
  const csp = r.headers.get('Content-Security-Policy');
  assert.ok(!csp.includes('unsafe-inline'));
  assert.match(csp, /frame-ancestors 'none'/);
  assert.equal(r.headers.get('X-Frame-Options'), 'DENY');
  const html = await r.text();
  const { createHash } = await import('node:crypto');
  const h = s => 'sha256-' + createHash('sha256').update(s).digest('base64');
  const js = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  const css = html.match(/<style>([\s\S]*?)<\/style>/)[1];
  assert.ok(csp.includes(h(js)) && csp.includes(h(css)));
  assert.ok(!/innerHTML/.test(js), 'dashboard builds DOM with textContent only');
  assert.equal(await dashboardCsp(), csp);
});

test('unknown routes and methods → 404', async () => {
  const e = env();
  assert.equal((await worker.fetch(new Request('https://w.example/'), e)).status, 404);
  assert.equal((await worker.fetch(new Request('https://w.example/e'), e)).status, 404);
  assert.equal((await worker.fetch(new Request('https://w.example/stats', { method: 'POST' }), e)).status, 404);
});

test('an internal error returns a bare 500 without leaking details', async () => {
  const e = env({ DB: { prepare: () => { throw new Error('secret internals'); } } });
  const orig = console.error; console.error = () => {};
  try {
    const r = await worker.fetch(beacon({ ev: [{ kind: 'node', key: 'fed', hits: 1 }] }), e);
    assert.equal(r.status, 500);
    assert.equal(await r.text(), '');
  } finally { console.error = orig; }
});
