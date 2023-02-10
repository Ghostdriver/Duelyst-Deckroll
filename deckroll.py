from typing import Dict, List, Literal
from CardPool import CardPool
from CardData import CardData
import random
from Deck import Deck
import xlsxwriter
import datetime
from factions import MAIN_FACTIONS


class Deckroll:
    def __init__(
        self,
        allowed_factions: List[
            Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"]
        ] = MAIN_FACTIONS,
        card_chances: Dict[int, float] = None,
        count_chances: Dict[int, float] = {1: 0.2, 2: 0.3, 3: 0.5},
        count_chances_two_remaining_deck_slots: Dict[int, float] = {1: 0.33, 2: 0.66},
    ) -> None:
        self.card_pool: CardPool = CardPool()
        self.all_collectible_cards: List[
            CardData
        ] = self.card_pool.get_all_collectible_cards()
        self.card_pool_ids: List[int] = [card.id for card in self.all_collectible_cards]
        self.allowed_factions: List[str] = allowed_factions
        # card_chances: dictionary containing all card ids and their respective roll chance, same chance for all cards if not given
        self.card_chances: Dict[int, float] = card_chances
        if not self.card_chances:
            self.card_chances = {}
            for collectible_card in self.all_collectible_cards:
                self.card_chances[collectible_card.id] = 1.0
        # count_chances: dictionary containing the amounts 1, 2 and 3 and the respective chance to get a rolled card the respective amount
        self.count_chances: Dict[int, float] = count_chances
        # count_chances_two_remaining_deck_slots containing the amounts 1 and 2 and the respective chance to get a rolled card the respective amount, when only two deck slots remain
        self.count_chances_two_remaining_deck_slots: Dict[
            int, float
        ] = count_chances_two_remaining_deck_slots
        self.check_inputs()

    def check_inputs(self) -> None:
        if not self.allowed_factions:
            raise ValueError("At least one faction must be allowed")
        if sorted(self.card_chances.keys()) != sorted(self.card_pool_ids):
            raise ValueError(
                f"The card ids from the given card chances and the card ids from all found cards in the card pool don't match"
            )
        if len(self.count_chances.keys()) != 3:
            raise ValueError("count_chances has to have exactly 3 values")
        for count in [1, 2, 3]:
            if count not in self.count_chances:
                raise ValueError(
                    f"the chance to get {count} card(s) has to be included in count_chances"
                )
        if len(self.count_chances_two_remaining_deck_slots.keys()) != 2:
            raise ValueError(
                "count_chances_two_remaining_deck_slots has to have exactly 2 values"
            )
        for count in [1, 2]:
            if count not in self.count_chances_two_remaining_deck_slots:
                raise ValueError(
                    f"the chance to get {count} card(s) has to be included in count_chances_two_remaining_deck_slots"
                )

    def create_deckroll_excel(
        self,
        amount_decks: int,
        decklink_prefix: str = "https://decklyst.vercel.app/decks/",
    ) -> str:
        if amount_decks < 0 or amount_decks > 10**7:
            raise ValueError("amount decks out of allowed range")
        start_time = datetime.datetime.now()
        path: str = "created_deckroll_excel_files/"
        workbook_name: str = f"Deckroll-{datetime.date.today().isoformat()}.xlsx"
        with xlsxwriter.Workbook(path + workbook_name) as workbook:
            worksheet = workbook.add_worksheet("rolled decks")
            for row in range(amount_decks):
                deckcode = self.roll_deck()
                worksheet.write(row, 0, deckcode)
                worksheet.write(row, 1, decklink_prefix + deckcode)
        end_time = datetime.datetime.now()
        needed_time = end_time - start_time
        print(
            f"Created Excel {workbook_name} with {amount_decks} rolled decks in {needed_time}"
        )
        return workbook_name

    def roll_deck(self) -> str:
        self.rolled_deck: Deck = Deck()
        # roll_faction
        self.rolled_faction: str = self.roll_faction()
        # roll general
        self.rolled_general: CardData = self.roll_general()
        self.rolled_deck.add_card_and_count(self.rolled_general.id, 1)
        # prepare rollable cards
        self.card_chances_specific_roll: Dict[int, float] = {}
        faction_and_neutral_cards = self.card_pool.get_collectible_cards_from_factions(
            factions=[self.rolled_faction, "Neutral"]
        )
        for faction_and_neutral_card in faction_and_neutral_cards:
            self.card_chances_specific_roll[
                faction_and_neutral_card.id
            ] = self.card_chances[faction_and_neutral_card.id]
        # roll collectible cards
        while self.rolled_deck.get_remaining_cards() > 0:
            if len(self.card_chances_specific_roll.keys()) == 0:
                raise ValueError("No card left to roll")
            rolled_card_id: int = self.roll_card_id()
            rolled_card_count: int = self.roll_card_count()
            self.rolled_deck.add_card_and_count(rolled_card_id, rolled_card_count)
        # convert rolled deck to deckcode
        return self.rolled_deck.deckcode

    def roll_faction(self) -> str:
        return random.choice(self.allowed_factions)

    def roll_general(self) -> CardData:
        generals = self.card_pool.get_generals_from_faction(faction=self.rolled_faction)
        return random.choice(generals)

    def roll_card_id(self) -> int:
        rolled_card_id = random.choices(
            list(self.card_chances_specific_roll.keys()),
            list(self.card_chances_specific_roll.values()),
        )[0]
        del self.card_chances_specific_roll[rolled_card_id]
        return rolled_card_id

    def roll_card_count(self) -> int:
        if self.rolled_deck.get_remaining_cards() == 1:
            return 1
        elif self.rolled_deck.get_remaining_cards() == 2:
            return random.choices(
                list(self.count_chances_two_remaining_deck_slots.keys()),
                list(self.count_chances_two_remaining_deck_slots.values()),
            )[0]
        else:
            return random.choices(
                list(self.count_chances.keys()), list(self.count_chances.values())
            )[0]
