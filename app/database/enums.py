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
