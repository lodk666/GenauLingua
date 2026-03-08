"""
Türkçe lokalizasyon - GenauLingua Bot
"""

TEXTS = {
    # ============================================================================
    # ANA MENÜ BUTONLARI
    # ============================================================================
    "btn_learn_words": "📚 Kelime öğren",
    "btn_stats": "📊 İstatistik",
    "btn_settings": "🦾 Ayarlar",
    "btn_help": "❓ Yardım",
    "btn_back": "◀️ Geri",
    "menu_placeholder": "Bir eylem seç...",

    # ============================================================================
    # KARŞILAMA VE BAŞLANGIÇ
    # ============================================================================
    "welcome_title": "👋 <b>Merhaba, {name}!</b>",
    "welcome_description": "🇩🇪 <b>GenauLingua</b> — her gün Almanca öğren.\nBot sonuçlarını analiz eder ve sana özel kelimeler seçer.",
    "welcome_separator": "──────────────────",

    "welcome_learn_words_title": "📚 <b>Kelime öğren</b>",
    "welcome_learn_words_desc": "Almanca kelimelerle eğlenceli testler. Ne kadar çok pratik yaparsan — kelime seçimi o kadar akıllı olur.",

    "welcome_stats_title": "📊 <b>İstatistik</b>",
    "welcome_stats_desc": "Seviyeye göre ilerleme, test geçmişi, diğer kullanıcılarla karşılaştırma.",

    "welcome_settings_title": "🦾 <b>Ayarlar</b>",
    "welcome_settings_desc": "Seviye (A1–C2), arayüz dili, test modu.",

    "welcome_help_title": "❓ <b>Yardım</b>",
    "welcome_help_desc": "İpuçları, son güncellemeler ve geri bildirim.",

    "welcome_your_level": "Seviyeniz: <b>{level}</b>\nMod: <b>{mode}</b>",
    "welcome_call_to_action": "📚 Kelime öğren'e bas — başlayalım!",

    "welcome_choose_level": "Önce Almanca seviyeni seç:",
    "choose_level_prompt": "Seviye seç:",

    "level_selected": "✅ <b>{level}</b> seviyesi seçildi.\n\n📚 Kelime öğren'e bas — başlayalım!",
    "level_locked": "🔒 Bu seviye yakında geliyor",

    # ============================================================================
    # HATIRLATICILAR
    # ============================================================================
    "notif_title": "🔔 <b>Hatırlatıcı Ayarları</b>",
    "notif_status": "Durum: {status}",
    "notif_status_on": "🔔 Açık",
    "notif_status_off": "🔕 Kapalı",
    "notif_time": "Saat: {time}",
    "notif_days": "Günler: {days}",
    "notif_timezone": "Zaman dilimi: {timezone}",
    "notif_hint": "💡 Hatırlatıcılar belirtilen saatte saat diliminize göre gelecek.",
    "notif_hint_off": "💡 Günlük çalışmayı unutmamak için hatırlatıcıları açın!",

    "notif_btn_toggle_on": "🔔 Hatırlatıcılar: Açık",
    "notif_btn_toggle_off": "🔕 Hatırlatıcılar: Kapalı",
    "notif_btn_time": "🕐 Saat: {time}",
    "notif_btn_days": "📅 Günleri seç",
    "notif_btn_timezone": "🌍 Zaman dilimini değiştir",

    "notif_timezone_title": "🌍 <b>Zaman diliminizi seçin</b>",
    "notif_timezone_current": "Şu anki: {timezone}",
    "notif_timezone_prompt": "Zaman diliminizde bir şehir seçin:",
    "notif_timezone_more": "🌍 Başka şehir seç ▼",
    "notif_timezone_back": "◀️ Geri",
    "notif_timezone_set": "✅ Zaman dilimi ayarlandı: {city}",

    "notif_time_title": "🕐 <b>Hatırlatıcı saatini seçin</b>",
    "notif_time_current": "Şu anki saat: {time}",
    "notif_time_timezone": "Zaman dilimi: {timezone}",
    "notif_time_hint": "Hatırlatıcı her gün seçilen saatte gelecek.",
    "notif_time_set": "✅ Saat ayarlandı: {time}",

    "notif_days_title": "📅 <b>Hatırlatıcı günlerini seçin</b>",
    "notif_days_hint": "Günü açmak/kapatmak için dokunun.\n✅ Yeşil işaret - gün açık\n❌ Kırmızı çarpı - gün kapalı\n\nBitirdiğinizde - 'Kaydet'e basın.",
    "notif_days_all": "📅 Tüm günler",
    "notif_days_weekdays": "🗓️ Hafta içi (Pzt-Cum)",
    "notif_days_save": "💾 Kaydet",
    "notif_days_saved": "✅ Günler kaydedildi!",
    "notif_days_all_selected": "✅ Tüm günler seçildi",
    "notif_days_weekdays_selected": "✅ Hafta içi seçildi (Pzt-Cum)",
    "notif_days_none": "⚠️ Hatırlatıcılar için en az bir gün seçin!",

    "notif_toggle_on": "🔔 Hatırlatıcılar açıldı!",
    "notif_toggle_off": "🔕 Hatırlatıcılar kapatıldı",

    "notif_message_title": "{emoji} <b>Çalışma zamanı!</b>",
    "notif_message_streak": "🔥 Seri: {days} gün",
    "notif_message_words": "📊 Öğrenilen kelimeler: {count}",
    "notif_message_cta": "💪 Serini kırma!",
    "notif_message_btn_start": "📚 Quiz başlat",
    "notif_message_btn_disable": "🔕 Hatırlatıcıları kapat",

    "day_mon": "Pzt",
    "day_tue": "Sal",
    "day_wed": "Çar",
    "day_thu": "Per",
    "day_fri": "Cum",
    "day_sat": "Cmt",
    "day_sun": "Paz",

    "notif_btn_back": "◀️ Ayarlara geri dön",

    # Gelişmiş bildirimler için anahtarlar
    "notif_default_name": "arkadaş",
    "notif_message_greeting": "🔥 <b>Çalışma zamanı, {name}!</b>",
    "notif_message_progress_title": "📊 <b>İlerlemeniz:</b>",
    "notif_progress_streak": "├ Seri: {days} gün 🎯",
    "notif_progress_quizzes": "├ Testler geçildi: {count}",
    "notif_progress_words": "├ Kelimeler öğrenildi: {count}",
    "notif_progress_accuracy": "└ Doğruluk: {percent}%",

    "notif_motivation_1": "Adım adım hedefinize ulaşıyorsunuz!",
    "notif_motivation_2": "Seriniz büyüyor — devam edin!",
    "notif_motivation_3": "Bugün akıcı Almanca'ya doğru bir adım daha!",
    "notif_motivation_4": "Her gün küçük çabalar = büyük sonuçlar!",
    "notif_motivation_5": "Doğru yoldasınız! Durmayın!",
    "notif_motivation_6": "Her test sizi hedefinize yaklaştırıyor!",

    # ============================================================================
    # AYARLAR
    # ============================================================================
    "settings_title": "🦾 <b>Ayarlar</b>",
    "settings_level": "📚 Seviye: <b>{level}</b>",
    "settings_mode": "🔄 Mod: <b>{mode}</b>",
    "settings_language": "🌍 Arayüz dili: <b>{language}</b>",
    "settings_choose": "Ne değiştirmek istediğini seç:",

    "settings_btn_change_level": "📚 Seviye değiştir",
    "settings_btn_change_mode": "🔄 Çeviri modu",
    "settings_btn_change_language": "🌍 Arayüz dili",
    "settings_btn_notifications": "🔔 Hatırlatıcılar",

    "settings_level_title": "📚 <b>Seviye seç</b>",
    "settings_level_description": "Mevcut Almanca seviyeni seç:\n\n• <b>A1</b> — Başlangıç (Merhaba, nasılsın?)\n• <b>A2</b> — Temel (Basit diyaloglar)\n• <b>B1</b> — Orta (Günlük iletişim)",

    "settings_mode_title": "🔄 <b>Çeviri modu</b>",
    "settings_mode_description": "Çeviri yönünü seç:",

    "settings_language_title": "🌍 <b>Arayüz dili</b>",
    "settings_language_description": "Bot arayüz dilini seç:",

    "language_changed": "✅ Dil {language} olarak değiştirildi",
    "level_not_selected": "Seçilmedi",
    "user_not_found": "❌ Kullanıcı bulunamadı. /start kullan",

    # Dil adları
    "lang_ru": "🏴 Русский",
    "lang_uk": "🇺🇦 Українська",
    "lang_en": "🇬🇧 English",
    "lang_tr": "🇹🇷 Türkçe",

    # Çeviri modları
    "mode_de_to_ru": "🇩🇪 DE → 🏴 RU",
    "mode_ru_to_de": "🏴 RU → 🇩🇪 DE",
    "mode_de_to_uk": "🇩🇪 DE → 🇺🇦 UK",
    "mode_uk_to_de": "🇺🇦 UK → 🇩🇪 DE",
    "mode_de_to_en": "🇩🇪 DE → 🇬🇧 EN",
    "mode_en_to_de": "🇬🇧 EN → 🇩🇪 DE",
    "mode_de_to_tr": "🇩🇪 DE → 🇹🇷 TR",
    "mode_tr_to_de": "🇹🇷 TR → 🇩🇪 DE",

    # ============================================================================
    # TEST
    # ============================================================================
    "quiz_no_level": "⚠️ Önce /start ile seviyeni seç",
    "quiz_error_generation": "❌ Test hazırlanırken hata oluştu.\n/start ile tekrar dene",
    "quiz_no_words": "❌ Üzgünüz, bu seviye için henüz kelime yok.\nBaşka bir seviye seçmeyi dene.",

    "quiz_question_number": "Soru {current}/{total}",
    "quiz_question_choose_word": "Doğru kelimeyi seç:",
    "quiz_question_choose_translation": "Doğru çeviriyi seç:",

    "quiz_correct": "✅ <b>Doğru!</b>",
    "quiz_wrong": "❌ <b>Yanlış!</b>",
    "quiz_correct_answer": "Doğru cevap:",

    "quiz_btn_next": "İleri →",
    "quiz_btn_repeat_errors": "🔄 Hataları tekrarla",

    "quiz_completed": "🎉 <b>Test tamamlandı!</b>",
    "quiz_result_correct": "✅ Doğru: <b>{correct}/{total}</b>",
    "quiz_result_percentage": "📈 Sonuç: <b>{percentage}%</b>",
    "quiz_result_details": "📝 <b>Detaylar:</b>",
    "quiz_result_errors": "❌ Hata: {count}",

    "quiz_repeat_title": "🔄 <b>Hataları tekrarla</b>",
    "quiz_repeat_question": "🔄 Tekrar {current}/{total}",
    "quiz_no_errors": "✅ Hiç hatan yoktu!",
    "quiz_error_next": "❌ Sonraki soru yüklenemedi.",
    "quiz_error_generate": "❌ Sonraki soru oluşturulamadı.",

    # ============================================================================
    # İSTATİSTİK
    # ============================================================================
    "stats_title": "📊 <b>İstatistik</b>",
    "stats_no_level": "⚠️ <b>Önce seviyeni seç!</b>\n\nBaşlamak için /start kullan.",

    "stats_all_words": "📚 Tüm kelimeler ({count})",
    "stats_learned": "✅ Öğrenildi: {count}",
    "stats_in_progress": "🔄 Devam ediyor: {count}",
    "stats_new": "🆕 Yeni: {count}",
    "stats_difficult": "❌ Zor: {count}",

    "stats_level_title": "🎯 Seviye {level} · {mode} ({count} kelime)",
    "stats_quizzes_title": "🏆 <b>Testler (seviye {level}):</b>",
    "stats_quizzes_passed": "Tamamlanan: {count}",
    "stats_quizzes_avg": "Ortalama sonuç: {percentage}%",
    "stats_quizzes_best": "En iyi sonuç: {percentage}%",
    "stats_quizzes_none": "Bu seviyede henüz test çözmedin.",

    "stats_activity_title": "🔥 <b>Aktivite:</b>",
    "stats_streak": "└─ Seri: <b>{days}</b> gün üst üste",

    "stats_recent_title": "<b>Son testler:</b>",
    "stats_learned_explanation": "💡 <b>Öğrenildi</b> — bir kelimeye üst üste 3 doğru cevap",

    # ============================================================================
    # YARDIM
    # ============================================================================
    "help_title": "❓ <b>Yardım — GenauLingua</b>",
    "help_description": "Burada talimatlar, yakında gelecek özellikler ve toplulukla iletişim bilgilerini bulacaksın.",
    "help_choose": "Bölüm seç:",

    "help_btn_how_to_use": "📖 Nasıl kullanılır",
    "help_btn_roadmap": "🚀 Yakında",
    "help_btn_community": "💬 Topluluk",
    "help_btn_about": "ℹ️ Hakkında",

    "help_how_to_use_title": "📖 <b>Botu nasıl kullanırsın</b>",
    "help_how_to_use_text": """1️⃣ <b>Seviye ve modu ayarla</b>
🦾 Ayarlar → A1–B1 seviye, çeviri modu ve arayüz dili seç.

2️⃣ <b>Her gün kelime öğren</b>
📚 Kelime öğren → 25 kelimelik test.
Bot hatalarını hatırlar ve zor kelimeleri daha sık gösterir.

3️⃣ <b>Hatalarını tekrarla</b>
Testten sonra hatalı kelimeleri hemen tekrarlayabilirsin.

4️⃣ <b>İlerlemeni takip et</b>
📊 İstatistik → kaç kelime öğrenildi, test geçmişi, seri.

5️⃣ <b>Diğerleriyle yarış</b>
🏆 Sıralamam → aylık ve tüm zamanlar puanların.
📊 Liderlik Tablosu → tüm katılımcılar arasında ilk 10.

6️⃣ <b>Hatırlatıcıları ayarla</b>
🦾 Ayarlar → 🔔 Hatırlatıcılar → saat, gün ve zaman dilimi seç.
Bot pratik yapmayı hatırlatır ve serini gösterir.

━━━━━━━━━━━━━━━━━
💡 Kelime <b>öğrenildi</b> sayılır — üst üste 3 doğru cevap verilince.
🔥 <b>Seri</b> günde en az 1 test çözersen artar.

Sorular? → t.me/genaulingua_chat""",

    "help_roadmap_title": "🚀 <b>GenauLingua'da yakında</b>",
    "help_roadmap_text": """🏆 <b>Başarılar</b>
İlerleme rozetleri — ilk test, 7 gün üst üste, 100 kelime öğrenildi ve daha fazlası.

🗂️ <b>Kelime kategorileri</b>
Konulara göre kelime öğren — yemek, ulaşım, iş, seyahat ve daha fazlası.

📚 <b>B2–C2 seviyeleri</b>
Şu an A1–B1 mevcut. B2, C1 ve C2 hazırlanıyor.

📖 <b>30.000 kelime</b>
Kelime tabanını 4 dilde çevirilerle 30.000'e genişletme.

🔄 <b>Yeni öğrenme modları</b>
Kelime öğrenmek için daha fazla format — testlerin ötesinde.

━━━━━━━━━━━━━━━━━
💬 Fikir ve öneriler — sohbete yaz:
t.me/genaulingua_chat""",

    "help_community_title": "💬 <b>GenauLingua Topluluğu</b>",
    "help_community_text": """👉 <b>t.me/genaulingua_chat</b>

Sohbette:
📢 Güncellemelerden ilk sen haberdar ol
🐛 Hata buldun — yaz veya ekran görüntüsü gönder
📝 Çeviri hatası — bildir, düzeltelim
💡 Fikir ve öneriler — hepsini okuyoruz
👥 Diğer öğrencilerle sohbet

━━━━━━━━━━━━━━━━━
Topluluk ne kadar aktif olursa — bot o kadar iyi olur. Çekinme! 🙌""",

    "help_about_title": "ℹ️ <b>Bot hakkında</b>",
    "help_about_text": """🤖 <b>GenauLingua</b> — kişisel Almanca öğrenme asistanın.

✨ <b>Özellikleri:</b>
• A1–B1 kelime tabanı (3000+ kelime)
• Akıllı kelime seçimi — SRS algoritması
• 4 dil: DE↔RU, DE↔UA, DE↔EN, DE↔TR
• Testten sonra hataları tekrarla
• İstatistik, seri ve ilerleme çubuğu
• Aylık sıralama ve liderlik tablosu
• Esnek hatırlatıcı bildirimleri
• Türkçe, İngilizce, Rusça, Ukraynaca arayüz

📅 <b>Güncellendi:</b> Mart 2026

💬 Güncellemeleri takip et: t.me/genaulingua_chat""",

    # ============================================================================
    # SIRALAMAM — RATING
    # ============================================================================
    "rating_title_monthly": "🏆 <b>Sıralamam — {month} {year}</b>",
    "rating_not_active": "❌ Sıralama henüz aktif değil.",
    "rating_not_in_ranking": "📍 Henüz sıralamada değilsin",
    "rating_start_quiz": "🚀 İlk testini çöz!",
    "rating_position": "📍 Pozisyon: <b>#{rank}</b> / {total}",
    "rating_points": "💎 Puan: <b>{score}</b>",
    "rating_your_month": "⭐ <b>{month} ayın:</b>",
    "rating_quizzes": "├ Testler: {count}",
    "rating_words_learned": "├ Öğrenilen kelimeler: {count}",
    "rating_streak": "├ Seri: {count} gün",
    "rating_avg_result": "└ Ortalama sonuç: {percent}%",
    "rating_goal": "🎯 #{rank} ({name}) için: {diff} puan daha",
    "rating_scoring_title": "💡 <b>Puan nasıl kazanılır:</b>",
    "rating_scoring_quiz": "• Tamamlanan test → +10",
    "rating_scoring_reverse": "• Ters mod → +5",
    "rating_scoring_word": "• Öğrenilen kelime → +2",
    "rating_scoring_streak": "• Gün serisi → +3",
    "rating_scoring_bonus": "• %90+ doğruluk → +50 bonus",

    "rating_title_alltime": "🏆 <b>Sıralamam — Tüm Zamanlar</b>",
    "rating_position_alltime": "📍 Pozisyon: <b>#{rank}</b>",
    "rating_position_none": "📍 Pozisyon: <b>—</b>",
    "rating_achievements": "⭐ <b>Başarıların:</b>",
    "rating_wins": "├ Galibiyet (1. sıra): {count}",
    "rating_total_words": "└ Öğrenilen kelimeler: {count}",
    "rating_motivation_start": "🚀 Kelime öğrenmeye başla — ilk adım en önemlisi!",
    "rating_motivation_continue": "🎯 Devam et — ilk galibiyet yakın!",
    "rating_motivation_champion": "🔥 Gerçek bir şampiyonsun!",
    "rating_lifetime_title": "🌟 <b>Lifetime puanlar:</b>",
    "rating_lifetime_desc": "• Tüm aylardan toplam puanlar\n• 🥇 için +100 · 🥈 için +50 · 🥉 için +25",

    "table_title_monthly": "📊 <b>Liderlik Tablosu — {month} {year}</b>",
    "table_title_alltime": "📊 <b>Liderlik Tablosu — Tüm Zamanlar</b>",
    "table_empty": "Henüz katılımcı yok.\nİlk testi sen çöz! 💪",
    "table_you_in_top": "📍 Sen: <b>#{rank}</b> / {total}",
    "table_you_not_in_top": "📍 Sen: <b>#{rank}</b> / {total} — {score} puan",
    "table_you_outside": "📍 Sen: ilk 10 dışında — {score} puan",
    "table_you_not_ranked": "📍 Henüz sıralamada değilsin",
    "table_points": "puan",
    "btn_leaderboard_table": "📊 Liderlik Tablosu",
    "btn_back_to_rating": "◀️ Sıralamaya geri dön",

    # İSTATİSTİK
    "stats_header": "📊 <b>İstatistiklerin</b>",
    "stats_learned_of": "└─ Öğrenildi <b>{learned}</b> / {total}",
    "stats_details": "🔄 Devam eden: {progress}\n🆕 Yeni: {new}\n⚠️ Zor: {difficult}",
    "stats_achievements_title": "<b>Başarıların</b>",
    "stats_words_count": "├─ Öğrenilen kelimeler: <b>{count}</b>",
    "stats_streak_line": "└─ Seri: <b>{days} gün üst üste</b>",
    "stats_quizzes_header": "<b>Testler ({level})</b>",
    "stats_quizzes_passed_line": "├─ Tamamlanan: <b>{count}</b>",
    "stats_quizzes_avg_line": "├─ Ortalama sonuç: <b>{percent}%</b>",
    "stats_quizzes_best_line": "└─ En iyi sonuç: <b>{percent}%</b>",
    "stats_quizzes_empty": "└─ Henüz tamamlanan test yok",
    "stats_recent_header": "📈 <b>Son testler</b>",
    "stats_overall_header": "🌍 <b>Genel ilerleme</b>",
    "stats_overall_learned": "└─ Öğrenildi <b>{learned}</b> / {total} kelime",
    "stats_cta_start": "💪 Kelime öğrenmeye başla — ilk adım en önemlisi!",
    "stats_cta_begin": "🚀 Harika başlangıç! Devam et!",
    "stats_cta_halfway": "🔥 Yarı yoldasın! Durma!",
    "stats_cta_almost": "🏆 Neredeyse hedefe ulaştın! Harikasın!",
    "stats_explanation": "—————————————————————\nÖğrenildi = üst üste 3 doğru cevap",
    "stats_btn_rating": "🏆 Sıralamam",
}