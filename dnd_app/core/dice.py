"""Dice expressions, for both apps' Dice Roller: "2d6 + 1d4 + 3", "d20 - 1",
"4d6kh3" (four d6, keep the highest three; kl for the lowest), with
advantage or disadvantage on a lone d20.

    roll(expr, mode="normal", rng=None) -> result
        {"expr": the expression tidied ("2d6 + 3"), "total", "parts": [{
         "dice": "2d6", "rolls": [3, 5], "kept": [3, 5], "sign": 1}, ...],
         "flat": the numbers added, "nat": 20 or 1 for a lone d20 that came
         up so (else 0), "mode": "advantage"... when it applied, "text": how
         the total was made ("2d6 [3, 5] + 3"), "error": "" or why it can't
         be rolled}
    add_die(expr, sides) -> the expression with one more of that die
        ("2d6 + 3" and a d6: "3d6 + 3"; a d8: "2d6 + 1d8 + 3")
"""
import random
import re

_TERM = re.compile(r"\s*([+-])?\s*(?:(\d*)\s*d\s*(\d+)(?:\s*(kh|kl)\s*(\d+))?|(\d+))\s*", re.I)
MAX_DICE = 100
MAX_SIDES = 1000


def parse(expr: str):
    """[(sign, count, sides, keep, keep_n) or (sign, value)] -- or a string
    saying what's wrong with it (no dice in it, too)."""
    terms = _terms(expr)
    if isinstance(terms, str):
        return terms
    if not any(len(t) == 5 for t in terms):
        return "Pick some dice first."
    return terms


def _terms(expr: str):
    """parse()'s terms, numbers alone allowed ("+ 3")."""
    text = (expr or "").strip()
    if not text:
        return []
    terms, pos = [], 0
    while pos < len(text):
        m = _TERM.match(text, pos)
        if not m or m.end() == pos:
            return f"Can't read “{text[pos:].strip()}”: use dice like 2d6 + 3."
        if terms and not m.group(1):
            return "Put + or − between the parts."
        sign = -1 if m.group(1) == "-" else 1
        if m.group(3):
            count = int(m.group(2) or 1)
            sides = int(m.group(3))
            if not 1 <= count <= MAX_DICE:
                return f"Up to {MAX_DICE} dice at a time."
            if not 2 <= sides <= MAX_SIDES:
                return "A die has 2 to 1000 sides."
            keep = (m.group(4) or "").lower()
            keep_n = int(m.group(5)) if m.group(5) else 0
            if keep and not 1 <= keep_n <= count:
                return f"Keep between 1 and {count} of {count}d{sides}."
            terms.append((sign, count, sides, keep, keep_n))
        else:
            terms.append((sign, int(m.group(6))))
        pos = m.end()
    return terms


def _tidy(terms) -> str:
    out = []
    for i, t in enumerate(terms):
        sign = "−" if t[0] < 0 else "+"
        body = (f"{t[1]}d{t[2]}" + (f"{t[3]}{t[4]}" if t[3] else "")) if len(t) == 5 else str(t[1])
        out.append(body if i == 0 and t[0] > 0 else (f"{sign} {body}" if i else f"−{body}"))
    return " ".join(out)


def roll(expr: str, mode: str = "normal", rng=None) -> dict:
    rng = rng or random
    terms = parse(expr)
    if isinstance(terms, str):
        return {"expr": (expr or "").strip(), "total": None, "parts": [], "flat": 0, "nat": 0,
                "mode": "normal", "text": "", "error": terms}
    dice_terms = [t for t in terms if len(t) == 5]
    lone_d20 = len(dice_terms) == 1 and dice_terms[0][1:3] == (1, 20) and not dice_terms[0][3]
    used_mode = mode if mode in ("advantage", "disadvantage") and lone_d20 else "normal"
    parts, flat, total, text = [], 0, 0, []
    for t in terms:
        if len(t) == 2:
            flat += t[0] * t[1]
            total += t[0] * t[1]
            text.append(("− " if t[0] < 0 else "+ ") + str(t[1]))
            continue
        sign, count, sides, keep, keep_n = t
        if used_mode != "normal":
            rolls = [rng.randint(1, 20), rng.randint(1, 20)]
            kept = [max(rolls) if used_mode == "advantage" else min(rolls)]
        else:
            rolls = [rng.randint(1, sides) for _ in range(count)]
            kept = (sorted(rolls, reverse=keep == "kh")[:keep_n] if keep else list(rolls))
        value = sum(kept)
        total += sign * value
        label = f"{count}d{sides}" + (f"{keep}{keep_n}" if keep else "")
        parts.append({"dice": label, "rolls": rolls, "kept": kept, "sign": sign})
        shown = ", ".join(map(str, rolls))
        if used_mode != "normal":
            piece = f"{label} ({used_mode}: {shown}) {kept[0]}"
        elif keep:
            piece = f"{label} [{shown}, kept {', '.join(map(str, kept))}]"
        else:
            piece = f"{label} [{shown}]" if count > 1 else f"{label} {rolls[0]}"
        text.append(piece if not text and sign > 0 else ("− " if sign < 0 else "+ ") + piece)
    nat = 0
    if lone_d20:
        nat = 20 if parts[0]["kept"][0] == 20 else 1 if parts[0]["kept"][0] == 1 else 0
    return {"expr": _tidy(terms), "total": total, "parts": parts, "flat": flat, "nat": nat,
            "mode": used_mode, "text": " ".join(text), "error": ""}


def add_die(expr: str, sides: int) -> str:
    """One more of that die in the expression (merged with the same die,
    if it's there)."""
    terms = _terms(expr)
    if isinstance(terms, str):          # can't be read: start again
        terms = []
    for i, t in enumerate(terms):
        if len(t) == 5 and t[0] > 0 and t[2] == sides and not t[3]:
            terms[i] = (1, t[1] + 1, sides, "", 0)
            break
    else:
        dice = [t for t in terms if len(t) == 5]
        flats = [t for t in terms if len(t) == 2]
        terms = dice + [(1, 1, sides, "", 0)] + flats
    return _tidy(terms)


def set_modifier(expr: str, modifier: int) -> str:
    """The expression with its numbers replaced by this one (0: none)."""
    terms = _terms(expr)
    terms = [t for t in terms if len(t) == 5] if not isinstance(terms, str) else []
    if modifier:
        terms.append((1 if modifier > 0 else -1, abs(modifier)))
    return _tidy(terms) if terms else ""
