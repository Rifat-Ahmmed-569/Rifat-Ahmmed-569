"""Fetch the minimum GitHub data the profile needs.

Privacy contract (enforced here, not just documented):
  * Private repositories contribute ONLY integers to the output:
    a repo count and a share of commit contributions.
  * No private repo name, topic, language or file path ever leaves this module.
  * Nothing returned by the API is printed to the log.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import urllib.error
import urllib.request

API = "https://api.github.com"
UA = "profile-bench-generator"

GRAPHQL_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  viewer { login }
  user(login: $login) {
    login
    createdAt
    publicRepos: repositories(privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false) { totalCount }
    repos: repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false,
                        orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name url description createdAt pushedAt isArchived
        defaultBranchRef { name }
        primaryLanguage { name }
        repositoryTopics(first: 20) { nodes { topic { name } } }
      }
    }
    contributionsCollection(from: $from, to: $to) {
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
      commitContributionsByRepository(maxRepositories: 100) {
        repository { isPrivate name repositoryTopics(first: 20) { nodes { topic { name } } } }
        contributions { totalCount }
      }
    }
  }
}
"""

PRIVATE_COUNT_QUERY = """
query { viewer { login privateRepos: repositories(privacy: PRIVATE, ownerAffiliations: OWNER, isFork: false) { totalCount } } }
"""


class GitHub:
    def __init__(self, token: str):
        self.token = token

    def _req(self, url: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method="POST" if data else "GET")
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("User-Agent", UA)
        req.add_header("Accept", "application/vnd.github+json")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            # Status only. Response bodies can echo repo names; never log them.
            raise RuntimeError(f"GitHub API {e.code} on {url.split('?')[0]}") from None

    def graphql(self, query: str, variables: dict | None = None) -> dict:
        out = self._req(f"{API}/graphql", {"query": query, "variables": variables or {}})
        if out.get("errors"):
            kinds = sorted({err.get("type", "ERROR") for err in out["errors"]})
            raise RuntimeError(f"GraphQL error(s): {', '.join(kinds)}")
        return out["data"]

    def tree(self, owner: str, repo: str, ref: str) -> list[dict]:
        out = self._req(f"{API}/repos/{owner}/{repo}/git/trees/{ref}?recursive=1")
        return [{"path": t["path"], "type": t["type"], "size": t.get("size", 0)} for t in out.get("tree", [])]


def topics_of(node: dict) -> list[str]:
    return [n["topic"]["name"] for n in (node.get("repositoryTopics") or {}).get("nodes", [])]


def fetch(login: str, token: str, private_token: str | None = None) -> dict:
    """Return a plain dict snapshot. Shape matches demo_snapshot()."""
    gh = GitHub(token)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    frm = now - dt.timedelta(days=364)
    d = gh.graphql(GRAPHQL_QUERY, {"login": login, "from": frm.isoformat(), "to": now.isoformat()})
    user = d["user"]
    cc = user["contributionsCollection"]

    days = [day for w in cc["contributionCalendar"]["weeks"] for day in w["contributionDays"]]

    # Commit share by domain. Private repos are collapsed to one anonymous bucket here.
    by_repo = []
    for item in cc["commitContributionsByRepository"]:
        repo = item["repository"]
        n = item["contributions"]["totalCount"]
        if repo["isPrivate"]:
            by_repo.append({"private": True, "topics": [], "commits": n})
        else:
            by_repo.append({"private": False, "topics": topics_of(repo), "commits": n})

    # Private repo count: only when the token belongs to the profile owner.
    private_count = None
    pt = private_token or token
    try:
        v = GitHub(pt).graphql(PRIVATE_COUNT_QUERY)["viewer"]
        if v["login"].lower() == login.lower():
            private_count = v["privateRepos"]["totalCount"]
    except RuntimeError:
        private_count = None  # rendered as "—", never guessed

    repos = []
    for r in user["repos"]["nodes"]:
        tree = []
        if r["defaultBranchRef"]:
            try:
                tree = gh.tree(login, r["name"], r["defaultBranchRef"]["name"])
            except RuntimeError:
                tree = []
        repos.append({
            "name": r["name"], "url": r["url"], "description": r["description"] or "",
            "created": r["createdAt"][:10], "pushed": (r["pushedAt"] or r["createdAt"])[:10],
            "archived": r["isArchived"],
            "language": (r["primaryLanguage"] or {}).get("name"),
            "topics": topics_of(r), "tree": tree,
        })

    return {
        "login": user["login"],
        "joined": user["createdAt"][:10],
        "generated": now.date().isoformat(),
        "public_repos": user["publicRepos"]["totalCount"],
        "private_repos": private_count,
        "days": days,
        "total_contributions": cc["contributionCalendar"]["totalContributions"],
        "restricted_contributions": cc["restrictedContributionsCount"],
        "commits_by_repo": by_repo,
        "repos": repos,
    }


def from_env(login: str) -> dict:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN not set")
    return fetch(login, token, os.environ.get("PRIVATE_COUNT_TOKEN"))
