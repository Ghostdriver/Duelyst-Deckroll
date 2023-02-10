from typing import Dict, List, Optional
from factions import get_faction_str_from_faction_int


class CardData:
    def __init__(self, card: Dict) -> None:
        self.name: str = card["name"]
        self.id: int = card["id"]
        self.card_set: str = card["cardSet"]
        self.faction: str = get_faction_str_from_faction_int(
            faction_int=card["faction"]
        )
        self.rarity: str = card["rarity"]
        self.description: str = card["description"]
        self.related_cards: List[int] = card["relatedCards"]
        self.gifs: List[str] = card["resource"]
        self.mana: int = card["mana"]
        self.attack: Optional[int] = card.get("attack")
        self.health: Optional[int] = card.get("health")
        self.card_type: str = card["cardType"]
        self.tribes: List[str] = card["tribes"]
