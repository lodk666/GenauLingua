# Words Import System

## Purpose

This folder contains maintenance scripts for rebuilding the `words` table from Excel datasets.

The main script:

    rebuild_words_from_excel.py

This script is used to:
- Fully reset the `words` table
- Reset user quiz progress
- Import validated word datasets
- Normalize CEFR levels and Part of Speech enums

---

## Current Dataset

- **Total words:** 12,805
- **Levels:** A1, A2, B1, B2, C1, C2
- **Categories:** 21 thematic categories
- **Languages:** DE, RU, UK, EN, TR
- **Source file:** `de_PERFECT_FIXED.xlsx`

---

## Expected Excel Structure

| Column           | Description                          |
|------------------|--------------------------------------|
| word_de          | German word                          |
| article          | der/die/das or "-"                   |
| pos              | Part of Speech (NOUN, VERB, etc.)    |
| level            | CEFR level (A1–C2)                   |
| category         | Thematic category                    |
| frequency_rank   | Frequency rank (optional)            |
| translation_ru   | Russian translation                  |
| translation_uk   | Ukrainian translation                |
| translation_en   | English translation                  |
| translation_tr   | Turkish translation                  |
| example_de       | German example sentence              |
| example_ru       | Russian example sentence             |
| example_uk       | Ukrainian example sentence           |
| example_en       | English example sentence             |
| example_tr       | Turkish example sentence             |

---

## How To Rebuild Words Database

1) Start database:

       docker compose up -d

2) Run script (single file):

       docker compose run --rm app python app/scripts/rebuild_words_from_excel.py /app/Wordsbase/de_PERFECT_FIXED.xlsx

3) Run script (directory with multiple files):

       docker compose run --rm app python app/scripts/rebuild_words_from_excel.py /app/Wordsbase

4) Import without truncating existing data:

       docker compose run --rm app python app/scripts/rebuild_words_from_excel.py /app/Wordsbase --no-truncate

5) Verify:

       SELECT COUNT(*) FROM words;
       SELECT level, COUNT(*) FROM words GROUP BY level ORDER BY level;
       SELECT category, COUNT(*) FROM words GROUP BY category ORDER BY category;

---

## Important

- Excel files are local only (not committed to Git).
- Default mode TRUNCATES user progress. Use `--no-truncate` to preserve it.
- Always verify counts after import.

