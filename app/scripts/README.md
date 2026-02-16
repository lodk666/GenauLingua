# Words Import System

## Purpose

This folder contains maintenance scripts for rebuilding the `words` table
from Excel datasets (A1 / A2 / B1).

The main script:

rebuild_words_from_excel.py

This script is used to:
- Fully reset the `words` table
- Reset user quiz progress
- Import validated word datasets
- Normalize CEFR levels and Part of Speech enums

---

# Current Dataset

Imported levels:
- A1
- A2
- B1

Total words: 3081

Languages supported:
- German (word_de)
- Russian (translation_ru, example_ru)
- Ukrainian (translation_uk, example_uk)

---

# Expected Excel Structure

Each Excel file must contain the following columns:

| Column Name        | Description                          |
|-------------------|--------------------------------------|
| word_de            | German word                          |
| article            | der/die/das or "-"                   |
| pos                | Part of Speech (see enum below)      |
| level              | CEFR level (A1/A2/B1)                |
| translation_ru     | Russian translation                  |
| translation_uk     | Ukrainian translation                |
| example_de         | German example sentence              |
| example_ru         | Russian example sentence             |
| example_uk         | Ukrainian example sentence           |

---

# POS Enum (Database)

Allowed values:

- NOUN
- VERB
- ADJECTIVE
- ADVERB
- PRONOUN
- PREPOSITION
- CONJUNCTION
- PHRASE
- OTHER

If a new POS is added:
1. Update DB enum
2. Update script mapping
3. Rebuild database

---

# Database Schema (words table)

Main fields:

- id (PK)
- word_de
- article
- pos (enum)
- level (enum)
- translation_ru
- translation_uk
- example_de
- example_ru
- example_uk
- times_shown
- times_correct
- created_at

---

# How To Rebuild Words Database

1) Start database:
   docker compose up -d

2) Run script:
   python app/scripts/rebuild_words_from_excel.py

3) Verify:

Total:
SELECT COUNT(*) FROM words;

By level:
SELECT level, COUNT(*) FROM words GROUP BY level ORDER BY level;

Check empty translations:
SELECT COUNT(*) FROM words WHERE translation_uk IS NULL OR translation_uk='';
SELECT COUNT(*) FROM words WHERE example_uk IS NULL OR example_uk='';

---

# Important

- Excel files are local only (not committed to Git).
- Rebuild script TRUNCATES user progress.
- Use with caution in production.
- Always verify counts after import.

---

# Future Extension

If adding a new language (e.g. English):

1. Add new DB columns (translation_en, example_en)
2. Update script payload mapping
3. Update quiz logic
4. Rebuild database
5. Verify data integrity

