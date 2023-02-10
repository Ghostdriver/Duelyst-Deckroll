from typing import List, Dict, Literal
from CardData import CardData
import requests
import json
from functools import cache


class CardPool:
    def __init__(self) -> None:
        self.all_cards: List[CardData] = get_all_cards()

    def get_card_data_by_card_id(self, card_id: int) -> CardData:
        for card in self.all_cards:
            if card.id == card_id:
                return card
        raise ValueError("No card with the card id {card_id} found")

    def get_all_generals(self) -> List[CardData]:
        return [card for card in self.all_cards if card.card_type == "General"]

    def get_generals_from_faction(
        self,
        faction: Literal[
            "Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"
        ],
    ) -> List[CardData]:
        return [
            card
            for card in self.all_cards
            if card.faction == faction and card.card_type == "General"
        ]

    def get_all_collectible_cards(self) -> List[CardData]:
        return [
            card
            for card in self.all_cards
            if card.rarity in ["Common", "Rare", "Epic", "Legendary"]
        ]

    def get_collectible_cards_from_factions(
        self,
        factions: List[
            Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"]
        ],
    ) -> List[CardData]:
        return [
            card
            for card in self.all_cards
            if card.faction in factions
            and card.rarity in ["Common", "Rare", "Epic", "Legendary"]
        ]


@cache
def get_all_cards() -> List[CardData]:
    """Get all cards from API or local file (as fallback) and convert them with CardData class"""
    CARDS_JSON_URL = "https://api.duelyst2.com/cards.json"
    r = requests.get(CARDS_JSON_URL)
    if r.status_code == 200:
        all_cards: List[Dict] = json.loads(r.text)
        print(f"Retrieved {len(all_cards)} cards from the API")
    else:
        with open("cards.json", encoding="UTF-8") as f:
            cards_json = f.read()
            all_cards: List[Dict] = json.loads(cards_json)
            print(
                f"API Request failed, using local cards.json file, which includes {len(all_cards)} cards"
            )
    all_cards_card_data: List[CardData] = []
    for card in all_cards:
        all_cards_card_data.append(CardData(card))
    return all_cards_card_data
