"""Immersive Health and Immersive Exhaustion -- the character sheet showing
how the character is doing, the same way on both apps.

  Immersive Health      colour drains from the sheet as hit points drop:
                        none at full HP, most of it (never all) near 0,
                        and it comes back as they heal.
  Immersive Exhaustion  a dark frame closes in from the edges of the
                        screen, one step per level of exhaustion, and the
                        page shrinks to fit inside it. (Level 6 is death,
                        which has its own screen.)

The numbers are untouched -- the effects only add to what the sheet
already says. Each is a setting, kept with the app's other settings:
  Full     the whole effect; the frame's dark blur reaches into the page
  Reduced  half the colour fade; the frame stays in the page's margin, so
           no text is ever under the darkness
  Off      nothing

Everything here is plain rules and numbers, except render_frame(), which
draws the frame with Qt's QtGui (imported only when it's called, so the
rest of core never needs Qt) -- both apps show the identical frame.
"""

MODES = ("Full", "Reduced", "Off")

# Near 0 HP, 85% of the colour is gone -- never all of it, so the
# colour-coded markers (rarity, the HP bar...) can still be told apart.
MAX_FADE = 0.85

# How far the page moves in from each edge, per exhaustion level 0-5.
_FRAME_PX = {"desktop": (0, 14, 22, 30, 40, 50), "phone": (0, 8, 12, 16, 20, 24)}

# What both apps say about the settings, so they say the same thing.
SETTINGS = {
    "health": ("Immersive Health",
               "Colour drains from the sheet as hit points drop, and comes back as you heal."),
    "exhaustion": ("Immersive Exhaustion",
                   "A dark frame closes in from the edges of the screen with each level of exhaustion."),
}
MODE_HELP = {
    "Full": "The whole effect.",
    "Reduced": "A gentler version: half the colour fade, and the exhaustion frame never covers any text.",
    "Off": "No effect.",
}
PROMPT_TITLE = "Immersive Health & Exhaustion"
PROMPT_TEXT = ("Your sheet now shows how your character is doing: colour drains from it as "
               "hit points drop, and a dark frame closes in with each level of exhaustion. "
               "The numbers stay exactly as they are. You can change these any time in Settings.")
PROMPT_FLAG = "immersive_prompt_seen"


# ── Settings ──────────────────────────────────────────────────────────────
# Read once, then kept in memory (the sheets check them several times a
# second); set_mode() saves the change and updates the copy.
_modes = {}


def mode(kind: str) -> str:
    """The setting for "health" or "exhaustion": "Full", "Reduced" or "Off"."""
    if kind not in _modes:
        from dnd_app.core.app_settings import get_immersive
        _modes[kind] = get_immersive(kind)
    return _modes[kind]


def set_mode(kind: str, value: str) -> None:
    from dnd_app.core.app_settings import set_immersive
    if value in MODES:
        set_immersive(kind, value)
        _modes[kind] = value


def prompt_seen() -> bool:
    """Whether the one-time note about the effects has been shown."""
    if "prompt" not in _modes:
        from dnd_app.core.app_settings import get_flag
        _modes["prompt"] = get_flag(PROMPT_FLAG)
    return _modes["prompt"]


def mark_prompt_seen() -> None:
    from dnd_app.core.app_settings import set_flag
    set_flag(PROMPT_FLAG, True)
    _modes["prompt"] = True


# ── Immersive Health ──────────────────────────────────────────────────────
def shown_hp(char: dict) -> tuple:
    """(current, maximum) hit points as the sheet shows them: a Wild Shape
    form's own pool while in one, the character's otherwise."""
    active = char.get("_wildshape_active")
    if active:
        from dnd_app.data.statblocks import WILDSHAPE_BEASTS
        beast = WILDSHAPE_BEASTS.get(active)
        if beast:
            return char.get("_wildshape_hp", beast["hp"]), beast["hp"]
    return char.get("current_hp", 0), char.get("max_hp", 0)


def health_fade(char: dict, setting: str = None) -> float:
    """How much colour to take away: 0 at full HP, MAX_FADE at 0 HP.
      1. the fraction of hit points left (temp HP doesn't count -- the page
         never gets brighter than normal)
      2. eased (to the power 0.8) so a scratch barely shows and the last few
         hit points count most
      3. halved when the setting is Reduced, nothing when it's Off"""
    setting = setting or mode("health")
    cur, mx = shown_hp(char)
    if setting == "Off" or mx <= 0:
        return 0.0
    left = max(0.0, min(1.0, cur / mx))
    fade = MAX_FADE * (1.0 - left) ** 0.8
    return fade / 2 if setting == "Reduced" else fade


def grey(rgb: tuple, fade: float) -> tuple:
    """A colour with `fade` of its colour taken out -- the same grey Qt's
    desaturation filter uses on desktop (its qGray weights), so both apps
    fade alike. rgb: 0-255 channels."""
    r, g, b = rgb[:3]
    lum = (r * 11 + g * 16 + b * 5) / 32
    return tuple(round(v + (lum - v) * fade) for v in (r, g, b))


# ── Immersive Exhaustion ──────────────────────────────────────────────────
def frame_level(char: dict, setting: str = None) -> int:
    """The exhaustion level the frame shows, 0-5 (0 = no frame)."""
    setting = setting or mode("exhaustion")
    if setting == "Off":
        return 0
    return max(0, min(5, int(char.get("exhaustion", 0) or 0)))


def frame_px(level: int, phone: bool = False) -> int:
    """How far the page moves in from each edge for a frame level."""
    return _FRAME_PX["phone" if phone else "desktop"][max(0, min(5, level))]


def render_frame(width: int, height: int, level: int, setting: str = "Full",
                 phone: bool = False, scale: float = 1.0):
    """The frame for an area `width` x `height` (logical pixels) whose page
    sits frame_px() in from every edge, as a QImage (transparent where the
    page shows through) drawn at `scale` device pixels per logical pixel.
      Full     solid black at the screen edge, the page's corners rounded
               off, and a dark blur reaching well into the page
      Reduced  the same black frame with gentler corners, kept entirely
               outside the page"""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath

    W, H = max(1, round(width * scale)), max(1, round(height * scale))
    out = QImage(W, H, QImage.Format_ARGB32_Premultiplied)
    out.fill(Qt.transparent)
    t = frame_px(level, phone)
    if level <= 0 or setting == "Off" or width <= 2 * t or height <= 2 * t:
        out.setDevicePixelRatio(scale)
        return out

    def blurred(img, radius):
        # A cheap, smooth blur: shrink and grow back, three times.
        k = max(2, int(radius / 2))
        for _ in range(3):
            small = img.scaled(max(1, img.width() // k), max(1, img.height() // k),
                               Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            img = small.scaled(img.width(), img.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        return img

    def outside(rect, r):
        # everything (well past the screen edges) outside a rounded rect
        area = QPainterPath(); area.addRect(QRectF(-3 * t, -3 * t, width + 6 * t, height + 6 * t))
        hole = QPainterPath(); hole.addRoundedRect(rect, r, r)
        return area.subtracted(hole)

    def layer(path):
        img = QImage(W, H, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        p = QPainter(img); p.setRenderHint(QPainter.Antialiasing); p.scale(scale, scale)
        p.fillPath(path, QColor(0, 0, 0))
        p.end()
        return img

    screen = QRectF(0, 0, width, height)
    page = QRectF(t, t, width - 2 * t, height - 2 * t)
    darkness = min(1.0, 0.55 + 0.09 * level)
    p = QPainter(out)

    if setting == "Reduced":
        # 1. gentler corners, pushed out just far enough (0.293 of their
        #    radius) that each curve passes through the page's corner
        r = max(16 if phone else 24, t)
        d = r * 0.293
        mask = layer(outside(page.adjusted(-d, -d, d, d), r))
        # 2. only a light softening, and nothing is drawn over the page
        soft = blurred(mask, t * 0.5 * scale)
        clip = QPainterPath(); clip.addRect(QRectF(0, 0, W, H))       # (device pixels)
        keep_page = QPainterPath()
        keep_page.addRect(QRectF(t * scale, t * scale, (width - 2 * t) * scale, (height - 2 * t) * scale))
        p.setClipPath(clip.subtracted(keep_page))
        p.setOpacity(darkness)
        p.drawImage(0, 0, soft)
        p.drawImage(0, 0, mask)
    else:
        # 1. everything outside the rounded page is black
        r = max(16 if phone else 24, 2 * t)
        mask = layer(outside(page, r))
        # 2. the dark blur reaching about three frame-widths into the page
        soft = blurred(mask, t * 3.2 * scale)
        # 3. the outer part of the band stays solid black, its inner edge
        #    rounded too
        solid = layer(outside(screen.adjusted(t * 0.55, t * 0.55, -t * 0.55, -t * 0.55), r * 0.8))
        sp = QPainter(soft); sp.drawImage(0, 0, solid); sp.end()
        # 4. the rounded corners as their own, only lightly softened layer
        #    -- the wide blur alone would smooth them back into square ones
        corners = blurred(mask, t * 0.35 * scale)
        # 5. the blur laid down twice for a deeper shade; lighter at low levels
        p.setOpacity(darkness)
        p.drawImage(0, 0, soft)
        p.drawImage(0, 0, soft)
        p.drawImage(0, 0, corners)
    p.end()
    out.setDevicePixelRatio(scale)
    return out
