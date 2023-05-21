from CardPool import CardPool
from Deckroll import Deckroll, DECKROLL_ATTEMPTS, DECKROLL_MODIFICATION_NOT_GIVEN
import discord
from copy import deepcopy
import re
from typing import Dict, Literal
from CardData import RARITIES, MAIN_FACTIONS
from tenacity import RetryError
import logging
import textwrap
from Draft import Draft, REACTIONS_NUMBERS
from constants import DECKLINK_PREFIX, LEGACY_DECKLINK_PREFIX

MAX_CARD_WEIGHT_CHANGE_FACTOR = 10000
MAX_FACTION_WEIGHT = 100000
MAX_CARDS = 100

# Formatter, Stream Handler, File Handler, Logger
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

fh = logging.FileHandler("debug.log")
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(ch)
logger.addHandler(fh)

class DiscordBot(discord.Client):
    def __init__(
        self,
        card_pool: CardPool,
        legacy_card_pool: CardPool,
        amount_cards_default: int,
        factions_and_weights_default: Dict[Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"], int],
        cards_and_weights_default: Dict[int, float],
        legacy_cards_and_weights_default: Dict[int, float],
        cards_and_weights_half_faction_half_neutral: Dict[int, float],
        legacy_cards_and_weights_half_faction_half_neutral: Dict[int, float],
        cards_and_weights_only_faction: Dict[int, float],
        legacy_cards_and_weights_only_faction: Dict[int, float],
        count_chances_default: Dict[int, float],
        count_chances_two_remaining_deck_slots_default: Dict[int, float],
        min_1_and_2_drops_default: int,
        max_1_and_2_drops_default: int,
    ) -> None:
        self.card_pool = card_pool
        self.legacy_card_pool = legacy_card_pool
        self.amount_cards_default = amount_cards_default
        self.factions_and_weights_default = factions_and_weights_default
        self.cards_and_weights_default = cards_and_weights_default
        self.legacy_cards_and_weights_default = legacy_cards_and_weights_default
        self.cards_and_weights_half_faction_half_neutral = cards_and_weights_half_faction_half_neutral
        self.legacy_cards_and_weights_half_faction_half_neutral = legacy_cards_and_weights_half_faction_half_neutral
        self.cards_and_weights_only_faction = cards_and_weights_only_faction
        self.legacy_cards_and_weights_only_faction = legacy_cards_and_weights_only_faction
        self.count_chances_default = count_chances_default
        self.count_chances_two_remaining_deck_slots_default = count_chances_two_remaining_deck_slots_default
        self.min_1_and_2_drops_default = min_1_and_2_drops_default
        self.max_1_and_2_drops_default = max_1_and_2_drops_default
        self.faction_offers_default = 3
        self.card_offers_per_pick_default = 3
        self.cards_to_choose_per_pick_default = 1
        self.card_bucket_size_default = 1
        self.drafts: Dict[int, Draft] = {}

        # START DISCORD BOT
        with open("discord_bot_token.key") as file:
            token = file.read()
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.run(token=token)

    async def on_ready(self):
        logger.info("I am ready to start rolling!")

    async def on_message(self, message: discord.Message):
        if isinstance(message.content, str):
            message_content: str = message.content.lower()
            if message_content.startswith("!deckroll") or message_content.startswith("!draft"):
                logger.info(f"Message from {message.author}: {message_content}")

            # DECKROLL HELP
            if message_content == "!deckroll help":
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
                """
                embed = discord.Embed(
                    title=title, description=help_message, color=0xF90202
                )
                await message.channel.send(embed=embed)

            # DECKROLL
            elif message_content.startswith("!deckroll"):
                legacy = await self._get_format(message_content=message_content)
                if legacy:
                    cards_and_weights = deepcopy(self.legacy_cards_and_weights_default)
                    card_pool = self.legacy_card_pool
                else:
                    cards_and_weights = deepcopy(self.cards_and_weights_default)
                    card_pool = self.card_pool

                amount_cards = await self._get_amount_cards(message_content=message_content, message=message)
                cards_and_weights = await self._get_cards_and_weights(message_content=message_content, message=message, legacy=legacy)
                await self._change_card_weights_based_on_their_rarity(message_content=message_content, message=message, cards_and_weights=cards_and_weights, card_pool=card_pool)
                factions_and_weights = await self._get_factions_and_weights(message_content=message_content, message=message)
                count_chances = await self._get_count_chances(message_content=message_content, message=message)
                count_chances_two_remaining_deck_slots = await self._get_count_chances_two_remaining_deck_slots(message_content=message_content, message=message)
                min_1_and_2_drops = await self._get_min_1_and_2_drops(message_content=message_content, message=message, amount_cards=amount_cards)
                max_1_and_2_drops = await self._get_max_1_and_2_drops(message_content=message_content, message=message, min_1_and_2_drops=min_1_and_2_drops)
                        
                deck_roll = Deckroll(
                    card_pool=card_pool,
                    amount_cards=amount_cards,
                    factions_and_weights=factions_and_weights,
                    cards_and_weights=cards_and_weights,
                    count_chances=count_chances,
                    count_chances_two_remaining_deck_slots=count_chances_two_remaining_deck_slots,
                    min_1_and_2_drops=min_1_and_2_drops,
                    max_1_and_2_drops=max_1_and_2_drops,
                    )

                try:
                    deckcode = deck_roll.roll_deck()
                except RetryError as e:
                    await message.channel.send(f"Even after {DECKROLL_ATTEMPTS} rolls no valid deck could be rolled for the given settings")
                    raise RetryError(f"Even after {DECKROLL_ATTEMPTS} rolls no valid deck could be rolled for the given settings")
                logger.info(f"the deckroll gave:  {deckcode}")
                
                if legacy:
                    await message.channel.send(LEGACY_DECKLINK_PREFIX + deckcode)
                else:
                    await message.channel.send(DECKLINK_PREFIX + deckcode)

            # DRAFT HELP
            elif message_content == "!draft help":
                title = "Draft help"
                help_message = """
                The bot is open source and can be found under:
                https://github.com/Ghostdriver/Duelyst-Deckroll

                The implemented drafting function lets you draft a deck with individual modifications with only reactions!

                the default draft (!draft) can be indivualized with the following modifications
                (combine them as you want, but wrong inputs and e.g. excluding all cards will return an error or just give no response,
                also if the modification doesn't get noticed by the input parser it just gets ignored):
                the deckroll modifications can be usedif they make sense in the context of drafting
                --> use "!deckroll help" to get more information
                Additionally the following modifications are possible:

                faction-offers=x --> How many factions you want to get offered, while drafting the factions (has to be between 1 and 6)

                card-offers-per-pick=x --> How many cards you want to get offered, while drafting the cards (has to be between 2 and 10)
                cards-to-choose-per-pick=x --> How many of the offered cards have to be picked with every pick

                card-bucket-size=x --> The deck is drafted from buckets with multiple cards (up to 5 for now)
                (can't be used together with cards_to_choose_per_pick (atleast for now))
                """
                embed = discord.Embed(
                    title=title, description=help_message, color=0xF90202
                )
                await message.channel.send(embed=embed)

            # ABANDON DRAFT
            elif message_content == "!abandon draft":
                message_id_of_ongoing_draft = False
                for message_id, draft in self.drafts.items():
                    if draft.user == message.author:
                        message_id_of_ongoing_draft = message_id
                if  message_id_of_ongoing_draft:
                    await self.drafts[message_id].abandon()
                    del self.drafts[message_id]

            # DRAFT
            elif message_content.startswith("!draft"):
                user_has_ongoing_draft = False
                for draft in self.drafts.values():
                    if draft.user == message.author:
                        user_has_ongoing_draft = True
                        await message.channel.send(content=textwrap.dedent(f"""
                            You have an already ongoing draft!
                            You can go to the draft message with this link ({draft.draft_message.jump_url})
                            or abandon that draft with the command:
                            !abandon draft
                        """))
                if not user_has_ongoing_draft:
                    # DECKROLL OPTIONS
                    legacy = await self._get_format(message_content=message_content)
                    if legacy:
                        cards_and_weights = deepcopy(self.legacy_cards_and_weights_default)
                        card_pool = self.legacy_card_pool
                    else:
                        cards_and_weights = deepcopy(self.cards_and_weights_default)
                        card_pool = self.card_pool

                    amount_cards = await self._get_amount_cards(message_content=message_content, message=message)
                    cards_and_weights = await self._get_cards_and_weights(message_content=message_content, message=message, legacy=legacy)
                    await self._change_card_weights_based_on_their_rarity(message_content=message_content, message=message, cards_and_weights=cards_and_weights, card_pool=card_pool)
                    factions_and_weights = await self._get_factions_and_weights(message_content=message_content, message=message)

                    # DRAFT OPTIONS
                    faction_offers = await self._get_faction_offers(message_content=message_content, message=message)
                    card_offers_per_pick = await self._get_card_offers_per_pick(message_content=message_content, message=message)
                    cards_to_choose_per_pick = await self._get_cards_to_choose_per_pick(message_content=message_content, message=message, card_offers_per_pick=card_offers_per_pick)
                    card_bucket_size = await self._get_card_bucket_size(message_content=message_content, message=message, cards_to_choose_per_pick=cards_to_choose_per_pick)

                    draft_message = await message.channel.send(content="Let's start drafting :)")
                    self.drafts[draft_message.id] = Draft(draft_init_message_content=message_content, draft_message=draft_message, discord_bot_user=self.user, user=message.author, card_pool=card_pool, amount_cards=amount_cards, factions_and_weights=factions_and_weights, cards_and_weights=cards_and_weights, faction_offers=faction_offers, card_offers_per_pick=card_offers_per_pick, cards_to_choose_per_pick=cards_to_choose_per_pick, card_bucket_size=card_bucket_size)
                    await self.drafts[draft_message.id].start_draft()

    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user != self.user and reaction.emoji in REACTIONS_NUMBERS.keys() and reaction.message.id in self.drafts.keys() and user == self.drafts[reaction.message.id].user:
            # Prevents the user to add reaction, that are out of bounds for the current choices
            if REACTIONS_NUMBERS[reaction.emoji] >= len(self.drafts[reaction.message.id].current_choices):
                await reaction.remove(user)
            else:
                draft_finished = await self.drafts[reaction.message.id].user_adds_reaction(reaction=reaction)
                await self.drafts[reaction.message.id].update_draft_message()
                if draft_finished:
                    del self.drafts[reaction.message.id]
            

        # Prevents other users to add emojis and other emojis to be added to drafting messages
        elif user != self.user and reaction.message.id in self.drafts.keys():
            await reaction.remove(user)
    
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        if user != self.user and reaction.emoji in REACTIONS_NUMBERS.keys() and reaction.message.id in self.drafts.keys() and user == self.drafts[reaction.message.id].user:
            if reaction in self.drafts[reaction.message.id].current_reactions:
                self.drafts[reaction.message.id].current_reactions.remove(reaction)

    async def _get_format(self, message_content: str) -> bool:
        return True if "legacy" in message_content else False

    async def _get_amount_cards(self, message_content: str, message: discord.Message) -> int:
        amount_cards = self.amount_cards_default
        amount_cards_regex = r".*cards=(\d+).*"
        amount_cards_regex_match = re.match(amount_cards_regex, message_content)
        if bool(amount_cards_regex_match):
            amount_cards = int(amount_cards_regex_match.group(1))
            if amount_cards < 1:
                error = f"detected a given amount of cards of {amount_cards}, but the amount of cards can not be less than 1!"
                await message.channel.send(error)
                raise ValueError(error)
            if amount_cards > MAX_CARDS:
                error = f"detected a given amount of cards of {amount_cards}, but the amount of cards can not be greater than {MAX_CARDS}!"
                await message.channel.send(error)
                raise ValueError(error)
        return amount_cards
    
    async def _get_factions_and_weights(self, message_content: str, message: discord.Message) -> Dict[str, int]:
        factions_and_weights = deepcopy(self.factions_and_weights_default)
        for faction_name in MAIN_FACTIONS:
            faction_weight_change_regex = rf".*{faction_name.lower()}=(\d+).*"
            faction_weight_change_regex_match = re.match(faction_weight_change_regex, message_content)
            if bool(faction_weight_change_regex_match):
                faction_weight_change = int(faction_weight_change_regex_match.group(1))
                factions_and_weights[faction_name] = faction_weight_change
                if faction_weight_change > MAX_FACTION_WEIGHT:
                    error = f"detected faction weight change for faction {faction_name} with the value {faction_weight_change} - only values between 0 and {MAX_FACTION_WEIGHT} are allowed."
                    await message.channel.send(error)
                    raise ValueError(error)
        return factions_and_weights
    
    async def _get_cards_and_weights(self, message_content: str, message: discord.Message, legacy: bool) -> Dict[int, float]:
        # default: all cards are equally likely
        if legacy:
            cards_and_weights = deepcopy(self.legacy_cards_and_weights_default)
        else:
            cards_and_weights = deepcopy(self.cards_and_weights_default)
        # half-faction-half-neutral
        if "half-faction-half-neutral" in message_content:
            if legacy:
                cards_and_weights = deepcopy(self.legacy_cards_and_weights_half_faction_half_neutral)
            else:
                cards_and_weights = deepcopy(self.cards_and_weights_half_faction_half_neutral)
        # only faction
        elif "only-faction" in message_content:
            if legacy:
                cards_and_weights = deepcopy(self.legacy_cards_and_weights_only_faction)
            else:
                cards_and_weights = deepcopy(self.cards_and_weights_only_faction)
        return cards_and_weights
    
    async def _change_card_weights_based_on_their_rarity(self, message_content: str, message: discord.Message, cards_and_weights: Dict[str, int], card_pool: CardPool) -> None:
        for rarity in RARITIES:
            card_weight_change_regex = rf".*{rarity.lower()}=(\d+).*"
            card_weight_change_regex_match = re.match(card_weight_change_regex, message_content)
            if bool(card_weight_change_regex_match):
                card_weight_change_factor = int(card_weight_change_regex_match.group(1))
                if card_weight_change_factor > MAX_CARD_WEIGHT_CHANGE_FACTOR:
                    error = f"detected card weight change for rarity {rarity} with the value {card_weight_change_factor} - only values between 0 and {MAX_CARD_WEIGHT_CHANGE_FACTOR} are allowed."
                    await message.channel.send(error)
                    raise ValueError(error)
                for collectible_card in card_pool.collectible_cards:
                    if collectible_card.rarity.lower() == rarity.lower():
                        cards_and_weights[collectible_card.id] *= card_weight_change_factor

    async def _get_count_chances(self, message_content: str, message: discord.Message) -> Dict[int, int]:
        count_chances = deepcopy(self.count_chances_default)
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
                await message.channel.send(error)
                raise ValueError(error)
        return count_chances
    
    async def _get_count_chances_two_remaining_deck_slots(self, message_content: str, message: discord.Message) -> Dict[int, int]:
        count_chances_two_remaining_deck_slots = deepcopy(self.count_chances_two_remaining_deck_slots_default)
        count_chances_two_remaining_deck_slots_regex = r".*count-chances-two-remaining-deck-slots=(\d+)/(\d+).*"
        count_chances_two_remaining_deck_slots_regex_match = re.match(count_chances_two_remaining_deck_slots_regex, message_content)
        if bool(count_chances_two_remaining_deck_slots_regex_match):
            count_chances_two_remaining_deck_slots_one_ofs = int(count_chances_two_remaining_deck_slots_regex_match.group(1))
            count_chances_two_remaining_deck_slots_two_ofs = int(count_chances_two_remaining_deck_slots_regex_match.group(2))
            count_chances_two_remaining_deck_slots = {
                1: count_chances_two_remaining_deck_slots_one_ofs,
                2: count_chances_two_remaining_deck_slots_two_ofs,
            }
            if (sum(list(count_chances_two_remaining_deck_slots.values())) != 100):
                error = f"detected count-chances-two-remaining-deck-slots (1/2 ofs) {count_chances_two_remaining_deck_slots_one_ofs}/{count_chances_two_remaining_deck_slots_two_ofs} -- the chances must sum up to 100!"
                await message.channel.send(error)
                raise ValueError(error)
        return count_chances_two_remaining_deck_slots
    
    async def _get_min_1_and_2_drops(self, message_content: str, message: discord.Message, amount_cards: int) -> int:
        min_1_and_2_drops = DECKROLL_MODIFICATION_NOT_GIVEN
        min_1_and_2_drops_regex = r".*min-1-and-2-drops=(\d+).*"
        min_1_and_2_drops_regex_regex_match = re.match(min_1_and_2_drops_regex, message_content)
        if bool(min_1_and_2_drops_regex_regex_match):
            min_1_and_2_drops = int(min_1_and_2_drops_regex_regex_match.group(1))
            if min_1_and_2_drops > amount_cards:
                error = f"The given amount of minimum 1 and 2 drops ({min_1_and_2_drops}) is higher than the given amount of total cards in the deck ({amount_cards})"
                await message.channel.send(error)
                raise ValueError(error)
        return min_1_and_2_drops
    
    async def _get_max_1_and_2_drops(self, message_content: str, message: discord.Message, min_1_and_2_drops: int) -> int:
        max_1_and_2_drops = DECKROLL_MODIFICATION_NOT_GIVEN
        max_1_and_2_drops_regex = r".*max-1-and-2-drops=(\d+).*"
        max_1_and_2_drops_regex_regex_match = re.match(max_1_and_2_drops_regex, message_content)
        if bool(max_1_and_2_drops_regex_regex_match):
            max_1_and_2_drops = int(max_1_and_2_drops_regex_regex_match.group(1))
            if max_1_and_2_drops < min_1_and_2_drops:
                error = f"The given amount of minimum 1 and 2 drops ({min_1_and_2_drops}) is higher than the given amount of maximum 1 and 2 drops ({max_1_and_2_drops})"
                await message.channel.send(error)
                raise ValueError(error)
        return max_1_and_2_drops
    
    # DRAFTING MODIFICATIONS
    async def _get_faction_offers(self, message_content: str, message: discord.Message) -> int:
        faction_offers = self.faction_offers_default
        faction_offers_regex = r".*faction-offers=(\d+).*"
        faction_offers_regex_match = re.match(faction_offers_regex, message_content)
        if bool(faction_offers_regex_match):
            faction_offers = int(faction_offers_regex_match.group(1))
            if faction_offers < 1 or faction_offers > 6:
                error = f"detected a given amount of faction_offers of {faction_offers}, but the amount of region_offers_per_pick has to be between 1 and 6!"
                await message.channel.send(error)
                raise ValueError(error)
        return faction_offers
    
    async def _get_card_offers_per_pick(self, message_content: str, message: discord.Message) -> int:
        card_offers_per_pick = self.card_offers_per_pick_default
        card_offers_per_pick_regex = r".*card-offers-per-pick=(\d+).*"
        card_offers_per_pick_regex_match = re.match(card_offers_per_pick_regex, message_content)
        if bool(card_offers_per_pick_regex_match):
            card_offers_per_pick = int(card_offers_per_pick_regex_match.group(1))
            if card_offers_per_pick < 2 or card_offers_per_pick > 10:
                error = f"detected a given amount of card_offers_per_pick of {card_offers_per_pick}, but the amount of card_offers_per_pick has to be between 2 and 10!"
                await message.channel.send(error)
                raise ValueError(error)
        return card_offers_per_pick
    
    async def _get_cards_to_choose_per_pick(self, message_content: str, message: discord.Message, card_offers_per_pick: int) -> int:
        cards_to_choose_per_pick = self.cards_to_choose_per_pick_default
        cards_to_choose_per_pick_regex = r".*cards-to-choose-per-pick=(\d+).*"
        cards_to_choose_per_pick_regex_match = re.match(cards_to_choose_per_pick_regex, message_content)
        if bool(cards_to_choose_per_pick_regex_match):
            cards_to_choose_per_pick = int(cards_to_choose_per_pick_regex_match.group(1))
            if cards_to_choose_per_pick < 1 or cards_to_choose_per_pick > 9:
                error = f"detected a given amount of card_offers_per_pick of {cards_to_choose_per_pick}, but the amount of cards_to_choose_per_pick has to be between 1 and 9!"
                await message.channel.send(error)
                raise ValueError(error)
            if cards_to_choose_per_pick >= card_offers_per_pick:
                error = f"detected a given amount of card_offers_per_pick of {cards_to_choose_per_pick} and a given amount of card_offers_per_pick of {card_offers_per_pick}, but the amount of cards_to_choose_per_pick has to be smaller than the amount of card_offers_per_pick"
                await message.channel.send(error)
                raise ValueError(error)
        return cards_to_choose_per_pick
    
    async def _get_card_bucket_size(self, message_content: str, message: discord.Message, cards_to_choose_per_pick: int) -> int:
        card_bucket_size = self.card_bucket_size_default
        card_bucket_size_regex = r".*card-bucket-size=(\d+).*"
        card_bucket_size_regex_match = re.match(card_bucket_size_regex, message_content)
        if bool(card_bucket_size_regex_match):
            card_bucket_size = int(card_bucket_size_regex_match.group(1))
            if card_bucket_size < 1 or card_bucket_size > 5:
                error = f"detected a given card_bucket_size of {card_bucket_size}, but the card_bucket_size has to be between 1 and 5!"
                await message.channel.send(error)
                raise ValueError(error)
            if card_bucket_size > 1 and cards_to_choose_per_pick > 1:
                error = f"Only one of card_bucket_size and cards_to_choose_per_pick can be greater than 1"
                await message.channel.send(error)
                raise ValueError(error)
        return card_bucket_size
