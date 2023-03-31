from CardPool import CardPool
from Deckroll import Deckroll, DECKROLL_ATTEMPTS, DECKROLL_MODIFICATION_NOT_GIVEN
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
LEGACY_DECKLINK_PREFIX: str = "https://dl.bagoum.com/deckbuilder#"

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

# default - all cards have the same chance
cards_and_weights_default: Dict[int, int] = {}
for collectible_card in card_pool.collectible_cards:
    cards_and_weights_default[collectible_card.id] = 1.0

legacy_cards_and_weights_default: Dict[int, int] = {}
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
min_total_removal_default = DECKROLL_MODIFICATION_NOT_GIVEN
min_hard_removal_default = DECKROLL_MODIFICATION_NOT_GIVEN
min_soft_removal_default = DECKROLL_MODIFICATION_NOT_GIVEN

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
min_total_removal = 6 # min_total_removal_default
min_hard_removal = min_hard_removal_default
min_soft_removal = min_soft_removal_default

if legacy:
    if kierans_ban_list:
        for card_id in legacy_card_pool.kierans_legacy_ban_list_card_ids:
            cards_and_weights[card_id] = 0
    deck_roll = Deckroll(card_pool=legacy_card_pool, amount_cards=amount_cards_default, factions_and_weights=factions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots, min_1_and_2_drops=min_1_and_2_drops, max_1_and_2_drops=max_1_and_2_drops, min_total_removal=min_total_removal, min_hard_removal=min_hard_removal, min_soft_removal=min_soft_removal)
else:
    deck_roll = Deckroll(card_pool=card_pool, amount_cards=amount_cards_default, factions_and_weights=factions_and_weights, cards_and_weights=cards_and_weights, count_chances=count_chances, count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots, min_1_and_2_drops=min_1_and_2_drops, max_1_and_2_drops=max_1_and_2_drops)

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

            if message_content.startswith(
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
                - "legacy" for legacy card pool 
                - cards=<number> --> cards=60
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
                - min-1-and-2-drops=<number>
                - max-1-and-2-drops=<number>
                (the deck is still created at random, the deck roll will roll a deck up to 100 times and afterwards check for number of 1 and 2 cost units)
                - only for legacy:
                    - kierans-ban-list to exclude cards, that can easily scale out of proportion
                    - min-total-removal=<number> --> total removal cards include hard and soft removal cards
                    - min-hard-removal=<number> --> hard removal cards are those, that destroy other cards from hand
                    - min-soft-removal=<number> --> soft removal cards are those, that damage or silence other cards from hand
                    (the deck is still created at random, the deck roll will roll a deck up to 100 times and afterwards check the amount of remvoal)
                """
                embed = discord.Embed(
                    title=title, description=help_message, color=0xF90202
                )
                await channel.send(embed=embed)

            # individual deckroll
            elif message_content.startswith("!deckroll"):
                # default values + legacy
                if "legacy" in message_content:
                    legacy = True
                    cards_and_weights = deepcopy(legacy_cards_and_weights_default)
                else:
                    legacy = False
                    cards_and_weights = deepcopy(cards_and_weights_default)

                amount_cards = amount_cards_default
                factions_and_weights = deepcopy(factions_and_weights_default)
                count_chances = deepcopy(count_chances_default)
                count_chances_two_remaining_deck_slots = deepcopy(count_chances_two_remaining_deck_slots_default)
                min_1_and_2_drops = min_1_and_2_drops_default
                max_1_and_2_drops = max_1_and_2_drops_default
                min_total_removal = min_total_removal_default
                min_hard_removal = min_hard_removal_default
                min_soft_removal = min_soft_removal_default
                
                # amount cards
                MAX_CARDS = 100
                amount_cards_regex = r".*cards=(\d+).*"
                amount_cards_regex_match = re.match(amount_cards_regex, message_content)
                if bool(amount_cards_regex_match):
                    amount_cards = int(amount_cards_regex_match.group(1))
                    if amount_cards < 1:
                        error = f"detected a given amount of cards of {amount_cards}, but the amount of cards can not be less than 1!"
                        await channel.send(error)
                        raise ValueError(error)
                    if amount_cards > MAX_CARDS:
                        error = f"detected a given amount of cards of {amount_cards}, but the amount of cards can not be greater than {MAX_CARDS}!"
                        await channel.send(error)
                        raise ValueError(error)

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
                    if legacy:
                        cards_and_weights = deepcopy(legacy_cards_and_weights_half_faction_half_neutral)
                    else:
                        cards_and_weights = deepcopy(cards_and_weights_half_faction_half_neutral)
                # only faction
                elif "only-faction" in message_content:
                    if legacy:
                        cards_and_weights = deepcopy(legacy_cards_and_weights_only_faction)
                    else:
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
                        if legacy:
                            for collectible_card in legacy_card_pool.collectible_cards:
                                if collectible_card.rarity.lower() == rarity.lower():
                                    cards_and_weights[collectible_card.id] *= card_weight_change_factor
                        else:
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
                
                # min-1-and-2-drops
                min_1_and_2_drops_regex = r".*min-1-and-2-drops=(\d+).*"
                min_1_and_2_drops_regex_regex_match = re.match(min_1_and_2_drops_regex, message_content)
                if bool(min_1_and_2_drops_regex_regex_match):
                    min_1_and_2_drops = int(min_1_and_2_drops_regex_regex_match.group(1))
                    if min_1_and_2_drops > amount_cards:
                        error = f"The given amount of minimum 1 and 2 drops ({min_1_and_2_drops}) is higher than the given amount of total cards in the deck ({amount_cards})"
                        await channel.send(error)
                        raise ValueError(error)
                    
                # max-1-and-2-drops
                max_1_and_2_drops_regex = r".*max-1-and-2-drops=(\d+).*"
                max_1_and_2_drops_regex_regex_match = re.match(max_1_and_2_drops_regex, message_content)
                if bool(max_1_and_2_drops_regex_regex_match):
                    max_1_and_2_drops = int(max_1_and_2_drops_regex_regex_match.group(1))
                    if max_1_and_2_drops < min_1_and_2_drops:
                        error = f"The given amount of minimum 1 and 2 drops ({min_1_and_2_drops}) is higher than the given amount of maximum 1 and 2 drops ({max_1_and_2_drops})"
                        await channel.send(error)
                        raise ValueError(error)

                if legacy:
                    # kierans-ban-list
                    if "kierans-ban-list" in message_content:
                        for card_id in legacy_card_pool.kierans_legacy_ban_list_card_ids:
                            cards_and_weights[card_id] = 0
                    # min-total-removal
                    min_total_removal_regex = r".*min-total-removal=(\d+).*"
                    min_total_removal_regex_match = re.match(min_total_removal_regex, message_content)
                    if bool(min_total_removal_regex_match):
                        min_total_removal = int(min_total_removal_regex_match.group(1))
                        if min_total_removal > amount_cards:
                            error = f"The given amount of total removal cards ({min_total_removal}) is higher than the given amount of total cards in the deck ({amount_cards})"
                            await channel.send(error)
                            raise ValueError(error)
                    # min-hard-removal
                    min_hard_removal_regex = r".*min-hard-removal=(\d+).*"
                    min_hard_removal_regex_match = re.match(min_hard_removal_regex, message_content)
                    if bool(min_hard_removal_regex_match):
                        min_hard_removal = int(min_hard_removal_regex_match.group(1))
                        if min_hard_removal > amount_cards:
                            error = f"The given amount of hard removal cards ({min_hard_removal}) is higher than the given amount of total cards in the deck ({amount_cards})"
                            await channel.send(error)
                            raise ValueError(error)
                    # min-soft-removal
                    min_soft_removal_regex = r".*min-soft-removal=(\d+).*"
                    min_soft_removal_regex_match = re.match(min_soft_removal_regex, message_content)
                    if bool(min_soft_removal_regex_match):
                        min_soft_removal = int(min_soft_removal_regex_match.group(1))
                        if min_soft_removal > amount_cards:
                            error = f"The given amount of soft removal cards ({min_soft_removal}) is higher than the given amount of total cards in the deck ({amount_cards})"
                            await channel.send(error)
                            raise ValueError(error)
                        
                if legacy:
                    deck_roll = Deckroll(
                        card_pool=legacy_card_pool,
                        amount_cards=amount_cards,
                        factions_and_weights=factions_and_weights,
                        cards_and_weights=cards_and_weights,
                        count_chances=count_chances,
                        count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots,
                        min_1_and_2_drops=min_1_and_2_drops,
                        max_1_and_2_drops=max_1_and_2_drops,
                        min_total_removal=min_total_removal,
                        min_hard_removal=min_hard_removal,
                        min_soft_removal=min_soft_removal
                    )
                else:
                    deck_roll = Deckroll(
                        card_pool=card_pool,
                        amount_cards=amount_cards,
                        factions_and_weights=factions_and_weights,
                        cards_and_weights=cards_and_weights,
                        count_chances=count_chances,
                        count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots,
                        min_1_and_2_drops=min_1_and_2_drops,
                        max_1_and_2_drops=max_1_and_2_drops
                    )

                try:
                    deckcode = deck_roll.roll_deck()
                except RetryError as e:
                    await channel.send(f"Even after {DECKROLL_ATTEMPTS} rolls no valid deck could be rolled for the given settings")
                    raise RetryError(f"Even after {DECKROLL_ATTEMPTS} rolls no valid deck could be rolled for the given settings")
                # print(f"{message.author.name}: {message_content} --> {deckcode}")
                if SEND_DECKCODE or legacy:
                    await channel.send(deckcode)
                if SEND_DECKLINK:
                    if legacy:
                        await channel.send(LEGACY_DECKLINK_PREFIX + deckcode)
                    else:
                        await channel.send(DECKLINK_PREFIX + deckcode)

    client.run(token=TOKEN)


if __name__ == "__main__":
    if CREATE_DECKROLL_EXCEL:
        if legacy:
            deck_roll.roll_deck_spreadsheat(
                amount_decks=AMOUNT_DECKS, decklink_prefix=LEGACY_DECKLINK_PREFIX
            )
        else:
            deck_roll.roll_deck_spreadsheat(
                amount_decks=AMOUNT_DECKS, decklink_prefix=DECKLINK_PREFIX
            )
    if START_DISCORD_BOT:
        start_discord_bot()
