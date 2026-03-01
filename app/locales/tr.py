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

    "welcome_your_level": "Seviyeniz: <b>{level}</b> · Mod: <b>{mode}</b>",
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
🦾 Ayarlar → A1–B1 seviye, çeviri modu ve dil seç.

2️⃣ <b>Her gün kelime öğren</b>
📚 Kelime öğren → 25 kelimelik test.
Bot hatalarını hatırlar ve zor kelimeleri daha sık gösterir.

3️⃣ <b>Hatalarını tekrarla</b>
Testten sonra hatalı kelimeleri hemen tekrarlayabilirsin.

4️⃣ <b>İlerlemeni takip et</b>
📊 İstatistik → kaç kelime öğrenildi, test geçmişi, seri.

━━━━━━━━━━━━━━━━━
💡 Kelime <b>öğrenildi</b> sayılır — üst üste 3 doğru cevap verilince.
🔥 <b>Seri</b> günde en az 1 test çözersen artar.

Sorular? → t.me/genaulingua_chat""",

    "help_roadmap_title": "🚀 <b>GenauLingua'da yakında</b>",
    "help_roadmap_text": """🏆 <b>Başarılar</b>
İlerleme rozetleri — ilk test, 7 gün üst üste, 100 kelime öğrenildi ve daha fazlası.

🥇 <b>Liderlik tablosu</b>
Tüm kullanıcılar arasında sıralama — kelime, seri ve test sonuçlarına göre.

🎯 <b>Meydan okumalar</b>
Haftalık görevler — 7 test üst üste, haftada 100 kelime, 3 kez %90+.

🔔 <b>Hatırlatıcılar</b>
Saat ayarla — bot pratik yapmayı hatırlatır ve serinizi gösterir.

📚 <b>B2–C2 seviyeleri</b>
Şu an A1–B1 mevcut. B2, C1 ve C2 hazırlanıyor.

🎤 <b>Telaffuz</b>
Kelime sesi — Almanca kelimelerin nasıl söylendiğini dinle.

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

✨ <b>Şu an yapabilecekleri:</b>
• A1–B1 kelime tabanı (3000+ kelime)
• Akıllı kelime seçimi — SRS algoritması
• DE→TR, TR→DE, DE→EN, DE→RU modları
• Testten sonra hataları tekrarla
• İstatistik ve seri
• Türkçe, İngilizce, Rusça, Ukraynaca arayüz

📅 <b>Güncellendi:</b> Şubat 2026

💬 Güncellemeleri takip et: t.me/genaulingua_chat""",
}