// Bullion analytics — aggregate-only, cookieless.
//
//   POST /e          the map sends a small batch of {kind, key, hits, ms} when a
//                    visitor leaves or hides the tab. Anyone can call it, so
//                    every field is validated against an allowlist and capped,
//                    and callers are rate limited.
//   GET  /stats      JSON totals. Requires `Authorization: Bearer <STATS_TOKEN>`.
//   GET  /dashboard  owner page; asks for the token and calls /stats.
//   cron (daily)     deletes yesterday's visitor hashes and totals past retention.
//
// What is never stored: IP address, user agent, cookies, anything typed into
// the page. A visitor is counted once per day via an HMAC of IP + user agent
// under a key derived from SALT_SECRET and the date, so the key changes every
// day. Only that hash is kept, and only until the daily purge.

import { ALLOWED } from './allowlist.js';

const MAX_BODY = 8192;           // bytes; a real batch is well under 2 KB
const MAX_EVENTS = 60;
const MAX_HITS = 50;
const MAX_MS = 30 * 60 * 1000;   // one item can't claim more than 30 min per batch
const MIN_TOKEN_LEN = 32;        // shorter STATS_TOKEN → /stats refuses everyone
const RETENTION_DAYS = 400;      // aggregate totals older than this are deleted

const BASE_HEADERS = {
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'X-Robots-Tag': 'noindex, nofollow',
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Cache-Control': 'no-store',
};

function respond(body, status = 200, extra = {}) {
  return new Response(body, { status, headers: { ...BASE_HEADERS, ...extra } });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    try {
      if (url.pathname === '/e' && request.method === 'POST') return await collect(request, env);
      if (url.pathname === '/stats' && request.method === 'GET') return await stats(request, env, url);
      if (url.pathname === '/dashboard' && request.method === 'GET') return await dashboard();
      return respond('Not found', 404, { 'Content-Type': 'text/plain; charset=utf-8' });
    } catch (err) {
      // Log the failure for `wrangler tail`, never echo internals to the caller.
      console.error('bullion-analytics error', url.pathname, err && err.stack || err);
      return respond(null, 500);
    }
  },

  async scheduled(controller, env) {
    await purge(env, today());
  },
};

export function today(now = Date.now()) { return new Date(now).toISOString().slice(0, 10); }

function hex(buf) { return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join(''); }

async function hmac(keyBytes, text) {
  const key = await crypto.subtle.importKey('raw', keyBytes, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']);
  return crypto.subtle.sign('HMAC', key, new TextEncoder().encode(text));
}

// Per-day key: HMAC(SALT_SECRET, day). Hashes from different days can't be
// matched without the secret, and the rows themselves are purged daily.
async function visitorHash(env, day, ip, ua) {
  const dayKey = await hmac(new TextEncoder().encode(env.SALT_SECRET), 'bullion-visitor|' + day);
  return hex(await hmac(dayKey, ip + '\n' + ua)).slice(0, 32);
}

// Reads at most `max` bytes; returns null if the body is larger.
async function readCapped(request, max) {
  const declared = Number(request.headers.get('Content-Length'));
  if (declared > max) return null;
  if (!request.body) return '';
  const reader = request.body.getReader();
  const chunks = [];
  let size = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > max) { await reader.cancel(); return null; }
    chunks.push(value);
  }
  const all = new Uint8Array(size);
  let off = 0;
  for (const c of chunks) { all.set(c, off); off += c.byteLength; }
  return new TextDecoder().decode(all);
}

// Optional binding: if the account has no rate limiting, everything is allowed
// (and the README says so) rather than the counter breaking.
async function allowed(limiter, key) {
  if (!limiter) return true;
  const { success } = await limiter.limit({ key });
  return success;
}

async function collect(request, env) {
  // Only the published map may write. This stops casual spam, not a
  // determined forger (Origin can be faked outside a browser) — the
  // allowlist, caps and rate limits below are what bound the damage.
  if (!env.ALLOWED_ORIGIN || request.headers.get('Origin') !== env.ALLOWED_ORIGIN) return respond(null, 403);
  if (request.headers.get('DNT') === '1' || request.headers.get('Sec-GPC') === '1') return respond(null, 204);
  // No Content-Type check on purpose: navigator.sendBeacon(string) sends
  // text/plain, and anything that would need a CORS preflight is dropped.

  const day = today();
  const ip = request.headers.get('CF-Connecting-IP') || '';
  const ua = request.headers.get('User-Agent') || '';
  const salted = !!env.SALT_SECRET;
  // Rate-limit key is the same daily hash, so no raw IP reaches the limiter.
  const rlKey = salted ? await visitorHash(env, day, ip, ua) : 'anon';
  if (!(await allowed(env.RL_COLLECT, rlKey)) || !(await allowed(env.RL_COLLECT_GLOBAL, 'global'))) {
    return respond(null, 429);
  }

  const text = await readCapped(request, MAX_BODY);
  if (text === null) return respond(null, 413);
  let body;
  try { body = JSON.parse(text); } catch { return respond(null, 400); }
  if (!body || typeof body !== 'object' || !Array.isArray(body.ev)) return respond(null, 400);

  const upsert = env.DB.prepare(
    'INSERT INTO agg (day, kind, key, hits, ms) VALUES (?1, ?2, ?3, ?4, ?5) ' +
    'ON CONFLICT(day, kind, key) DO UPDATE SET hits = hits + ?4, ms = ms + ?5');

  // Merge duplicates inside one batch so a padded batch can't multiply writes.
  const merged = new Map();
  for (const e of body.ev.slice(0, MAX_EVENTS)) {
    if (!e || typeof e !== 'object') continue;
    const set = Object.hasOwn(ALLOWED, e.kind) ? ALLOWED[e.kind] : null;
    if (!set || typeof e.key !== 'string' || !set.has(e.key)) continue;
    const hits = Math.min(Math.max(0, Math.trunc(Number(e.hits)) || 0), MAX_HITS);
    const ms = Math.min(Math.max(0, Math.round(Number(e.ms)) || 0), MAX_MS);
    if (!hits && !ms) continue;
    const k = e.kind + '|' + e.key;
    const m = merged.get(k) || { kind: e.kind, key: e.key, hits: 0, ms: 0 };
    m.hits = Math.min(m.hits + hits, MAX_HITS);
    m.ms = Math.min(m.ms + ms, MAX_MS);
    merged.set(k, m);
  }
  const stmts = [...merged.values()].map(m => upsert.bind(day, m.kind, m.key, m.hits, m.ms));

  // Daily unique visitor, only on the batch that starts a page view.
  if (body.first === true && salted) {
    const ins = await env.DB.prepare('INSERT OR IGNORE INTO seen (day, h) VALUES (?1, ?2)').bind(day, rlKey).run();
    if (ins.meta && ins.meta.changes === 1) stmts.push(upsert.bind(day, 'visitor', 'all', 1, 0));
  }

  if (stmts.length) await env.DB.batch(stmts);
  return respond(null, 204);
}

export async function purge(env, day) {
  const cutoff = today(Date.parse(day + 'T00:00:00Z') - RETENTION_DAYS * 86400000);
  await env.DB.batch([
    env.DB.prepare('DELETE FROM seen WHERE day < ?1').bind(day),
    env.DB.prepare('DELETE FROM agg WHERE day < ?1').bind(cutoff),
  ]);
}

async function authorized(request, env) {
  const secret = env.STATS_TOKEN || '';
  if (secret.length < MIN_TOKEN_LEN) {
    console.error('STATS_TOKEN missing or shorter than ' + MIN_TOKEN_LEN + ' chars; /stats is locked');
    return false;
  }
  const header = request.headers.get('Authorization') || '';
  const got = header.startsWith('Bearer ') ? header.slice(7) : '';
  // Compare HMACs under a fresh random key: fixed-length, constant-time, and
  // nothing about the real token's length or prefix leaks through timing.
  const k = crypto.getRandomValues(new Uint8Array(32));
  const [a, b] = await Promise.all([hmac(k, got), hmac(k, secret)]);
  const x = new Uint8Array(a), y = new Uint8Array(b);
  let diff = 0;
  for (let i = 0; i < x.length; i++) diff |= x[i] ^ y[i];
  return diff === 0;
}

async function stats(request, env, url) {
  if (!(await allowed(env.RL_AUTH, 'stats'))) return respond('Too many requests', 429, { 'Content-Type': 'text/plain; charset=utf-8' });
  if (!(await authorized(request, env))) {
    return respond('Unauthorized', 401, { 'Content-Type': 'text/plain; charset=utf-8', 'WWW-Authenticate': 'Bearer' });
  }
  const days = Math.min(Math.max(parseInt(url.searchParams.get('days'), 10) || 30, 1), 365);
  const since = today(Date.now() - (days - 1) * 86400000);

  const [daily, items] = await Promise.all([
    env.DB.prepare(
      "SELECT day, SUM(CASE WHEN kind='visitor' THEN hits ELSE 0 END) AS visitors, " +
      "SUM(CASE WHEN kind='visit' THEN hits ELSE 0 END) AS visits, " +
      "SUM(CASE WHEN kind='visit' THEN ms ELSE 0 END) AS ms " +
      'FROM agg WHERE day >= ?1 GROUP BY day ORDER BY day').bind(since).all(),
    env.DB.prepare(
      "SELECT kind, key, SUM(hits) AS hits, SUM(ms) AS ms FROM agg " +
      "WHERE day >= ?1 AND kind IN ('tab','node','shock') GROUP BY kind, key").bind(since).all(),
  ]);
  return respond(JSON.stringify({ since, days, daily: daily.results, items: items.results }), 200,
    { 'Content-Type': 'application/json; charset=utf-8' });
}

// ── Owner dashboard ────────────────────────────────────────────────────
// Strict CSP: the one inline <style> and <script> are allowed by hash, not by
// 'unsafe-inline', and the script builds every cell with textContent, so a
// stored key can never become markup.

const DASHBOARD_CSS = `
:root{--bg:#0d0d0f;--fg:#e5e7eb;--mut:#9ca3af;--gold:#e0b15a;--line:#26262b;--bar:#e0b15a33}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:16px;max-width:900px;margin-inline:auto}
h1{color:var(--gold);font-size:1.4rem;margin:.2rem 0 1rem}h2{font-size:1rem;margin:1.6rem 0 .5rem;color:var(--gold)}
input,select,button{font:inherit;background:#17171b;color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:.45rem .6rem}
button{background:var(--gold);color:#111;border:0;cursor:pointer}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.tile{border:1px solid var(--line);border-radius:8px;padding:.7rem}.tile b{display:block;font-size:1.5rem;font-variant-numeric:tabular-nums}
.tile span{color:var(--mut);font-size:.85rem}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}td,th{padding:.35rem .4rem;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--mut);font-weight:500;font-size:.85rem}td.n,th.n{text-align:right;white-space:nowrap}
td.k{position:relative;isolation:isolate}td.k i{position:absolute;inset:3px auto 3px 0;background:var(--bar);border-radius:3px;z-index:-1}
.err{color:#f87171}.mut{color:var(--mut);font-size:.85rem}
`;

const DASHBOARD_JS = `
const $=s=>document.querySelector(s);let token='';
const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!=null)e.textContent=String(text);return e};
const dur=ms=>{const s=Math.round(ms/1000);if(s<60)return s+'s';const m=Math.floor(s/60);if(m<60)return m+'m '+(s%60)+'s';return Math.floor(m/60)+'h '+(m%60)+'m'};
const msg=(t,cls)=>{$('#msg').textContent=t;$('#msg').className=cls};
$('#f').addEventListener('submit',e=>{e.preventDefault();token=$('#t').value;$('#t').value='';load()});
$('#d').addEventListener('change',()=>{if(token)load()});
function table(heads,rows){const t=el('table'),h=el('tr');heads.forEach(([x,c])=>h.append(el('th',c,x)));t.append(h);rows.forEach(r=>t.append(r));return t}
function section(out,title,j,kind,by,label){
  out.append(el('h2',null,title));
  const rows=j.items.filter(x=>x.kind===kind).sort((a,b)=>b[by]-a[by]).slice(0,25);
  if(!rows.length){out.append(el('p','mut','No data yet.'));return}
  const max=rows[0][by]||1;
  out.append(table([[label],['Opens','n'],['Time','n'],['Avg','n']],rows.map(x=>{
    const tr=el('tr'),k=el('td','k'),bar=el('i');bar.style.width=(100*x[by]/max).toFixed(1)+'%';
    k.append(bar,document.createTextNode(String(x.key)));
    tr.append(k,el('td','n',x.hits),el('td','n',dur(x.ms)),el('td','n',dur(x.hits?x.ms/x.hits:0)));return tr})));
}
async function load(){
  msg('Loading…','mut');const out=$('#out');out.replaceChildren();
  let r;try{r=await fetch('stats?days='+encodeURIComponent($('#d').value),{headers:{Authorization:'Bearer '+token},cache:'no-store'})}catch(e){msg('Network error.','err');return}
  if(!r.ok){msg(r.status===401?'Wrong token.':r.status===429?'Too many attempts — wait a minute.':'Error '+r.status,'err');if(r.status===401)token='';return}
  const j=await r.json();msg('Since '+j.since+' (UTC). Visitors are counted once per day, so the total adds daily counts.','mut');
  const sum=(a,k)=>a.reduce((x,y)=>x+(Number(y[k])||0),0);
  const V=sum(j.daily,'visitors'),N=sum(j.daily,'visits'),T=sum(j.daily,'ms');
  const tiles=el('div','tiles');
  [[V,'visitor-days'],[N,'page views'],[dur(N?T/N:0),'avg time per view'],[dur(T),'total time on site']].forEach(([v,l])=>{const t=el('div','tile');t.append(el('b',null,v),el('span',null,l));tiles.append(t)});
  out.append(tiles);
  section(out,'Where people stay longest — tabs',j,'tab','ms','Tab');
  section(out,'Where people stay longest — nodes',j,'node','ms','Node');
  section(out,'Most engagement — nodes opened',j,'node','hits','Node');
  section(out,'Most engagement — shock scenarios run',j,'shock','hits','Scenario');
  out.append(el('h2',null,'Daily'));
  out.append(table([['Day'],['Visitors','n'],['Views','n'],['Time','n']],j.daily.slice().reverse().map(d=>{
    const tr=el('tr');tr.append(el('td',null,d.day),el('td','n',d.visitors),el('td','n',d.visits),el('td','n',dur(d.ms)));return tr})));
}
`;

const DASHBOARD_HTML = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><meta name="referrer" content="no-referrer"><title>Bullion Analytics</title>
<style>${DASHBOARD_CSS}</style></head><body>
<h1>Bullion Analytics</h1>
<form id="f"><input id="t" type="password" placeholder="Stats token" autocomplete="current-password" required>
<select id="d"><option value="7">7 days</option><option value="30" selected>30 days</option><option value="90">90 days</option><option value="365">365 days</option></select>
<button>Load</button></form>
<p id="msg" class="mut">The token stays in this tab's memory only.</p>
<div id="out"></div>
<script>${DASHBOARD_JS}</script></body></html>`;

let cspPromise;
async function sha256b64(text) {
  const d = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return btoa(String.fromCharCode(...new Uint8Array(d)));
}
export function dashboardCsp() {
  cspPromise ||= Promise.all([sha256b64(DASHBOARD_JS), sha256b64(DASHBOARD_CSS)]).then(([js, css]) =>
    "default-src 'none'; " +
    `script-src 'sha256-${js}'; ` +
    `style-src 'sha256-${css}'; ` +
    "connect-src 'self'; img-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'");
  return cspPromise;
}

async function dashboard() {
  return respond(DASHBOARD_HTML, 200, {
    'Content-Type': 'text/html; charset=utf-8',
    'Content-Security-Policy': await dashboardCsp(),
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'same-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), interest-cohort=()',
    'X-Frame-Options': 'DENY',
  });
}
