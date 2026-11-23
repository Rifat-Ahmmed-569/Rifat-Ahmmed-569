# How this profile works

The profile is a **workbench**. A robot sits on it, and documented engineering work is what assembles it. Every number is generated. Everything written by hand lives in `profile.toml`, where it can be reviewed like code.

---

## 1. Where I pushed back on the original concept

| Original idea | Problem | What this design does instead |
|---|---|---|
| Robot matures as you **create repos and contribute** | That rewards volume. It encourages repo spam and daily trivial commits, which is the opposite of "real systems". A recruiter who reads the rule will discount the robot. | The robot's **build stage** comes from *documented builds*: repos with a real README plus at least two pieces of evidence (schematic, firmware, CAD, test data, demo). Activity only drives **power** (LED, sensor pings), and power decays when you're idle. |
| A **contribution chart** | GitHub already draws one directly under your README. A copy adds nothing. | A 52-week **oscilloscope trace** of weekly totals, plus a commit-share bar **by engineering domain** (firmware / robotics / IoT / automation), which GitHub doesn't show. It sits *below* the projects on purpose. |
| Public **and** private repo counts as headline stats | Counts are cheap. 40 private repos says nothing about skill. | They're shown, but as secondary telemetry. The highlighted number is **DOCUMENTED**. |
| Animated character | It can turn into a mascot fast. | Blueprint line art, no face, no "cute". Parts that aren't built yet are drawn as dashed blueprint ghosts, so the robot shows what's *missing* too. |
| Skills section | Icon walls are what make profiles look generic. | A plain-text **stack from silicon up** (hardware → firmware → interfaces → software → bench tools). Text is searchable, and every line can be challenged in an interview. |
| Concise bio | Agreed, and taken further: | No university, no achievements list. Four principles, written as *how you work*, not what you've won. |

One more thing you didn't ask about: **your old work.** Don't backdate commits or pretend old builds are new. Each build shows `built 2023 → documented 2026`. Being honest about a restoration in progress reads as maturity. Fake history reads as a red flag to anyone who checks `git log`.

---

## 2. Visual layout and palette

```
┌──────────────────────────────────────────────────────────────────────┐
│ // bench log · github.com/…            BUILD 2/5 · BRAIN             │  bench-*.svg
│ Rifat Ahmmed                           next → SENSE · 2 more builds  │  840×300
│ Robotics · Embedded · Automation · IoT        ┌─ robot (assembled ─┐ │
│ tagline                                        │ parts + dashed     │ │
│ DOCUMENTED  PUBLIC  PRIVATE  SIGNAL  POWER     │ ghost parts)   ☕  │ │
│    03         09      04      685    100%      └────────────────────┘ │
├──────────────────────────────────────────────────────────────────────┤
│ intro paragraph · How I work (4 principles)                          │  markdown
│ On the bench: 3–5 builds, each with an evidence row                  │  markdown (generated)
│ archive recovery ▰▰▱▱▱▱ 2/8                                          │  markdown (generated)
├──────────────────────────────────────────────────────────────────────┤
│ CH1 weekly trace · domain share bar · "signal ≠ quality"             │  signal-*.svg 840×232
├──────────────────────────────────────────────────────────────────────┤
│ Stack from silicon up · Field notes · Off the bench                  │  markdown
└──────────────────────────────────────────────────────────────────────┘
```

Only two images. Everything a recruiter might search for or copy stays as real text.

| Role | Dark | Light | Used for |
|---|---|---|---|
| Background | `#0A0E13` | `#F4F1EA` | bench (light = drafting paper) |
| Panel | `#0F151C` | `#FBF9F4` | part fills |
| Grid | `#16202A` | `#E9E4D8` | 20 px drafting grid |
| Ink | `#D7DEE7` | `#1D2733` | line art, primary text |
| Dim | `#7D8B9B` | `#5E6B79` | labels |
| Solder amber | `#F5A524` | `#B86E00` | DOCUMENTED, status LED, wiring |
| Scope cyan | `#3DD6C6` | `#0B857B` | signal trace, power, sensor pings |
| PCB green | `#46C28E` | `#2A8457` | the controller board |
| Blueprint | `#5B7FA3` | `#7F9AB8` | ghost (unbuilt) parts |

Type: the system UI sans for the name, the system monospace for all readouts. No web fonts, because GitHub would block them anyway (see §7).

---

## 3. Architecture

```
profile.toml ──┐  (human-owned: identity, featured builds, notes, thresholds)
               ▼
GitHub GraphQL + REST ──► github_data.py ──► snapshot (dict, private repos already anonymised)
                                               │
                                               ▼
                                         metrics.py   (evidence, documented, stage, power, domains)
                                               │
                              ┌────────────────┴────────────────┐
                              ▼                                 ▼
                       render.py → assets/*.svg      generate.py → README.md marker blocks
                              └──────────── commit only if content changed ───────────┘
```

**Robot build stages** (thresholds live in `profile.toml`):

| Stage | Unlocks at | Adds |
|---|---|---|
| 0 FRAME | 0 documented | chassis on bench stands |
| 1 DRIVE | 1 | wheels + motor housings |
| 2 BRAIN | 3 | controller PCB, status LED, wiring |
| 3 SENSE | 5 | sensor mast, ultrasonic head, lidar puck |
| 4 REACH | 8 | 2-link arm + gripper, a part on the bench |
| 5 LINK | 12 | antenna + radio |

Stages are **monotonic in practice** (documented repos rarely disappear). If you delete or exclude a repo the robot can lose a part, and that's intentional: it stays honest.

**Power**, the only activity-driven element:
`power = contributions in the last 28 days ÷ max(4 × your 75th-percentile week, 8)`, clamped to 0–1.
It's measured against *your own* typical week, so it can't be read as a ranking against other people. At 0 the LED goes dark and the pings stop (`IDLE`). Nothing breaks, and the robot doesn't look sad. Idle is normal on a workbench.

**Evidence detection** (`metrics.py`, path regexes over the repo's git tree):

| Lamp | Matches |
|---|---|
| schematic | `hardware/`, `pcb/`, `*.kicad_sch`, `*.kicad_pcb`, `*.sch`, `*.brd`, `*.fzz`, `*.epro` |
| firmware | `firmware/`, `platformio.ini`, `sdkconfig`, `idf_component.yml`, `*.ino` |
| mechanical | `cad/`, `mechanical/`, `*.step`, `*.stl`, `*.f3d`, `*.scad`, `*.dxf`, `*.3mf` |
| test data | `tests/`, `logs/`, `bench/`, `test_*.py`, `*_test.c` |
| demo | `media/`, `demo/`, `*.gif`, `*.mp4`, or a `demo_url` in `profile.toml` |

"Documented" means a README of at least 1200 bytes plus at least 2 lamps. Both thresholds are configurable. The rule is deliberately crude and fully explainable. Anyone can open the repo and check it.

---

## 4. GitHub API data points

| Data | Source | Shown as |
|---|---|---|
| `user.login`, `user.createdAt` | GraphQL | handle, "on GitHub since" |
| `user.repositories(privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false).totalCount` | GraphQL | PUBLIC REPOS |
| `viewer.repositories(privacy: PRIVATE, ownerAffiliations: OWNER, isFork: false).totalCount` | GraphQL, owner's token | PRIVATE REPOS (integer only) |
| public repo `name, url, description, createdAt, pushedAt, isArchived, defaultBranchRef, primaryLanguage, repositoryTopics` | GraphQL | project links, build dates, domains |
| `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1` (public repos only) | REST | evidence lamps, README size, DOCUMENTED |
| `contributionsCollection.contributionCalendar.weeks.contributionDays{date, contributionCount}` | GraphQL | weekly trace, POWER |
| `contributionCalendar.totalContributions` | GraphQL | SIGNAL · 365D |
| `contributionsCollection.commitContributionsByRepository{repository{isPrivate, repositoryTopics}, contributions.totalCount}` | GraphQL | domain share bar (private → one anonymous bucket) |
| `restrictedContributionsCount` | GraphQL | fetched for completeness, not displayed |

Cost: 2 GraphQL queries + 1 REST call per public repo. That's well under 100 requests a day against a 5,000/hour limit. `contributionsCollection` covers at most one year, which matches the 52-week window.

---

## 5. GitHub Actions strategy

- **Triggers:** daily at 03:23 Dhaka time, the manual *Run workflow* button, and any push that changes `profile.toml` or the scripts. Editing your featured builds re-renders immediately.
- **Zero dependencies:** Python 3.12 stdlib only (`tomllib`, `urllib`, `json`), with no `pip install` step. That means a smaller supply-chain surface and less to break.
- **Commits only real changes:** the generator ignores the "synced <date>" line when deciding whether to write a file. A quiet day produces no commit.
- **Bot identity:** commits are authored by `github-actions[bot]`, so they **never count toward your contribution graph**. The profile can't inflate the numbers it reports.
- **Failure mode:** if the token expires or the API fails, the job fails loudly (GitHub emails you) and the last good SVGs stay in place with their old sync date. No partial or guessed numbers get written.
- **Least privilege:** `permissions: contents: write` for the built-in token, which can only write to this repo. No `pull_request_target` trigger, so secrets are never exposed to fork PRs.
- **Hardening to do after setup:** pin `actions/checkout` and `actions/setup-python` to full commit SHAs.
- **Known GitHub behaviour:** a scheduled workflow in a public repo is auto-disabled after 60 days without repository activity. If you go quiet for two months, re-enable it from the Actions tab (or push anything).
- **Alternative if history noise bothers you:** write the SVGs to an orphan `output` branch and reference them by raw URL. I didn't default to this, because raw URLs are proxied and cached by GitHub's image proxy (camo), which delays updates. Relative paths on `main` update with the commit.

---

## 6. Private repository counts, safely

**Why a token is needed:** the built-in `GITHUB_TOKEN` in Actions is scoped to the one repo running the workflow. It can't see your other private repos.

**Create a fine-grained personal access token** (Settings → Developer settings → Fine-grained tokens):

- **Resource owner:** you
- **Repository access:** All repositories (needed for the private *count*)
- **Permissions:** Repository → **Metadata: Read-only**. Nothing else to start with. If the "private" share of the domain bar stays at 0 while you do have private commits, add **Contents: Read-only**. Still no write access anywhere.
- **Expiration:** 1 year, with a calendar reminder.
- Save it as the repo secret **`PROFILE_STATS_TOKEN`**.

Do **not** use a classic token with the `repo` scope. It grants full *write* access to every repository you own, which is far more than a stats job needs.

**Guarantees built into the code, not just the docs:**

1. `github_data.py` anonymises private entries at fetch time. Names and topics of private repos are dropped before anything else sees the data. The test in the build fed a fake private repo named `TOPSECRET` through `fetch()` and asserted it wasn't in the snapshot.
2. The private count is used only if `viewer.login` equals the profile login. A wrong token renders `—`, never someone else's number.
3. Private repos never get tree-scanned, so no private file paths are ever read.
4. Logs print aggregates only (`stage=2 documented=3 …`). HTTP errors print status code and endpoint, never response bodies.
5. The SVGs and README are public, so they're the only output. Anything that isn't an integer or a percentage never reaches them.

**What you still disclose:** that you *have* N private repos and roughly what share of your commits went into them. That's the trade-off you asked for. If you change your mind, set `show_private_count = false` in `profile.toml` and it renders `—`. Do the same if you give the token public-repo access only, or it would show a misleading `00`.

**Contribution totals:** the calendar from your own token can include private contributions. Turn on *Settings → Public profile → Include private contributions on my profile* so the README trace and GitHub's own graph agree. Otherwise visitors will notice the mismatch.

---

## 7. What GitHub READMEs can and can't do

| Works | Doesn't |
|---|---|
| SVG via `<img>`, including `<style>`, CSS `@keyframes` and `@media (prefers-reduced-motion)` | JavaScript, `<foreignObject>`, external fonts or images *inside* the SVG |
| `<picture>` + `prefers-color-scheme` for dark/light variants | `<style>` or `class` in the Markdown itself. GitHub strips them. |
| `<sub>`, `<details>`, `<br>`, `<code>`, `align`, tables | Multi-column layouts (except table hacks), custom colours in text |
| Relative image paths in the profile repo | Clickable links *inside* an SVG image: the whole image is one link at most |

**Practical consequences:**

- **Text inside SVG is invisible to search and screen readers.** Each SVG carries a `<title>`/`<desc>`, and the `alt` text is regenerated with the real numbers. All prose is Markdown.
- **Mobile:** an 840 px SVG is scaled to roughly 360 px, so 9–10 px labels become hard to read. The big readouts (25 px) survive. That's why nothing essential lives *only* in small SVG text.
- **The GitHub mobile app** may not play SVG animations. Every animated element has a sensible static state: trace visible, pings at low opacity.
- **Fonts** come from the viewer's OS, so the exact look differs slightly between macOS, Windows and Linux.

---

## 8. Activity vs. engineering quality

The design keeps these apart on purpose:

- **Activity** (trace, SIGNAL, POWER) shows *presence and momentum*. It's labelled "signal ≠ quality" in the chart itself, with a plain-language note under it.
- **Engineering quality** can't be measured by the API, so the profile shows **evidence** instead: per-build lamps for schematic, firmware, mechanical, test data and demo. These are things a reviewer can open and judge.
- The **robot**, the most visual element, is tied to evidence, not activity. The headline metric is DOCUMENTED, not commits.

---

## 9. Three ideas that make it memorable without being gimmicky

1. **Evidence lamps on every build.** `■ schematic ■ firmware □ mechanical ■ test data □ demo`, computed from the actual repo tree. It's honest and inspectable, and it nudges you to finish documenting. A recruiter learns more from this row than from any stats card.
2. **A robot assembled from documentation, powered by activity.** Two separate meanings, which is what keeps it from being a gimmick: *structure* only grows with documented builds, and *power* only reflects recent momentum and decays. The dashed blueprint ghosts show the target build, so the profile is visibly a work in progress.
3. **The archive recovery log and field notes.** `archive recovery ▰▰▱▱▱▱▱▱▱▱ 2 / 8` plus `built 2023 → documented 2026` on each build tells the true story: years of building, and now the record is catching up. Field notes (*On the bench* / *Last thing that broke*) are short, dated and human. Robotics teams hire people who can explain a failure. Two lines of symptom → root cause → fix says more than a skills list.

---

## 10. Setup checklist

1. Create a public repo named exactly **`Rifat-Ahmmed-569`**, then copy these files into it.
2. Edit `profile.toml`: confirm your name, set `legacy_total`, and add 3–5 `[[featured]]` builds and 1–2 `[[notes]]`.
3. Replace the `‹placeholders›` in `README.md` (stack, contact). The generator warns while any remain.
4. Add topics to your repos (`esp32`, `robotics`, `iot` …) so the domain bar isn't mostly "untagged".
5. Create the fine-grained token (§6) → secret `PROFILE_STATS_TOKEN`.
6. Actions tab → *regenerate profile* → **Run workflow**.
7. Preview locally anytime: `python scripts/generate.py --demo` writes stamped sample SVGs to `preview/`.
