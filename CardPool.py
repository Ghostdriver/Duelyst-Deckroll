from typing import List, Dict, DefaultDict, Literal
from CardData import CardData
import requests
import json
from collections import defaultdict


class CardPool:
    def __init__(self, legacy: bool) -> None:
        '''init card pool'''
        if legacy:
            print("Initializing Legacy CardPool")
        else:
            print("Initializing Duelyst II CardPool")
        self.legacy = legacy
        self.all_cards: List[CardData] = []
        self.generals: List[CardData] = []
        self.generals_by_faction: DefaultDict[Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"], List[CardData]] = defaultdict(lambda: [])
        self.collectible_cards: List[CardData] = []
        self.collectible_cards_by_faction: DefaultDict[Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar", "Neutral"], List[CardData]] = defaultdict(lambda: [])

        # get all cards, legacy / new
        DUELYST_API = "https://api.duelyst2.com/"
        CARDS_JSON = "cards.json"
        LEGACY_CARDS_JSON = "legacy-cards.json"
        if legacy:
            r = requests.get(f"{DUELYST_API}{LEGACY_CARDS_JSON}")
        else:
            r = requests.get(f"{DUELYST_API}{CARDS_JSON}")
        if r.status_code == 200:
            all_cards_json: List[Dict] = json.loads(r.text)
            print(f"Retrieved {len(all_cards_json)} cards from the API")
        else:
            if legacy:
                with open(LEGACY_CARDS_JSON, encoding="UTF-8") as f:
                    cards_json = f.read()
                    all_cards_json: List[Dict] = json.loads(cards_json)
            else:
                with open(CARDS_JSON, encoding="UTF-8") as f:
                    cards_json = f.read()
                    all_cards_json: List[Dict] = json.loads(cards_json)
            print(f"API Request failed, using local cards.json file, which includes {len(all_cards_json)} cards")
        for card in all_cards_json:
            self.all_cards.append(CardData(card))
        print(f"CardPool initialized with {len(self.all_cards)} total cards")

        # categorize cards
        for card in self.all_cards:
            # Gauntlet cards, that can't be used normally
            if card.card_set != "Gauntlet Specials":
                if card.card_type == "General":
                    self.generals.append(card)
                    self.generals_by_faction[card.faction].append(card)
                if card.rarity in ["Common", "Rare", "Epic", "Legendary", "Mythron"]:
                    self.collectible_cards.append(card)
                    self.collectible_cards_by_faction[card.faction].append(card)
        print(f"CardPool initialized with {len(self.generals)} generals")
        print(f"CardPool initialized with {len(self.collectible_cards)} collectible cards")
        for faction, cards in self.collectible_cards_by_faction.items():
            print(f"CardPool initialized with {len(cards)} cards from faction {faction}")

    def get_card_data_by_card_id(self, card_id: int) -> CardData:
        for card in self.all_cards:
            if card.id == card_id:
                return card
        raise ValueError("No card with the card id {card_id} found")
    
    def get_general_by_card_name(self, card_name: str) -> CardData:
        for card in self.generals:
            if card_name.lower() == card.name.lower():
                return card
        raise ValueError(f"No Card with card name {card_name} found")

    def get_collectible_card_by_card_name(self, card_name: str) -> CardData:
        for card in self.collectible_cards:
            if card_name.lower() == card.name.lower():
                return card
        raise ValueError(f"No Card with card name {card_name} found")
    
    def get_collectible_card_by_card_name_from_faction(self, card_name: str, faction: str) -> CardData:
        for card in self.collectible_cards_by_faction[faction]:
            if card_name.lower() == card.name.lower():
                return card
        for card in self.collectible_cards_by_faction["Neutral"]:
            if card_name.lower() == card.name.lower():
                return card
        raise ValueError(f"No Card with card name {card_name} found")
        