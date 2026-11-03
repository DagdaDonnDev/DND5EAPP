"""The project README, as both apps' Credits screens show it.

README.md is written for GitHub: a centred logo, badges, screenshots and
collapsible sections. Qt's Markdown viewer can't show those -- images
don't load offline, and an HTML block swallows the text after it -- so
the apps show a plain-Markdown copy:
  1. anything between <!-- github-only --> and <!-- /github-only --> goes
  2. a collapsible section's summary becomes a ### heading, with its
     content shown underneath
  3. HTML headings and bold become Markdown ones; any other tag and every
     image goes, keeping the text around it
  4. a link to another file in the repo becomes its plain text, since
     that file isn't there to open (web links stay clickable)
"""
import os
import re
import sys

_FALLBACK = (
    "# MIMIC\n\nA complete D&D 5e character creator and character sheet.\n\n"
    "Created by Ethan O'Brien.\n\nThank you for downloading MIMIC, and for "
    "supporting the project.\n\n(The full README.md could not be found "
    "alongside this build.)\n"
)


def _candidates() -> list:
    """Where README.md can be: next to a frozen desktop build, at the repo
    root when running from source, or next to the Android app's main.py
    (the clean build stages it there)."""
    out = []
    if getattr(sys, "frozen", False):
        out.append(os.path.join(getattr(sys, "_MEIPASS", ""), "README.md"))
        out.append(os.path.join(os.path.dirname(sys.executable), "README.md"))
    # dnd_app/core/readme.py -> core -> dnd_app -> repo root
    out.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "README.md"))
    main_mod = sys.modules.get("__main__")
    if getattr(main_mod, "__file__", None):
        out.append(os.path.join(os.path.dirname(os.path.abspath(main_mod.__file__)), "README.md"))
    out.append(os.path.join(os.getcwd(), "README.md"))
    return out


def readme_source() -> str:
    """README.md as written, or a short fallback if it can't be found."""
    for path in _candidates():
        if path and os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except OSError:
                continue
    return _FALLBACK


def for_app(text: str) -> str:
    """The README with its GitHub-only parts turned into plain Markdown."""
    text = re.sub(r"<!--\s*github-only\s*-->.*?<!--\s*/github-only\s*-->", "", text, flags=re.S)
    text = re.sub(r"<details[^>]*>\s*<summary>(.*?)</summary>",
                  lambda m: "### " + re.sub(r"<[^>]+>", "", m.group(1)).strip(), text, flags=re.S)
    text = re.sub(r"</details>", "", text)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"<h([1-6])[^>]*>(.*?)</h\1>",
                  lambda m: "#" * int(m.group(1)) + " " + m.group(2).strip(), text, flags=re.S)
    text = re.sub(r"<(?:b|strong)>(.*?)</(?:b|strong)>", r"**\1**", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)       # images
    text = re.sub(r"\[([^\]]+)\]\((?!https?:)[^)]*\)", r"\1", text)   # links to repo files
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)           # any other tag
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def readme_text() -> str:
    """What the Credits screens show."""
    return for_app(readme_source())
