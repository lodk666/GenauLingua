import enum

class CEFRLevel(enum.Enum):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"


class TranslationMode(enum.Enum):
    DE_TO_RU = "DE_TO_RU"
    RU_TO_DE = "RU_TO_DE"
    DE_TO_UK = "DE_TO_UK"
    UK_TO_DE = "UK_TO_DE"
    DE_TO_EN = "DE_TO_EN"  # <-- ЗАГЛАВНЫЕ
    EN_TO_DE = "EN_TO_DE"
    DE_TO_TR = "DE_TO_TR"
    TR_TO_DE = "TR_TO_DE"


class PartOfSpeech(enum.Enum):
    """Части речи"""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PHRASE = "phrase"
    PRONOUN = "pronoun"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    OTHER = "other"