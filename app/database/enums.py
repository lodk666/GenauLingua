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
    DE_TO_EN = "DE_TO_EN"
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


class QuizMode(enum.Enum):
    """Режим викторины"""
    LEVEL = "level"             # По уровню (A1–C2)
    CATEGORY = "category"       # По категории
    ALL_WORDS = "all_words"     # Топ 10К (вся база)
    DIFFICULT = "difficult"     # Сложные слова


class WordCategory(enum.Enum):
    """Категории слов (20 категорий)"""
    ARBEIT_BERUF = "Arbeit & Beruf"
    BILDUNG_LERNEN = "Bildung & Lernen"
    EINKAUFEN_GELD = "Einkaufen & Geld"
    EMOTIONEN_CHARAKTER = "Emotionen & Charakter"
    ESSEN_TRINKEN = "Essen & Trinken"
    FREIZEIT_SPORT = "Freizeit & Sport"
    GESUNDHEIT_MEDIZIN = "Gesundheit & Medizin"
    GRAMMATIK = "Grammatik"
    KLEIDUNG_MODE = "Kleidung & Mode"
    KOMMUNIKATION = "Kommunikation"
    KULTUR_KUNST = "Kultur & Kunst"
    MENSCH_FAMILIE = "Mensch & Familie"
    NATUR_WETTER = "Natur & Wetter"
    RECHT_STAAT = "Recht & Staat"
    REISEN_TRANSPORT = "Reisen & Transport"
    TECHNIK_DIGITAL = "Technik & Digital"
    WIRTSCHAFT = "Wirtschaft"
    WISSENSCHAFT = "Wissenschaft"
    WOHNEN_HAUS = "Wohnen & Haus"
    ZEIT_ALLTAG = "Zeit & Alltag"