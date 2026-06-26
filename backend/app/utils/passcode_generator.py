import random

# A clean, simple list of words to generate easy-to-remember, non-offensive passcodes.
WORDS = [
    "Crop", "Profession", "Substance", "Light", "River", "Canvas", "Mountain", "Glass",
    "Ocean", "Forest", "Desert", "Storm", "Valley", "Canyon", "Summit", "Stone",
    "Silver", "Golden", "Spring", "Summer", "Autumn", "Winter", "Shadow", "Beacon",
    "Bridge", "Castle", "Flame", "Frost", "Timber", "Meadow", "Cloud", "Star",
    "Planet", "Galactic", "Cosmos", "Wave", "Tide", "Pebble", "Feather", "Crystal",
    "Marble", "Amber", "Flint", "Spire", "Haven", "Shield", "Crown", "Voyager",
    "Pioneer", "Explorer", "Ranger", "Keeper", "Sentry", "Warden", "Scholar", "Artist"
]

def generate_passcode() -> str:
    """
    Generates a human-readable passcode for new students.
    Format: Word + Word + Word + Word + Number (1-9)
    """
    selected_words = [random.choice(WORDS) for _ in range(4)]
    number = random.randint(1, 9)
    return "".join(selected_words) + str(number)
