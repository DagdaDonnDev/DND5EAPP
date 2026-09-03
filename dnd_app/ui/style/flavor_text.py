"""Small pools of flavor text for cosmetic-only touches around the
sheet -- death screen quips, long rest dream lines, and similar. None
of this has any gameplay effect; it's purely for fun.
"""
import random

# Critical Flavor (DM Secrets, optional rule, default off): a random
# quip appended to the death-screen toast.
DEATH_MESSAGES = [
    "Did you really think that would work?",
    "Your party is already discussing who gets your stuff.",
    "Your character sheet is already in the trash.",
    "Maybe don't charge the dragon next time?",
    "The app is not responsible for your bad decisions.",
    "You'll get 'em next time, champ.",
    "Your death was so predictable.",
    "At least you didn't die to a goblin. Right?",
    "You literally died of exhaustion. That's embarrassing.",
    "I've seen rocks with better survival instincts.",
    "Again. I'm starting to take this personally.",
    "You were the chosen one. Until you weren't.",
    "MIMIC will remember this.",
]

# Long rest (always on): a one-line "you dream of--" flourish appended
# to the existing rest-complete toast.
LONG_REST_DREAMS = [
    "You dream of gold.",
    "You dream of home.",
    "You dream of the one that got away.",
    "You dream of nothing at all — which, honestly, is a nice change.",
    "You dream in numbers. Too many numbers.",
    "You dream of a warm bed that isn't a dungeon floor.",
    "You dream of what it would be like to have a stove maybe even a spoon.",
    "You dream of the fight you almost lost.",
]


def random_death_message() -> str:
    return random.choice(DEATH_MESSAGES)


def random_long_rest_dream() -> str:
    return random.choice(LONG_REST_DREAMS)
