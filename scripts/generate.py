#!/usr/bin/env python3
"""Regenerate the profile: SVGs in assets/ and the generated blocks in README.md.

  python scripts/generate.py                 # live (needs GH_TOKEN)
  python scripts/generate.py --demo          # sample data, stamped "SAMPLE DATA", writes to preview/
  python scripts/generate.py --snapshot f.json
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import tomllib
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import metrics as M  # noqa: E402
import render as R  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


# ----------------------------------------------------------------------------- metrics
def build_metrics(cfg: dict, snap: dict) -> dict:
    rules = cfg["documented"]
    featured = {f["repo"]: f for f in cfg.get("featured", [])}
    excluded = set(cfg.get("exclude", []))

    repos = {}
    for r in snap["repos"]:
        if r["name"] in excluded or r["name"].lower() == snap["login"].lower():
            continue
        extra = {"demo": bool(featured.get(r["name"], {}).get("demo_url"))}
        ev = M.evidence(r["tree"], rules["min_readme_bytes"], extra)
        r = {**r, "evidence": ev, "documented": M.is_documented(ev, rules["min_evidence"])}
        repos[r["name"]] = r

    documented = sum(1 for r in repos.values() if r["documented"])
    stages = cfg["robot"]["stages"]
    stage, nxt = M.stage_for(documented, stages)
    weeks = M.weekly(snap["days"])
    pwr = M.power(snap["days"], weeks)
    return {
        "name": cfg["identity"]["name"], "role": cfg["identity"]["role"],
        "tagline": cfg["identity"]["tagline"],
        "login": snap["login"], "joined": snap["joined"], "generated": snap["generated"],
        "public_repos": snap["public_repos"],
        "private_repos": snap["private_repos"] if cfg.get("privacy", {}).get("show_private_count", True) else None,
        "total": snap["total_contributions"], "weeks": weeks,
        "power": pwr, "power_label": M.power_label(pwr),
        "documented": documented, "stages": stages, "stage": stage, "next_stage": nxt,
        "domains": M.domain_split(snap["commits_by_repo"], cfg.get("domains", {})),
        "repos": repos,
    }


# ----------------------------------------------------------------------------- README blocks
def picture(name: str, alt: str, base: str) -> str:
    return (f'<picture>\n  <source media="(prefers-color-scheme: light)" srcset="{base}/{name}-light.svg">\n'
            f'  <img src="{base}/{name}-dark.svg" width="100%" alt="{alt}">\n</picture>')


def block_projects(cfg: dict, m: dict) -> str:
    out = []
    for f in cfg.get("featured", []):
        r = m["repos"].get(f["repo"])
        title = f.get("title") or f["repo"]
        summary = f.get("summary") or (r or {}).get("description") or ""
        if r is None and not f.get("private"):
            out.append(f"<!-- skipped '{f['repo']}': not found as a public repo -->")
            continue
        head = f"#### [{title}]({r['url']})" if r else f"#### {title} <sub>· source private</sub>"
        meta = []
        if f.get("stack"):
            meta.append(" · ".join(f["stack"]))
        built = f.get("built")
        documented = f.get("documented") or (M.year(r["created"]) if r else None)
        if built and documented and built != documented:
            meta.append(f"built {built} → documented {documented}")
        elif built or documented:
            meta.append(f"built {built or documented}")
        if f.get("role"):
            meta.append(f["role"])
        lines = [head, summary, f"<sub>{' &nbsp;·&nbsp; '.join(meta)}</sub>" if meta else ""]
        if r:
            ev = r["evidence"]["items"]
            lamps = " &nbsp; ".join(f"{'■' if ok else '□'} {name}" for name, ok in ev.items())
            demo = f" &nbsp;·&nbsp; [demo]({f['demo_url']})" if f.get("demo_url") else ""
            lines.append(f"<br><sub><code>evidence</code> &nbsp;{lamps}{demo}</sub>")
        out.append("\n".join(l for l in lines if l))
    if not out:
        return "_The bench is being restocked. First documented builds land here._"
    return "\n\n".join(out)


def block_archive(cfg: dict, m: dict) -> str:
    a = cfg.get("archive", {})
    total = a.get("legacy_total", 0)
    if not total:
        return ""
    since = a.get("documenting_since", 2026)
    restored = 0
    for f in cfg.get("featured", []):
        r = m["repos"].get(f["repo"])
        if r and r["documented"] and f.get("built") and f["built"] < since:
            restored += 1
    restored = min(restored, total)
    bar = "▰" * round(10 * restored / total) + "▱" * (10 - round(10 * restored / total))
    return (f"<sub><code>archive recovery</code> &nbsp;{bar}&nbsp; {restored} / {total} builds from before "
            f"{since} documented. Each one keeps its real build year.</sub>")


def block_notes(cfg: dict) -> str:
    notes = sorted(cfg.get("notes", []), key=lambda n: n["date"], reverse=True)[:3]
    if not notes:
        return ""
    rows = []
    for n in notes:
        when = dt.date.fromisoformat(n["date"]).strftime("%b %Y")
        rows.append(f"> **{n['kind']}** · <sub>{when}</sub><br>\n> {n['text']}")
    return "\n>\n".join(rows)


def replace_block(text: str, key: str, body: str) -> str:
    pat = re.compile(rf"(<!-- {key}:START -->)(.*?)(<!-- {key}:END -->)", re.S)
    if not pat.search(text):
        print(f"warn: README has no {key} markers", file=sys.stderr)
        return text
    return pat.sub(lambda mo: f"{mo.group(1)}\n{body}\n{mo.group(3)}", text)


# ----------------------------------------------------------------------------- writing
SYNC_RE = re.compile(r'<text[^>]*data-sync="1"[^>]*>.*?</text>')


def write_if_changed(path: Path, content: str) -> bool:
    """Ignore the 'synced <date>' line so the bot doesn't commit daily for nothing."""
    if path.exists() and SYNC_RE.sub("", path.read_text()) == SYNC_RE.sub("", content):
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return True


def stamp(svg: str) -> str:
    return svg.replace("</svg>", '<text x="800" y="22" text-anchor="end" font-family="monospace" '
                       'font-size="10" fill="#EF5B5B">PREVIEW · SAMPLE DATA</text>\n</svg>')


# ----------------------------------------------------------------------------- demo data
def demo_snapshot(cfg: dict, seed: int = 7, documented_target: int = 3) -> dict:
    rnd = random.Random(seed)
    today = dt.date(2026, 11, 24)
    days = []
    for i in range(364, -1, -1):
        d = today - dt.timedelta(days=i)
        base = 0.25 + 0.6 * (i < 120) + 0.3 * (150 < i < 200)
        c = 0 if rnd.random() > base else rnd.choice([1, 1, 2, 3, 4, 6, 9])
        days.append({"date": d.isoformat(), "contributionCount": c})
    good_tree = [{"path": "README.md", "type": "blob", "size": 4000},
                 {"path": "hardware/main.kicad_sch", "type": "blob", "size": 1},
                 {"path": "firmware/platformio.ini", "type": "blob", "size": 1},
                 {"path": "media/demo.gif", "type": "blob", "size": 1}]
    thin_tree = [{"path": "README.md", "type": "blob", "size": 300}, {"path": "main.ino", "type": "blob", "size": 1}]
    repos = []
    for i in range(9):
        repos.append({"name": f"sample-build-{i+1}", "url": f"https://github.com/{cfg['login']}/sample-build-{i+1}",
                      "description": "Sample repository (preview only).", "created": "2026-03-01",
                      "pushed": "2026-11-01", "archived": False, "language": "C++", "topics": [],
                      "tree": good_tree if i < documented_target else thin_tree})
    return {"login": cfg["login"], "joined": "2022-05-10", "generated": today.isoformat(),
            "public_repos": 9, "private_repos": 4, "days": days,
            "total_contributions": sum(d["contributionCount"] for d in days), "restricted_contributions": 0,
            "commits_by_repo": [{"private": False, "topics": ["firmware"], "commits": 140},
                                {"private": False, "topics": ["robotics"], "commits": 95},
                                {"private": False, "topics": ["iot"], "commits": 60},
                                {"private": False, "topics": [], "commits": 25},
                                {"private": True, "topics": [], "commits": 70}],
            "repos": repos}


# ----------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--demo-documented", type=int, default=3)
    ap.add_argument("--snapshot")
    ap.add_argument("--out", default=None, help="output dir for SVGs (default assets/, demo: preview/)")
    a = ap.parse_args()

    cfg = tomllib.loads((ROOT / "profile.toml").read_text())
    if a.demo:
        snap = demo_snapshot(cfg, documented_target=a.demo_documented)
    elif a.snapshot:
        snap = json.loads(Path(a.snapshot).read_text())
    else:
        import github_data
        snap = github_data.from_env(cfg["login"])

    m = build_metrics(cfg, snap)
    out = ROOT / (a.out or ("preview" if a.demo else "assets"))
    changed = []
    for theme in ("dark", "light"):
        for name, fn in (("bench", R.header_svg), ("signal", R.signal_svg)):
            svg = fn(m, theme)
            if a.demo:
                svg = stamp(svg)
            if write_if_changed(out / f"{name}-{theme}.svg", svg):
                changed.append(f"{name}-{theme}.svg")

    if not a.demo:
        readme = ROOT / "README.md"
        text = readme.read_text()
        priv = "—" if m["private_repos"] is None else m["private_repos"]
        bench_alt = (f"{m['name']}: robot at build stage {m['stage']} ({m['stages'][m['stage']]['name']}); "
                     f"{m['documented']} documented builds, {m['public_repos']} public / {priv} private repos, "
                     f"{m['total']} contributions in 365 days")
        text = replace_block(text, "BENCH", picture("bench", bench_alt, "assets"))
        text = replace_block(text, "SIGNAL", picture("signal", "Weekly contribution signal and commit share by domain, last 52 weeks", "assets"))
        text = replace_block(text, "PROJECTS", block_projects(cfg, m))
        text = replace_block(text, "ARCHIVE", block_archive(cfg, m))
        text = replace_block(text, "NOTES", block_notes(cfg))
        if text != readme.read_text():
            readme.write_text(text)
            changed.append("README.md")
        if "‹" in text:
            print("warn: README still contains ‹placeholders›", file=sys.stderr)

    # Log aggregates only, never repo names.
    print(f"stage={m['stage']} documented={m['documented']} power={m['power']:.2f} changed={len(changed)}")


if __name__ == "__main__":
    main()
