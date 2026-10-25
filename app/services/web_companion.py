"""
Optional read-only web companion for local monitoring.

Uses the Python standard library only (``http.server``). Exposes JSON status
endpoints and a minimal HTML dashboard. No write / control / send routes.

Bind to localhost by default. Non-loopback binds require ``WEB_COMPANION_TOKEN``
(Bearer / ``X-TMAS-Token`` / ``?token=``). Prefer keeping the process on
``127.0.0.1`` and terminating TLS + forwarding at a reverse proxy that preserves
the ``Authorization`` header.
"""

from __future__ import annotations

import hmac
import json
import secrets
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple
from urllib.parse import parse_qs, quote, urlparse

from sqlmodel import select

from .. import __version__
from ..core.analytics import AnalyticsCollector, CampaignAnalytics
from ..models import Campaign, SendLog
from .account_health import AccountHealthMonitor
from .db import get_session
from .logger import get_logger
from .settings import Settings, get_settings

# Read-only API paths (exact match). Anything else under /api/ is 404.
READ_ONLY_API_PATHS: Set[str] = {
    "/api/status",
    "/api/accounts",
    "/api/campaigns",
    "/api/activity",
    "/api/overview",
    "/api/charts",
}

ALLOWED_METHODS: Set[str] = {"GET", "HEAD", "OPTIONS"}

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_ACTIVITY_LIMIT = 50
MAX_ACTIVITY_LIMIT = 200
DEFAULT_CHART_HOURS = 24
MAX_CHART_HOURS = 168
DEFAULT_CHART_LOG_LIMIT = 2000
MAX_CHART_CAMPAIGNS = 8

LOOPBACK_HOSTS: Set[str] = {"127.0.0.1", "localhost", "::1"}

_HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>TMAS Monitor</title>
  <style>
    :root { color-scheme: light dark; --bg:#0f1419; --card:#1a2332; --fg:#e7ecf3; --muted:#9aa7b8; --ok:#3dcc91; --warn:#e6b84d; --bad:#e85d5d; --accent:#2d6cdf; --sent:#3dcc91; --fail:#e85d5d; --skip:#9aa7b8; }
    body { margin:0; font-family: ui-sans-serif, system-ui, sans-serif; background:var(--bg); color:var(--fg); }
    main { max-width:1100px; margin:0 auto; padding:1.5rem; }
    h1 { font-size:1.35rem; margin:0 0 .25rem; }
    .sub { color:var(--muted); margin:0 0 1.25rem; font-size:.9rem; }
    .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:.75rem; margin-bottom:1.25rem; }
    .card { background:var(--card); border-radius:8px; padding:.9rem 1rem; }
    .card .n { font-size:1.4rem; font-weight:600; }
    .card .l { color:var(--muted); font-size:.75rem; text-transform:uppercase; letter-spacing:.04em; }
    .charts { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:.75rem; margin-bottom:1.5rem; }
    .chart-card { background:var(--card); border-radius:8px; padding:.9rem 1rem; }
    .chart-card h3 { margin:0 0 .5rem; font-size:.85rem; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.04em; }
    .chart-card svg { width:100%; height:auto; display:block; }
    .legend { display:flex; flex-wrap:wrap; gap:.6rem; margin-top:.5rem; font-size:.75rem; color:var(--muted); }
    .legend span::before { content:''; display:inline-block; width:.55rem; height:.55rem; border-radius:2px; margin-right:.3rem; vertical-align:middle; background:currentColor; }
    section { margin-bottom:1.5rem; }
    h2 { font-size:1rem; margin:0 0 .6rem; color:var(--muted); font-weight:600; }
    table { width:100%; border-collapse:collapse; font-size:.85rem; }
    th, td { text-align:left; padding:.45rem .5rem; border-bottom:1px solid #2a3545; }
    th { color:var(--muted); font-weight:500; }
    .pill { display:inline-block; padding:.1rem .45rem; border-radius:999px; font-size:.75rem; background:#2a3545; }
    .ok { color:var(--ok); } .warn { color:var(--warn); } .bad { color:var(--bad); }
    .err { color:var(--bad); white-space:pre-wrap; }
    button { background:#2d6cdf; color:#fff; border:0; border-radius:6px; padding:.4rem .8rem; cursor:pointer; }
    button:hover { filter:brightness(1.08); }
    .bar { display:flex; gap:.75rem; align-items:center; margin-bottom:1rem; flex-wrap:wrap; }
    input[type=password] { background:var(--card); color:var(--fg); border:1px solid #2a3545; border-radius:6px; padding:.4rem .6rem; min-width:12rem; }
  </style>
</head>
<body>
<main>
  <h1>Telegram Multi-Account Sender — Monitor</h1>
  <p class="sub">Read-only local companion with live charts. Desktop app remains the control surface.</p>
  <div class="bar">
    <button type="button" id="refresh">Refresh</button>
    <input type="password" id="token" placeholder="Bearer token (if required)" autocomplete="off"/>
    <button type="button" id="saveToken">Save token</button>
    <span class="sub" id="stamp">Loading…</span>
  </div>
  <div class="grid" id="summary"></div>
  <section>
    <h2>Live charts</h2>
    <div class="charts">
      <div class="chart-card"><h3>Activity (24h)</h3><div id="chart-activity"></div>
        <div class="legend"><span style="color:var(--sent)">Sent</span><span style="color:var(--fail)">Failed</span><span style="color:var(--skip)">Other</span></div>
      </div>
      <div class="chart-card"><h3>Send status</h3><div id="chart-status"></div></div>
      <div class="chart-card"><h3>Campaigns (sent vs failed)</h3><div id="chart-campaigns"></div></div>
      <div class="chart-card"><h3>Account health</h3><div id="chart-health"></div></div>
    </div>
  </section>
  <section>
    <h2>Accounts</h2>
    <table><thead><tr><th>Name</th><th>Health</th><th>Score</th><th>Status</th></tr></thead>
    <tbody id="accounts"></tbody></table>
  </section>
  <section>
    <h2>Campaigns</h2>
    <table><thead><tr><th>Name</th><th>Status</th><th>Sent</th><th>Failed</th><th>Success</th></tr></thead>
    <tbody id="campaigns"></tbody></table>
  </section>
  <section>
    <h2>Recent activity</h2>
    <table><thead><tr><th>When</th><th>Campaign</th><th>Account</th><th>Status</th></tr></thead>
    <tbody id="activity"></tbody></table>
  </section>
  <p class="err" id="error" hidden></p>
</main>
<script>
const COLORS = {sent:'#3dcc91',failed:'#e85d5d',other:'#9aa7b8',excellent:'#3dcc91',good:'#5bb8a0',warning:'#e6b84d',critical:'#e85d5d',offline:'#6b7785',accent:'#2d6cdf'};
function getToken() {
  const params = new URLSearchParams(location.search);
  const q = params.get('token');
  if (q) { try { sessionStorage.setItem('tmas_token', q); } catch (_) {} return q; }
  try { return sessionStorage.getItem('tmas_token') || ''; } catch (_) { return ''; }
}
function authHeaders() {
  const t = getToken();
  const h = {};
  if (t) h['Authorization'] = 'Bearer ' + t;
  return h;
}
function esc(v){ return String(v==null?'':v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function _status(s){ if (s && typeof s === 'object' && s.value) return s.value; return s; }
function emptyChart(msg){ return `<svg viewBox="0 0 320 120" role="img"><text x="160" y="64" text-anchor="middle" fill="#9aa7b8" font-size="12">${esc(msg)}</text></svg>`; }
function renderActivity(series) {
  const el = document.getElementById('chart-activity');
  if (!series || !series.length) { el.innerHTML = emptyChart('No activity in window'); return; }
  const w=320,h=140,padL=28,padR=8,padT=12,padB=28;
  const max = Math.max(1, ...series.map(p => (p.sent||0)+(p.failed||0)+(p.other||0)));
  const iw=w-padL-padR, ih=h-padT-padB;
  const x = (i) => padL + (series.length<=1 ? iw/2 : (i/(series.length-1))*iw);
  const y = (v) => padT + ih - (v/max)*ih;
  const path = (key, color) => {
    const pts = series.map((p,i) => `${i?'L':'M'}${x(i).toFixed(1)},${y(p[key]||0).toFixed(1)}`).join(' ');
    return `<path d="${pts}" fill="none" stroke="${color}" stroke-width="2"/>`;
  };
  const labels = [0, Math.floor(series.length/2), series.length-1].filter((v,i,a)=>a.indexOf(v)===i);
  const labelEls = labels.map(i => {
    const lab = (series[i].label || series[i].hour || '').toString().slice(-5);
    return `<text x="${x(i).toFixed(1)}" y="${h-6}" text-anchor="middle" fill="#9aa7b8" font-size="9">${esc(lab)}</text>`;
  }).join('');
  el.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Hourly activity">
    <line x1="${padL}" y1="${padT}" x2="${padL}" y2="${padT+ih}" stroke="#2a3545"/>
    <line x1="${padL}" y1="${padT+ih}" x2="${padL+iw}" y2="${padT+ih}" stroke="#2a3545"/>
    ${path('sent', COLORS.sent)}${path('failed', COLORS.failed)}${path('other', COLORS.other)}
    ${labelEls}
  </svg>`;
}
function renderDonut(items, targetId) {
  const el = document.getElementById(targetId);
  const rows = (items || []).filter(r => (r.count||0) > 0);
  if (!rows.length) { el.innerHTML = emptyChart('No data'); return; }
  const total = rows.reduce((s,r)=>s+(r.count||0),0);
  const cx=90,cy=70,r=48,stroke=16;
  let angle = -Math.PI/2;
  const arcs = rows.map(row => {
    const frac = (row.count||0)/total;
    const sweep = frac * Math.PI * 2;
    const x1 = cx + r*Math.cos(angle), y1 = cy + r*Math.sin(angle);
    angle += sweep;
    const x2 = cx + r*Math.cos(angle), y2 = cy + r*Math.sin(angle);
    const large = sweep > Math.PI ? 1 : 0;
    const color = row.color || COLORS[row.key] || COLORS[row.label] || COLORS.accent;
    const d = `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`;
    return `<path d="${d}" fill="none" stroke="${color}" stroke-width="${stroke}" stroke-linecap="butt"/>`;
  }).join('');
  const legend = rows.map(r => {
    const color = r.color || COLORS[r.key] || COLORS[r.label] || COLORS.accent;
    return `<span style="color:${color}">${esc(r.label||r.key)} (${r.count})</span>`;
  }).join('');
  el.innerHTML = `<svg viewBox="0 0 180 140" role="img">${arcs}
    <text x="${cx}" y="${cy+4}" text-anchor="middle" fill="#e7ecf3" font-size="14" font-weight="600">${total}</text>
    <text x="${cx}" y="${cy+18}" text-anchor="middle" fill="#9aa7b8" font-size="9">total</text>
  </svg><div class="legend">${legend}</div>`;
}
function renderBars(items, keys, colors) {
  const el = document.getElementById('chart-campaigns');
  const rows = items || [];
  if (!rows.length) { el.innerHTML = emptyChart('No campaigns'); return; }
  const w=320, rowH=22, padL=90, padR=12, padT=8, h=padT+rows.length*rowH+8;
  const max = Math.max(1, ...rows.map(r => keys.reduce((s,k)=>s+(r[k]||0),0)));
  const iw = w-padL-padR;
  const body = rows.map((r,i) => {
    const y = padT + i*rowH;
    let x = padL;
    const segs = keys.map((k,ki) => {
      const val = r[k]||0;
      const bw = (val/max)*iw;
      const rect = `<rect x="${x.toFixed(1)}" y="${y+4}" width="${Math.max(0,bw).toFixed(1)}" height="12" fill="${colors[ki]}" rx="2"/>`;
      x += bw;
      return rect;
    }).join('');
    const name = String(r.label||r.name||'—').slice(0,14);
    return `<text x="${padL-6}" y="${y+14}" text-anchor="end" fill="#9aa7b8" font-size="10">${esc(name)}</text>${segs}`;
  }).join('');
  el.innerHTML = `<svg viewBox="0 0 ${w} ${h}" role="img">${body}</svg>`;
}
function renderCharts(charts) {
  const c = charts || {};
  renderActivity(c.activity_hourly || []);
  renderDonut(c.status_breakdown || [], 'chart-status');
  renderBars(c.campaign_bars || [], ['sent','failed'], [COLORS.sent, COLORS.failed]);
  renderDonut(c.health_breakdown || [], 'chart-health');
}
async function load() {
  const err = document.getElementById('error');
  err.hidden = true;
  const tokenInput = document.getElementById('token');
  if (tokenInput && !tokenInput.value) tokenInput.value = getToken();
  try {
    const res = await fetch('/api/overview', { headers: authHeaders() });
    if (res.status === 401) throw new Error('Unauthorized — set the bearer token (Authorization / ?token=)');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    const s = data.health_summary || {};
    const a = (data.analytics && data.analytics.summary) || {};
    document.getElementById('summary').innerHTML = [
      ['Accounts', s.total ?? 0],
      ['Healthy', s.healthy ?? 0],
      ['Needs attention', s.needs_attention ?? 0],
      ['Avg score', (s.average_score != null ? Number(s.average_score).toFixed(1) : '—')],
      ['Campaigns', a.campaign_count ?? 0],
      ['Total sent', a.total_sent ?? 0],
    ].map(([l,n]) => `<div class="card"><div class="n">${n}</div><div class="l">${l}</div></div>`).join('');
    renderCharts(data.charts);
    const healthClass = (h) => (h === 'excellent' || h === 'good') ? 'ok' : (h === 'warning' ? 'warn' : 'bad');
    document.getElementById('accounts').innerHTML = (data.accounts || []).map(r =>
      `<tr><td>${esc(r.account_name)}</td><td class="${healthClass(r.health_status)}"><span class="pill">${esc(r.health_status)}</span></td><td>${Number(r.score||0).toFixed(0)}</td><td>${esc(_status(r.status))}</td></tr>`
    ).join('') || '<tr><td colspan="4">No accounts</td></tr>';
    document.getElementById('campaigns').innerHTML = ((data.analytics && data.analytics.campaigns) || []).map(c =>
      `<tr><td>${esc(c.campaign_name)}</td><td><span class="pill">${esc(c.status)}</span></td><td>${c.sent_count}</td><td>${c.failed_count}</td><td>${Number(c.success_rate||0).toFixed(1)}%</td></tr>`
    ).join('') || '<tr><td colspan="5">No campaigns</td></tr>';
    document.getElementById('activity').innerHTML = (data.activity || []).map(ev =>
      `<tr><td>${esc(ev.sent_at || '—')}</td><td>${esc(String(ev.campaign_id ?? '—'))}</td><td>${esc(String(ev.account_id ?? '—'))}</td><td>${esc(ev.status)}</td></tr>`
    ).join('') || '<tr><td colspan="4">No recent activity</td></tr>';
    document.getElementById('stamp').textContent = 'Updated ' + (data.generated_at || new Date().toISOString()) +
      ' · v' + ((data.app && data.app.version) || '') + ' · charts auto-refresh 15s';
  } catch (e) {
    err.hidden = false;
    err.textContent = 'Failed to load overview: ' + e;
  }
}
document.getElementById('refresh').onclick = load;
document.getElementById('saveToken').onclick = () => {
  const t = (document.getElementById('token').value || '').trim();
  try { if (t) sessionStorage.setItem('tmas_token', t); else sessionStorage.removeItem('tmas_token'); } catch (_) {}
  load();
};
load();
setInterval(load, 15000);
</script>
</body>
</html>
"""


def is_loopback_host(host: str) -> bool:
    """Return True when *host* is a loopback bind (or empty → default loopback)."""
    normalized = (host or DEFAULT_HOST).strip().lower()
    return normalized in LOOPBACK_HOSTS


def normalize_companion_token(token: Optional[str]) -> Optional[str]:
    """Strip whitespace; empty becomes None."""
    if token is None:
        return None
    cleaned = str(token).strip()
    return cleaned or None


def generate_companion_token() -> str:
    """Generate a URL-safe companion bearer token."""
    return secrets.token_urlsafe(32)


def require_token_for_bind(host: str, token: Optional[str]) -> None:
    """
    Non-loopback binds must have a configured token.

    Raises:
        ValueError: when binding beyond loopback without a token.
    """
    if not is_loopback_host(host) and normalize_companion_token(token) is None:
        raise ValueError(
            "Non-localhost web companion bind requires WEB_COMPANION_TOKEN "
            "(or --token). Prefer binding 127.0.0.1 behind a TLS reverse proxy "
            "that preserves the Authorization header. See docs/configuration.md."
        )


def tokens_match(expected: Optional[str], provided: Optional[str]) -> bool:
    """Constant-time compare of companion tokens."""
    exp = normalize_companion_token(expected)
    got = normalize_companion_token(provided)
    if exp is None or got is None:
        return False
    return hmac.compare_digest(exp.encode("utf-8"), got.encode("utf-8"))


def extract_request_token(
    headers: Any,
    query: str,
) -> Optional[str]:
    """
    Pull a token from Authorization Bearer, X-TMAS-Token, or ``?token=``.

    Args:
        headers: mapping-like header object (case-insensitive preferred).
        query: raw URL query string (no leading ``?``).
    """
    auth = ""
    xtoken = ""
    if headers is not None:
        getter = getattr(headers, "get", None)
        if callable(getter):
            auth = str(getter("Authorization") or getter("authorization") or "")
            xtoken = str(getter("X-TMAS-Token") or getter("x-tmas-token") or "")
    if auth.lower().startswith("bearer "):
        return normalize_companion_token(auth[7:])
    if xtoken:
        return normalize_companion_token(xtoken)
    if query:
        params = parse_qs(query, keep_blank_values=False)
        values = params.get("token") or []
        if values:
            return normalize_companion_token(values[0])
    return None


def _enum_value(value: Any) -> str:
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"Object of type {type(obj)!r} is not JSON serializable")


def build_accounts_payload(monitor: Optional[AccountHealthMonitor] = None) -> Dict[str, Any]:
    """Account health rows + summary (read-only)."""
    health = monitor or AccountHealthMonitor()
    rows = health.get_all_accounts_health()
    # Normalize enum status for JSON
    normalized: List[Dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["status"] = _enum_value(item.get("status"))
        normalized.append(item)
    return {
        "summary": health.get_health_summary(normalized),
        "accounts": normalized,
    }


def build_campaigns_payload() -> Dict[str, Any]:
    """Campaign status list without message bodies."""
    with get_session() as session:
        campaigns = list(
            session.exec(select(Campaign).where(Campaign.is_deleted.is_(False))).all()  # type: ignore[attr-defined]
        )
    items: List[Dict[str, Any]] = []
    for campaign in campaigns:
        total = int(campaign.total_recipients or 0)
        sent = int(campaign.sent_count or 0)
        failed = int(campaign.failed_count or 0)
        skipped = int(campaign.skipped_count or 0)
        attempted = sent + failed
        items.append(
            {
                "id": campaign.id,
                "name": campaign.name,
                "status": _enum_value(campaign.status),
                "campaign_type": _enum_value(campaign.campaign_type),
                "total_recipients": total,
                "sent_count": sent,
                "failed_count": failed,
                "skipped_count": skipped,
                "success_rate": (sent / attempted * 100) if attempted else 0.0,
                "completion_rate": (sent / total * 100) if total else 0.0,
                "start_time_actual": (
                    campaign.start_time_actual.isoformat() if campaign.start_time_actual else None
                ),
                "end_time_actual": (
                    campaign.end_time_actual.isoformat() if campaign.end_time_actual else None
                ),
            }
        )
    by_status: Dict[str, int] = {}
    for item in items:
        st = str(item["status"])
        by_status[st] = by_status.get(st, 0) + 1
    return {
        "summary": {
            "campaign_count": len(items),
            "by_status": by_status,
            "running": by_status.get("running", 0),
            "paused": by_status.get("paused", 0),
        },
        "campaigns": items,
    }


def build_activity_payload(limit: int = DEFAULT_ACTIVITY_LIMIT) -> Dict[str, Any]:
    """Recent send-log activity (metadata only)."""
    limit = max(1, min(int(limit), MAX_ACTIVITY_LIMIT))
    with get_session() as session:
        logs = list(
            session.exec(
                select(SendLog).order_by(SendLog.created_at.desc()).limit(limit)  # type: ignore[attr-defined]
            ).all()
        )
    events: List[Dict[str, Any]] = []
    for log in logs:
        events.append(
            {
                "id": log.id,
                "campaign_id": log.campaign_id,
                "account_id": log.account_id,
                "status": _enum_value(log.status),
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                "completed_at": log.completed_at.isoformat() if log.completed_at else None,
                "error_message": (log.error_message[:200] if log.error_message else None),
            }
        )
    return {"limit": limit, "activity": events}


def build_analytics_overview() -> Dict[str, Any]:
    """Campaign analytics overview (same shape as dashboard export summary)."""
    with get_session() as session:
        campaigns = list(
            session.exec(select(Campaign).where(Campaign.is_deleted.is_(False))).all()  # type: ignore[attr-defined]
        )
        logs_by_campaign: Dict[int, List[SendLog]] = {}
        for campaign in campaigns:
            if campaign.id is None:
                continue
            logs_by_campaign[campaign.id] = list(
                session.exec(select(SendLog).where(SendLog.campaign_id == campaign.id)).all()
            )
    analytics = CampaignAnalytics(AnalyticsCollector())
    overview = analytics.build_overview_export(campaigns, logs_by_campaign)
    # Drop heavy per-campaign reports for the live monitor; keep summary + table.
    return {
        "export_type": overview.get("export_type"),
        "generated_at": overview.get("generated_at"),
        "summary": overview.get("summary"),
        "campaigns": overview.get("campaigns"),
    }


def _log_event_time(log: Any) -> Optional[datetime]:
    """Best available timestamp for chart bucketing."""
    for attr in ("sent_at", "completed_at", "created_at"):
        value = getattr(log, attr, None)
        if isinstance(value, datetime):
            return value
    return None


def _log_status_key(log: Any) -> str:
    status = getattr(log, "status", None)
    return _enum_value(status).lower() if status is not None else "unknown"


def aggregate_hourly_activity(
    logs: Sequence[Any],
    *,
    hours: int = DEFAULT_CHART_HOURS,
    now: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """
    Build hourly sent/failed/other series for the last *hours* window.

    Pure helper (duck-typed logs) so unit tests need no database.
    """
    window = max(1, min(int(hours), MAX_CHART_HOURS))
    end = now or datetime.utcnow()
    end_hour = end.replace(minute=0, second=0, microsecond=0)
    start = end_hour - timedelta(hours=window - 1)
    buckets: Dict[datetime, Dict[str, int]] = {}
    cursor = start
    while cursor <= end_hour:
        buckets[cursor] = {"sent": 0, "failed": 0, "other": 0}
        cursor += timedelta(hours=1)

    for log in logs:
        when = _log_event_time(log)
        if when is None:
            continue
        bucket_key = when.replace(minute=0, second=0, microsecond=0)
        if bucket_key < start or bucket_key > end_hour:
            continue
        slot = buckets.setdefault(bucket_key, {"sent": 0, "failed": 0, "other": 0})
        status = _log_status_key(log)
        if status == "sent":
            slot["sent"] += 1
        elif status == "failed":
            slot["failed"] += 1
        else:
            slot["other"] += 1

    series: List[Dict[str, Any]] = []
    for hour in sorted(buckets.keys()):
        counts = buckets[hour]
        series.append(
            {
                "hour": hour.isoformat(),
                "label": hour.strftime("%H:00"),
                "sent": counts["sent"],
                "failed": counts["failed"],
                "other": counts["other"],
                "total": counts["sent"] + counts["failed"] + counts["other"],
            }
        )
    return series


def aggregate_status_breakdown(logs: Sequence[Any]) -> List[Dict[str, Any]]:
    """Pie/donut slices for send-status counts."""
    counts: Dict[str, int] = {}
    for log in logs:
        key = _log_status_key(log)
        counts[key] = counts.get(key, 0) + 1
    color_map = {
        "sent": "#3dcc91",
        "failed": "#e85d5d",
        "skipped": "#9aa7b8",
        "rate_limited": "#e6b84d",
        "pending": "#2d6cdf",
        "sending": "#5b8def",
        "cancelled": "#6b7785",
    }
    items = [
        {
            "key": key,
            "label": key.replace("_", " "),
            "count": count,
            "color": color_map.get(key, "#2d6cdf"),
        }
        for key, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    return items


def aggregate_campaign_bars(
    campaigns: Sequence[Any],
    *,
    limit: int = MAX_CHART_CAMPAIGNS,
) -> List[Dict[str, Any]]:
    """Horizontal bar rows for top campaigns by attempted sends."""
    rows: List[Dict[str, Any]] = []
    for campaign in campaigns:
        sent = int(getattr(campaign, "sent_count", None) or 0)
        failed = int(getattr(campaign, "failed_count", None) or 0)
        name = str(getattr(campaign, "name", None) or getattr(campaign, "campaign_name", None) or "—")
        cid = getattr(campaign, "id", None)
        rows.append(
            {
                "id": cid,
                "label": name,
                "name": name,
                "sent": sent,
                "failed": failed,
                "attempted": sent + failed,
            }
        )
    rows.sort(key=lambda r: (-int(r["attempted"]), str(r["label"])))
    return rows[: max(1, int(limit))] if rows else []


def aggregate_health_breakdown(accounts: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Donut slices for account health_status distribution."""
    counts: Dict[str, int] = {}
    for row in accounts:
        key = str(row.get("health_status") or "offline").lower()
        counts[key] = counts.get(key, 0) + 1
    color_map = {
        "excellent": "#3dcc91",
        "good": "#5bb8a0",
        "warning": "#e6b84d",
        "critical": "#e85d5d",
        "offline": "#6b7785",
    }
    return [
        {
            "key": key,
            "label": key,
            "count": count,
            "color": color_map.get(key, "#2d6cdf"),
        }
        for key, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    ]


def build_charts_payload(
    *,
    hours: int = DEFAULT_CHART_HOURS,
    log_limit: int = DEFAULT_CHART_LOG_LIMIT,
    now: Optional[datetime] = None,
    monitor: Optional[AccountHealthMonitor] = None,
) -> Dict[str, Any]:
    """
    Live chart series for the companion dashboard (read-only, real DB data).

    Returns hourly activity, status breakdown, campaign bars, and health donut.
    """
    window = max(1, min(int(hours), MAX_CHART_HOURS))
    end = now or datetime.utcnow()
    since = end - timedelta(hours=window)
    fetch_limit = max(1, min(int(log_limit), DEFAULT_CHART_LOG_LIMIT))

    with get_session() as session:
        logs = list(
            session.exec(
                select(SendLog)
                .where(SendLog.created_at >= since)
                .order_by(SendLog.created_at.desc())  # type: ignore[attr-defined]
                .limit(fetch_limit)
            ).all()
        )
        campaigns = list(
            session.exec(select(Campaign).where(Campaign.is_deleted.is_(False))).all()  # type: ignore[attr-defined]
        )

    accounts_payload = build_accounts_payload(monitor)
    return {
        "window_hours": window,
        "generated_at": end.isoformat() + "Z",
        "activity_hourly": aggregate_hourly_activity(logs, hours=window, now=end),
        "status_breakdown": aggregate_status_breakdown(logs),
        "campaign_bars": aggregate_campaign_bars(campaigns),
        "health_breakdown": aggregate_health_breakdown(accounts_payload["accounts"]),
        "meta": {
            "logs_sampled": len(logs),
            "campaign_count": len(campaigns),
            "account_count": len(accounts_payload["accounts"]),
        },
    }


def build_status_payload(
    settings: Optional[Settings] = None,
    *,
    auth_required: bool = False,
) -> Dict[str, Any]:
    """Lightweight app / companion status (never includes the raw token)."""
    cfg = settings or get_settings()
    host = cfg.web_companion_host or DEFAULT_HOST
    loopback = is_loopback_host(host)
    token_configured = bool(normalize_companion_token(cfg.web_companion_token))
    bind_warning: Optional[str] = None
    if not loopback:
        bind_warning = (
            "Bound beyond localhost — bearer token auth is required; "
            "prefer 127.0.0.1 behind a TLS reverse proxy"
        )
    elif token_configured:
        bind_warning = None
    return {
        "app": {
            "name": cfg.app_name,
            "version": __version__,
            "read_only": True,
        },
        "companion": {
            "enabled": bool(cfg.web_companion_enabled),
            "host": host,
            "port": int(cfg.web_companion_port),
            "auth_required": bool(auth_required or token_configured),
            "token_configured": token_configured,
            "bind_warning": bind_warning,
        },
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


def build_overview_payload(
    settings: Optional[Settings] = None,
    activity_limit: int = DEFAULT_ACTIVITY_LIMIT,
    *,
    auth_required: bool = False,
) -> Dict[str, Any]:
    """Combined monitoring snapshot for the HTML dashboard."""
    accounts = build_accounts_payload()
    campaigns = build_campaigns_payload()
    activity = build_activity_payload(activity_limit)
    analytics = build_analytics_overview()
    charts = build_charts_payload()
    status = build_status_payload(settings, auth_required=auth_required)
    return {
        **status,
        "health_summary": accounts["summary"],
        "accounts": accounts["accounts"],
        "campaign_summary": campaigns["summary"],
        "campaigns": campaigns["campaigns"],
        "analytics": analytics,
        "charts": charts,
        "activity": activity["activity"],
    }


SnapshotBuilder = Callable[[], Dict[str, Any]]


class WebCompanionHandler(BaseHTTPRequestHandler):
    """HTTP handler: GET/HEAD/OPTIONS only; JSON API + static index."""

    server_version = "TMASWebCompanion/1.0"
    # Injected on the server instance
    snapshot_builders: Dict[str, SnapshotBuilder] = {}

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        get_logger().debug("web-companion: " + format % args)

    def _builders(self) -> Dict[str, SnapshotBuilder]:
        builders = getattr(self.server, "snapshot_builders", None)
        if isinstance(builders, dict):
            return builders
        return {}

    def _expected_token(self) -> Optional[str]:
        return normalize_companion_token(getattr(self.server, "auth_token", None))

    def _auth_required(self) -> bool:
        return self._expected_token() is not None

    def _authorized(self) -> bool:
        expected = self._expected_token()
        if expected is None:
            return True
        parsed = urlparse(self.path)
        provided = extract_request_token(self.headers, parsed.query or "")
        return tokens_match(expected, provided)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors_headers()
        self.send_header("Allow", ", ".join(sorted(ALLOWED_METHODS)))
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        self._handle_read(include_body=True)

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle_read(include_body=False)

    def do_POST(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_PUT(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_PATCH(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def _method_not_allowed(self) -> None:
        body = json.dumps(
            {
                "error": "method_not_allowed",
                "detail": "Web companion is read-only; mutating HTTP methods are rejected.",
                "allowed": sorted(ALLOWED_METHODS),
            }
        ).encode("utf-8")
        self.send_response(405)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Allow", ", ".join(sorted(ALLOWED_METHODS)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _unauthorized(self, *, include_body: bool) -> None:
        payload = {
            "error": "unauthorized",
            "detail": (
                "Valid companion token required. Send Authorization: Bearer <token>, "
                "X-TMAS-Token: <token>, or ?token=<token>."
            ),
        }
        body = json.dumps(payload).encode("utf-8")
        self.send_response(401)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("WWW-Authenticate", 'Bearer realm="tmms-web-companion"')
        self.send_header("Cache-Control", "no-store")
        self._cors_headers()
        self.end_headers()
        if include_body:
            self.wfile.write(body)

    def _cors_headers(self) -> None:
        # Local companion only; permissive CORS is fine for localhost tooling.
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", ", ".join(sorted(ALLOWED_METHODS)))
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-TMAS-Token",
        )

    def _handle_read(self, *, include_body: bool) -> None:
        if self._auth_required() and not self._authorized():
            self._unauthorized(include_body=include_body)
            return

        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path == "/":
            payload = _HTML_PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self._cors_headers()
            self.end_headers()
            if include_body:
                self.wfile.write(payload)
            return

        if path.startswith("/api/") and path not in READ_ONLY_API_PATHS:
            self._send_json(404, {"error": "not_found", "path": path}, include_body=include_body)
            return

        builders = self._builders()
        builder = builders.get(path)
        if builder is None:
            self._send_json(404, {"error": "not_found", "path": path}, include_body=include_body)
            return
        try:
            data = builder()
        except Exception as exc:  # pragma: no cover - surfaced in tests via mock
            get_logger().error(f"web-companion handler error on {path}: {exc}")
            self._send_json(
                500,
                {"error": "internal_error", "detail": str(exc)},
                include_body=include_body,
            )
            return
        self._send_json(200, data, include_body=include_body)

    def _send_json(self, status: int, data: Dict[str, Any], *, include_body: bool) -> None:
        body = json.dumps(data, default=_json_default).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors_headers()
        self.end_headers()
        if include_body:
            self.wfile.write(body)


def make_snapshot_builders(
    settings: Optional[Settings] = None,
    activity_limit: int = DEFAULT_ACTIVITY_LIMIT,
    *,
    auth_required: bool = False,
) -> Dict[str, SnapshotBuilder]:
    """Map API paths to snapshot callables (injectable for tests)."""

    def status() -> Dict[str, Any]:
        return build_status_payload(settings, auth_required=auth_required)

    def accounts() -> Dict[str, Any]:
        return build_accounts_payload()

    def campaigns() -> Dict[str, Any]:
        return build_campaigns_payload()

    def activity() -> Dict[str, Any]:
        return build_activity_payload(activity_limit)

    def overview() -> Dict[str, Any]:
        return build_overview_payload(settings, activity_limit, auth_required=auth_required)

    def charts() -> Dict[str, Any]:
        return build_charts_payload()

    return {
        "/api/status": status,
        "/api/accounts": accounts,
        "/api/campaigns": campaigns,
        "/api/activity": activity,
        "/api/overview": overview,
        "/api/charts": charts,
    }


class WebCompanionServer:
    """Threading HTTP server wrapper for the read-only companion."""

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        settings: Optional[Settings] = None,
        snapshot_builders: Optional[Dict[str, SnapshotBuilder]] = None,
        auth_token: Optional[str] = None,
    ) -> None:
        self.host = host
        self.port = int(port)
        self.settings = settings
        token_from_settings = None
        if settings is not None:
            token_from_settings = normalize_companion_token(settings.web_companion_token)
        self.auth_token = normalize_companion_token(auth_token) or token_from_settings
        auth_required = self.auth_token is not None
        self.snapshot_builders = snapshot_builders or make_snapshot_builders(
            settings, auth_required=auth_required
        )
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def base_url(self) -> str:
        display_host = "127.0.0.1" if self.host in ("0.0.0.0", "::") else self.host
        base = f"http://{display_host}:{self.port}"
        if self.auth_token:
            return f"{base}/?token={quote(self.auth_token, safe='')}"
        return base

    @property
    def is_running(self) -> bool:
        return self._httpd is not None and self._thread is not None and self._thread.is_alive()

    def start(self, *, background: bool = True) -> str:
        """Start the server; return the base URL (may include ``?token=``)."""
        if self.is_running:
            return self.base_url

        require_token_for_bind(self.host, self.auth_token)

        if not is_loopback_host(self.host):
            get_logger().warning(
                f"Web companion binding to {self.host}:{self.port} with bearer-token auth. "
                "Prefer 127.0.0.1 behind a TLS reverse proxy that preserves Authorization."
            )

        httpd = ThreadingHTTPServer((self.host, self.port), WebCompanionHandler)
        setattr(httpd, "snapshot_builders", self.snapshot_builders)
        setattr(httpd, "auth_token", self.auth_token)
        self._httpd = httpd

        if background:
            thread = threading.Thread(
                target=httpd.serve_forever,
                name="tmms-web-companion",
                daemon=True,
            )
            thread.start()
            self._thread = thread
        else:
            self._thread = None
            httpd.serve_forever()
        get_logger().info(
            f"Web companion listening at {self.base_url.split('?', 1)[0]} "
            f"(read-only{'; auth_required' if self.auth_token else ''})"
        )
        return self.base_url

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        self._thread = None


_runtime_server: Optional[WebCompanionServer] = None
_runtime_gui_owned: bool = False
_runtime_lock = threading.Lock()


def get_runtime_server() -> Optional[WebCompanionServer]:
    """Return the process-wide companion server if started from the desktop app."""
    return _runtime_server


def is_companion_gui_owned() -> bool:
    """True when the desktop GUI started (and still owns) the process-wide companion."""
    return _runtime_gui_owned


def start_companion_from_settings(
    settings: Optional[Settings] = None,
    *,
    background: bool = True,
    gui_owned: bool = False,
) -> WebCompanionServer:
    """Start (or return) the singleton companion using Settings host/port/token."""
    global _runtime_server, _runtime_gui_owned
    cfg = settings or get_settings()
    with _runtime_lock:
        if _runtime_server is not None and _runtime_server.is_running:
            if gui_owned:
                _runtime_gui_owned = True
            return _runtime_server
        server = WebCompanionServer(
            host=cfg.web_companion_host or DEFAULT_HOST,
            port=int(cfg.web_companion_port or DEFAULT_PORT),
            settings=cfg,
            auth_token=cfg.web_companion_token,
        )
        server.start(background=background)
        _runtime_server = server
        if gui_owned:
            _runtime_gui_owned = True
        return server


def stop_companion(*, only_if_gui_owned: bool = False) -> bool:
    """
    Stop the process-wide companion if running.

    When ``only_if_gui_owned`` is True, stop only if the desktop GUI started it
    (auto-start or Settings → Start & Open). Returns True when a server was stopped.
    """
    global _runtime_server, _runtime_gui_owned
    with _runtime_lock:
        if only_if_gui_owned and not _runtime_gui_owned:
            return False
        stopped = False
        if _runtime_server is not None:
            _runtime_server.stop()
            _runtime_server = None
            stopped = True
        _runtime_gui_owned = False
        return stopped


def maybe_autostart_companion_from_settings(
    settings: Optional[Settings] = None,
) -> Optional[WebCompanionServer]:
    """
    Start the companion in the background when ``web_companion_auto_start`` is set.

    Does not open a browser. Marks the server as GUI-owned so app exit can stop it.
    Returns the server on success, or ``None`` when auto-start is disabled / failed.
    """
    cfg = settings or get_settings()
    if not bool(cfg.web_companion_auto_start):
        return None
    try:
        server = start_companion_from_settings(cfg, background=True, gui_owned=True)
        listen = server.base_url.split("?", 1)[0]
        get_logger().info(f"Web companion auto-started at {listen} (background, no browser)")
        return server
    except Exception as exc:
        get_logger().error(f"Web companion auto-start failed: {exc}")
        return None


def companion_url_from_settings(settings: Optional[Settings] = None) -> str:
    cfg = settings or get_settings()
    return cfg.get_web_companion_url()


def parse_web_monitor_argv(
    argv: Sequence[str],
) -> Tuple[bool, Optional[str], Optional[int], Optional[str]]:
    """
    Detect ``web-monitor`` / ``web-companion`` CLI mode.

    Returns ``(is_web_mode, host_override, port_override, token_override)``.
    """
    tokens = list(argv[1:]) if argv else []
    if not tokens:
        return False, None, None, None
    cmd = tokens[0].lower().replace("_", "-")
    if cmd not in ("web-monitor", "web-companion", "serve-monitor"):
        return False, None, None, None
    host: Optional[str] = None
    port: Optional[int] = None
    token: Optional[str] = None
    i = 1
    while i < len(tokens):
        tok = tokens[i]
        if tok in ("--host", "-H") and i + 1 < len(tokens):
            host = tokens[i + 1]
            i += 2
            continue
        if tok in ("--port", "-p") and i + 1 < len(tokens):
            port = int(tokens[i + 1])
            i += 2
            continue
        if tok in ("--token", "-t") and i + 1 < len(tokens):
            token = tokens[i + 1]
            i += 2
            continue
        if tok.startswith("--host="):
            host = tok.split("=", 1)[1]
            i += 1
            continue
        if tok.startswith("--port="):
            port = int(tok.split("=", 1)[1])
            i += 1
            continue
        if tok.startswith("--token="):
            token = tok.split("=", 1)[1]
            i += 1
            continue
        i += 1
    return True, host, port, token


def _print_web_monitor_help() -> None:
    print(
        """TMAS web companion (read-only local monitor)

  telegram-sender web-monitor
  telegram-sender web-monitor --host 127.0.0.1 --port 8765
  telegram-sender web-monitor --host 0.0.0.0 --port 8765 --token <secret>

Options:
  --host / -H   Bind address (default 127.0.0.1)
  --port / -p   Port (default 8765)
  --token / -t  Bearer token (required for non-localhost binds)

Read-only endpoints: /  /api/status  /api/accounts  /api/campaigns
  /api/activity  /api/overview  /api/charts
No write/control routes. Prefer localhost; use a TLS reverse proxy for remote access.
See docs/configuration.md and SECURITY.md.
"""
    )


def run_web_monitor_cli(argv: Sequence[str]) -> int:
    """
    CLI entry for read-only monitoring server (blocks until Ctrl+C).

    Example::

        telegram-sender web-monitor
        telegram-sender web-monitor --host 127.0.0.1 --port 8765
        telegram-sender web-monitor --host 0.0.0.0 --port 8765 --token "$(openssl rand -hex 32)"
    """
    is_web, host_override, port_override, token_override = parse_web_monitor_argv(argv)
    if not is_web:
        raise ValueError("run_web_monitor_cli requires a web-monitor argv")

    if any(tok in ("-h", "--help") for tok in list(argv[1:])):
        _print_web_monitor_help()
        return 0

    initialize = __import__("app.services.db", fromlist=["initialize_database"]).initialize_database
    initialize()
    settings = get_settings()
    host = host_override or settings.web_companion_host or DEFAULT_HOST
    port = port_override if port_override is not None else int(settings.web_companion_port or DEFAULT_PORT)
    token = normalize_companion_token(token_override) or normalize_companion_token(
        settings.web_companion_token
    )

    require_token_for_bind(host, token)

    server = WebCompanionServer(host=host, port=port, settings=settings, auth_token=token)
    listen = server.base_url.split("?", 1)[0]
    print(f"TMAS web companion (read-only) at {listen}")
    print(
        "Endpoints: /  /api/status  /api/accounts  /api/campaigns  "
        "/api/activity  /api/overview  /api/charts"
    )
    print("No write/control routes. Ctrl+C to stop.")
    if token:
        print("Auth: Authorization: Bearer <token> | X-TMAS-Token | ?token=")
        print("Token is configured (value not printed). Open the dashboard with ?token=… or a reverse proxy that preserves Authorization.")
    if not is_loopback_host(host):
        print(
            "NOTE: Bound beyond localhost with token auth. "
            "Recommended: bind 127.0.0.1 and put Caddy/nginx TLS in front — see docs/configuration.md."
        )
    try:
        server.start(background=False)
    except KeyboardInterrupt:
        print("\nStopping web companion…")
        server.stop()
    return 0
