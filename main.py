from CardPool import CardPool
from Deckroll import Deckroll
import discord
from discord.ext import commands
from copy import deepcopy
import re
from typing import Dict
from CardData import RARITIES, ALL_FACTIONS, MAIN_FACTIONS
from tenacity import RetryError

# MAIN OPTIONS
CREATE_DECKROLL_EXCEL: bool = False
AMOUNT_DECKS: int = 100
START_DISCORD_BOT: bool = True
SEND_DECKCODE: bool = False
SEND_DECKLINK: bool = True
DECKLINK_PREFIX: str = "https://decklyst.vercel.app/decks/"

# DECKROLL OPTIONS

# faction_chances
factions_and_weights_default: Dict[str, int] = {}
for faction in MAIN_FACTIONS:
    factions_and_weights_default[faction] = 1

# card_chances
# prepare collectible card pool
card_pool = CardPool()
cards_per_faction: Dict[str, int] = {}
for faction in ALL_FACTIONS:
    cards_per_faction[faction] = len(card_pool.collectible_cards_by_faction[faction])
# print(cards_per_faction)

# default - all cards have the same chance
cards_and_weights_default: Dict[int, int] = {}
for collectible_card in card_pool.collectible_cards:
    cards_and_weights_default[collectible_card.id] = 1.0
# adjust faction card chances in a way, that they are equally likely as neutral cards
cards_and_weights_half_faction_half_neutral: Dict[int, int] = {}
for collectible_card in card_pool.collectible_cards:
    cards_and_weights_half_faction_half_neutral[collectible_card.id] = cards_per_faction["Neutral"] / cards_per_faction[collectible_card.faction]
# exclude neutral cards
cards_and_weights_only_faction: Dict[int, int] = {}
for collectible_card in card_pool.collectible_cards:
    if collectible_card.faction == "Neutral":
        cards_and_weights_only_faction[collectible_card.id] = 0.0
    else:
        cards_and_weights_only_faction[collectible_card.id] = 1.0

# count chances
count_chances_default: Dict[int, int] = {1: 20, 2: 30, 3: 50}

# count chances two remaining deck slots
count_chances_two_remaining_deck_slots_default: Dict[int, int] = {1: 33, 2: 67}
default_deck_roll = Deckroll(
    card_pool=card_pool,
    factions_and_weights=factions_and_weights_default,
    cards_and_weights=cards_and_weights_default,
    count_chances=count_chances_default,
    count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots_default
)

# INDIVIDUAL DECKROLL FOR EXCEL SPREADSHEAT - change the values to fit your needs!
factions_and_weights = deepcopy(factions_and_weights_default)
cards_and_weights = deepcopy(cards_and_weights_default)
count_chances = deepcopy(count_chances_default)
count_chances_two_remaining_deck_slots = deepcopy(count_chances_two_remaining_deck_slots_default)
# deck_roll = Deckroll(card_pool=card_pool, factions_and_weights=factions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots)
# print(deck_roll.roll_deck())

def start_discord_bot() -> None:
    # the following line will fail, because on git is not the discord bot token and I won't share it (security)
    # for personal use I think having the create excel spreadsheat command should be sufficient for most use cases
    # so if the script fails here please set START_DISCORD_BOT = False
    with open("discord_bot_token.key") as file:
        TOKEN = file.read()
    intents = discord.Intents.default()
    intents.message_content = True
    client = commands.Bot(command_prefix="!deckroll", intents=intents)

    @client.event
    async def on_message(message):
        channel = message.channel

        if isinstance(message.content, str):
            message_content: str = message.content.lower()

            # default deckroll
            if message_content == "!deckroll":
                deckcode = default_deck_roll.roll_deck()
                print(f"{message.author.name} {message_content} --> {deckcode}")
                if SEND_DECKCODE:
                    await channel.send(deckcode)
                if SEND_DECKLINK:
                    await channel.send(DECKLINK_PREFIX + deckcode)

            elif message_content.startswith(
                "!deckroll"
            ) and "help" in message_content:
                title = "The Duelyst Deckroll bot can be used for individual deckrolls"
                help_message = """
                The bot is open source and can be found under:
                https://github.com/Ghostdriver/Duelyst-Deckroll

                Short explanation of the deckroll functionality:
                - At first the faction (weighted to the given faction weights)
                - one of the 3 available faction generals is rolled and added to the deck
                - then the 39 deckslots are rolled card by card until the deck is full
                (the cards are chosen based on the given card weights and then the amount of the rolled card is rolled based on the count chances)

                For the default deckroll use: !deckroll
                The used settings are: all factions have the same chance, all cards have the same chance,
                card amount chances are for 1/2/3 ofs: 20%/30%/50%
                if only two cards remain following count chances are used 1/2 of 33%/67%

                this default deckroll can be indivualized with the following modifications (combine them as you want,
                but wrong inputs and e.g. excluding all cards will return an error or just give no response,
                also if the modification doesn't get noticed by the input parser it just gets ignored):
                - change faction weights (standard weight is 1) with <faction-name>=<number>
                e.g. exclude region Magmar=0 // make region very very likely Vetruvian=1000
                the correct faction names have to be used: Lyonar, Songhai, Vetruvian, Abyssian, Magmar, Vanar
                - card chances:
                - set chances of factions cards so high, that around half of the rolled cards will be from the rolled faction
                with: half-faction-half-neutral
                - exclude neutral cards with: only-faction
                - change card chances based on their rarity: <rarity>=<number> --> epic=10
                Rarities: common, rare, epic, legendary
                - count-chances=<number>/<number>/<number> --> count-chances=33/33/34 (1/2/3 ofs)
                - count-chances-two-remaining-deck-slots=<number>/<number> --> count-chances-two-remaining-deck-slots=50/50 (1/2 ofs)
                """
                embed = discord.Embed(
                    title=title, description=help_message, color=0xF90202
                )
                await channel.send(embed=embed)

            # individual deckroll
            elif message_content.startswith("!deckroll"):
                factions_and_weights = deepcopy(factions_and_weights_default)
                cards_and_weights = deepcopy(cards_and_weights_default)
                count_chances = deepcopy(count_chances_default)
                count_chances_two_remaining_deck_slots = deepcopy(count_chances_two_remaining_deck_slots_default)
                
                # factions
                MAX_FACTION_WEIGHT = 100000
                for faction_name in MAIN_FACTIONS:
                    faction_weight_change_regex = rf".*{faction_name.lower()}=(\d+).*"
                    faction_weight_change_regex_match = re.match(faction_weight_change_regex, message_content)
                    if bool(faction_weight_change_regex_match):
                        faction_weight_change = int(faction_weight_change_regex_match.group(1))
                        factions_and_weights[faction_name] = faction_weight_change
                        if faction_weight_change > MAX_FACTION_WEIGHT:
                            error = f"detected faction weight change for faction {faction_name} with the value {faction_weight_change} - only values between 0 and {MAX_FACTION_WEIGHT} are allowed."
                            await channel.send(error)
                            raise ValueError(error)

                # card chances
                # half-faction-half-neutral
                if "half-faction-half-neutral" in message_content:
                    cards_and_weights = deepcopy(cards_and_weights_half_faction_half_neutral)
                # only faction
                elif "only-faction" in message_content:
                    cards_and_weights = deepcopy(cards_and_weights_only_faction)
                # change them based on rarity
                MAX_CARD_WEIGHT_CHANGE_FACTOR = 10000
                for rarity in RARITIES:
                    card_weight_change_regex = rf".*{rarity.lower()}=(\d+).*"
                    card_weight_change_regex_match = re.match(card_weight_change_regex, message_content)
                    if bool(card_weight_change_regex_match):
                        card_weight_change_factor = int(card_weight_change_regex_match.group(1))
                        if card_weight_change_factor > MAX_CARD_WEIGHT_CHANGE_FACTOR:
                            error = f"detected card weight change for rarity {rarity} with the value {card_weight_change_factor} - only values between 0 and {MAX_CARD_WEIGHT_CHANGE_FACTOR} are allowed."
                            await channel.send(error)
                            raise ValueError(error)
                        for collectible_card in card_pool.collectible_cards:
                            if collectible_card.rarity.lower() == rarity.lower():
                                cards_and_weights[collectible_card.id] *= card_weight_change_factor
                            
                # count chances
                count_chances_regex = r".*count-chances=(\d+)/(\d+)/(\d+).*"
                count_chances_regex_match = re.match(count_chances_regex, message_content)
                if bool(count_chances_regex_match):
                    count_chances_one_ofs = int(count_chances_regex_match.group(1))
                    count_chances_two_ofs = int(count_chances_regex_match.group(2))
                    count_chances_three_ofs = int(count_chances_regex_match.group(3))
                    count_chances = {
                        1: count_chances_one_ofs,
                        2: count_chances_two_ofs,
                        3: count_chances_three_ofs,
                    }
                    if (sum(list(count_chances.values())) != 100):
                        error = f"detected count-chances (1/2/3 ofs) {count_chances_one_ofs}/{count_chances_two_ofs}/{count_chances_three_ofs} -- the chances must sum up to 100!"
                        await channel.send(error)
                        raise ValueError(error)
                    
                # count_chances_two_remaining_deck_slots
                count_chances_two_remaining_deck_slots_regex = r".*count-chances-two-remaining-deck-slots=(\d+)/(\d+).*"
                count_chances_two_remaining_deck_slots_regex_match = re.match(count_chances_two_remaining_deck_slots_regex, message_content)
                if bool(count_chances_two_remaining_deck_slots_regex_match):
                    count_chances_two_remaining_deck_slots_one_ofs = int(count_chances_two_remaining_deck_slots_regex_match.group(1))
                    count_chances_two_remaining_deck_slots_two_ofs = int(count_chances_two_remaining_deck_slots_regex_match.group(2))
                    count_chances_two_remaining_deck_slots = {
                        1: count_chances_two_remaining_deck_slots_one_ofs,
                        2: count_chances_two_remaining_deck_slots_two_ofs,
                    }
                    if (sum(list(count_chances.values())) != 100):
                        error = f"detected count-chances-two-remaining-deck-slots (1/2 ofs) {count_chances_two_remaining_deck_slots_one_ofs}/{count_chances_two_remaining_deck_slots_two_ofs} -- the chances must sum up to 100!"
                        await channel.send(error)
                        raise ValueError(error)

                deck_roll = Deckroll(
                    card_pool=card_pool,
                    factions_and_weights=factions_and_weights,
                    cards_and_weights=cards_and_weights,
                    count_chances=count_chances,
                    count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots,
                )
                try:
                    deckcode = deck_roll.roll_deck()
                except RetryError as e:
                    await channel.send("Even after 10 rolls no valid deck could be rolled for the given settings")
                    raise RetryError("Even after 10 rolls no valid deck could be rolled for the given settings")
                print(f"{message.author.name}: {message_content} --> {deckcode}")
                if SEND_DECKCODE:
                    await channel.send(deckcode)
                if SEND_DECKLINK:
                    await channel.send(DECKLINK_PREFIX + deckcode)

    client.run(token=TOKEN)


if __name__ == "__main__":
    if CREATE_DECKROLL_EXCEL:
        deck_roll = Deckroll(
            card_pool=card_pool,
            factions_and_weights=factions_and_weights,
            cards_and_weights=cards_and_weights,
            count_chances=count_chances,
            count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots
        )
        deck_roll.roll_deck_spreadsheat(
            amount_decks=AMOUNT_DECKS, decklink_prefix=DECKLINK_PREFIX
        )
    if START_DISCORD_BOT:
        start_discord_bot()
