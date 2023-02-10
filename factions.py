from typing import Dict, List

MAIN_FACTIONS: List[str] = [
    "Lyonar",
    "Songhai",
    "Vetruvian",
    "Abyssian",
    "Magmar",
    "Vanar",
]

FACTIONS_DICT: Dict[int, str] = {
    1: "Lyonar",
    2: "Songhai",
    3: "Vetruvian",
    4: "Abyssian",
    5: "Magmar",
    6: "Vanar",
    100: "Neutral",
}


def get_faction_str_from_faction_int(faction_int: int) -> str:
    if faction_int not in FACTIONS_DICT.keys():
        raise ValueError(
            f"The given faction_int {faction_int} is not in FACTIONS_DICT keys {FACTIONS_DICT.keys()}"
        )
    else:
        return FACTIONS_DICT[faction_int]
