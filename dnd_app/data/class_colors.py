"""One colour per class -- used for the class cards in the sheet header.

The colours players associate with each class (Wizard blue, Cleric
white, Rogue black...).

Shown as a card's border, left stripe and tint -- never as the text
colour, since several (Rogue's black, Blood Hunter's crimson, Cleric's
white on a light theme) would be unreadable as text. A colour too close
to the theme's background also gets a neutral outline: see
needs_outline().
"""

CLASS_COLORS = {
    "Artificer":    "#b5933f",   # brass
    "Barbarian":    "#d93a3a",   # red
    "Bard":         "#f48fb8",   # pink -- light and soft, apart from Sorcerer's raspberry
    "Blood Hunter": "#7d0f24",   # deep crimson
    "Cleric":       "#f2f0e8",   # white
    "Druid":        "#4caf50",   # green
    "Fighter":      "#8b5a2b",   # brown
    "Monk":         "#f08a24",   # orange
    "Paladin":      "#e0b030",   # gold
    "Ranger":       "#24502f",   # deep, gloomy forest green
    "Rogue":        "#1b1b1e",   # black
    "Sorcerer":     "#d0306f",   # raspberry -- a red, but apart from Barbarian's
    "Warlock":      "#8b45c4",   # purple
    "Wizard":       "#3f86e8",   # blue
}

FALLBACK_COLOR = "#8f8da8"   # a homebrew or unknown class


def class_color(class_name: str) -> str:
    return CLASS_COLORS.get(class_name, FALLBACK_COLOR)


def _luminance(hex_colour: str) -> float:
    """Relative luminance (0 black .. 1 white), as WCAG defines it."""
    h = hex_colour.lstrip("#")[:6]
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = out
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def needs_outline(colour: str, background: str) -> bool:
    """True when `colour` would all but vanish against `background` -- a
    contrast ratio under 1.6 (Rogue's black on a dark theme, Cleric's
    white on a light one), so the card needs a neutral outline too."""
    a, b = _luminance(colour), _luminance(background)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05) < 1.6
