import enum

class CEFRLevel(enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class TranslationMode(enum.Enum):
    DE_TO_RU = "de_to_ru"
    RU_TO_DE = "ru_to_de"
    DE_TO_UK = "de_to_uk"  # Немецкий → Украинский
    UK_TO_DE = "uk_to_de"  # Украинский → Немецкий


class PartOfSpeech(enum.Enum):
    """Части речи"""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    PRONOUN = "pronoun"
    NUMERAL = "numeral"
    INTERJECTION = "interjection"
    PARTICLE = "particle"