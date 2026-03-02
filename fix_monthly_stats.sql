-- Добавляем недостающие колонки
ALTER TABLE monthly_stats ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE monthly_stats ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Добавляем недостающие колонки в user_words если их нет
ALTER TABLE user_words ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE user_words ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();