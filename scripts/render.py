"""SVG renderers: the bench header (robot + telemetry) and the signal panel.

Constraints honoured (GitHub serves README images through <img>/camo):
  * no JavaScript, no external fonts/images, no foreignObject
  * CSS + @keyframes inside <style> are fine; reduced-motion is respected
  * system font stacks only, so rendering depends on the viewer's OS
"""
from __future__ import annotations

import datetime as dt
import math
from xml.sax.saxutils import escape

PALETTES = {
    "dark": dict(bg="#0A0E13", panel="#0F151C", grid="#16202A", line="#263241", ink="#D7DEE7",
                 dim="#7D8B9B", faint="#3A4757", amber="#F5A524", cyan="#3DD6C6", green="#46C28E",
                 violet="#9D8CF2", ghost="#5B7FA3"),
    "light": dict(bg="#F4F1EA", panel="#FBF9F4", grid="#E9E4D8", line="#D3CBBA", ink="#1D2733",
                  dim="#5E6B79", faint="#BDB5A5", amber="#B86E00", cyan="#0B857B", green="#2A8457",
                  violet="#5B49C9", ghost="#7F9AB8"),
}
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
W = 840


def _frame(h: int, P: dict) -> str:
    c = []
    c.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{h-1}" rx="12" fill="{P["bg"]}" stroke="{P["line"]}"/>')
    c.append(f'<rect x="1" y="1" width="{W-2}" height="{h-2}" rx="12" fill="url(#grid)"/>')
    # crop marks: drafting-sheet corners
    for x, y, dx, dy in [(14, 14, 1, 1), (W - 14, 14, -1, 1), (14, h - 14, 1, -1), (W - 14, h - 14, -1, -1)]:
        c.append(f'<path d="M{x} {y+10*dy} V{y} H{x+10*dx}" fill="none" stroke="{P["faint"]}" stroke-width="1"/>')
    return "\n".join(c)


def _defs(P: dict) -> str:
    return (f'<defs><pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">'
            f'<path d="M20 0H0V20" fill="none" stroke="{P["grid"]}" stroke-width="1"/></pattern>'
            f'<pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="5" height="5" fill="{P["line"]}"/><path d="M0 0V5" stroke="{P["dim"]}" stroke-width="2"/></pattern></defs>')


# ----------------------------------------------------------------------------- robot
# Each part is drawn in one coordinate system (bench surface at y=258).
def _p_frame():
    return """
<rect class="s" x="655" y="236" width="14" height="22"/><rect class="s" x="702" y="236" width="14" height="22"/>
<rect class="b" x="610" y="206" width="150" height="30" rx="5"/>
<circle class="s" cx="620" cy="221" r="2.5"/><circle class="s" cx="750" cy="221" r="2.5"/>
<path class="s" d="M672 213v16M678 213v16M684 213v16"/>"""


def _p_drive():
    out = []
    for cx in (635, 735):
        out.append(f'<circle class="b" cx="{cx}" cy="240" r="17"/><circle class="b" cx="{cx}" cy="240" r="12"/>'
                   f'<circle class="s" cx="{cx}" cy="240" r="4"/>'
                   f'<path class="s" d="M{cx} 228v8M{cx-10.4} 246l6.9-4M{cx+10.4} 246l-6.9-4"/>')
    out.append('<rect class="b" x="652" y="225" width="20" height="9" rx="1.5"/><rect class="b" x="698" y="225" width="20" height="9" rx="1.5"/>')
    return "\n".join(out)


def _p_brain():
    pins = "".join(f"M{x} 190v-4" for x in range(644, 660, 3))
    return f"""
<rect class="pcb" x="640" y="190" width="70" height="16" rx="2"/>
<rect class="b" x="662" y="193" width="14" height="10" rx="1"/>
<path class="s" d="{pins}"/>
<path class="w" d="M710 199C730 199 742 199 750 206"/>
<circle class="led" cx="700" cy="198" r="3"/>"""


def _p_sense():
    # ultrasonic pings: arcs to the right of the sensor head
    arcs = []
    for i, r in enumerate((14, 21, 28)):
        a = math.radians(32)
        x1, y1 = 744 + r * math.cos(-a), 143 + r * math.sin(-a)
        x2, y2 = 744 + r * math.cos(a), 143 + r * math.sin(a)
        arcs.append(f'<path class="ping p{i}" d="M{x1:.1f} {y1:.1f}A{r} {r} 0 0 1 {x2:.1f} {y2:.1f}"/>')
    return f"""
<path class="s" d="M733 206V152M737 206V152"/>
<rect class="b" x="716" y="134" width="40" height="18" rx="4"/>
<circle class="b" cx="728" cy="143" r="5.5"/><circle class="b" cx="744" cy="143" r="5.5"/>
<circle class="s" cx="728" cy="143" r="2"/><circle class="s" cx="744" cy="143" r="2"/>
<rect class="b" x="727" y="126" width="18" height="8" rx="2"/>
{''.join(arcs)}"""


def _p_reach():
    return """
<g class="arm">
<rect class="b" x="616" y="198" width="18" height="8" rx="1.5"/>
<path class="link" d="M625 196L590 165L568 198"/><path class="linki" d="M625 196L590 165L568 198"/>
<circle class="b" cx="625" cy="196" r="5"/><circle class="b" cx="590" cy="165" r="4.5"/>
<rect class="b" x="562" y="197" width="12" height="6" rx="1"/>
<path class="s" d="M564 203l-3 10M572 203l3 10"/>
</g>
<rect class="b" x="560" y="251" width="16" height="7" rx="1"/><path class="s" d="M563 251v-2M567 251v-2M571 251v-2M563 258v2M567 258v2M571 258v2"/>"""


def _p_link():
    return """
<path class="s" d="M690 190V120"/><circle class="b" cx="690" cy="117" r="3"/>
<path class="wave q0" d="M682 109a12 12 0 0 1 16 0"/><path class="wave q1" d="M677 103a19 19 0 0 1 26 0"/>"""


PARTS = [_p_frame, _p_drive, _p_brain, _p_sense, _p_reach, _p_link]
# draw order differs from unlock order so occlusion looks right (wheels behind chassis)
DRAW_ORDER = [1, 0, 4, 2, 3, 5]


def robot(stage: int, pwr: float, P: dict) -> str:
    live, ghost = [], []
    for i in DRAW_ORDER:
        svg = PARTS[i]()
        if i <= stage:
            live.append(svg)
        else:
            cls = "ghost next" if i == stage + 1 else "ghost"
            ghost.append(f'<g class="{cls}">{svg}</g>')
    return "\n".join(ghost + live)


def _robot_css(P: dict, pwr: float) -> str:
    led_dur = 2.6 - 1.6 * pwr
    anim = pwr > 0
    return f"""
.s{{fill:none;stroke:{P['ink']};stroke-width:1.4;stroke-linecap:round}}
.b{{fill:{P['panel']};stroke:{P['ink']};stroke-width:1.4}}
.pcb{{fill:{P['panel']};stroke:{P['green']};stroke-width:1.6}}
.w{{fill:none;stroke:{P['amber']};stroke-width:1.2;opacity:.8}}
.link{{fill:none;stroke:{P['ink']};stroke-width:7;stroke-linecap:round;stroke-linejoin:round}}
.linki{{fill:none;stroke:{P['panel']};stroke-width:4;stroke-linecap:round;stroke-linejoin:round}}
.led{{fill:{P['amber'] if anim else P['faint']};{'animation:led ' + f'{led_dur:.2f}' + 's ease-in-out infinite' if anim else ''}}}
.ping,.wave{{fill:none;stroke:{P['cyan']};stroke-width:1.3;opacity:{.35 if anim else .2}}}
{'.ping{animation:ping 2.4s linear infinite}.p1{animation-delay:.4s}.p2{animation-delay:.8s}' if anim else ''}
{'.wave{animation:ping 3s linear infinite}.q1{animation-delay:.5s}' if anim else ''}
.arm{{transform-origin:625px 196px;{'animation:arm 7s ease-in-out infinite' if anim else ''}}}
.ghost *{{fill:none!important;stroke:{P['ghost']}!important;stroke-dasharray:3 3;stroke-width:1.1!important;animation:none!important;opacity:1}}
.ghost{{opacity:.28}} .ghost.next{{opacity:.75}}
.steam{{fill:none;stroke:{P['dim']};stroke-width:1.2;stroke-linecap:round;opacity:.5;animation:steam 4s ease-in-out infinite}}
.st2{{animation-delay:2s}}
@keyframes led{{0%,100%{{opacity:.35}}50%{{opacity:1}}}}
@keyframes ping{{0%{{opacity:0}}15%{{opacity:.9}}60%,100%{{opacity:0}}}}
@keyframes arm{{0%,100%{{transform:rotate(0deg)}}50%{{transform:rotate(-3deg)}}}}
@keyframes steam{{0%{{opacity:0;transform:translateY(4px)}}40%{{opacity:.55}}100%{{opacity:0;transform:translateY(-8px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.ping,.wave{{opacity:.5}}}}"""


def _mug(P: dict) -> str:
    return f"""
<path class="steam" d="M790 228c-3-4 3-7 0-11s3-7 0-10"/><path class="steam st2" d="M798 228c-3-4 3-7 0-11s3-7 0-10"/>
<path class="b" d="M784 234h22v20a4 4 0 0 1-4 4h-14a4 4 0 0 1-4-4z"/>
<path class="s" d="M806 239h3a5 5 0 0 1 0 10h-3"/>"""


def header_svg(m: dict, theme: str) -> str:
    P = PALETTES[theme]
    H = 300
    stages, si, nxt = m["stages"], m["stage"], m["next_stage"]
    pv = m["power"]
    priv = "—" if m["private_repos"] is None else f"{m['private_repos']:02d}"
    cells = [
        ("DOCUMENTED", f"{m['documented']:02d}", P["amber"]),
        ("PUBLIC REPOS", f"{m['public_repos']:02d}", P["ink"]),
        ("PRIVATE REPOS", priv, P["ink"]),
        ("SIGNAL · 365D", f"{m['total']}", P["ink"]),
        ("POWER", f"{round(pv*100)}%", P["cyan"]),
    ]
    tel = []
    for i, (label, val, col) in enumerate(cells):
        x = 40 + i * 94
        tel.append(f'<text x="{x}" y="200" font-family="{MONO}" font-size="9.5" letter-spacing="1" fill="{P["dim"]}">{label}</text>')
        tel.append(f'<text x="{x}" y="232" font-family="{MONO}" font-size="25" font-weight="600" fill="{col}">{escape(val)}</text>')
        tel.append(f'<path d="M{x} 244h82" stroke="{P["line"]}" stroke-width="2"/>')
    # power gauge on the last cell
    px = 40 + 4 * 94
    tel.append(f'<path d="M{px} 244h{82*pv:.1f}" stroke="{P["cyan"]}" stroke-width="2"/>')
    tel.append(f'<text x="{px}" y="258" font-family="{MONO}" font-size="9" fill="{P["dim"]}">{m["power_label"]}</text>')

    stage_line = f"BUILD {si}/{len(stages)-1} · {stages[si]['name']}"
    if nxt:
        need = nxt["at"] - m["documented"]
        next_line = f"next → {nxt['name']} · {need} more documented build{'s' if need != 1 else ''}"
    else:
        next_line = "all stages assembled"

    ruler = "".join(f"M{x} 258v{6 if x % 50 == 0 else 3}" for x in range(520, 821, 10))
    title = f"{m['name']} — robotics, embedded systems, automation"
    desc = (f"Workshop bench. Robot at build stage {si} of {len(stages)-1} ({stages[si]['name']}). "
            f"{m['documented']} documented builds, {m['public_repos']} public repositories, "
            f"{priv} private repositories, {m['total']} contributions in the last 365 days, "
            f"power {round(pv*100)} percent ({m['power_label']}).")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">{escape(title)}</title><desc id="d">{escape(desc)}</desc>
<style>{_robot_css(P, pv)}</style>
{_defs(P)}
{_frame(H, P)}
<text x="40" y="46" font-family="{MONO}" font-size="11" fill="{P['dim']}">// bench log · github.com/{escape(m['login'])} · on GitHub since {m['joined'][:4]}</text>
<text x="40" y="92" font-family="{SANS}" font-size="34" font-weight="700" fill="{P['ink']}">{escape(m['name'])}</text>
<text x="40" y="120" font-family="{SANS}" font-size="15" fill="{P['ink']}">{escape(m['role'])}</text>
<text x="40" y="146" font-family="{SANS}" font-size="13" font-style="italic" fill="{P['dim']}">{escape(m['tagline'])}</text>
<path d="M40 170H500" stroke="{P['line']}" stroke-dasharray="2 4"/>
{''.join(tel)}
<text x="800" y="46" text-anchor="end" font-family="{MONO}" font-size="11" font-weight="600" fill="{P['amber']}">{escape(stage_line)}</text>
<text x="800" y="62" text-anchor="end" font-family="{MONO}" font-size="10" fill="{P['dim']}">{escape(next_line)}</text>
<g transform="translate(665 258) scale(1.14) translate(-665 -258)">{robot(si, pv, P)}</g>
{_mug(P)}
<path d="M520 258H820" stroke="{P['dim']}" stroke-width="1.2"/>
<path d="{ruler}" stroke="{P['faint']}" stroke-width="1"/>
<text x="40" y="284" font-family="{MONO}" font-size="9.5" fill="{P['faint']}" data-sync="1">synced {m['generated']} · every number here is generated from the GitHub API</text>
</svg>
"""


# ----------------------------------------------------------------------------- signal
DOMAIN_COLORS = ["amber", "cyan", "green", "violet", "ink"]


def signal_svg(m: dict, theme: str) -> str:
    P = PALETTES[theme]
    H = 232
    weeks = m["weeks"]
    x0, x1, y0, y1 = 40, 800, 50, 156
    n = max(len(weeks), 1)
    step = (x1 - x0) / n
    peak = max([w["count"] for w in weeks] + [1])
    top = peak * 1.15

    def y(c):
        return y1 - (c / top) * (y1 - y0)

    d = [f"M{x0} {y(weeks[0]['count']) if weeks else y1:.1f}"]
    for i, w in enumerate(weeks):
        d.append(f"H{x0 + i*step:.1f}V{y(w['count']):.1f}H{x0 + (i+1)*step:.1f}")
    path = "".join(d)
    # exact length of the step path, so the draw-in animation ends exactly at the end
    plen, cy = 0.0, (y(weeks[0]['count']) if weeks else y1)
    for i, w in enumerate(weeks):
        ny = y(w['count']); plen += abs(ny - cy) + step; cy = ny
    plen = max(plen, 1)

    grid = []
    for i in range(14):
        gx = x0 + i * (x1 - x0) / 13
        grid.append(f'<path d="M{gx:.1f} {y0}V{y1}" stroke="{P["line"]}" stroke-width="{1 if i in (0,13) else .6}" opacity=".7"/>')
    for j in range(5):
        gy = y0 + j * (y1 - y0) / 4
        grid.append(f'<path d="M{x0} {gy:.1f}H{x1}" stroke="{P["line"]}" stroke-width=".6" opacity=".7"/>')

    months, last = [], None
    for i, w in enumerate(weeks):
        mo = dt.date.fromisoformat(w["start"]).strftime("%b")
        if mo != last and i > 0:
            months.append(f'<text x="{x0 + i*step:.1f}" y="170" font-family="{MONO}" font-size="9.5" fill="{P["dim"]}">{mo}</text>')
        last = mo

    split = m["domains"]
    total_c = sum(split.values())
    bar, legend, bx, lx = [], [], x0, x0
    for k, (name, v) in enumerate(split.items()):
        col = ("url(#hatch)" if name == "private" else P["faint"] if name == "untagged"
               else P[DOMAIN_COLORS[k % len(DOMAIN_COLORS)]])
        wdt = (x1 - x0) * v / total_c
        bar.append(f'<rect x="{bx:.1f}" y="188" width="{max(wdt-2,1):.1f}" height="7" rx="1.5" fill="{col}"/>')
        bx += wdt
        label = f"{name} {round(100*v/total_c)}%"
        legend.append(f'<rect x="{lx}" y="206" width="7" height="7" rx="1" fill="{col}"/>'
                      f'<text x="{lx+11}" y="213" font-family="{MONO}" font-size="10" fill="{P["dim"]}">{escape(label)}</text>')
        lx += 11 + 6.2 * len(label) + 16
    if not split:
        legend.append(f'<text x="{x0}" y="213" font-family="{MONO}" font-size="10" fill="{P["dim"]}">no commit data in window</text>')

    active = sum(1 for w in weeks if w["count"] > 0)
    desc = (f"Weekly contributions over 52 weeks, peak {peak} in one week, {active} of {len(weeks)} weeks active. "
            "Commit share by domain: " + ", ".join(f"{k} {round(100*v/total_c)}%" for k, v in split.items()) + "."
            if split else "No commit data.")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">Contribution signal, last 52 weeks</title><desc id="d">{escape(desc)}</desc>
<style>.tr{{stroke-dasharray:{plen:.0f};stroke-dashoffset:0;animation:draw 2.4s ease-out}}
@keyframes draw{{from{{stroke-dashoffset:{plen:.0f}}}to{{stroke-dashoffset:0}}}}@media (prefers-reduced-motion:reduce){{.tr{{animation:none}}}}</style>
{_defs(P)}
{_frame(H, P)}
<text x="40" y="36" font-family="{MONO}" font-size="11" font-weight="600" fill="{P['cyan']}">CH1</text>
<text x="70" y="36" font-family="{MONO}" font-size="11" fill="{P['dim']}">contribution signal · weekly · 52w · peak {peak}/wk</text>
<text x="800" y="36" text-anchor="end" font-family="{MONO}" font-size="11" fill="{P['dim']}">{m['total']} total · {active}/{len(weeks)} weeks active</text>
{''.join(grid)}
<path d="{path}" fill="none" stroke="{P['cyan']}" stroke-width="6" opacity=".14" stroke-linejoin="round"/>
<path class="tr" d="{path}" fill="none" stroke="{P['cyan']}" stroke-width="1.6" stroke-linejoin="round"/>
{''.join(months)}
{''.join(bar)}
{''.join(legend)}
<text x="800" y="213" text-anchor="end" font-family="{MONO}" font-size="10" fill="{P['faint']}">signal ≠ quality · evidence per build ↓</text>
</svg>
"""
