from CardPool import CardPool
from deckroll import Deckroll
from collections import defaultdict
import discord
from discord.ext import commands
from copy import deepcopy
from factions import MAIN_FACTIONS
import re

RARITIES = ["Common", "Rare", "Epic", "Legendary"]

# DECKLINK
SEND_DECKCODE = False
SEND_DECKLINK = True
DECKLINK_PREFIX = "https://decklyst.vercel.app/decks/"

# DECKROLL OPTIONS

# allowed factions
# exclude faction by removing it from the list
all_factions_allowed = MAIN_FACTIONS

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

# count chances
count_chances_default = {1: 0.2, 2: 0.3, 3: 0.5}
count_chances_singleton = {1: 1.0, 2: 0.0, 3: 0.0}
count_chances_only_three_ofs = {1: 0.0, 2: 0.0, 3: 1.0}

# count chances two remaining deck slots
count_chances_two_remaining_deck_slots_default = {1: 0.33, 2: 0.66}
count_chances_two_remaining_deck_slots_singleton = {1: 1.0, 2: 0.0}
count_chances_two_remaining_deck_slots_always_two_of = {1: 0.0, 2: 1.0}


def run_discord_bot() -> None:
    with open("discord_bot_token.key") as file:
        TOKEN = file.read()
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix="!", intents=intents)

    @client.event
    async def on_message(message):
        channel = message.channel

        if isinstance(message.content, str):
            message_content: str = message.content.lower()

            # default deckroll
            if message_content == "!deckroll":
                deck_roll = Deckroll()
                deckcode = deck_roll.roll_deck()
                if SEND_DECKCODE:
                    await channel.send(deckcode)
                if SEND_DECKLINK:
                    await channel.send(DECKLINK_PREFIX + deckcode)

            elif message_content.startswith("!deckroll") and message_content.__contains__("help"):
                help_message = '''
                Duelyst Deckroll Bot Help
                This bot can process default and individual deckrolls

                For the default deckroll use: !deckroll
                The used settings are: all factions allowed, all cards have the same chance,
                a rolled card will be included as 1 of with a 20%, as 2 of with a 30% and as 3 of with a 50% chance

                For the individual deckroll use !deckroll followed by modifications
                (the script checks if the keywords are included, order doesn't matter)
                Following modifications are available:
                - factions:
                    - exclude faction with: no_<faction> (e.g. no_lyonar)
                    - allow only one faction with: only_<faction> (e.g. only_lyonar)
                - card_chances:
                    - set chances of factions cards so high, that around half of the rolled cards will be from the rolled faction
                    with: half_faction_half_neutral
                    - exclude neutral cards with: only_faction
                    - exclude by rarity with: no_<rarity> (no_common / no_rare / no_epic / no_legendary)
                - count chances - 1/2/3 ofs:
                    - as said default is 20/30/50
                    - every card only once 100/0/0 with: singleton
                    - every card as 3 of 0/0/100 with: only_three_ofs
                    - individual with: count_chances:<1of-chance>/<2of-chance>/<3of-chance> (e.g. count_chances:10/30/60)
                '''
                await channel.send(help_message)

            # individual deckroll
            elif message_content.startswith("!deckroll"):
                # change allowed_factions
                allowed_factions = deepcopy(all_factions_allowed)
                for faction in MAIN_FACTIONS:
                    if message_content.__contains__(f"no_{faction.lower()}"):
                        allowed_factions.remove(faction)
                for faction in MAIN_FACTIONS:
                    if message_content.__contains__(f"only_{faction.lower()}"):
                        allowed_factions = [faction]

                # card chances
                card_chances = deepcopy(card_chances_default)
                # set chances of factions cards so high, that half of the rolled cards are from the faction
                if message_content.__contains__(
                    "half_faction_half_neutral"
                ):
                    card_chances = deepcopy(card_chances_half_faction_half_neutral)
                # exclude neutral cards
                elif message_content.__contains__("only_faction"):
                    card_chances = deepcopy(card_chances_only_faction)
                # exclude by rarity
                for rarity in RARITIES:
                    if message_content.__contains__(f"no_{rarity.lower()}"):
                        for collectible_card in all_collectible_cards:
                            if collectible_card.rarity == rarity:
                                card_chances[collectible_card.id] = 0.0

                # count chances and count chances two remaining deck slots
                count_chances = count_chances_default
                count_chances_two_remaining_deck_slots = count_chances_two_remaining_deck_slots_default
                if message_content.__contains__("singleton"):
                    count_chances = count_chances_singleton
                    count_chances_two_remaining_deck_slots = (
                        count_chances_two_remaining_deck_slots_singleton
                    )
                elif message_content.__contains__("only_three_ofs"):
                    count_chances = count_chances_only_three_ofs
                count_chances_regex = r".*count_chances:(\d+)/(\d+)/(\d+).*"
                count_chances_regex_match = re.match(count_chances_regex, message_content)
                if bool(count_chances_regex_match):
                    count_chances_one_ofs = int(count_chances_regex_match.group(1))
                    count_chances_two_ofs = int(count_chances_regex_match.group(2))
                    count_chances_three_ofs = int(count_chances_regex_match.group(3))
                    if sum([count_chances_one_ofs, count_chances_two_ofs, count_chances_three_ofs]) != 100:
                        await channel.send("individual count chances found, but their sum is not 100")
                        raise ValueError("individual count chances found, but their sum is not 100")
                    count_chances = { 1: count_chances_one_ofs/100, 2: count_chances_two_ofs/100, 3: count_chances_three_ofs/100 }

                try:
                    deck_roll = Deckroll(
                        allowed_factions=allowed_factions,
                        card_chances=card_chances,
                        count_chances=count_chances,
                        count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots,
                    )
                except Exception:
                    await channel.send("Error while initialising Deckroll occured")
                try:
                    deckcode = deck_roll.roll_deck()
                except Exception:
                    await channel.send("Error while rolling deck occured - probably too small card pool")
                if SEND_DECKCODE:
                    await channel.send(deckcode)
                if SEND_DECKLINK:
                    await channel.send(DECKLINK_PREFIX + deckcode)

    client.run(token=TOKEN)


if __name__ == "__main__":
    run_discord_bot()
