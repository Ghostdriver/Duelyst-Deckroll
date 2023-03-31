import base64
from typing import Literal, Dict, List, DefaultDict
from CardPool import CardPool
from CardData import CardData, CARD_TYPES
from collections import defaultdict


class Deck:
    def __init__(self, card_pool: CardPool) -> None:
        self.card_pool = card_pool
        self.max_cards = 40
        self.cards_and_counts: DefaultDict[int, int] = defaultdict(lambda: 0)
        self.faction: Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"] = None

    @property
    def amount_cards(self) -> int:
        return sum(list(self.cards_and_counts.values()))

    @property
    def remaining_cards(self) -> int:
        return self.max_cards - self.amount_cards
    
    @property
    def deck_sorted_by_card_type(self) -> Dict[str, List[CardData]]:
        deck_sorted_by_card_type = {}
        for card_type in CARD_TYPES:
            deck_sorted_by_card_type[card_type] = []
        allowed_cards = self.card_pool.generals_by_faction[self.faction] + self.card_pool.collectible_cards_by_faction[self.faction] + self.card_pool.collectible_cards_by_faction["Neutral"]
        for card_code in self.cards_and_counts.keys():
            for card in allowed_cards:
                if card.id == card_code:
                    deck_sorted_by_card_type[card.card_type].append(card)
        return deck_sorted_by_card_type
    
    @property
    def deckcode(self) -> str:
        concatenated_string_with_counts_and_cards = ""
        for card_id, count in self.cards_and_counts.items():
            if 1 <= count <= 3:
                concatenated_string_with_counts_and_cards += f"{count}:{card_id},"
        # remove trailing comma
        if concatenated_string_with_counts_and_cards.endswith(","):
            concatenated_string_with_counts_and_cards = (
                concatenated_string_with_counts_and_cards[:-1]
            )
        return base64.standard_b64encode(concatenated_string_with_counts_and_cards.encode()).decode()

    def create_cards_and_counts_from_deckcode(self, deckcode: str) -> None:
        """Transforms a deckcode to a dict containing card_id: count"""
        # strip [<deckname>] from the start of the deckcode
        if deckcode.startswith("[") and "]" in deckcode:
            deckcode = deckcode[deckcode.index("]") + 1 :]
        # decode
        concatenated_string_with_counts_and_cards = base64.b64decode(deckcode).decode()
        list_with_counts_and_cards = concatenated_string_with_counts_and_cards.split(",")
        self.cards_and_counts = {}
        for count_and_card in list_with_counts_and_cards:
            count, card_id = count_and_card.split(":")
            self.cards_and_counts[card_id] = count

    def add_card_and_count(self, card_id: int, count: int) -> None:
        card: CardData = self.card_pool.get_card_data_by_card_id(card_id)
        # first card added to the deck has to be a general
        if self.amount_cards == 0:
            if card.card_type == "General" and count == 1:
                self.faction = card.faction
            else:
                raise ValueError("The first card must be one general")
        # All further cards can't be Tokens and Generals, must be from the generals faction or neutral and the new count has to be between 1 and 3 and the resulting decksize mustn't be greater than the maximum deck size
        else:
            if not (
                card.rarity in ["Common", "Rare", "Epic", "Legendary"]
                and card.faction in [self.faction, "Neutral"]
                and 1 <= self.cards_and_counts[card.id] + count <= 3
                and self.amount_cards + count <= self.max_cards
            ):
                raise ValueError("Either the card has the wrong rarity or faction or with the addition the count of the card is not between 1 and 3 or the deck has too much cards after the addition of the card(s)")
        # update deck
        self.cards_and_counts[card.id] += count

    def get_cards_by_card_type_sorted_by_cost_and_alphabetical(self, card_type: Literal["General", "Minion", "Spell", "Artifact"]) -> List[CardData]:
        return sorted(self.deck_sorted_by_card_type[card_type], key=lambda card: (card.mana, card.name))
