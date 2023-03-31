from typing import List, Dict, DefaultDict, Literal
from CardData import CardData
import requests
import json
from collections import defaultdict


class CardPool:
    def __init__(self, legacy: bool) -> None:
        '''init card pool'''
        if legacy:
            print("Initializing Legacy CardPool")
        else:
            print("Initializing Duelyst II CardPool")
        self.legacy = legacy
        self.all_cards: List[CardData] = []
        self.generals: List[CardData] = []
        self.generals_by_faction: DefaultDict[Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar"], List[CardData]] = defaultdict(lambda: [])
        self.collectible_cards: List[CardData] = []
        self.collectible_cards_by_faction: DefaultDict[Literal["Lyonar", "Songhai", "Vetruvian", "Abyssian", "Magmar", "Vanar", "Neutral"], List[CardData]] = defaultdict(lambda: [])

        # get all cards, legacy / new
        DUELYST_API = "https://api.duelyst2.com/"
        CARDS_JSON = "cards.json"
        LEGACY_CARDS_JSON = "legacy-cards.json"
        if legacy:
            r = requests.get(f"{DUELYST_API}{LEGACY_CARDS_JSON}")
        else:
            r = requests.get(f"{DUELYST_API}{CARDS_JSON}")
        if r.status_code == 200:
            all_cards_json: List[Dict] = json.loads(r.text)
            print(f"Retrieved {len(all_cards_json)} cards from the API")
        else:
            if legacy:
                with open(LEGACY_CARDS_JSON, encoding="UTF-8") as f:
                    cards_json = f.read()
                    all_cards_json: List[Dict] = json.loads(cards_json)
            else:
                with open(CARDS_JSON, encoding="UTF-8") as f:
                    cards_json = f.read()
                    all_cards_json: List[Dict] = json.loads(cards_json)
            print(f"API Request failed, using local cards.json file, which includes {len(all_cards_json)} cards")
        for card in all_cards_json:
            self.all_cards.append(CardData(card))
        print(f"CardPool initialized with {len(self.all_cards)} total cards")

        # categorize cards
        for card in self.all_cards:
            # Gauntlet cards, that can't be used normally
            if card.card_set != "Gauntlet Specials":
                if card.card_type == "General":
                    self.generals.append(card)
                    self.generals_by_faction[card.faction].append(card)
                if card.rarity in ["Common", "Rare", "Epic", "Legendary"]:
                    self.collectible_cards.append(card)
                    self.collectible_cards_by_faction[card.faction].append(card)
        print(f"CardPool initialized with {len(self.generals)} generals")
        print(f"CardPool initialized with {len(self.collectible_cards)} collectible cards")

        # Order in the card lists
        # Lyonar
        # Songhai
        # Vetruvian
        # Abyssian
        # Magmar
        # Vanar
        # Neutral

        kierans_legacy_ban_list = [
            "Call to Arms", "Ironcliffe Monument", "Grand Strategos", "Indominus", "Prominence", "Alabaster Titan" \
            "Seeker Squad", "Hideatsu the Ebon Ox" "Grandmaster Zendo", \
            "Nimbus", "Simulacra Obelysk", "Monolithic Vision", "Khanuum-ka", "Notion of Starless Eternity", "Swarmking Scarab", "Cataclysmic Fault", "Grandmaster Nosh-Rak", \
            "Gate to the Undervault", "Moonrider", "Grandmaster Variax", "Nightmare Operant", "Underlord Xor'Xuul", "Doom", \
            "Rizen", "Biomimetic Hulk", "Armada", "Dorgon", "Gigaloth", "Progenitor", "Hatefurnace", "Zoetic Charm", "Chrysalis Burst", "Grandmaster Kraigon", "Juggernaut", "Moloki Huntress", \
            "Draugar Eyolith", "Oak in the Nemeton", "Drake Dowager", "Ice Age", \
            "Bloodbound Mentor", "Bloodsworn Gambler", "Alcuin Fugitive", "Grimes", "Meltdown", "Timekeeper", "Mnemovore", "Blue Conjurer", "Blood Taura", "Grailmaster", "Worldcore Golem"
        ]

        # No Neutral Hard Removal
        legacy_hard_removal = [
            "Aperions Claim", "Decimate", "Martyrdom", \
            "Eternity Painter", "Bamboozle", "Onyx Bear Seal", \
            "Blood of Air", "Circle of Desiccation", "Entropic Decay", "Wither", \
            "Dark Transformation", "Necrotic Sphere", "Ritual Banishing", \
            "Egg Morph", "Metamorphosis", "Natural Selection", "Plasma Storm", \
            "Aspect of the Ravager", "Aspect of Shim'Zar", "Aspect of the Bear", "Aspect of Ego", "Aspect of the Mountains", "Hailstone Prison"
        ]

        legacy_soft_removal = [
            "Sunstrike", "Lucent Beam", "Arclyte Sentinel", "Holy Immolation", "Sky Burial", "Circle of Life", "Tempest", "Draining Wave", "Lasting Judgement", "Sun Bloom", \
            "Phoenix Fire", "Phoenix Barrage", "Cobra Strike", "Ghost Lightning", "Gotatsu", "Spiral Technique", "Thunderbomb", \
            "Bone Swarm", "Lost in the Desert", "Sand Trap", "Siphon Energy", \
            "Breath Of The Unborn", "Betrayal", "Daemonic Lure", "Grasp of Agony", "Spectral Blade", \
            "Elucidator", "Makantor Warbeast", "Spirit Harvester", \
            "Chromatic Cold", "Cryogenesis", "Flash Freeze", "Mana Deathgrip", "Enfeeble", "Blinding Snowstorm", \
            "Ephemeral Shroud", "Repulsor Beast", "Bloodtear Alchemist", "Blistering Skorn", "Bonereaper", "Dancing Blades", "Dust Wailer", "EMP", "Fizzling Mystic", "Frostbone Naga", "Ironclad", "Lightbender", "Red Synja", "Riftwalker", "Rokadoptera", "Saberspine Tiger", "Saberspine Alpha"
        ]

        if legacy:
            self.kierans_legacy_ban_list_card_ids: List[int] = []
            self.legacy_all_removal_card_ids: List[int] = []
            self.legacy_hard_removal_card_ids: List[int] = []
            self.legacy_soft_removal_card_ids: List[int] = []
            for collectible_card in self.collectible_cards:
                if collectible_card.name in kierans_legacy_ban_list:
                    self.kierans_legacy_ban_list_card_ids.append(collectible_card.id)
                if collectible_card.name in legacy_hard_removal:
                    self.legacy_hard_removal_card_ids.append(collectible_card.id)
                if collectible_card.name in legacy_soft_removal:
                    self.legacy_soft_removal_card_ids.append(collectible_card.id)
            self.legacy_all_removal_card_ids = list(set(self.legacy_hard_removal_card_ids + self.legacy_soft_removal_card_ids))
            print(f"CardPool kierans ban list initialized with {len(self.kierans_legacy_ban_list_card_ids)} card ids from the {len(kierans_legacy_ban_list)} card names")
            print(f"CardPool hard removal list initialized with {len(self.legacy_hard_removal_card_ids)} card ids from the {len(legacy_hard_removal)} card names")
            print(f"CardPool soft removal list initialized with {len(self.legacy_soft_removal_card_ids)} card ids from the {len(legacy_soft_removal)} card names")
            print(f"CardPool all removal list initialized with {len(self.legacy_all_removal_card_ids)} card ids")

    def get_card_data_by_card_id(self, card_id: int) -> CardData:
        for card in self.all_cards:
            if card.id == card_id:
                return card
        raise ValueError("No card with the card id {card_id} found")
        