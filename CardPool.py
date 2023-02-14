from typing import List, Dict, DefaultDict, Literal
from CardData import CardData
import requests
import json
from collections import defaultdict


class CardPool:
    def __init__(self) -> None:
        '''init card pool'''
        self.all_cards: List[CardData] = []
        self.generals: List[CardData] = []
        self.generals_by_faction: DefaultDict[Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"], List[CardData]] = defaultdict(lambda: [])
        self.collectible_cards: List[CardData] = []
        self.collectible_cards_by_faction: DefaultDict[Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar", "Neutral"], List[CardData]] = defaultdict(lambda: [])
        
        # get all cards
        CARDS_JSON_URL = "https://api.duelyst2.com/cards.json"
        r = requests.get(CARDS_JSON_URL)
        if r.status_code == 200:
            all_cards_json: List[Dict] = json.loads(r.text)
            print(f"Retrieved {len(all_cards_json)} cards from the API")
        else:
            with open("cards.json", encoding="UTF-8") as f:
                cards_json = f.read()
                all_cards_json: List[Dict] = json.loads(cards_json)
                print(f"API Request failed, using local cards.json file, which includes {len(all_cards_json)} cards")
        for card in all_cards_json:
            self.all_cards.append(CardData(card))
        print(f"CardPool initialized with {len(self.all_cards)} total cards")

        # categorize cards
        for card in self.all_cards:
            if card.card_type == "General":
                self.generals.append(card)
                self.generals_by_faction[card.faction].append(card)
            if card.rarity in ["Common", "Rare", "Epic", "Legendary"]:
                self.collectible_cards.append(card)
                self.collectible_cards_by_faction[card.faction].append(card)
        print(f"CardPool initialized with {len(self.generals)} generals")
        print(f"CardPool initialized with {len(self.collectible_cards)} collectible cards")

    def get_card_data_by_card_id(self, card_id: int) -> CardData:
        for card in self.all_cards:
            if card.id == card_id:
                return card
        raise ValueError("No card with the card id {card_id} found")
        