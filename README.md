# Bot Invite URL
https://discord.com/api/oauth2/authorize?client_id=1073170361648152626&permissions=3072&scope=bot
# Formatting
poetry run black .
# execute main
poetry run Python ./main.py

# DECKROLL OPTIONS

# allowed factions
# exclude faction by removing it from the list
all_factions_allowed = ["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"]

# card_chances
# prepare collectible card pool
card_pool = CardPool()
all_collectible_cards = card_pool.get_all_collectible_cards()
cards_per_faction = defaultdict(lambda: 0)
for collectible_card in all_collectible_cards:
    cards_per_faction[collectible_card.faction] += 1
# default - all cards have the same chance
card_chances_default = {}
for collectible_card in all_collectible_cards:
    card_chances_default[collectible_card.id] = 1.0
# adjust faction card chances in a way, that they are equally likely as neutral cards
card_chances_half_faction_half_neutral = {}
for collectible_card in all_collectible_cards:
    card_chances_half_faction_half_neutral[collectible_card.id] = (
        cards_per_faction["Neutral"] / cards_per_faction[collectible_card.faction]
    )
# exclude neutral cards
card_chances_only_faction = {}
for collectible_card in all_collectible_cards:
    if collectible_card.faction == "Neutral":
        card_chances_only_faction[collectible_card.id] = 0.0
    else:
        card_chances_only_faction[collectible_card.id] = 1.0
# exclude legendary cards
card_chances_no_legendaries = {}
for collectible_card in all_collectible_cards:
    if collectible_card.rarity == "Legendary":
        card_chances_no_legendaries[collectible_card.id] = 0.0
    else:
        card_chances_no_legendaries[collectible_card.id] = 1.0

# count chances
count_chances_default = {1: 0.2, 2: 0.3, 3: 0.5}
count_chances_singleton = {1: 1.0, 2: 0.0, 3: 0.0}
count_chances_only_three_ofs = {1: 0.0, 2: 0.0, 3: 1.0}

# count chances two remaining deck slots
count_chances_two_remaining_deck_slots_default = {1: 0.33, 2: 0.66}
count_chances_two_remaining_deck_slots_singleton = {1: 1.0, 2: 0.0}
count_chances_two_remaining_deck_slots_always_two_of = {1: 0.0, 2: 1.0}

# create deckroll
deckroll = Deckroll(
    allowed_factions=all_factions_allowed,
    card_chances=card_chances_half_faction_half_neutral,
    count_chances=count_chances_default,
    count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots_default,
)
deckroll.create_deckroll_excel(amount_decks=100)