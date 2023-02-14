from typing import Dict, List, Optional

RARITIES = ["Common", "Rare", "Epic", "Legendary"]
MAIN_FACTIONS: List[str] = ["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar",]
ALL_FACTIONS: List[str] = ["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar", "Neutral"]

class CardData:
    def __init__(self, card: Dict) -> None:
        self.name: str = card["name"]
        self.id: int = card["id"]
        self.card_set: str = card["cardSet"]
        self.faction: str = get_faction_str_from_faction_int(faction_int=card["faction"])
        self.rarity: str = card["rarity"]
        self.description: str = card["description"]
        self.related_cards: List[int] = card["relatedCards"]
        self.gifs: List[str] = card["resource"]
        self.mana: int = card["mana"]
        self.attack: Optional[int] = card.get("attack")
        self.health: Optional[int] = card.get("health")
        self.card_type: str = card["cardType"]
        self.tribes: List[str] = card["tribes"]

def get_faction_str_from_faction_int(faction_int: int) -> str:
    FACTIONS_DICT: Dict[int, str] = {
        1: "Lyonar",
        2: "Songhai",
        3: "Vetruvian",
        4: "Abyssian",
        5: "Magmar",
        6: "Vanar",
        100: "Neutral",
    }
    if faction_int not in FACTIONS_DICT.keys():
        raise ValueError(
            f"The given faction_int {faction_int} is not in FACTIONS_DICT keys {FACTIONS_DICT.keys()}"
        )
    else:
        return FACTIONS_DICT[faction_int]
    