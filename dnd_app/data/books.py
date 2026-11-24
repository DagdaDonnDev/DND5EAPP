"""What the book codes beside spells, feats, magic items and creatures
mean -- the Reference popup on both apps (Reference, next to Settings).
Two codes for one book (the reference files spell some two ways) both
list it."""

BOOKS = {
    "PHB": "Player's Handbook (2014)",
    "DMG": "Dungeon Master's Guide (2014)",
    "MM": "Monster Manual (2014)",
    "MPMM": "Mordenkainen Presents: Monsters of the Multiverse",
    "VGM": "Volo's Guide to Monsters",
    "MTF": "Mordenkainen's Tome of Foes",
    "XGE": "Xanathar's Guide to Everything",
    "TCE": "Tasha's Cauldron of Everything",
    "FTD": "Fizban's Treasury of Dragons",
    "BGG": "Bigby Presents: Glory of the Giants",
    "BP:GOG": "Bigby Presents: Glory of the Giants",
    "BOMT": "The Book of Many Things",
    "BMT": "The Book of Many Things",
    "SCAG": "Sword Coast Adventurer's Guide",
    "EEPC": "Elemental Evil Player's Companion",
    "AI": "Acquisitions Incorporated",
    "EGW": "Explorer's Guide to Wildemount",
    "ERLW": "Eberron: Rising from the Last War",
    "E:RLW": "Eberron: Rising from the Last War",
    "WGTE": "Wayfinder's Guide to Eberron",
    "GGR": "Guildmasters' Guide to Ravnica",
    "MOT": "Mythic Odysseys of Theros",
    "VRGR": "Van Richten's Guide to Ravenloft",
    "SCC": "Strixhaven: A Curriculum of Chaos",
    "STRIX": "Strixhaven: A Curriculum of Chaos",
    "AAG": "Spelljammer: Astral Adventurer's Guide",
    "SAS": "Spelljammer: Adventures in Space",
    "SatO": "Planescape: Sigil and the Outlands",
    "PSAIM": "Planescape: Adventures in the Multiverse",
    "DSotDQ": "Dragonlance: Shadow of the Dragon Queen",
    "D:SDQ": "Dragonlance: Shadow of the Dragon Queen",
    "MCV2": "Monstrous Compendium Vol. 2: Dragonlance Creatures",
    "CoS": "Curse of Strahd",
    "ToA": "Tomb of Annihilation",
    "SKT": "Storm King's Thunder",
    "OoA": "Out of the Abyss",
    "PoA": "Princes of the Apocalypse",
    "ToD": "Tyranny of Dragons",
    "RoT": "The Rise of Tiamat",
    "LMP": "Lost Mine of Phandelver",
    "PBTSO": "Phandelver and Below: The Shattered Obelisk",
    "SDW": "Sleeping Dragon's Wake",
    "WDH": "Waterdeep: Dragon Heist",
    "WDMM": "Waterdeep: Dungeon of the Mad Mage",
    "BG:DA": "Baldur's Gate: Descent into Avernus",
    "GoS": "Ghosts of Saltmarsh",
    "TYP": "Tales from the Yawning Portal",
    "LLK": "Lost Laboratory of Kwalish",
    "IMR": "Infernal Machine Rebuild",
    "ID:RF": "Icewind Dale: Rime of the Frostmaiden",
    "IDRotF": "Icewind Dale: Rime of the Frostmaiden",
    "WBW": "The Wild Beyond the Witchlight",
    "CM": "Candlekeep Mysteries",
    "CR:CN": "Critical Role: Call of the Netherdeep",
    "JRC": "Journeys through the Radiant Citadel",
    "KGV": "Keys from the Golden Vault",
    "QIS": "Quests from the Infinite Staircase",
    "VEOR": "Vecna: Eve of Ruin",
    "HAT": "Honor Among Thieves",
    "DC": "Divine Contention",
}


def book_rows() -> list:
    """[(code, book)] sorted by code, for the popup."""
    return sorted(BOOKS.items(), key=lambda kv: kv[0].casefold())


def book_name(code: str) -> str:
    return BOOKS.get((code or "").strip(), "")
