"""Icon artwork shared by the desktop and Android UIs -- plain data, no Qt.

ICON_PATHS maps an icon name to SVG path data on a 24x24 grid, drawn as
round-capped, round-joined strokes of width STROKE in a single colour
(each UI uses its theme's accent: IND2 on desktop, Theme.indigo2 on
Android). ICON_FILLS holds the solid parts of an icon (paw pads, the "i"
dot, a bolt...), filled exactly as drawn (no edge stroke) in that same
colour. Only absolute M/L/Q/C/Z commands are used, so desktop's small
parser (icons.py) and Qt Quick's Canvas (`ctx.path = ...`, see
ui_android/qml/imports/Mimic/MIcon.qml) both read the same strings.
These replace the emoji the UIs used to show.

CHEESE_PIXELS / CHEESE_PALETTE are the pixel-art cheese wedge for the
"type cheese" easter egg: one character per pixel, "." transparent.
"""
import math
import re

STROKE = 1.9


def _n(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _pt(x, y):
    return f"{_n(x)} {_n(y)}"


def line(x1, y1, x2, y2):
    return f"M {_pt(x1, y1)} L {_pt(x2, y2)}"


def poly(*pts, closed=True):
    s = f"M {_pt(*pts[0])} " + " ".join(f"L {_pt(*p)}" for p in pts[1:])
    return s + (" Z" if closed else "")


def arc(cx, cy, rx, ry, a0, a1, move=True):
    """Elliptical arc from angle a0 to a1 (degrees, screen coordinates:
    0 = right, 90 = down) as cubic segments of at most 90 degrees."""
    n = max(1, math.ceil(abs(a1 - a0) / 90))
    step = math.radians(a1 - a0) / n
    k = 4 / 3 * math.tan(step / 4)
    t = math.radians(a0)
    out = [f"M {_pt(cx + rx * math.cos(t), cy + ry * math.sin(t))}"] if move else []
    for _ in range(n):
        t2 = t + step
        c1 = (cx + rx * (math.cos(t) - k * math.sin(t)), cy + ry * (math.sin(t) + k * math.cos(t)))
        c2 = (cx + rx * (math.cos(t2) + k * math.sin(t2)), cy + ry * (math.sin(t2) - k * math.cos(t2)))
        out.append(f"C {_pt(*c1)} {_pt(*c2)} {_pt(cx + rx * math.cos(t2), cy + ry * math.sin(t2))}")
        t = t2
    return " ".join(out)


def ellipse(cx, cy, rx, ry):
    return arc(cx, cy, rx, ry, 0, 360) + " Z"


def circle(cx, cy, r):
    return ellipse(cx, cy, r, r)


def hole(cx, cy, r):
    """A circle wound the other way: inside a filled shape it cuts a hole
    (both renderers fill non-zero), e.g. bubbles in a potion."""
    return arc(cx, cy, r, r, 360, 0) + " Z"


def rrect(x, y, w, h, r):
    return (f"M {_pt(x + r, y)} L {_pt(x + w - r, y)} Q {_pt(x + w, y)} {_pt(x + w, y + r)} "
            f"L {_pt(x + w, y + h - r)} Q {_pt(x + w, y + h)} {_pt(x + w - r, y + h)} "
            f"L {_pt(x + r, y + h)} Q {_pt(x, y + h)} {_pt(x, y + h - r)} "
            f"L {_pt(x, y + r)} Q {_pt(x, y)} {_pt(x + r, y)} Z")


def sparkle(cx, cy, rx, ry):
    """Four-point star with concave sides."""
    return (f"M {_pt(cx, cy - ry)} Q {_pt(cx, cy)} {_pt(cx + rx, cy)} Q {_pt(cx, cy)} {_pt(cx, cy + ry)} "
            f"Q {_pt(cx, cy)} {_pt(cx - rx, cy)} Q {_pt(cx, cy)} {_pt(cx, cy - ry)} Z")


def star(cx, cy, r_out, r_in, points=5):
    pts = []
    for i in range(points * 2):
        r = r_out if i % 2 == 0 else r_in
        a = math.radians(-90 + i * 180 / points)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return poly(*pts)


def _cog(cx, cy, r_out, r_in, teeth=8):
    pts = []
    for i in range(teeth):
        a = 360 / teeth * i
        for da, r in ((-16, r_in), (-9, r_out), (9, r_out), (16, r_in)):
            t = math.radians(a + da)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return poly(*pts)


def _arrowhead(cx, cy, r, a, size=2.6, clockwise=True):
    """Chevron at the end of an arc of radius r at angle a (degrees)."""
    t = math.radians(a)
    px, py = cx + r * math.cos(t), cy + r * math.sin(t)
    # direction of travel along the arc
    dx, dy = (-math.sin(t), math.cos(t)) if clockwise else (math.sin(t), -math.cos(t))
    bx, by = px - dx * size, py - dy * size          # back along the arc
    nx, ny = -dy, dx                                   # normal
    return poly((bx + nx * size * 0.8, by + ny * size * 0.8), (px, py),
                (bx - nx * size * 0.8, by - ny * size * 0.8), closed=False)


def _tip(x, y, dx, dy, size=3.0, spread=40):
    """Open arrowhead at (x, y) pointing along (dx, dy)."""
    a = math.atan2(dy, dx)
    pts = []
    for s_ in (spread, -spread):
        t = a + math.pi - math.radians(s_)
        pts.append((x + size * math.cos(t), y + size * math.sin(t)))
    return poly(pts[0], (x, y), pts[1], closed=False)


def _hex_pts(cx, cy, radii):
    return [(cx + r * math.cos(math.radians(-90 + 60 * i)), cy + r * math.sin(math.radians(-90 + 60 * i)))
            for i, r in enumerate(radii)]


def _wrench(cx, cy, r, handle_angle, hx, hy):
    """Open-ended wrench: a ring head with a U-slot facing away from the
    handle, and a handle running to (hx, hy)."""
    slot = handle_angle + 180            # slot points away from the handle
    half, depth = 28, r * 0.42
    a0, a1 = slot + half, slot - half + 360
    pt = lambda ang, rad: (cx + rad * math.cos(math.radians(ang)), cy + rad * math.sin(math.radians(ang)))
    head = arc(cx, cy, r, r, a0, a1)
    inner_a, inner_b = pt(slot - half, depth), pt(slot + half, depth)
    head += f" L {_pt(*inner_a)} L {_pt(*inner_b)} Z"
    return _join(head, line(*pt(handle_angle, r), hx, hy))


def rot_ellipse(cx, cy, rx, ry, angle, n=28):
    a = math.radians(angle)
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rx * math.cos(t), ry * math.sin(t)
        pts.append((cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)))
    return poly(*pts)


def dashed_arc(cx, cy, rx, ry, a0, a1, dash=26, gap=16):
    out, a = [], a0
    while a < a1:
        out.append(arc(cx, cy, rx, ry, a, min(a + dash, a1)))
        a += dash + gap
    return " ".join(out)


def spiral(cx, cy, r, turns=1.75, start=-90, n=40):
    """Open spiral winding outward from the centre to radius r."""
    pts = []
    for i in range(n + 1):
        f = i / n
        t = math.radians(start + 360 * turns * f)
        pts.append((cx + r * f * math.cos(t), cy + r * f * math.sin(t)))
    return poly(*pts, closed=False)


def capsule(cx, cy, length, width, angle, n=10):
    """Stadium (rounded-end bar) centred on (cx, cy), its long axis at
    `angle` degrees -- a chain link seen face-on or edge-on."""
    a = math.radians(angle)
    ux, uy, vx, vy = math.cos(a), math.sin(a), -math.sin(a), math.cos(a)
    half, r = length / 2 - width / 2, width / 2
    pts = []
    for end, base in ((half, -90), (-half, 90)):
        for i in range(n + 1):
            t = math.radians(base + 180 * i / n)
            x, y = end + r * math.cos(t), r * math.sin(t)
            pts.append((cx + x * ux + y * vx, cy + x * uy + y * vy))
    return poly(*pts)


_BIRD = [  # facing right, about 8 x 7, centred on the origin
    ("M", (-4.0, -1.6)), ("L", (-1.8, -0.4)), ("L", (-1.0, -4.1)), ("L", (0.6, -2.4)),
    ("C", (1.0, -2.7), (1.9, -2.8), (2.4, -2.5)), ("C", (2.9, -2.2), (3.1, -1.6), (3.0, -1.0)),
    ("L", (4.3, -0.5)), ("L", (2.9, 0.1)), ("C", (2.7, 1.8), (1.3, 2.6), (-0.1, 2.6)),
    ("C", (-1.5, 2.6), (-2.3, 1.7), (-2.4, 0.9)), ("L", (-4.0, 0.4)), ("L", (-3.0, -0.5)),
]


def _bird(x, y, s=1.0, flip=False):
    """Little cartoon bird silhouette, wing flapped up -- filled."""
    d = -1 if flip else 1
    out = []
    for op, *pts in _BIRD:
        out.append(op + " " + " ".join(_pt(x + d * px * s, y + py * s) for px, py in pts))
    return " ".join(out) + " Z"


def _xf(pts, cx, cy, angle):
    """Rotate local (x, y) points by `angle` degrees and move to (cx, cy)."""
    a = math.radians(angle)
    return [(cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(a) + y * math.cos(a)) for x, y in pts]


def _xf_path(d, cx, cy, angle):
    """_xf() applied to every coordinate pair of an absolute-command path."""
    toks = re.split(r"(-?\d*\.?\d+)", d)
    nums = [float(t) for t in toks if re.fullmatch(r"-?\d*\.?\d+", t or "x")]
    pts = iter(_xf(list(zip(nums[0::2], nums[1::2])), cx, cy, angle))
    out, pending = [], None
    for t in toks:
        if re.fullmatch(r"-?\d*\.?\d+", t or "x"):
            if pending is None:
                pending = next(pts)
                out.append(_n(pending[0]))
            else:
                out.append(_n(pending[1]))
                pending = None
        else:
            out.append(t)
    return "".join(out)


# Lute, drawn along +x (body at the left, neck to the right), then turned
# to lie on the diagonal
_LUTE_BODY = ("M 2.6 -1.4 C -0.4 -4.4 -3.6 -5.6 -6.2 -4.4 C -9 -3 -9 3 -6.2 4.4 "
              "C -3.6 5.6 -0.4 4.4 2.6 1.4 Z")
_LUTE_NECK = "M 2.6 -1.1 L 9.4 -1.1 M 2.6 1.1 L 9.4 1.1"
_LUTE_HEAD = "M 9.4 -1.3 L 12.6 1.6 L 11.4 2.8 L 9.4 1.3"     # pegbox, bent back
_LUTE_STRINGS = "M -7 0 L 9.4 0"
_LUTE_BRIDGE = "M -6.6 -1.6 L -6.6 1.6"


def _outline(d, inset=0.58):
    """A thin solid outline of closed shape `d`: the shape, filled, minus a
    copy shrunk about its centre by `inset` and wound the other way -- for
    small details a full-width stroke would clog (the lantern's flame)."""
    num = re.compile(r"-?\d*\.?\d+")
    segs, cur = [], None
    toks = re.findall(r"[MLCZ]|-?\d*\.?\d+", d)
    i = 0
    while i < len(toks):
        op = toks[i]
        if op == "M":
            cur = (float(toks[i + 1]), float(toks[i + 2])); start = cur; i += 3
        elif op == "L":
            segs.append(("L", [], (float(toks[i + 1]), float(toks[i + 2])))); i += 3
        elif op == "C":
            v = [float(t) for t in toks[i + 1:i + 7]]
            segs.append(("C", [(v[0], v[1]), (v[2], v[3])], (v[4], v[5]))); i += 7
        else:
            i += 1
    xs = [p[0] for _, c, e in segs for p in c + [e]]
    ys = [p[1] for _, c, e in segs for p in c + [e]]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    sc = lambda p: (cx + (p[0] - cx) * inset, cy + (p[1] - cy) * inset)
    # walk the segments backwards: each one runs from its end to the
    # previous segment's end, with its control points swapped
    ends = [start] + [e for _, _, e in segs]
    out = [f"M {_pt(*sc(ends[-1]))}"]
    for k in range(len(segs) - 1, -1, -1):
        op, ctrl, _ = segs[k]
        if op == "C":
            out.append(f"C {_pt(*sc(ctrl[1]))} {_pt(*sc(ctrl[0]))} {_pt(*sc(ends[k]))}")
        else:
            out.append(f"L {_pt(*sc(ends[k]))}")
    return d + " " + " ".join(out) + " Z"


_SMALL_FLAME = ("M 11 9.4 C 12 10.8 14.4 12.4 14.4 14.4 C 14.4 15.9 13.3 16.9 12 16.9 "
                "C 10.7 16.9 9.6 15.9 9.6 14.6 C 9.6 13.5 10.3 12.8 10.7 12.1 C 11.1 11.4 11.2 10.6 11 9.4 Z")


_HEART = ("M 12 20.4 C 5 15.4 2.8 11.6 2.8 8.4 C 2.8 5.6 5 3.6 7.6 3.6 C 9.6 3.6 11.1 4.8 12 6.6 "
          "C 12.9 4.8 14.4 3.6 16.4 3.6 C 19 3.6 21.2 5.6 21.2 8.4 C 21.2 11.6 19 15.4 12 20.4 Z")


def heart(cx, cy, scale, tilt=0):
    """_HEART shrunk by `scale` about its middle, moved to (cx, cy), tilted."""
    a = math.radians(tilt)
    def xf(m):
        x, y = (float(m.group(1)) - 12) * scale, (float(m.group(2)) - 12) * scale
        return f"{_n(cx + x * math.cos(a) - y * math.sin(a))} {_n(cy + x * math.sin(a) + y * math.cos(a))}"
    return re.sub(r"(-?\d*\.?\d+) (-?\d*\.?\d+)", xf, _HEART)


def _join(*parts):
    return " ".join(parts)


_HEX = [(12, 3), (19.8, 7.5), (19.8, 16.5), (12, 21), (4.2, 16.5), (4.2, 7.5)]
_D20 = _join(poly(*_HEX), poly((12, 8), (16.3, 15.2), (7.7, 15.2)),
             line(12, 3, 12, 8), line(4.2, 16.5, 7.7, 15.2), line(19.8, 16.5, 16.3, 15.2))
_SWORDS = _join(line(4.5, 4.5, 14.6, 14.6), line(12.4, 16.8, 16.8, 12.4), line(14.6, 14.6, 19, 19),
                line(19.5, 4.5, 9.4, 14.6), line(7.2, 12.4, 11.6, 16.8), line(9.4, 14.6, 5, 19))
_SPARKLES = _join(sparkle(10.5, 13.5, 6.8, 7.5), sparkle(18, 5.5, 2.6, 2.8))
_FLASK = _join(line(9.4, 3.5, 14.6, 3.5),
               "M 10.4 3.5 L 10.4 9.2 L 4.9 18.6 Q 4.1 20.5 6.2 20.5 L 17.8 20.5 Q 19.9 20.5 19.1 18.6 "
               "L 13.6 9.2 L 13.6 3.5", line(7.3, 15, 16.7, 15))
_BOOK = _join("M 12 6.8 Q 8.4 4.6 3.8 5.2 L 3.8 18.6 Q 8.4 18 12 20.2",
              "M 12 6.8 Q 15.6 4.6 20.2 5.2 L 20.2 18.6 Q 15.6 18 12 20.2", line(12, 6.8, 12, 20.2))
_PAGE = _join(poly((6, 3.5), (14, 3.5), (18.5, 8), (18.5, 20.5), (6, 20.5)),
              poly((14, 3.5), (14, 8), (18.5, 8), closed=False),
              line(8.8, 12, 15.7, 12), line(8.8, 15, 15.7, 15), line(8.8, 18, 12.8, 18))


def _moon_solid():
    return _moon(r1=9.3, c2=(16.4, 8.1), r2=7.3)


def _moon(r1=8.5, c2=(16.0, 8.5), r2=7.2):
    # Crescent: the outer circle's arc, then back along an inner circle's
    # arc between their two intersection points.
    c1 = (12.0, 12.0)
    d = math.dist(c1, c2)
    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h = math.sqrt(r1 * r1 - a * a)
    mx, my = c1[0] + a * (c2[0] - c1[0]) / d, c1[1] + a * (c2[1] - c1[1]) / d
    p1 = (mx + h * (c2[1] - c1[1]) / d, my - h * (c2[0] - c1[0]) / d)
    p2 = (mx - h * (c2[1] - c1[1]) / d, my + h * (c2[0] - c1[0]) / d)
    ang = lambda c, p: math.degrees(math.atan2(p[1] - c[1], p[0] - c[0]))
    a1s, a1e = ang(c1, p1), ang(c1, p2)
    if a1e < a1s:
        a1e += 360
    # outer arc goes the long way round (away from the inner circle)
    if a1e - a1s < 180:
        a1s, a1e = a1e, a1s + 360
    outer = arc(*c1, r1, r1, a1s, a1e)
    end = (c1[0] + r1 * math.cos(math.radians(a1e)), c1[1] + r1 * math.sin(math.radians(a1e)))
    start = (c1[0] + r1 * math.cos(math.radians(a1s)), c1[1] + r1 * math.sin(math.radians(a1s)))
    b0, b1 = ang(c2, end), ang(c2, start)
    # inner arc: the short way, bulging toward c1
    if (b1 - b0) % 360 > 180:
        b1 = b0 - ((b0 - b1) % 360)
    else:
        b1 = b0 + ((b1 - b0) % 360)
    inner = arc(*c2, r2, r2, b0, b1, move=False)
    return outer + " " + inner + " Z"


ICON_PATHS = {
    # ── Character sheet tabs ────────────────────────────────────────────
    # Abilities & Saves: a six-point radar chart -- one spoke per ability score
    "abilities": poly(*_hex_pts(12, 12.4, [8.6] * 6)),
    # Skills & Proficiencies: proficiency bubbles beside skill lines, as on a paper sheet
    "skills": _join(circle(5.6, 6, 1.9), line(10, 6, 20, 6),
                    circle(5.6, 12, 1.9), line(10, 12, 17, 12),
                    circle(5.6, 18, 1.9), line(10, 18, 19, 18)),
    "combat": _SWORDS,
    "gear": _join(rrect(5, 7, 14, 14, 3.2),
                  "M 9.2 7 L 9.2 5.4 Q 9.2 3.8 10.8 3.8 L 13.2 3.8 Q 14.8 3.8 14.8 5.4 L 14.8 7",
                  rrect(8.3, 13.2, 7.4, 4.8, 1.4), line(5, 11, 19, 11)),
    # Spells: a wand throwing a spark
    "spells": _join(line(4.2, 19.8, 13.4, 10.6), line(11.6, 9.9, 14.1, 12.4)),
    # Infusions (Artificer): an anvil throwing magic sparks
    "infusions": "M 3.2 8.6 L 19.8 8.6 L 19.8 11.3 Q 16.5 11.7 15.5 14 L 16.6 16.8 L 17.8 16.8 L 17.8 19.8 "
                 "L 6.6 19.8 L 6.6 16.8 L 7.8 16.8 L 8.9 14 Q 7.9 11.7 5.3 11.3 Q 3.6 10.9 3.2 8.6 Z",
    # Choices: a path that forks two ways
    "choices": _join(line(12, 20.5, 12, 13.6), "M 12 13.6 Q 12 10.6 6.6 6.4", "M 12 13.6 Q 12 10.6 17.4 6.4",
                     _tip(6.6, 6.4, -1, -0.78), _tip(17.4, 6.4, 1, -0.78)),
    "features": _BOOK,
    # A document (recent files, scrolls)
    "file": _PAGE,
    # Traits & Notes: a quill writing on a line
    "notes": _join("M 19.8 3.6 C 13.2 4.4 8.6 9.4 7.6 16 L 9.3 14.3 C 15.4 13.4 18.8 8.6 19.8 3.6 Z",
                   line(16.2, 7.2, 4.4, 19.6), line(11, 20.4, 19.6, 20.4)),
    # ── Actions & combat ────────────────────────────────────────────────
    "dice": _D20,
    # Advantage / disadvantage: a d20 outline with an A or a D inside
    # (each UI colours them green / red rather than the accent)
    "adv": _join(poly(*_HEX), poly((8.9, 16.2), (12, 7.4), (15.1, 16.2), closed=False), line(10.1, 13.2, 13.9, 13.2)),
    "disadv": _join(poly(*_HEX), "M 9.6 7.6 L 9.6 16.4 L 11.8 16.4 Q 15.4 16.4 15.4 12 Q 15.4 7.6 11.8 7.6 Z"),
    # Magic items: sparkles
    "magic": _SPARKLES,
    # Potions: a flask, partly full
    "potion": _FLASK,
    "bonus": _join(circle(12, 12, 8.5), line(12, 8, 12, 16), line(8, 12, 16, 12)),
    "bolt": "",
    # "Other" (passive features): more, in a circle
    "passive": circle(12, 12, 8.6),
    # Active effects: an aura ringing a core
    "effects": _join(*[arc(12, 12, 8, 8, a, a + 34) for a in range(-80, 280, 60)]),
    # Ammunition: an arrow with fletching
    "ammo": _join(line(4.6, 19.4, 16.4, 7.6),
                  *[_join(line(x, y, x - 2.9, y), line(x, y, x, y + 2.9)) for x, y in ((6.6, 17.4), (8.9, 15.1))]),
    "dagger": _join(poly((12, 3), (14.2, 6), (14.2, 14), (9.8, 14), (9.8, 6)),
                    line(7, 14, 17, 14), line(12, 14, 12, 18.6)),
    "shield": "M 12 3.5 L 19 6 L 19 11.5 Q 19 17.5 12 20.5 Q 5 17.5 5 11.5 L 5 6 Z",
    "skull": _join("M 12 3.5 C 7 3.5 4.5 7 4.5 10.5 C 4.5 13.5 6 15 7.5 15.6 L 7.5 19 Q 7.5 20.2 8.7 20.2 "
                   "L 15.3 20.2 Q 16.5 20.2 16.5 19 L 16.5 15.6 C 18 15 19.5 13.5 19.5 10.5 "
                   "C 19.5 7 17 3.5 12 3.5 Z",
                   line(10.6, 17, 10.6, 20.2), line(13.4, 17, 13.4, 20.2)),

    # ── Conditions ──────────────────────────────────────────────────────
    "cond_blinded": _join("M 2.6 12 Q 12 3.8 21.4 12 Q 12 20.2 2.6 12 Z", line(4.2, 19.8, 19.8, 4.2)),
    "cond_charmed": "",
    "cond_deafened": _join("M 9.2 20.2 C 9.2 17.4 7.6 16.2 7.1 14.2 C 6.6 12.2 6.6 9.4 7.6 7.6 "
                           "C 8.8 5.2 11 4 13.3 4 C 16.6 4 19 6.6 19 9.9 C 19 12.4 17.6 13.6 16.4 14.6 "
                           "C 15.2 15.6 14.6 16.8 14.6 18 Q 14.6 20.6 11.9 20.6",
                           "M 10.6 10 C 10.6 8.1 11.9 7 13.4 7 C 15 7 16.2 8.3 16 10", line(3.6, 3.6, 20.4, 20.4)),
    # Frightened: solid -- see ICON_FILLS / ICON_CUTS
    "cond_frightened": "",
    # Surprised: eyes gone wide, pupils shrunk to pinpricks, brows shot up
    "cond_surprised": _join(ellipse(8, 13.6, 4, 5.2), ellipse(16, 13.6, 4, 5.2),
                             "M 4.6 5.8 Q 7.4 3.4 10.4 4.8", "M 13.6 4.8 Q 16.6 3.4 19.4 5.8"),

    # Gagged: a mouth, struck through (like blinded's eye, deafened's ear)
    "cond_gagged": _join("M 2.6 12.4 Q 6 7.2 9.4 7.8 Q 11 8.2 12 9.6 Q 13 8.2 14.6 7.8 Q 18 7.2 21.4 12.4 "
                         "Q 17 18.4 12 18.4 Q 7 18.4 2.6 12.4 Z",
                         "M 2.6 12.4 Q 12 14.6 21.4 12.4", line(4.2, 19.8, 19.8, 4.2)),
    # Grappled: a hand clamped round a forearm -- knuckles on top, fingers
    # curling down over the arm, the grabber's wrist coming in from above
    "cond_grappled": _join(line(2.2, 10.4, 3.6, 10.4), line(2.2, 16.2, 7.2, 16.2),
                           line(17, 10.4, 21.6, 10.4), line(17, 16.2, 21.6, 16.2),
                           "M 8.8 2.6 L 7.6 8 Q 4.2 8.6 4.4 11.6 Q 4.6 13.8 7.2 13.6 L 7.2 17.4 "
                           "Q 7.2 19.4 8.4 19.4 Q 9.6 19.4 9.6 17.4 Q 9.6 19.4 10.8 19.4 Q 12 19.4 12 17.4 "
                           "Q 12 19.4 13.2 19.4 Q 14.4 19.4 14.4 17.4 Q 14.4 19.4 15.6 19.4 Q 17 19.4 17 17.4 "
                           "L 17 9.2 L 15.4 2.6",
                           line(9.6, 13.8, 9.6, 17.4), line(12, 13.8, 12, 17.4), line(14.4, 13.8, 14.4, 17.4)),
    # Incapacitated: dazed -- swirls for eyes, a wobbly mouth
    "cond_incapacitated": _join(circle(12, 12, 9), spiral(8.4, 10.2, 3.1, turns=1.3, start=-120),
                                spiral(15.6, 10.2, 3.1, turns=1.3, start=-60),
                                "M 8.4 16.2 Q 10.2 14.6 12 16.2 Q 13.8 17.8 15.6 16.2"),
    # Unconscious: out cold -- Zzz
    "cond_unconscious": _join(poly((4, 11), (10, 11), (4, 18.6), (10, 18.6), closed=False),
                              poly((12.6, 6.6), (16.6, 6.6), (12.6, 11.8), (16.6, 11.8), closed=False),
                              poly((18.2, 3), (20.6, 3), (18.2, 6.2), (20.6, 6.2), closed=False)),
    "cond_invisible": "",
    # Paralyzed: an empty wheelchair
    "cond_paralyzed": _join(circle(9.6, 16.6, 4.9), "M 4.4 3.2 Q 6.6 3.2 6.6 5.4 L 6.6 7.6 Q 6.6 9.2 8.2 9.2 L 14 9.2 "
                            "Q 15.4 9.2 15.8 10.6 L 17.4 16.4 Q 17.6 17 18.2 17 L 20.8 17", circle(18.6, 21.2, 1.2)),
    # Petrified: turned into a statue on its plinth
    "cond_petrified": _join(circle(12, 4.2, 2.3),
                            poly((8.4, 7.8), (15.6, 7.8), (15.6, 13.2), (14.2, 13.2), (14.2, 17.4),
                                 (9.8, 17.4), (9.8, 13.2), (8.4, 13.2)),
                            poly((9.4, 17.4), (14.6, 17.4), (16.4, 20.2), (7.6, 20.2))),
    "cond_poisoned": "M 12 3.4 C 12 3.4 5.4 11 5.4 14.6 C 5.4 18.2 8.4 21 12 21 C 15.6 21 18.6 18.2 18.6 14.6 "
                     "C 18.6 11 12 3.4 12 3.4 Z",
    # Prone: the Family Guy fall -- a solid silhouette traced from the
    # pose, with the arm, hands, collar, belt and shoes carved out (ICON_CUTS)
    "cond_prone": "",
    # Restrained: a length of chain -- face-on links threaded on an
    # edge-on one (solid, see ICON_FILLS)
    "cond_restrained": _join(*[capsule(12 + t * 0.7071, 12 - t * 0.7071, 8.4, 5.4, -45) for t in (-8.4, 2.8)]),
    # Stunned: little birds circling the head


    "cond_stunned": _join("M 4.6 22 Q 4.6 16.8 12 16.8 Q 19.4 16.8 19.4 22",
                          arc(12, 8.8, 9.4, 3.6, 96, 186), arc(12, 8.8, 9.4, 3.6, 276, 366)),
    # Exhaustion: heavy-lidded eyes with bags under them
    "cond_exhaustion": _join(*[_join(line(x - 4.3, 9.4, x + 4.3, 9.4), arc(x, 9.4, 3.5, 3.2, 0, 180),
                                     f"M {x - 3.6} 15.6 Q {x} 18.8 {x + 3.6} 15.6")
                               for x in (6.6, 17.4)]),
    # Quick-spell pin: a star (outline = unpinned, solid = pinned)
    "star": star(12, 12.6, 9.2, 4.0),
    "star_solid": "",
    # Hit points: a heart outline
    "heart": "M 12 20.4 C 5 15.4 2.8 11.6 2.8 8.4 C 2.8 5.6 5 3.6 7.6 3.6 C 9.6 3.6 11.1 4.8 12 6.6 "
             "C 12.9 4.8 14.4 3.6 16.4 3.6 C 19 3.6 21.2 5.6 21.2 8.4 C 21.2 11.6 19 15.4 12 20.4 Z",
    # ── Rests & status ──────────────────────────────────────────────────
    "short_rest": _join(line(6.5, 3.5, 17.5, 3.5), line(6.5, 20.5, 17.5, 20.5),
                        "M 7.8 3.5 Q 7.8 9 12 12 Q 16.2 9 16.2 3.5",
                        "M 7.8 20.5 Q 7.8 15 12 12 Q 16.2 15 16.2 20.5", line(10, 18.2, 14, 18.2)),
    "long_rest": "",
    # Inspiration: a lightbulb with a spark inside
    "inspiration": _join("M 9.2 15.6 C 6.8 14.2 5.6 12 5.6 9.8 C 5.6 6.3 8.5 3.5 12 3.5 C 15.5 3.5 18.4 6.3 18.4 9.8 "
                         "C 18.4 12 17.2 14.2 14.8 15.6 L 14.8 17.2 L 9.2 17.2 Z",
                         line(9.6, 19.4, 14.4, 19.4), line(10.6, 21.3, 13.4, 21.3)),
    # Experience: a medal on a ribbon
    "experience": _join(poly((7.6, 3.4), (10.4, 10.4), closed=False), poly((16.4, 3.4), (13.6, 10.4), closed=False),
                        line(7.6, 3.4, 16.4, 3.4), circle(12, 15.3, 5.3)),
    # Identity: an ID card
    "identity": _join(rrect(3.4, 5.4, 17.2, 13.2, 2.2),
                      "M 5.9 16 Q 5.9 13.1 8.5 13.1 Q 11.1 13.1 11.1 16",
                      line(13.6, 10, 17.8, 10), line(13.6, 13.4, 16.4, 13.4)),
    "orb": _join(circle(12, 10.5, 6.6), line(7.4, 20.5, 16.6, 20.5), line(9, 16.6, 7.4, 20.5),
                 line(15, 16.6, 16.6, 20.5), arc(12, 10.5, 3.8, 3.8, 200, 250)),
    # ── Items ───────────────────────────────────────────────────────────
    "package": _join(poly((4, 8), (12, 4), (20, 8), (20, 16.5), (12, 20.5), (4, 16.5)),
                     poly((4, 8), (12, 12), (20, 8), closed=False), line(12, 12, 12, 20.5)),
    "coins": _join(ellipse(12, 7, 7, 2.6), line(5, 7, 5, 17), line(19, 7, 19, 17),
                   "M 5 10.5 C 5 13.9 19 13.9 19 10.5", "M 5 14 C 5 17.4 19 17.4 19 14",
                   "M 5 17 C 5 20.4 19 20.4 19 17"),
    # Vehicles: a wagon
    "wagon": _join("M 5 9.6 L 5 7.4 Q 5 3 12 3 Q 19 3 19 7.4 L 19 9.6", line(9.4, 3.5, 9.4, 9.6),
                   line(14.6, 3.5, 14.6, 9.6), poly((3.4, 9.6), (20.6, 9.6), (19.4, 14.6), (4.6, 14.6)),
                   circle(8, 18, 2.6), circle(16, 18, 2.6)),
    "paw": "",
    # Items you use rather than just carry:
    # tool kits, artisan's tools, thieves' tools -- a toolbox
    "toolkit": _join(rrect(2.8, 9.4, 18.4, 10.8, 1.8), line(2.8, 13.6, 21.2, 13.6),
                     "M 8.6 9.4 L 8.6 6.8 Q 8.6 5.2 10.2 5.2 L 13.8 5.2 Q 15.4 5.2 15.4 6.8 L 15.4 9.4"),
    # healer's kit: a satchel with a cross
    "medkit": _join(rrect(3, 7.6, 18, 12.8, 2.4),
                    "M 9 7.6 L 9 5.8 Q 9 4.4 10.4 4.4 L 13.6 4.4 Q 15 4.4 15 5.8 L 15 7.6"),
    # musical instruments: a lute
    "instrument": _join(*[_xf_path(d, 11.2, 12.8, -45) for d in (_LUTE_BODY, _LUTE_NECK, _LUTE_HEAD,
                                                                  _LUTE_STRINGS, _LUTE_BRIDGE)]),
    # tinderbox, torch, candle, alchemist's fire: a flame
    "flame": "M 12.6 2.4 C 13.4 6.2 19 8.6 18.8 14.6 C 18.6 18.6 15.6 21.6 12 21.6 C 8.4 21.6 5.2 18.8 5.2 14.8 "
             "C 5.2 11.6 7 9.6 8.2 8.2 C 8.4 10.2 9.2 11.6 10.4 12.2 C 9.8 8.6 10.8 5 12.6 2.4 Z",
    # lamps and lanterns
    "lantern": _join(circle(12, 3, 1.2), poly((6.8, 7.4), (8.8, 5), (15.2, 5), (17.2, 7.4)),
                     rrect(6.6, 7.4, 10.8, 10.8, 1.6), poly((5.6, 21), (6.6, 18.2), (17.4, 18.2), (18.4, 21))),
    # flasks you throw or apply (acid, holy water, oil, poison)
    "vial": _join(line(9.4, 3, 14.6, 3), "M 10.4 3 L 10.4 8.2 Q 4.6 9.8 4.6 14.6 Q 4.6 21 12 21 "
                  "Q 19.4 21 19.4 14.6 Q 19.4 9.8 13.6 8.2 L 13.6 3"),
    # ── App chrome ──────────────────────────────────────────────────────
    "settings": _join(_cog(12, 12, 9.3, 7.1), circle(12, 12, 2.9)),
    "save": _join(rrect(4, 4, 16, 16, 2), poly((8, 4), (8, 8.6), (15.5, 8.6), (15.5, 4), closed=False),
                  poly((7.5, 20), (7.5, 13.6), (16.5, 13.6), (16.5, 20), closed=False)),
    "folder": "M 3.5 7 Q 3.5 5.5 5 5.5 L 9.5 5.5 L 11.5 7.5 L 19 7.5 Q 20.5 7.5 20.5 9 L 20.5 17.5 "
              "Q 20.5 19 19 19 L 5 19 Q 3.5 19 3.5 17.5 Z",
    "trash": _join(line(4.5, 6.5, 19.5, 6.5), poly((9.5, 6.5), (9.5, 4.2), (14.5, 4.2), (14.5, 6.5), closed=False),
                   poly((6.5, 6.5), (7.5, 20), (16.5, 20), (17.5, 6.5), closed=False),
                   line(10.2, 10, 10.2, 16.5), line(13.8, 10, 13.8, 16.5)),
    "refresh": _join(arc(12, 12, 7.5, 7.5, 200, 330), _arrowhead(12, 12, 7.5, 330),
                     arc(12, 12, 7.5, 7.5, 20, 150), _arrowhead(12, 12, 7.5, 150)),
    "home": _join(poly((3.5, 11.5), (12, 4), (20.5, 11.5), closed=False),
                  poly((6, 10), (6, 20), (18, 20), (18, 10), closed=False),
                  poly((10, 20), (10, 15), (14, 15), (14, 20), closed=False)),
    "pencil": _join("M 4.5 19.5 L 5.4 15.1 L 15.4 5.1 Q 16.8 3.7 18.2 5.1 L 18.9 5.8 Q 20.3 7.2 18.9 8.6 "
                    "L 8.9 18.6 Z", line(13.8, 6.7, 17.3, 10.2)),
    "search": _join(circle(10.5, 10.5, 6.2), line(15.1, 15.1, 20, 20)),
    "info": _join(circle(12, 12, 9), line(12, 10.8, 12, 16.8)),
    "credits": _join(circle(12, 12, 9), arc(12, 12, 4.3, 4.3, 45, 315)),
    "arrow_left": _join(line(19, 12, 5, 12), poly((10.5, 6.5), (5, 12), (10.5, 17.5), closed=False)),
    "arrow_up": _join(line(12, 19.5, 12, 5), poly((6.5, 10.5), (12, 5), (17.5, 10.5), closed=False)),
    "arrow_down": _join(line(12, 4.5, 12, 19), poly((6.5, 13.5), (12, 19), (17.5, 13.5), closed=False)),
    "chevron_right": poly((9, 5.5), (15.5, 12), (9, 18.5), closed=False),
    "chevron_down": poly((5.5, 9), (12, 15.5), (18.5, 9), closed=False),
}

def _center_icons():
    """Shift every icon so its artwork (outline and solid parts together)
    is centred on the 24x24 grid -- the shapes above are drawn wherever
    reads naturally, which left many sitting off-centre (sparkles leaning
    top-right, the medal low). Every command here is absolute M/L/Q/C/Z,
    so translating is just offsetting each coordinate pair; the bounding
    box uses the curves' control points, exact for this set's circles
    and arcs and close enough for the rest."""
    num = re.compile(r"-?\d*\.?\d+")
    for name in set(ICON_PATHS) | set(ICON_FILLS):
        parts = [ICON_PATHS.get(name, ""), ICON_FILLS.get(name, "")]   # cuts sit inside these
        coords = [float(v) for d in parts for v in num.findall(d)]
        if not coords:
            continue
        xs, ys = coords[0::2], coords[1::2]
        dx = 12 - (min(xs) + max(xs)) / 2
        dy = 12 - (min(ys) + max(ys)) / 2
        if abs(dx) < 0.05 and abs(dy) < 0.05:
            continue

        def shift(d):
            vals = iter(num.findall(d))
            out, i = [], 0
            for tok in re.split(r"(-?\d*\.?\d+)", d):
                if num.fullmatch(tok or "x"):
                    out.append(_n(float(tok) + (dx if i % 2 == 0 else dy)))
                    i += 1
                else:
                    out.append(tok)
            return "".join(out)
        if ICON_PATHS.get(name):
            ICON_PATHS[name] = shift(ICON_PATHS[name])
        if ICON_FILLS.get(name):
            ICON_FILLS[name] = shift(ICON_FILLS[name])
        if ICON_CUTS.get(name):
            ICON_CUTS[name] = shift(ICON_CUTS[name])


# Pixel-art cheese wedge (30x19): light from the top-left, holes with lit
# lower-right rims, a darker cut end, a dark-brown outline.
CHEESE_PIXELS = [
    "..........................ooo.",
    "........................ootsso",
    ".....................ooottssso",
    "..................oooTTTssssso",
    "...............oootTThhhssssso",
    ".............ootTTThhYYYssDsso",
    "..........oooWTThhhYYYYYsDdsso",
    ".......oooTWThhhYYDYYYYYsDdsso",
    ".....ootTThhhYYYYDddYYYYssssso",
    "...ooTTThhYYYYYYYYhhYYYYssssso",
    "..oTThhhYYYDDDYYYYYYYYYYsssDso",
    ".ohhhYYYYYDDDddYhYYYYYYYssDdso",
    "ohYYYYYYYYDDdddhhYYYYYYYsssdso",
    "oYYYYDDYYYYddddhYYDDDYYYSSSSSo",
    "oYYYDDddhYYYhhhYYYDDdhYYSSSSSo",
    "oYYYDdddhYYYYYYYYYdddhYYSSSSo.",
    "oyyyyddhyyyyyyyyyyyhhyyySSoo..",
    "oyyyyyyyyyDdhyyyyyyyyyyySo....",
    ".oooooooooooooooooooooooo.....",
]
CHEESE_PALETTE = {
    "o": "#4a2c0a",   # outline
    "t": "#ffe07a",   # top face
    "T": "#fff0b0",   # top face, front-edge light
    "W": "#ffffff",   # glint
    "h": "#ffe68e",   # highlight (edges, hole rims)
    "Y": "#f6c440",   # front face
    "y": "#e3aa2a",   # front face, base shadow
    "s": "#e0a127",   # cut end
    "S": "#c98a1a",   # cut end, shadow
    "d": "#b07812",   # hole
    "D": "#7a4e08",   # hole, deep shadow
}


# Prone's silhouette, traced from the classic Family Guy fall (Peter face
# down, rump up, one arm flopped over his back) and smoothed.
_PETER_FALL = (
    "M 15.08 5.29 Q 15.33 5.19 15.99 5.34 Q 16.64 5.49 17.05 5.89 Q 17.45 6.30 17.85 7.05 Q 18.26 7.8"
    "1 18.41 8.57 Q 18.56 9.33 19.97 10.08 Q 21.39 10.84 21.79 11.24 Q 22.19 11.65 22.50 12.30 Q 22.8"
    "0 12.96 22.75 13.31 Q 22.70 13.67 22.50 13.87 Q 22.30 14.07 22.14 14.57 Q 21.99 15.08 21.89 15.0"
    "3 Q 21.79 14.98 21.69 15.08 Q 21.59 15.18 21.69 15.48 Q 21.79 15.79 21.34 15.84 Q 20.88 15.89 20"
    ".63 15.68 Q 20.38 15.48 20.13 15.68 Q 19.87 15.89 19.27 15.89 Q 18.66 15.89 18.66 16.49 Q 18.66 "
    "17.10 18.26 17.50 Q 17.85 17.90 17.35 18.01 Q 16.84 18.11 15.94 18.01 Q 15.03 17.90 14.78 18.01 "
    "Q 14.52 18.11 14.17 18.46 Q 13.82 18.81 13.61 18.81 Q 13.41 18.81 13.36 18.51 Q 13.31 18.21 12.9"
    "1 18.21 Q 12.50 18.21 12.71 17.90 Q 12.91 17.60 12.66 17.60 Q 12.40 17.60 12.25 17.50 Q 12.10 17"
    ".40 12.15 17.20 Q 12.20 17.00 12.66 16.74 Q 13.11 16.49 12.91 16.34 Q 12.71 16.19 11.85 16.29 Q "
    "10.99 16.39 10.18 16.09 Q 9.38 15.79 9.07 16.09 Q 8.77 16.39 8.21 16.69 Q 7.66 17.00 7.31 17.10 "
    "Q 6.95 17.20 6.20 17.20 Q 5.44 17.20 5.14 17.05 Q 4.83 16.90 4.63 16.59 Q 4.43 16.29 4.43 15.63 "
    "Q 4.43 14.98 3.98 15.03 Q 3.52 15.08 3.32 15.28 Q 3.12 15.48 2.71 15.63 Q 2.31 15.79 1.91 15.63 "
    "Q 1.50 15.48 1.35 14.93 Q 1.20 14.37 1.20 13.82 Q 1.20 13.26 1.35 12.50 Q 1.50 11.75 1.70 11.34 "
    "Q 1.91 10.94 3.07 10.79 Q 4.23 10.64 5.09 10.39 Q 5.94 10.13 6.40 9.88 Q 6.85 9.63 7.16 9.22 Q 7"
    ".46 8.82 8.27 8.11 Q 9.07 7.41 9.68 7.16 Q 10.28 6.90 11.24 6.80 Q 12.20 6.70 12.66 6.50 Q 13.11"
    " 6.30 13.56 6.30 Q 14.02 6.30 14.42 5.84 Q 14.83 5.39 15.08 5.29 Z"
)

_FRIGHT = (
    "M 10.69 2.62 Q 11.43 2.47 11.75 2.43 Q 12.06 2.39 12.41 2.43 Q 12.76 2.46 13.25 2.63 Q 13.74 2.7"
    "9 14.21 3.04 Q 14.68 3.28 15.08 3.62 Q 15.47 3.95 15.70 4.45 Q 15.93 4.95 16.07 5.12 Q 16.22 5.2"
    "9 16.86 5.68 Q 17.49 6.07 18.74 6.65 Q 19.99 7.24 20.43 7.50 Q 20.87 7.76 21.64 8.50 Q 22.40 9.2"
    "4 22.54 9.44 Q 22.69 9.64 22.76 9.82 Q 22.83 10.00 22.85 10.57 Q 22.86 11.13 22.77 11.38 Q 22.69"
    " 11.63 22.53 11.87 Q 22.37 12.10 21.70 12.83 Q 21.03 13.57 20.76 13.75 Q 20.49 13.94 19.69 14.33"
    " Q 18.89 14.72 18.70 14.88 Q 18.51 15.03 18.39 15.20 Q 18.26 15.37 18.17 15.62 Q 18.08 15.87 18."
    "00 16.41 Q 17.91 16.94 17.65 17.81 Q 17.39 18.68 17.35 19.42 Q 17.30 20.16 17.21 20.74 Q 17.12 2"
    "1.32 17.03 21.51 Q 16.93 21.69 16.76 21.79 Q 16.60 21.88 15.25 21.98 Q 13.89 22.08 12.51 22.01 Q"
    " 11.12 21.94 9.58 21.93 Q 8.05 21.91 7.83 21.85 Q 7.60 21.78 7.50 21.68 Q 7.39 21.57 7.33 21.43 "
    "Q 7.27 21.30 7.12 20.60 Q 6.98 19.91 6.78 19.25 Q 6.59 18.58 6.43 17.57 Q 6.28 16.56 6.19 16.26 "
    "Q 6.09 15.96 5.88 15.52 Q 5.66 15.08 5.56 14.94 Q 5.45 14.80 5.29 14.68 Q 5.14 14.56 4.49 14.36 "
    "Q 3.84 14.16 3.09 13.68 Q 2.34 13.20 1.98 12.85 Q 1.63 12.51 1.45 12.14 Q 1.27 11.76 1.25 11.38 "
    "Q 1.22 11.01 1.31 10.63 Q 1.40 10.25 1.68 9.79 Q 1.96 9.33 2.32 8.91 Q 2.68 8.49 3.03 8.24 Q 3.3"
    "8 7.98 4.26 7.57 Q 5.15 7.16 6.07 6.57 Q 6.98 5.98 7.20 5.72 Q 7.41 5.46 7.58 5.06 Q 7.75 4.66 7"
    ".89 4.41 Q 8.04 4.17 8.53 3.74 Q 9.01 3.31 9.48 3.04 Q 9.95 2.77 10.69 2.62 Z M 15.46 7.47 Q 15."
    "36 7.51 15.29 7.60 Q 15.22 7.68 14.82 8.54 Q 14.41 9.39 14.38 9.60 Q 14.35 9.80 14.43 9.97 Q 14."
    "52 10.14 14.93 10.32 Q 15.35 10.50 15.57 10.53 Q 15.78 10.57 16.39 10.44 Q 16.99 10.31 17.63 10."
    "25 Q 18.27 10.19 18.38 10.15 Q 18.49 10.11 18.50 10.04 Q 18.50 9.96 18.43 9.85 Q 18.36 9.74 17.7"
    "0 8.97 Q 17.03 8.21 16.57 7.87 Q 16.11 7.53 15.97 7.47 Q 15.83 7.42 15.69 7.42 Q 15.56 7.42 15.4"
    "6 7.47 Z M 8.13 7.83 Q 7.85 7.95 7.27 8.42 Q 6.69 8.90 6.31 9.35 Q 5.93 9.81 5.89 9.92 Q 5.85 10"
    ".04 5.89 10.13 Q 5.92 10.22 6.03 10.28 Q 6.14 10.34 6.31 10.37 Q 6.48 10.40 7.08 10.36 Q 7.68 10"
    ".33 8.10 10.35 Q 8.53 10.38 8.86 10.34 Q 9.19 10.31 9.34 10.22 Q 9.49 10.14 9.56 10.02 Q 9.62 9."
    "90 9.61 9.77 Q 9.61 9.64 9.36 9.00 Q 9.11 8.36 8.96 8.10 Q 8.80 7.85 8.71 7.80 Q 8.62 7.74 8.52 "
    "7.73 Q 8.41 7.72 8.13 7.83 Z M 9.7 10.9 C 10.1 13.8 13.9 13.8 14.3 10.9 L 14.2 10.35 C 13.8 12.9"
    " 10.2 12.9 9.8 10.35 Z"
)

# Solid parts, filled (and edged with the stroke) in the same colour.
_SPARKLE_SMALL = sparkle(18, 5.5, 2.6, 2.8)
ICON_FILLS = {
    "star_solid": star(12, 12.6, 10.1, 4.6),
    "cond_blinded": circle(12, 12, 2.9),
    # Charmed: hearts floating up, big to small
    "cond_charmed": _join(heart(8.66, 15.05, 0.693, -12), heart(17.83, 7.44, 0.425, 14), heart(19.84, 18.63, 0.246, 20)),
    # Frightened: someone clutching their head and screaming -- outline
    # hand-drawn over a photo, the gaps between arms and head kept open
    "cond_frightened": _FRIGHT,
    "cond_surprised": _join(circle(8.4, 13.6, 0.85), circle(15.6, 13.6, 0.85)),
    "cond_paralyzed": circle(9.6, 16.6, 1.7),
    "cond_prone": _PETER_FALL,
    "cond_petrified": rrect(5, 20.2, 14, 2.2, 0.4),
    "cond_poisoned": _join(circle(10, 15.6, 1.7), circle(14.2, 12.4, 1.1), circle(13.6, 17.6, 0.9)),

    "cond_stunned": _join(_bird(15.6, 11.6, 1.0), _bird(8.6, 5.6, 0.85, flip=True)),
    "cond_restrained": _join(*[capsule(12 + t * 0.7071, 12 - t * 0.7071, 8.4, 2.5, -45) for t in (-2.8, 8.4)]),
    # a figure traced in dots -- there, but not quite
    "cond_invisible": _join(*[circle(12 + 3.7 * math.cos(math.radians(a)), 7.6 + 3.7 * math.sin(math.radians(a)), 0.95)
                              for a in range(-90, 270, 45)],
                            *[circle(12 + 7.4 * math.cos(math.radians(a)), 20.6 + 6.8 * math.sin(math.radians(a)), 0.95)
                              for a in range(180, 361, 30)]),
    # pupils peeking out from under the drooping lids
    "cond_exhaustion": _join(*[arc(x, 9.4, 1.8, 1.8, 0, 180) + " Z" for x in (6.6, 17.4)]),
    # filled radar polygon: this character's (illustrative) scores
    "abilities": poly(*_hex_pts(12, 12.4, [6.4, 5.8, 3.6, 5.2, 3.7, 6.1])),
    # proficient, not, proficient
    "skills": _join(circle(5.6, 6, 2.3), circle(5.6, 18, 2.3)),
    "spells": sparkle(17.4, 6.6, 4.2, 4.5),
    "infusions": _join(sparkle(13.6, 3.7, 2.7, 3.0), sparkle(7.6, 4.4, 1.7, 1.9), sparkle(19.4, 4.6, 1.5, 1.7)),
    "magic": sparkle(18, 5.5, 3.3, 3.6),
    # the liquid, with bubbles in it (holes) and one rising above
    "potion": _join("M 7.3 15 L 16.7 15 L 19.1 18.6 Q 19.9 20.5 17.8 20.5 L 6.2 20.5 Q 4.1 20.5 4.9 18.6 Z",
                    hole(9.6, 18, 0.95), hole(13.4, 17.4, 0.75), hole(15.4, 19.2, 0.6), circle(12.4, 12.2, 0.85)),
    "paw": _join(ellipse(12, 16.4, 4.05, 3.45), ellipse(5.9, 10.9, 1.9, 2.3), ellipse(9.4, 7, 1.9, 2.35),
                 ellipse(14.6, 7, 1.9, 2.35), ellipse(18.1, 10.9, 1.9, 2.3)),
    "info": circle(12, 7.3, 1.4),
    "skull": _join(circle(9, 10.8, 2.3), circle(15, 10.8, 2.3)),
    "bolt": poly((13.9, 2.4), (5.6, 14), (11.2, 14), (10.1, 21.6), (18.4, 10), (12.8, 10)),
    "passive": _join(circle(8, 12, 1.45), circle(12, 12, 1.45), circle(16, 12, 1.45)),
    "effects": circle(12, 12, 3.7),
    "wagon": _join(circle(8, 18, 1.2), circle(16, 18, 1.2)),
    "dagger": circle(12, 20.2, 2.1),
    "ammo": poly((19.8, 4.2), (17.9, 11.2), (12.8, 6.1)),
    "long_rest": _moon_solid(),
    "inspiration": sparkle(12, 10, 3.0, 3.5),
    "experience": star(12, 15.3, 3.5, 1.6),
    "identity": circle(8.5, 9.9, 2.2),
    "toolkit": rrect(10.4, 12.2, 3.2, 3, 0.7),
    # a small candle flame in the glass, as a thin outline (see _outline)
    "lantern": _outline(_SMALL_FLAME),
    "medkit": poly((10.6, 9.6), (13.4, 9.6), (13.4, 12.6), (16.4, 12.6), (16.4, 15.4), (13.4, 15.4),
                   (13.4, 18.4), (10.6, 18.4), (10.6, 15.4), (7.6, 15.4), (7.6, 12.6), (10.6, 12.6)),
    "instrument": _xf_path(circle(-2.8, 0, 1.7), 11.2, 12.8, -45),
    "flame": "M 12.2 11.4 C 13.8 13.4 15.4 14.8 15.2 17.2 C 15 19.2 13.6 20.2 12 20.2 C 10.2 20.2 8.8 19 8.8 17.2 "
             "C 8.8 15.8 9.8 15 10.6 14.2 C 10.8 15.2 11.2 15.8 11.8 16 C 11.4 14.4 11.6 12.8 12.2 11.4 Z",

    "vial": "M 6.5 14.2 Q 9.2 12.8 12 14.2 Q 14.8 15.6 17.5 14.2 Q 17.6 19.1 12 19.1 Q 6.4 19.1 6.5 14.2 Z",
}


# Lines carved OUT of an icon after it's drawn (erased, CUT_WIDTH wide) --
# the detail inside a solid silhouette.
CUT_WIDTH = 0.8
CUT_WIDTHS = {"cond_frightened": 0.5}      # per-icon overrides: fainter lines
ICON_CUTS = {
    # faint lines (hand-drawn over the photo): the hands' edges, the elbow
    # creases and the sleeve hems; the neck is a crescent cut out of _FRIGHT
    "cond_frightened": _join("M 9.09 7.66 Q 9.44 5.10 9.41 4.71 Q 9.38 4.31 9.30 4.15 Q 9.22 3.99 9.25 3.88 Q 9.28 3.77 9.49 3.63 Q 9.69 3.49 9.79 3.02",
                             "M 13.48 3.05 Q 13.36 3.17 13.37 3.28 Q 13.39 3.39 13.71 3.52 Q 14.02 3.65 14.02 4.06 Q 14.02 4.47 14.12 4.91 Q 14.21 5.35 14.32 5.57 Q 14.43 5.79 14.78 6.28 Q 15.13 6.77 15.51 6.96",
                             "M 5.37 10.22 Q 5.05 10.94 4.85 11.19 Q 4.64 11.45 4.26 11.64",
                             "M 20.87 11.67  Q 20.21 11.54 19.48 10.78",
                             "M 4.39 14.19 Q 5.27 14.10 5.81 13.58 Q 6.35 13.06 6.47 12.49 Q 6.60 11.92 6.19 11.16",
                             "M 5.53 10.50  Q 5.65 10.75 6.13 11.13",
                             "M 19.39 14.26 Q 19.01 14.19 18.66 13.85 Q 18.32 13.50 17.95 12.90 Q 17.59 12.30 17.64 11.92 Q 17.68 11.54 17.78 11.37 Q 17.87 11.19 18.21 10.82 Q 18.54 10.44 18.88 10.41",
                             "M 19.04 10.25 L 19.33 10.66"),
    "cond_prone": _join(
        "M 14.73 5.89 Q 15.13 5.69 15.53 5.74 Q 15.94 5.79 16.29 6.04 Q 16.64 6.30 16.79 6.65 Q 16.95 7.00 16.84 7.61 Q 16.74 8.21 15.89 8.92 Q 15.03 9.63 15.18 9.93 Q 15.33 10.23 15.28 10.44 Q 15.23 10.64 14.88 10.54 Q 14.52 10.44 14.17 10.89 Q 13.82 11.34 13.61 11.39 Q 13.41 11.44 13.31 11.14 Q 13.21 10.84 12.86 10.94 Q 12.50 11.04 12.40 10.94 Q 12.30 10.84 12.35 10.64 Q 12.40 10.44 12.10 10.33 Q 11.80 10.23 11.80 10.08 Q 11.80 9.93 12.15 9.68 Q 12.50 9.43 12.61 9.12 Q 12.71 8.82 12.96 8.62 Q 13.21 8.42 14.02 6.50",
        "M 12.71 15.99 Q 12.81 15.68 13.56 15.79 Q 14.32 15.89 15.03 15.58 Q 15.73 15.28 16.39 15.28 Q 17.05 15.28 17.55 15.73 Q 18.06 16.19 18.06 16.74 Q 18.06 17.30 17.85 17.50",
        "M 18.46 15.68 Q 17.15 14.17 17.15 13.67 Q 17.15 13.16 17.45 12.15 Q 17.75 11.14 18.66 9.73",
        "M 11.80 7.00 Q 10.69 7.51 10.28 7.91 Q 9.88 8.32 9.68 8.62 Q 9.48 8.92 9.68 9.02 Q 9.88 9.12 9.83 9.33 Q 9.78 9.53 9.53 9.58 Q 9.27 9.63 9.12 9.83 Q 8.97 10.03 8.82 10.64 Q 8.67 11.24 8.67 11.95 Q 8.67 12.66 8.82 12.76 Q 8.97 12.86 8.97 13.16 Q 8.97 13.46 8.87 13.51 Q 8.77 13.56 8.87 13.82 Q 8.97 14.07 8.21 13.87 Q 7.46 13.67 7.00 13.72 Q 6.55 13.77 5.79 14.07 Q 5.04 14.37 4.73 14.78",
        "M 4.73 14.78 Q 5.94 13.97 6.80 13.87 Q 7.66 13.77 8.32 13.92 Q 8.97 14.07 9.17 14.42 Q 9.38 14.78 9.48 15.58",
        "M 3.42 14.88  Q 2.61 12.86 2.71 11.04"),
}


_center_icons()


# ── Android export ──────────────────────────────────────────────────────
# The Android UI reads the same artwork from a generated QML JavaScript
# library (QML can't import Python modules). Regenerated by
# installer/android/clean_build_android.sh before every build, and by
# hand with:  python3 -m dnd_app.ui_desktop.icon_data
QML_JS_PATH = "dnd_app/ui_android/qml/imports/Mimic/IconData.js"


def qml_js() -> str:
    import json
    return (
        "// GENERATED from dnd_app/ui_desktop/icon_data.py -- do not edit by hand.\n"
        "// Regenerate: python3 -m dnd_app.ui_desktop.icon_data\n"
        ".pragma library\n\n"
        f"var stroke = {STROKE};\n"
        f"var paths = {json.dumps(ICON_PATHS, indent=1, sort_keys=True)};\n"
        f"var fills = {json.dumps(ICON_FILLS, indent=1, sort_keys=True)};\n"
        f"var cutWidth = {CUT_WIDTH};\n"
        f"var cutWidths = {json.dumps(CUT_WIDTHS, sort_keys=True)};\n"
        f"var cuts = {json.dumps(ICON_CUTS, indent=1, sort_keys=True)};\n"
        f"var cheese = {json.dumps(CHEESE_PIXELS, indent=1)};\n"
        f"var cheesePalette = {json.dumps(CHEESE_PALETTE, indent=1, sort_keys=True)};\n"
    )


if __name__ == "__main__":
    import os
    import sys
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = os.path.join(root, QML_JS_PATH)
    new = qml_js()
    old = open(out, encoding="utf-8").read() if os.path.exists(out) else None
    if old != new:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(new)
        print(f"wrote {QML_JS_PATH}")
    else:
        print(f"{QML_JS_PATH} up to date")
    sys.exit(0)
