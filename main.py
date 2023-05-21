from CardPool import CardPool
from Deckroll import Deckroll,  DECKROLL_MODIFICATION_NOT_GIVEN
from copy import deepcopy
from typing import Dict
from CardData import ALL_FACTIONS, MAIN_FACTIONS
from DiscordBot import DiscordBot

# MAIN OPTIONS
CREATE_DECKROLL_EXCEL: bool = False
AMOUNT_DECKS: int = 100
START_DISCORD_BOT: bool = True
SEND_DECKCODE: bool = False
SEND_DECKLINK: bool = True

# DECKROLL OPTIONS

# amount cards
amount_cards_default = 40

# faction_chances
factions_and_weights_default: Dict[str, int] = {}
for faction in MAIN_FACTIONS:
    factions_and_weights_default[faction] = 1

# prepare collectible card pool
card_pool = CardPool(legacy=False)
legacy_card_pool = CardPool(legacy=True)

# card_chances
cards_per_faction: Dict[str, int] = {}
for faction in ALL_FACTIONS:
    cards_per_faction[faction] = len(card_pool.collectible_cards_by_faction[faction])

legacy_cards_per_faction: Dict[str, int] = {}
for faction in ALL_FACTIONS:
    legacy_cards_per_faction[faction] = len(legacy_card_pool.collectible_cards_by_faction[faction])

# general card weights - default unweighted
legacy_general_cards_and_weights_default: Dict[int, float] = {}
for general in legacy_card_pool.generals:
    legacy_general_cards_and_weights_default[general.id] = 1.0

# default - all cards have the same chance
cards_and_weights_default: Dict[int, float] = {}
for collectible_card in card_pool.collectible_cards:
    cards_and_weights_default[collectible_card.id] = 1.0

legacy_cards_and_weights_default: Dict[int, float] = {}
for collectible_card in legacy_card_pool.collectible_cards:
    legacy_cards_and_weights_default[collectible_card.id] = 1.0

# adjust faction card chances in a way, that they are equally likely as neutral cards
cards_and_weights_half_faction_half_neutral: Dict[int, int] = {}
for collectible_card in card_pool.collectible_cards:
    cards_and_weights_half_faction_half_neutral[collectible_card.id] = cards_per_faction["Neutral"] / cards_per_faction[collectible_card.faction]

legacy_cards_and_weights_half_faction_half_neutral: Dict[int, int] = {}
for collectible_card in legacy_card_pool.collectible_cards:
    legacy_cards_and_weights_half_faction_half_neutral[collectible_card.id] = cards_per_faction["Neutral"] / cards_per_faction[collectible_card.faction]

# exclude neutral cards
cards_and_weights_only_faction: Dict[int, int] = {}
for collectible_card in card_pool.collectible_cards:
    if collectible_card.faction == "Neutral":
        cards_and_weights_only_faction[collectible_card.id] = 0.0
    else:
        cards_and_weights_only_faction[collectible_card.id] = 1.0

legacy_cards_and_weights_only_faction: Dict[int, int] = {}
for collectible_card in legacy_card_pool.collectible_cards:
    if collectible_card.faction == "Neutral":
        legacy_cards_and_weights_only_faction[collectible_card.id] = 0.0
    else:
        legacy_cards_and_weights_only_faction[collectible_card.id] = 1.0

# count chances
count_chances_default: Dict[int, int] = {1: 20, 2: 30, 3: 50}

# count chances two remaining deck slots
count_chances_two_remaining_deck_slots_default: Dict[int, int] = {1: 33, 2: 67}

# minima of cards
min_1_and_2_drops_default = DECKROLL_MODIFICATION_NOT_GIVEN
max_1_and_2_drops_default = DECKROLL_MODIFICATION_NOT_GIVEN

# INDIVIDUAL DECKROLL FOR EXCEL SPREADSHEAT - change the values to fit your needs!
legacy = True
kierans_ban_list = True
amount_cards = 40 # amount_cards_default
factions_and_weights = deepcopy(factions_and_weights_default)
cards_and_weights = deepcopy(legacy_cards_and_weights_default) # deepcopy(cards_and_weights_half_faction_half_neutral)
count_chances = deepcopy(count_chances_default)
count_chances_two_remaining_deck_slots = deepcopy(count_chances_two_remaining_deck_slots_default)
min_1_and_2_drops = 9 # min_1_and_2_drops_default
max_1_and_2_drops = 14 # max_1_and_2_drops_default

if legacy:
    deck_roll = Deckroll(card_pool=legacy_card_pool, amount_cards=amount_cards_default, factions_and_weights=factions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots, min_1_and_2_drops=min_1_and_2_drops, max_1_and_2_drops=max_1_and_2_drops)
else:
    deck_roll = Deckroll(card_pool=card_pool, amount_cards=amount_cards_default, factions_and_weights=factions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots, min_1_and_2_drops=min_1_and_2_drops, max_1_and_2_drops=max_1_and_2_drops)



if __name__ == "__main__":
    if CREATE_DECKROLL_EXCEL:
        if legacy:
            deck_roll.roll_deck_spreadsheat(
                amount_decks=AMOUNT_DECKS
            )
        else:
            deck_roll.roll_deck_spreadsheat(
                amount_decks=AMOUNT_DECKS
            )
    if START_DISCORD_BOT:
        discord_bot = DiscordBot(
            card_pool=card_pool, legacy_card_pool=legacy_card_pool,
            amount_cards_default=amount_cards_default,
            factions_and_weights_default=factions_and_weights_default,
            cards_and_weights_default=cards_and_weights_default,
            legacy_cards_and_weights_default=legacy_cards_and_weights_default,
            cards_and_weights_half_faction_half_neutral=cards_and_weights_half_faction_half_neutral,
            legacy_cards_and_weights_half_faction_half_neutral=legacy_cards_and_weights_half_faction_half_neutral,
            cards_and_weights_only_faction=cards_and_weights_only_faction,
            legacy_cards_and_weights_only_faction=legacy_cards_and_weights_only_faction,
            count_chances_default=count_chances_default,
            count_chances_two_remaining_deck_slots_default=count_chances_two_remaining_deck_slots_default,
            min_1_and_2_drops_default=min_1_and_2_drops_default,
            max_1_and_2_drops_default=max_1_and_2_drops_default           
            )
