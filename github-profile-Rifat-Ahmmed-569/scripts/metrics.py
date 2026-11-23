"""Turn a raw snapshot into the few numbers the profile actually displays.

Every displayed number is derived here, so the rules are auditable in one file.
"""
from __future__ import annotations

import datetime as dt
import re
from collections import OrderedDict

# --- Evidence: what a repo contains that proves real engineering -----------------
# Rules match on file paths from the git tree. Deliberately simple and explainable.
EVIDENCE_RULES: "OrderedDict[str, re.Pattern]" = OrderedDict([
    ("schematic", re.compile(r"(^|/)(hardware|pcb|electronics|schematics?)/|\.(kicad_sch|kicad_pcb|sch|brd|fzz|epro)$", re.I)),
    ("firmware",  re.compile(r"(^|/)(firmware|fw)/|(^|/)(platformio\.ini|sdkconfig|idf_component\.yml)$|\.ino$", re.I)),
    ("mechanical", re.compile(r"(^|/)(cad|mechanical|3d)/|\.(step|stp|stl|f3d|scad|dxf|3mf)$", re.I)),
    ("test data", re.compile(r"(^|/)(tests?|test_data|logs|bench)/|(^|/)test_[^/]+\.py$|_test\.(c|cpp|py)$", re.I)),
    ("demo",      re.compile(r"(^|/)(media|demo|video)/|\.(gif|mp4|mov|webm)$", re.I)),
])
README_RE = re.compile(r"^readme(\.(md|rst|txt))?$", re.I)


def evidence(tree: list[dict], min_readme_bytes: int, extra: dict | None = None) -> dict:
    """Return {'readme': bool, 'items': {name: bool}}."""
    readme = any(README_RE.match(t["path"]) and t.get("size", 0) >= min_readme_bytes for t in tree)
    paths = [t["path"] for t in tree]
    items = {name: any(rx.search(p) for p in paths) for name, rx in EVIDENCE_RULES.items()}
    for k, v in (extra or {}).items():  # e.g. a demo video hosted on YouTube
        if v:
            items[k] = True
    return {"readme": readme, "items": items}


def is_documented(ev: dict, min_items: int) -> bool:
    return ev["readme"] and sum(ev["items"].values()) >= min_items


# --- Robot build stage --------------------------------------------------------
def stage_for(documented: int, stages: list[dict]) -> tuple[int, dict | None]:
    """stages = [{'name':..., 'at': int}, ...] ascending. Returns (index, next_stage)."""
    idx = 0
    for i, s in enumerate(stages):
        if documented >= s["at"]:
            idx = i
    nxt = stages[idx + 1] if idx + 1 < len(stages) else None
    return idx, nxt


# --- Activity ---------------------------------------------------------------
def weekly(days: list[dict]) -> list[dict]:
    days = sorted(days, key=lambda d: d["date"])[-364:]
    out = []
    for i in range(0, len(days), 7):
        chunk = days[i:i + 7]
        out.append({"start": chunk[0]["date"], "count": sum(d["contributionCount"] for d in chunk)})
    return out


def power(days: list[dict], weeks: list[dict]) -> float:
    """Recent momentum vs. this person's own typical week. Decays to 0 when idle.

    0..1 = contributions in the last 28 days / (4 x 75th-percentile week).
    Compared against yourself only, so it can't be read as a ranking.
    """
    recent = sum(d["contributionCount"] for d in sorted(days, key=lambda d: d["date"])[-28:])
    counts = sorted(w["count"] for w in weeks)
    p75 = counts[int(0.75 * (len(counts) - 1))] if counts else 0
    baseline = max(4 * p75, 8)  # floor so a single commit isn't "full power"
    return max(0.0, min(1.0, recent / baseline))


def power_label(p: float) -> str:
    return "ACTIVE" if p >= 0.66 else "WARM" if p >= 0.25 else "LOW" if p > 0 else "IDLE"


def domain_split(commits_by_repo: list[dict], domains: dict[str, list[str]]) -> "OrderedDict[str, int]":
    """Commit contributions per domain. Private repos -> one anonymous 'private' bucket."""
    out: "OrderedDict[str, int]" = OrderedDict((k, 0) for k in domains)
    out["untagged"] = 0
    out["private"] = 0
    for r in commits_by_repo:
        if r["private"]:
            out["private"] += r["commits"]
            continue
        topics = {t.lower() for t in r["topics"]}
        for name, keys in domains.items():
            if topics & {k.lower() for k in keys}:
                out[name] += r["commits"]
                break
        else:
            out["untagged"] += r["commits"]
    return OrderedDict((k, v) for k, v in out.items() if v > 0)


def year(iso: str) -> int:
    return dt.date.fromisoformat(iso[:10]).year
