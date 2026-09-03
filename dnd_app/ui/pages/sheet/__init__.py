"""Character Sheet package.

CharacterSheet is composed from per-domain mixins (one file per tab/
concern) rather than living as one 12,000-line class -- see
KNOWN_IMPLEMENTATION_GAPS.md for the reorg this came from. Every mixin
shares one real `self`/QWidget instance, so a method in one file can
freely call `self._build_statblock_card(...)` etc. even though that
method is defined in a different mixin's file; Python resolves it via
the composed class's MRO at runtime, not via imports between the mixin
files themselves.
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal

from .base import BaseSheetMixin
from .abilities import AbilitiesMixin
from .skills import SkillsMixin
from .combat import CombatMixin
from .gear import GearMixin
from .companions import CompanionsMixin
from .choices import ChoicesMixin
from .infusions import InfusionsMixin
from .spells import SpellsMixin
from .features import FeaturesMixin
from .traits import TraitsNotesMixin
from .action_tabs import ActionTabsMixin


class CharacterSheet(
    BaseSheetMixin, AbilitiesMixin, SkillsMixin, CombatMixin, GearMixin,
    CompanionsMixin, ChoicesMixin, InfusionsMixin, SpellsMixin,
    FeaturesMixin, TraitsNotesMixin, ActionTabsMixin, QWidget,
):
    """Main PySide6 widget shown after character creation or when loading
    a saved character. See BaseSheetMixin.__init__/_build_ui for the
    actual construction logic -- this class exists only to compose the
    mixins into one real object.

    back_to_menu must live here rather than on BaseSheetMixin: PySide6's
    Signal descriptor is only registered by Qt's metaclass machinery for
    classes that actually derive from QObject at the point the class
    body is processed, which a plain mixin doesn't."""
    back_to_menu = Signal()
