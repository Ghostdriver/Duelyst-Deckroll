from typing import Dict, List, Literal
from CardPool import CardPool
from CardData import CardData
import random
from Deck import Deck
import xlsxwriter
import datetime
from tenacity import retry, stop_after_attempt


class Deckroll:
    def __init__(
        self,
        card_pool: CardPool,
        amount_cards: int,
        factions_and_weights: Dict[Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"], int],
        cards_and_weights: Dict[int, float],
        count_chances: Dict[int, float],
        count_chances_two_remaining_deck_slots: Dict[int, float],
        min_1_and_2_drops: int = 0,
        min_total_removal: int = 0,
        min_hard_removal: int = 0,
        min_soft_removal: int = 0
    ) -> None:
        self.card_pool = card_pool
        self.amount_cards = amount_cards
        self.factions_and_weights = factions_and_weights
        self.cards_and_weights = cards_and_weights
        self.count_chances = count_chances
        self.count_chances_two_remaining_deck_slots = count_chances_two_remaining_deck_slots
        self.min_1_and_2_drops = min_1_and_2_drops
        self.min_total_removal = min_total_removal
        self.min_hard_removal = min_hard_removal
        self.min_soft_removal = min_soft_removal

    def roll_deck_spreadsheat(
        self,
        amount_decks: int,
        decklink_prefix: str = "https://decklyst.vercel.app/decks/"
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
        print(f"Created Excel {workbook_name} with {amount_decks} rolled decks in {needed_time}")
        return workbook_name

    @retry(stop=stop_after_attempt(10))
    def roll_deck(self) -> str:
        # init deck
        self.rolled_deck = Deck(card_pool=self.card_pool)
        self.rolled_deck.max_cards = self.amount_cards
        # roll deck
        self._roll_faction()
        self._roll_general()
        self._roll_collectible_cards()
        # check deck
        self._check_amount_of_1_and_2_drops()
        self._check_amount_removal()
        return self.rolled_deck.deckcode

    def _roll_faction(self) -> None:
        self.rolled_faction = random.choices(list(self.factions_and_weights.keys()), weights=list(self.factions_and_weights.values()))[0]

    def _roll_general(self) -> None:
        generals_from_faction = self.card_pool.generals_by_faction[self.rolled_faction]
        rolled_general = random.choice(generals_from_faction)
        self.rolled_deck.add_card_and_count(rolled_general.id, 1)

    def _roll_collectible_cards(self) -> None:
        faction_and_neutral_cards: List[CardData] = self.card_pool.collectible_cards_by_faction[self.rolled_faction] + self.card_pool.collectible_cards_by_faction["Neutral"]
        cards_and_weights_specific_roll: Dict[int, int] = {}
        for faction_and_neutral_card in faction_and_neutral_cards:
            cards_and_weights_specific_roll[faction_and_neutral_card.id] = self.cards_and_weights[faction_and_neutral_card.id]
        while self.rolled_deck.remaining_cards > 0:
            rolled_card_id = random.choices(list(cards_and_weights_specific_roll.keys()), weights=list(cards_and_weights_specific_roll.values()))[0]
            self._roll_card_count(rolled_card_id)
            cards_and_weights_specific_roll[rolled_card_id] = 0

    def _roll_card_count(self, card_id: int) -> None:
        if self.rolled_deck.remaining_cards == 1:
            count = 1
        elif self.rolled_deck.remaining_cards == 2:
            count = random.choices(list(self.count_chances_two_remaining_deck_slots.keys()), list(self.count_chances_two_remaining_deck_slots.values()))[0]
        else:
            count = random.choices(list(self.count_chances.keys()), list(self.count_chances.values()))[0]
        self.rolled_deck.add_card_and_count(card_id=card_id, count=count)

    def _check_amount_of_1_and_2_drops(self) -> None:
        if self.min_1_and_2_drops > 0:
            minions_sorted = self.rolled_deck.get_cards_by_card_type_sorted_by_cost_and_alphabetical(card_type="Minion")
            amount_1_and_2_drops = 0
            for minion in minions_sorted:
                if minion.mana <= 2:
                    amount_1_and_2_drops += self.rolled_deck.cards_and_counts[minion.id]
                else:
                    break
            if amount_1_and_2_drops < self.min_1_and_2_drops:
                raise ValueError("Check failed - the rolled deck has less 1 and 2 drops than needed")
        
    def _check_amount_removal(self) -> None:
        if self.card_pool.legacy:
            # total removal
            if self.min_total_removal > 0:
                amount_total_removal_cards = 0
                for card_id, count in self.rolled_deck.cards_and_counts:
                    if card_id in self.card_pool.legacy_all_removal_card_ids:
                        amount_total_removal_cards += count
                if amount_total_removal_cards < self.min_total_removal:
                    raise ValueError("Check failed - the rolled deck has less total removal cards than needed")
            # hard removal
            if self.min_hard_removal > 0:
                amount_hard_removal_cards = 0
                for card_id, count in self.rolled_deck.cards_and_counts:
                    if card_id in self.card_pool.legacy_hard_removal_card_ids:
                        amount_hard_removal_cards += count
                if amount_hard_removal_cards < self.min_hard_removal:
                    raise ValueError("Check failed - the rolled deck has less hard removal cards than needed")
            # soft removal
            if self.min_soft_removal > 0:
                amount_soft_removal_cards = 0
                for card_id, count in self.rolled_deck.cards_and_counts:
                    if card_id in self.card_pool.legacy_soft_removal_card_ids:
                        amount_soft_removal_cards += count
                if amount_soft_removal_cards < self.min_soft_removal:
                    raise ValueError("Check failed - the rolled deck has less soft removal cards than needed")
            
