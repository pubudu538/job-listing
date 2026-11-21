#!/usr/bin/env python3
"""Build the daily job pages for GitHub Pages.

Reads every data/YYYY-MM-DD.json and writes:
  daily/YYYY-MM-DD.html  one page per day with that day's new roles
  daily/index.html       the date-wise archive

The main index.html is never touched by this script.

data/YYYY-MM-DD.json format:
{
  "date": "2026-11-19",
  "sources_checked": ["topjobs.lk", "itpro.lk", ...],   (optional)
  "jobs": [
    {"group": "lk" | "rem" | "eu" | "us", "kind": "BA" | "PM" | "Product",
     "role": "...", "company": "...", "location": "...",
     "arrangement": "Remote" | "Hybrid" | "Onsite" | "Not stated",
     "fit": "Strong" | "Good" | "Stretch",
     "posted": "YYYY-MM-DD" or free text or "", "closes": "YYYY-MM-DD" or "",
     "note": "...", "url": "https://..."}
  ]
}
"""
import datetime as dt
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "daily"
CSS = (ROOT / "tools" / "page.css").read_text(encoding="utf-8")
SITE = "https://pubudu538.github.io/job-listing/"

HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
body{{margin:0}} img{{max-width:100%}}
{css}
.nav{{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:.9rem}}
.nav a{{font-weight:500}}
.daylist{{display:grid;gap:8px;margin:0;padding:0;list-style:none}}
.daylist li{{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px 14px;display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline}}
.daylist .d{{font-family:var(--mono);font-weight:500;min-width:120px}}
.daylist .c{{color:var(--muted);font-size:.88rem}}
</style></head><body>
"""
FOOT = "</body></html>\n"


def esc(s):
    return html.escape(str(s or ""), quote=True)


def parse(s):
    try:
        return dt.date.fromisoformat(s)
    except (TypeError, ValueError):
        return None


def fmt(s):
    d = parse(s)
    if d:
        return d.strftime("%d %b %Y")
    return s or "Not shown"


def long_date(d):
    return f"{d.day} {d.strftime('%B %Y')}"


def load_days():
    days = []
    for p in sorted(DATA.glob("*.json")):
        day = json.loads(p.read_text(encoding="utf-8"))
        d = parse(day.get("date") or p.stem)
        if not d:
            sys.exit(f"{p.name}: missing or bad date")
        day["_date"] = d
        day.setdefault("jobs", [])
        days.append(day)
    days.sort(key=lambda x: x["_date"])
    return days


SECTIONS = [
    ("strong", "Strong fit", "Healthcare or lead-level matches. Look at these first."),
    ("lk", "Sri Lanka: onsite, hybrid and local remote", "Roles hiring in Sri Lanka."),
    ("rem", "Remote, open to Sri Lanka", "Remote roles open to Anywhere, Asia, APAC, or a country list that includes Sri Lanka."),
    ("eu", "Remote with European companies", "Europe-based teams whose adverts allow working from Sri Lanka or anywhere, usually with some overlap with European hours."),
    ("us", "Remote healthcare, check eligibility", "Close skill match, but probably US-only."),
]


def section_of(job):
    g = job.get("group", "lk")
    if job.get("fit") == "Strong" and g != "us":
        return "strong"
    return g if g in ("lk", "rem", "eu", "us") else "lk"


def row(job, day):
    a = job.get("arrangement") or "Not stated"
    ac = {"Remote": "p-remote", "Hybrid": "p-hybrid"}.get(a, "p-onsite")
    al = "Onsite / not stated" if a in ("Onsite", "Not stated") else a
    fit = job.get("fit") or "Good"
    closes = job.get("closes", "")
    cd = parse(closes)
    close_html = esc(fmt(closes))
    if cd and 0 <= (cd - day).days <= 3:
        close_html = f'<span class="pill soon">{close_html}</span>'
    note = f"<small>{esc(job.get('note'))}</small>" if job.get("note") else ""
    url = job.get("url") or ""
    link = f'<a href="{esc(url)}" target="_blank" rel="noopener">Open ad</a>' if url else ""
    return (f"<tr><td class=\"role\">{esc(job.get('role'))}{note}</td>"
            f"<td>{esc(job.get('company'))}</td><td>{esc(job.get('location'))}</td>"
            f"<td><span class=\"pill {ac}\">{esc(al)}</span></td>"
            f"<td class=\"date\">{esc(fmt(job.get('posted')))}</td><td class=\"date\">{close_html}</td>"
            f"<td><span class=\"pill f-{esc(fit.lower())}\">{esc(fit)}</span></td><td>{link}</td></tr>")


def day_page(day, prev_day, next_day):
    d = day["_date"]
    jobs = day["jobs"]
    nav = ['<a href="../">Main report</a>', '<a href="./">All dates</a>']
    if prev_day:
        nav.append(f'<a href="{prev_day["_date"].isoformat()}.html">&larr; {fmt(prev_day["_date"].isoformat())}</a>')
    if next_day:
        nav.append(f'<a href="{next_day["_date"].isoformat()}.html">{fmt(next_day["_date"].isoformat())} &rarr;</a>')
    strong = sum(1 for j in jobs if j.get("fit") == "Strong")
    soon = sum(1 for j in jobs if parse(j.get("closes")) and 0 <= (parse(j["closes"]) - d).days <= 3)
    parts = [HEAD.format(title=f"New Roles, {fmt(d.isoformat())}", css=CSS),
             '<div class="wrap"><header>',
             f'<div class="eyebrow">Daily job watch · {esc(long_date(d))}</div>',
             f'<h1>New roles, {esc(long_date(d))}</h1>',
             '<p class="lede">Roles found for the first time on this date. Earlier roles are in the main report and on earlier dates.</p>',
             f'</header><nav class="nav" aria-label="Pages">{" ".join(nav)}</nav>',
             f'<div class="stats"><span><strong>{len(jobs)}</strong> new roles</span>'
             f'<span><strong>{strong}</strong> strong fit</span><span><strong>{soon}</strong> closing within 3 days</span></div>']
    if not jobs:
        parts.append('<p class="empty">No new roles were found on this date.</p>')
    for key, title, blurb in SECTIONS:
        rows = [j for j in jobs if section_of(j) == key]
        if not rows:
            continue
        rows.sort(key=lambda j: j.get("posted") or "", reverse=True)
        parts.append(f'<section><div class="sechead"><h2>{esc(title)}</h2><p>{esc(blurb)}</p></div>'
                     '<div class="tbl"><table><thead><tr><th>Role</th><th>Company</th><th>Location</th>'
                     '<th>Arrangement</th><th>Posted</th><th>Closes</th><th>Fit</th><th>Ad</th></tr></thead><tbody>'
                     + "".join(row(j, d) for j in rows) + "</tbody></table></div></section>")
    src = day.get("sources_checked")
    if src:
        parts.append(f'<div class="notes"><p>Sources checked: {esc(", ".join(src))}.</p>'
                     '<p>Confirm each role is still open on the employer\'s site before applying.</p></div>')
    parts.append("</div>")
    parts.append(FOOT)
    return "".join(parts)


def index_page(days):
    items = []
    for day in reversed(days):
        d = day["_date"]
        n = len(day["jobs"])
        strong = sum(1 for j in day["jobs"] if j.get("fit") == "Strong")
        items.append(f'<li><a class="d" href="{d.isoformat()}.html">{esc(fmt(d.isoformat()))}</a>'
                     f'<span>{n} new role{"s" if n != 1 else ""}</span>'
                     f'<span class="c">{strong} strong fit</span></li>')
    items.append('<li><a class="d" href="../">18 Nov 2026</a><span>Initial report</span>'
                  '<span class="c">56 roles, on the main page</span></li>')
    return "".join([HEAD.format(title="Job Watch by Date", css=CSS),
                    '<div class="wrap"><header><div class="eyebrow">Daily job watch</div>',
                    '<h1>New roles by date</h1>',
                    '<p class="lede">Each date lists the BA, PM and Product roles first found that morning. Pick a date to see its roles.</p>',
                    '</header><nav class="nav" aria-label="Pages"><a href="../">Main report</a></nav>',
                    f'<ul class="daylist">{"".join(items)}</ul></div>', FOOT])


def main():
    days = load_days()
    OUT.mkdir(exist_ok=True)
    for i, day in enumerate(days):
        prev_day = days[i - 1] if i > 0 else None
        next_day = days[i + 1] if i + 1 < len(days) else None
        (OUT / f"{day['_date'].isoformat()}.html").write_text(day_page(day, prev_day, next_day), encoding="utf-8")
    (OUT / "index.html").write_text(index_page(days), encoding="utf-8")
    print(f"built {len(days)} day page(s) and daily/index.html")
    if days:
        print("latest:", SITE + f"daily/{days[-1]['_date'].isoformat()}.html")


if __name__ == "__main__":
    main()
