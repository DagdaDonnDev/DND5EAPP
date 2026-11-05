"""D&D 5e condition definitions with full mechanical text. "icon" names a
line icon from dnd_app/data/icon_data.py (ICON_PATHS); "summary" is what
the condition does to you, in a line, for the sheet's condition rows (the
full text is in "effects").

Author: Ethan O'Brien
Date: 2026-08-20
"""

CONDITIONS = {
    "Blinded": {
        "icon": "cond_blinded",
        "color": "#888",
        "effects": [
            "A blinded creature can't see and automatically fails any ability check that requires sight.",
            "Attack rolls against the creature have advantage.",
            "The creature's attack rolls have disadvantage.",
        ],
        "source": "PHB p.290",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You can't see, and fail any check that needs sight. Your attacks have disadvantage; attacks against you have advantage.",
    },
    "Charmed": {
        "icon": "cond_charmed",
        "color": "#d4a0d4",
        "effects": [
            "A charmed creature can't attack the charmer or target the charmer with harmful abilities or magical effects.",
            "The charmer has advantage on any ability check to interact socially with the creature.",
        ],
        "source": "PHB p.290",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You can't attack the charmer or target it with harmful abilities or magic. It has advantage on social checks with you.",
    },
    "Deafened": {
        "icon": "cond_deafened",
        "color": "#888",
        "effects": [
            "A deafened creature can't hear and automatically fails any ability check that requires hearing.",
        ],
        "source": "PHB p.290",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You can't hear, and fail any check that needs hearing.",
    },
    "Frightened": {
        "icon": "cond_frightened",
        "color": "#e67e22",
        "effects": [
            "A frightened creature has disadvantage on ability checks and attack rolls while the source of its fear is within line of sight.",
            "The creature can't willingly move closer to the source of its fear.",
        ],
        "source": "PHB p.290",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "Disadvantage on checks and attacks while you can see its source, and you can't willingly move closer to it.",
    },
    "Gagged": {
        "icon": "cond_gagged",
        "color": "#8a6d3b",
        "effects": [
            "A gagged creature can't speak and automatically fails any check or effect that requires speaking.",
            "Spells requiring a verbal component can't be cast.",
        ],
        "source": "Homebrew — not an official condition; pairs with the "
                   "\"Component Restrictions\" optional rule.",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You can't speak: no spells with a verbal component, and anything that needs speech fails.",
    },
    "Grappled": {
        "icon": "cond_grappled",
        "color": "#c9921a",
        "effects": [
            "A grappled creature's speed becomes 0, and it can't benefit from any bonus to its speed.",
            "The condition ends if the grappler is incapacitated.",
            "The condition also ends if an effect removes the grappled creature from the reach of the grappler or grappling effect.",
        ],
        "source": "PHB p.290",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "Your speed is 0. It ends if the grappler is incapacitated, or something moves you out of its reach.",
    },
    "Incapacitated": {
        "icon": "cond_incapacitated",
        "color": "#c0392b",
        "effects": [
            "An incapacitated creature can't take actions or reactions.",
        ],
        "source": "PHB p.290",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You can't take actions or reactions.",
    },
    "Invisible": {
        "icon": "cond_invisible",
        "color": "#7b9aff",
        "effects": [
            "An invisible creature is impossible to see without the aid of magic or a special sense.",
            "For the purpose of hiding, the creature is heavily obscured. The creature's location can be detected by noise or tracks it leaves.",
            "Attack rolls against the creature have disadvantage.",
            "The creature's attack rolls have advantage.",
        ],
        "source": "PHB p.291",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You can't be seen without magic or a special sense. Your attacks have advantage; attacks against you have disadvantage.",
    },
    "Paralyzed": {
        "icon": "cond_paralyzed",
        "color": "#e74c3c",
        "effects": [
            "A paralyzed creature is incapacitated and can't move or speak.",
            "The creature automatically fails STR and DEX saving throws.",
            "Attack rolls against the creature have advantage.",
            "Any attack that hits the creature is a critical hit if the attacker is within 5 feet.",
        ],
        "source": "PHB p.291",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You're incapacitated and can't move or speak. You fail STR and DEX saves. Attacks against you have advantage, and a hit from within 5 ft is a critical hit.",
    },
    "Petrified": {
        "icon": "cond_petrified",
        "color": "#888",
        "effects": [
            "A petrified creature is transformed into a solid inanimate substance (usually stone).",
            "Its weight increases by a factor of ten, and it ceases aging.",
            "The creature is incapacitated, can't move or speak, and is unaware of its surroundings.",
            "Attack rolls against the creature have advantage.",
            "The creature automatically fails STR and DEX saving throws.",
            "The creature has resistance to all damage.",
            "Immune to poison and disease, but doesn't neutralize existing effects.",
        ],
        "source": "PHB p.291",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "Turned to stone: incapacitated, can't move or speak, unaware. You fail STR and DEX saves, resist all damage, and are immune to poison and disease. Attacks against you have advantage.",
    },
    "Poisoned": {
        "icon": "cond_poisoned",
        "color": "#27ae60",
        "effects": [
            "A poisoned creature has disadvantage on attack rolls and ability checks.",
        ],
        "source": "PHB p.292",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "Disadvantage on attack rolls and ability checks.",
    },
    "Prone": {
        "icon": "cond_prone",
        "color": "#c9921a",
        "effects": [
            "A prone creature's only movement option is to crawl, unless it stands up (costs half movement speed).",
            "The creature has disadvantage on attack rolls.",
            "Attack rolls against the creature have advantage if the attacker is within 5 feet; otherwise, disadvantage.",
        ],
        "source": "PHB p.292",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You can only crawl, or stand up for half your speed. Your attacks have disadvantage. Attacks against you have advantage within 5 ft, disadvantage beyond.",
    },
    "Restrained": {
        "icon": "cond_restrained",
        "color": "#e67e22",
        "effects": [
            "A restrained creature's speed becomes 0, and it can't benefit from any bonus to its speed.",
            "Attack rolls against the creature have advantage.",
            "The creature's attack rolls have disadvantage.",
            "The creature has disadvantage on DEX saving throws.",
        ],
        "source": "PHB p.292",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "Your speed is 0. Your attacks and DEX saves have disadvantage; attacks against you have advantage.",
    },
    "Stunned": {
        "icon": "cond_stunned",
        "color": "#e74c3c",
        "effects": [
            "A stunned creature is incapacitated, can't move, and can speak only falteringly.",
            "The creature automatically fails STR and DEX saving throws.",
            "Attack rolls against the creature have advantage.",
        ],
        "source": "PHB p.292",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You're incapacitated, can't move, and can speak only falteringly. You fail STR and DEX saves. Attacks against you have advantage.",
    },
    "Surprised": {
        "icon": "cond_surprised",
        "color": "#f1c40f",
        "effects": [
            "A surprised creature can't move or take an action on its first turn of the combat.",
            "It can't take a reaction until that turn ends. Remove this once your first turn is over.",
        ],
        "source": "PHB p.189 (Surprise) -- tracked here as a condition.",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "On your first turn you can't move or take an action, and you can't take a reaction until that turn ends.",
    },
    "Unconscious": {
        "icon": "cond_unconscious",
        "color": "#888",
        "effects": [
            "An unconscious creature is incapacitated, can't move or speak, and is unaware of its surroundings.",
            "The creature drops whatever it's holding and falls prone.",
            "The creature automatically fails STR and DEX saving throws.",
            "Attack rolls against the creature have advantage.",
            "Any attack that hits the creature is a critical hit if the attacker is within 5 feet.",
        ],
        "source": "PHB p.292",
        # what it does to you, in a line (the sheet's condition rows)
        "summary": "You're incapacitated, can't move or speak, and are unaware; you drop what you're holding and fall prone. You fail STR and DEX saves. Attacks against you have advantage, and a hit from within 5 ft is a critical hit.",
    },
    "Exhaustion": {
        "icon": "cond_exhaustion",
        "color": "#d68910",
        "levels": [
            "Level 1: Disadvantage on ability checks.",
            "Level 2: Speed halved.",
            "Level 3: Disadvantage on attack rolls and saving throws.",
            "Level 4: Hit point maximum halved.",
            "Level 5: Speed reduced to 0.",
            "Level 6: Death.",
        ],
        "effects": [
            "Exhaustion is cumulative. Each long rest removes one level.",
            "Finishing a long rest reduces exhaustion level by 1, provided you have eaten and drunk.",
        ],
        "source": "PHB p.291",
    },
}

def get_condition(name: str) -> dict:
    return CONDITIONS.get(name, {
        "effects": [f"No mechanical description found for '{name}'."],
        "source": "",
        "color": "#888",
    })
