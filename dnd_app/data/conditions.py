"""D&D 5e condition definitions with full mechanical text.

Author: Ethan O'Brien
Date: 2026-08-20
"""

CONDITIONS = {
    "Blinded": {
        "icon": "👁",
        "color": "#888",
        "effects": [
            "A blinded creature can't see and automatically fails any ability check that requires sight.",
            "Attack rolls against the creature have advantage.",
            "The creature's attack rolls have disadvantage.",
        ],
        "source": "PHB p.290",
    },
    "Charmed": {
        "icon": "💕",
        "color": "#d4a0d4",
        "effects": [
            "A charmed creature can't attack the charmer or target the charmer with harmful abilities or magical effects.",
            "The charmer has advantage on any ability check to interact socially with the creature.",
        ],
        "source": "PHB p.290",
    },
    "Deafened": {
        "icon": "🔇",
        "color": "#888",
        "effects": [
            "A deafened creature can't hear and automatically fails any ability check that requires hearing.",
        ],
        "source": "PHB p.290",
    },
    "Frightened": {
        "icon": "😱",
        "color": "#e67e22",
        "effects": [
            "A frightened creature has disadvantage on ability checks and attack rolls while the source of its fear is within line of sight.",
            "The creature can't willingly move closer to the source of its fear.",
        ],
        "source": "PHB p.290",
    },
    "Grappled": {
        "icon": "🤼",
        "color": "#c9921a",
        "effects": [
            "A grappled creature's speed becomes 0, and it can't benefit from any bonus to its speed.",
            "The condition ends if the grappler is incapacitated.",
            "The condition also ends if an effect removes the grappled creature from the reach of the grappler or grappling effect.",
        ],
        "source": "PHB p.290",
    },
    "Incapacitated": {
        "icon": "💫",
        "color": "#c0392b",
        "effects": [
            "An incapacitated creature can't take actions or reactions.",
        ],
        "source": "PHB p.290",
    },
    "Invisible": {
        "icon": "👻",
        "color": "#7b9aff",
        "effects": [
            "An invisible creature is impossible to see without the aid of magic or a special sense.",
            "For the purpose of hiding, the creature is heavily obscured. The creature's location can be detected by noise or tracks it leaves.",
            "Attack rolls against the creature have disadvantage.",
            "The creature's attack rolls have advantage.",
        ],
        "source": "PHB p.291",
    },
    "Paralyzed": {
        "icon": "⚡",
        "color": "#e74c3c",
        "effects": [
            "A paralyzed creature is incapacitated and can't move or speak.",
            "The creature automatically fails STR and DEX saving throws.",
            "Attack rolls against the creature have advantage.",
            "Any attack that hits the creature is a critical hit if the attacker is within 5 feet.",
        ],
        "source": "PHB p.291",
    },
    "Petrified": {
        "icon": "🪨",
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
    },
    "Poisoned": {
        "icon": "☠",
        "color": "#27ae60",
        "effects": [
            "A poisoned creature has disadvantage on attack rolls and ability checks.",
        ],
        "source": "PHB p.292",
    },
    "Prone": {
        "icon": "🏚",
        "color": "#c9921a",
        "effects": [
            "A prone creature's only movement option is to crawl, unless it stands up (costs half movement speed).",
            "The creature has disadvantage on attack rolls.",
            "Attack rolls against the creature have advantage if the attacker is within 5 feet; otherwise, disadvantage.",
        ],
        "source": "PHB p.292",
    },
    "Restrained": {
        "icon": "⛓",
        "color": "#e67e22",
        "effects": [
            "A restrained creature's speed becomes 0, and it can't benefit from any bonus to its speed.",
            "Attack rolls against the creature have advantage.",
            "The creature's attack rolls have disadvantage.",
            "The creature has disadvantage on DEX saving throws.",
        ],
        "source": "PHB p.292",
    },
    "Stunned": {
        "icon": "💥",
        "color": "#e74c3c",
        "effects": [
            "A stunned creature is incapacitated, can't move, and can speak only falteringly.",
            "The creature automatically fails STR and DEX saving throws.",
            "Attack rolls against the creature have advantage.",
        ],
        "source": "PHB p.292",
    },
    "Unconscious": {
        "icon": "💤",
        "color": "#888",
        "effects": [
            "An unconscious creature is incapacitated, can't move or speak, and is unaware of its surroundings.",
            "The creature drops whatever it's holding and falls prone.",
            "The creature automatically fails STR and DEX saving throws.",
            "Attack rolls against the creature have advantage.",
            "Any attack that hits the creature is a critical hit if the attacker is within 5 feet.",
        ],
        "source": "PHB p.292",
    },
    "Exhaustion": {
        "icon": "😓",
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
