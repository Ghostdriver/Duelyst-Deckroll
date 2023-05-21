from CardPool import CardPool
from typing import Dict, List, Literal
import discord
from Deck import Deck
import random
import numpy as np
import discord
from constants import DECKLINK_PREFIX, LEGACY_DECKLINK_PREFIX

REACTIONS_NUMBERS = {
    "0️⃣": 0,
    "1️⃣": 1,
    "2️⃣": 2,
    "3️⃣": 3,
    "4️⃣": 4,
    "5️⃣": 5,
    "6️⃣": 6,
    "7️⃣": 7,
    "8️⃣": 8,
    "9️⃣": 9
}

NUMBERS_REACTIONS = { value: key for key, value in REACTIONS_NUMBERS.items() }

class Draft:
    def __init__(self, draft_init_message_content: str, draft_message: discord.Message, discord_bot_user: discord.User, user: discord.User, card_pool: CardPool, amount_cards: int, factions_and_weights: Dict[Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"], int], cards_and_weights: Dict[int, float], faction_offers: int, card_offers_per_pick: int, cards_to_choose_per_pick: int, card_bucket_size: int) -> None:
        self.draft_init_message_content = draft_init_message_content
        self.draft_message = draft_message
        self.discord_bot_user = discord_bot_user
        self.user = user
        self.card_pool = card_pool
        self.cards_and_weights = cards_and_weights
        self.factions_and_weights = factions_and_weights
        self.faction_offers = faction_offers
        self.card_offers_per_pick = card_offers_per_pick
        self.cards_to_choose_per_pick = cards_to_choose_per_pick
        self.card_bucket_size = card_bucket_size
        self.cards_and_weights = cards_and_weights
        self.drafted_deck = Deck(card_pool=self.card_pool)
        self.drafted_deck.max_cards = amount_cards
        self.current_choices: List[str] | List[List[str]] = []
        self.current_reactions: List[discord.Reaction] = []
        self.status: Literal["Init", "Picking Faction", "Picking Cards", "Draft Completed", "!!! Draft abandoned !!!"] = "Init"
        self.user_task: str = ""
        self.deck_embed: discord.Embed = None
        self.maximum_offers = max(faction_offers, card_offers_per_pick)

    async def _update_deck_embed(self) -> None:
        self.deck_embed = self.drafted_deck.create_deck_embed()

    async def update_draft_message(self) -> None:
        current_choices_message = ""
        for index, current_choice in enumerate(self.current_choices):
            current_choices_message += f"{NUMBERS_REACTIONS[index]} {current_choice}\n"
        message = f"""
{self.user.name}'s draft
{self.draft_init_message_content}
Faction: {self.drafted_deck.faction}
Cards drafted: {self.drafted_deck.amount_cards}/{self.drafted_deck.max_cards}
{self.status}
{self.user_task}

{current_choices_message}
        """
        await self.draft_message.edit(content=message, embed=self.deck_embed)

    async def abandon(self) -> None:
        self.status = "!!! Draft abandoned !!!"
        await self.update_draft_message()
        await self._remove_user_reactions()
        await self._remove_own_reactions()

    async def start_draft(self) -> None:
        self.status = "Picking Faction"
        await self._roll_choices()
        await self._add_reactions()
        await self.update_draft_message()

    async def user_adds_reaction(self, reaction: discord.Reaction) -> bool: 
        self.current_reactions.append(reaction)
        if self.status == "Picking Faction":
            if len(self.current_reactions) == 1:
                await self._add_chosen_general()
                self.status = "Picking Cards"
                await self._prepare_card_weights()
                await self._prepare_next_choices()
        elif self.status == "Picking Cards":
            if len(self.current_reactions) == self.cards_to_choose_per_pick:
                await self._add_chosen_cards()
                if self.drafted_deck.remaining_cards == 0:
                    self.status = "Draft Completed"
                    await self._finish_draft()
                    return True
                await self._prepare_next_choices()
        return False
    
    async def _prepare_next_choices(self) -> None:
        await self._roll_choices()
        await self._remove_user_reactions()
        await self.update_draft_message()

    async def _roll_choices(self) -> None:
        if self.status == "Picking Faction":
            await self._roll_general_choices()
        elif self.status == "Picking Cards":
            await self._roll_card_choices()

    async def _roll_general_choices(self) -> None:
        # Weights for numpy choice have to be equal to one
        total_weight = sum(self.factions_and_weights.values())
        for key, value in self.factions_and_weights.items():
            self.factions_and_weights[key] = value / total_weight
        factions_to_offer = np.random.choice(a=list(self.factions_and_weights.keys()), size=self.faction_offers, replace=False, p=list(self.factions_and_weights.values()))
        generals_to_offer = []
        for faction_to_offer in factions_to_offer:
            rolled_general = random.choice(self.card_pool.generals_by_faction[faction_to_offer])
            generals_to_offer.append(rolled_general.name)
        self.current_choices = generals_to_offer
        self.user_task = "Pick your General by reacting"

    async def _add_chosen_general(self) -> None:
        reaction = self.current_reactions[0]
        picked_general = self.current_choices[REACTIONS_NUMBERS[reaction.emoji]]
        picked_general_card = self.card_pool.get_general_by_card_name(picked_general)
        self.drafted_deck.faction = picked_general_card.faction
        self.drafted_deck.add_card_and_count(picked_general_card.id, 1)
        await self._update_deck_embed()

    async def _prepare_card_weights(self) -> None:
        for card_id in self.cards_and_weights.keys():
            card = self.card_pool.get_card_data_by_card_id(card_id=card_id)
            if card.faction != self.drafted_deck.faction and card.faction != "Neutral":
                self.cards_and_weights[card_id] = 0

    async def _roll_card_choices(self) -> None:
        self.current_choices = []
        amount_of_draftable_cards = len(list(self.cards_and_weights.keys()))
        # for single cards
        if self.drafted_deck.remaining_cards < self.cards_to_choose_per_pick:
            self.cards_to_choose_per_pick = self.drafted_deck.remaining_cards
        if amount_of_draftable_cards < self.card_offers_per_pick:
            self.card_offers_per_pick = amount_of_draftable_cards
        # for card buckets
        if self.drafted_deck.remaining_cards < self.card_bucket_size:
            self.card_bucket_size = self.drafted_deck.remaining_cards
        if amount_of_draftable_cards < self.card_bucket_size:
            self.card_bucket_size = amount_of_draftable_cards
            self.card_offers_per_pick = 1
        # Weights for numpy choice have to be equal to one
        total_weight = sum(self.cards_and_weights.values())
        for key, value in self.cards_and_weights.items():
            self.cards_and_weights[key] = value / total_weight
        # for single cards
        if self.card_bucket_size == 1:
            card_ids = np.random.choice(a=list(self.cards_and_weights.keys()), size=self.card_offers_per_pick, replace=False, p=list(self.cards_and_weights.values()))
            # Convert IDs to names
            for card_id in card_ids:
                card_name = self.card_pool.get_card_data_by_card_id(card_id).name
                self.current_choices.append(card_name)
        # for card buckets
        else:
            for card_offer_per_pick in range(self.card_offers_per_pick):
                for _ in range(10):
                    card_ids = np.random.choice(a=list(self.cards_and_weights.keys()), size=self.card_bucket_size, replace=False, p=list(self.cards_and_weights.values()))
                    # Convert IDs to names
                    card_names = []
                    for card_id in card_ids:
                        card_name = self.card_pool.get_card_data_by_card_id(card_id).name
                        card_names.append(card_name)
                    card_names.sort()
                    if card_names not in self.current_choices:
                        self.current_choices.append(card_names)
                        break
        self.user_task = f"Pick {self.cards_to_choose_per_pick} Card Bucket(s) by reacting"

    async def _add_chosen_cards(self) -> None:
        for reaction in self.current_reactions:
            picked_card_bucket = self.current_choices[REACTIONS_NUMBERS[reaction.emoji]]
            # If the option is a card bucket
            if isinstance(picked_card_bucket, list):
                for card_name in picked_card_bucket:
                    await self._add_chosen_card(card_name=card_name)
            # If the option is a single card
            else:
                await self._add_chosen_card(card_name=picked_card_bucket)
        await self._update_deck_embed()

    async def _add_chosen_card(self, card_name: str) -> None:
        card = self.card_pool.get_collectible_card_by_card_name_from_faction(card_name=card_name, faction=self.drafted_deck.faction)
        self.drafted_deck.add_card_and_count(card.id, 1)
        if self.drafted_deck.cards_and_counts[card.id] == 3:
            del self.cards_and_weights[card.id]

    async def _finish_draft(self) -> None:
        self.user_task = ""
        self.current_choices = []
        await self._update_deck_embed()
        await self.update_draft_message()
        await self._remove_user_reactions()
        await self._remove_own_reactions()

    async def _add_reactions(self) -> None:
        for number in range(self.maximum_offers):
            await self.draft_message.add_reaction(NUMBERS_REACTIONS[number])

    async def _remove_own_reactions(self) -> None:
        for number in reversed(range(self.maximum_offers)):
            await self.draft_message.remove_reaction(NUMBERS_REACTIONS[number], self.discord_bot_user)

    async def _remove_user_reactions(self) -> None:
        for reaction in reversed(self.current_reactions):
            await reaction.remove(user=self.user)