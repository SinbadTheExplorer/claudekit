// Bullion analytics — aggregate-only, cookieless.
//
//   POST /e          the map sends a small batch of {kind, key, hits, ms} when a
//                    visitor leaves or hides the tab. Anyone can call it, so
//                    every field is validated and capped.
//   GET  /stats      JSON totals. Requires `Authorization: Bearer <STATS_TOKEN>`.
//   GET  /dashboard  owner page; asks for the token and calls /stats.
//
// What is never stored: IP address, user agent, cookies, anything typed into
// the page. A visitor is counted once per day via sha256(daily salt + IP + UA);
// only that hash is kept, only for today, and the salt rotates daily.

const KINDS = new Set(['visit', 'tab', 'node', 'shock']);
const KEY_RE = /^[A-Za-z0-9_.:-]{1,48}$/;
const MAX_EVENTS = 60;
const MAX_MS = 30 * 60 * 1000; // one item can't claim more than 30 min per batch

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/e' && request.method === 'POST') return collect(request, env);
    if (url.pathname === '/stats' && request.method === 'GET') return stats(request, env, url);
    if (url.pathname === '/dashboard' && request.method === 'GET') return dashboard();
    return new Response('Not found', { status: 404 });
  },
};

function today() { return new Date().toISOString().slice(0, 10); }

async function sha256Hex(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
}

async function collect(request, env) {
  // Only the published map may write. This stops casual spam, not a
  // determined forger (Origin can be faked outside a browser).
  if (request.headers.get('Origin') !== env.ALLOWED_ORIGIN) return new Response(null, { status: 403 });
  if (request.headers.get('DNT') === '1' || request.headers.get('Sec-GPC') === '1') return new Response(null, { status: 204 });

  let body;
  try {
    const text = await request.text();
    if (text.length > 8000) return new Response(null, { status: 413 });
    body = JSON.parse(text);
  } catch { return new Response(null, { status: 400 }); }
  if (!body || !Array.isArray(body.ev)) return new Response(null, { status: 400 });

  const day = today();
  const stmts = [];
  const upsert = env.DB.prepare(
    'INSERT INTO agg (day, kind, key, hits, ms) VALUES (?1, ?2, ?3, ?4, ?5) ' +
    'ON CONFLICT(day, kind, key) DO UPDATE SET hits = hits + ?4, ms = ms + ?5');

  for (const e of body.ev.slice(0, MAX_EVENTS)) {
    if (!e || !KINDS.has(e.kind) || typeof e.key !== 'string' || !KEY_RE.test(e.key)) continue;
    const hits = Math.min(Math.max(0, e.hits | 0), 50);
    const ms = Math.min(Math.max(0, Math.round(Number(e.ms) || 0)), MAX_MS);
    if (!hits && !ms) continue;
    stmts.push(upsert.bind(day, e.kind, e.key, hits, ms));
  }

  // Daily unique visitor, only on the batch that starts a page view.
  if (body.first === true && env.SALT_SECRET) {
    const ip = request.headers.get('CF-Connecting-IP') || '';
    const ua = request.headers.get('User-Agent') || '';
    const h = (await sha256Hex(env.SALT_SECRET + '|' + day + '|' + ip + '|' + ua)).slice(0, 32);
    const ins = await env.DB.prepare('INSERT OR IGNORE INTO seen (day, h) VALUES (?1, ?2)').bind(day, h).run();
    if (ins.meta && ins.meta.changes === 1) stmts.push(upsert.bind(day, 'visitor', 'all', 1, 0));
    stmts.push(env.DB.prepare('DELETE FROM seen WHERE day < ?1').bind(day));
  }

  if (stmts.length) await env.DB.batch(stmts);
  return new Response(null, { status: 204 });
}

async function authorized(request, env) {
  if (!env.STATS_TOKEN) return false; // not configured → nobody gets in
  const got = (request.headers.get('Authorization') || '').replace(/^Bearer /, '');
  // Compare digests so the check takes the same time whatever was sent.
  const [a, b] = await Promise.all([sha256Hex(got), sha256Hex(env.STATS_TOKEN)]);
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function stats(request, env, url) {
  if (!(await authorized(request, env))) return new Response('Unauthorized', { status: 401 });
  const days = Math.min(Math.max(parseInt(url.searchParams.get('days'), 10) || 30, 1), 365);
  const since = new Date(Date.now() - (days - 1) * 86400000).toISOString().slice(0, 10);

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
  return Response.json({ since, days, daily: daily.results, items: items.results },
    { headers: { 'Cache-Control': 'no-store' } });
}

function dashboard() {
  return new Response(DASHBOARD_HTML, {
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store',
      'Content-Security-Policy': "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'",
      'X-Robots-Tag': 'noindex',
    },
  });
}

const DASHBOARD_HTML = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Bullion Analytics</title>
<style>
:root{--bg:#0d0d0f;--fg:#e5e7eb;--mut:#9ca3af;--gold:#e0b15a;--line:#26262b;--bar:#e0b15a33}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:16px;max-width:900px;margin-inline:auto}
h1{color:var(--gold);font-size:1.4rem;margin:.2rem 0 1rem}h2{font-size:1rem;margin:1.6rem 0 .5rem;color:var(--gold)}
input,select,button{font:inherit;background:#17171b;color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:.45rem .6rem}
button{background:var(--gold);color:#111;border:0;cursor:pointer}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.tile{border:1px solid var(--line);border-radius:8px;padding:.7rem}.tile b{display:block;font-size:1.5rem;font-variant-numeric:tabular-nums}
.tile span{color:var(--mut);font-size:.85rem}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}td,th{padding:.35rem .4rem;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--mut);font-weight:500;font-size:.85rem}td.n{text-align:right;white-space:nowrap}
td.k{position:relative;isolation:isolate}td.k i{position:absolute;inset:3px auto 3px 0;background:var(--bar);border-radius:3px;z-index:-1}
.err{color:#f87171}.mut{color:var(--mut);font-size:.85rem}
</style></head><body>
<h1>Bullion Analytics</h1>
<form id="f"><input id="t" type="password" placeholder="Stats token" autocomplete="current-password" required>
<select id="d"><option value="7">7 days</option><option value="30" selected>30 days</option><option value="90">90 days</option><option value="365">365 days</option></select>
<button>Load</button></form>
<p id="msg" class="mut">The token stays in this tab's memory only.</p>
<div id="out"></div>
<script>
const $=s=>document.querySelector(s);let token='';
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dur=ms=>{const s=Math.round(ms/1000);if(s<60)return s+'s';const m=Math.floor(s/60);if(m<60)return m+'m '+(s%60)+'s';return Math.floor(m/60)+'h '+(m%60)+'m'};
$('#f').onsubmit=async e=>{e.preventDefault();token=$('#t').value;$('#t').value='';load()};
$('#d').onchange=()=>token&&load();
async function load(){
  $('#msg').textContent='Loading…';$('#msg').className='mut';
  const r=await fetch('stats?days='+$('#d').value,{headers:{Authorization:'Bearer '+token}});
  if(!r.ok){$('#msg').textContent=r.status===401?'Wrong token.':'Error '+r.status;$('#msg').className='err';$('#out').innerHTML='';return}
  const j=await r.json();$('#msg').textContent='Since '+j.since+' (UTC). Visitors are counted once per day, so the total adds daily counts.';
  const sum=(a,k)=>a.reduce((x,y)=>x+(y[k]||0),0);
  const V=sum(j.daily,'visitors'),N=sum(j.daily,'visits'),T=sum(j.daily,'ms');
  let h='<div class="tiles"><div class="tile"><b>'+V+'</b><span>visitor-days</span></div><div class="tile"><b>'+N+'</b><span>page views</span></div><div class="tile"><b>'+dur(N?T/N:0)+'</b><span>avg time per view</span></div><div class="tile"><b>'+dur(T)+'</b><span>total time on site</span></div></div>';
  const sect=(title,kind,by,label)=>{const rows=j.items.filter(x=>x.kind===kind).sort((a,b)=>b[by]-a[by]).slice(0,25);
    if(!rows.length)return '<h2>'+title+'</h2><p class="mut">No data yet.</p>';
    const max=rows[0][by]||1;
    return '<h2>'+title+'</h2><table><tr><th>'+label+'</th><th class="n">Opens</th><th class="n">Time</th><th class="n">Avg</th></tr>'+rows.map(x=>'<tr><td class="k"><i style="width:'+(100*x[by]/max).toFixed(1)+'%"></i>'+esc(x.key)+'</td><td class="n">'+x.hits+'</td><td class="n">'+dur(x.ms)+'</td><td class="n">'+dur(x.hits?x.ms/x.hits:0)+'</td></tr>').join('')+'</table>'};
  h+=sect('Where people stay longest — tabs','tab','ms','Tab');
  h+=sect('Where people stay longest — nodes','node','ms','Node');
  h+=sect('Most engagement — nodes opened','node','hits','Node');
  h+=sect('Most engagement — shock scenarios run','shock','hits','Scenario');
  h+='<h2>Daily</h2><table><tr><th>Day</th><th class="n">Visitors</th><th class="n">Views</th><th class="n">Time</th></tr>'+j.daily.slice().reverse().map(d=>'<tr><td>'+d.day+'</td><td class="n">'+d.visitors+'</td><td class="n">'+d.visits+'</td><td class="n">'+dur(d.ms)+'</td></tr>').join('')+'</table>';
  $('#out').innerHTML=h;
}
</script></body></html>`;
