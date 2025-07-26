# src/utils/i18n.py
import re
translations = {
    'en': {
        'welcome': "Welcome, {name}! Please choose your role:",
        'main_menu_prompt': "What would you like to do?",
        'browse_properties': "🔍 Browse Properties",
        'filter_properties': "📊 Filter Properties", # <<< NEW KEY
        'submit_property': "➕ Submit a Property",
        'my_listings': "📋 My Listings",
        'admin_panel': "👑 Admin Panel",
        'language_select': "🌐 Language", # <<< NEW KEY
        'back': "⬅️ Back",
        'cancel': "❌ Cancel",
        'buyer_role': "I'm a Buyer",
        'broker_role': "I'm a Broker",
        'admin_pending_listings': "⏳ View Pending Listings",
        'back_to_main_menu': "⬅️ Back to Main Menu",
        'admin_approve': "✅ Approve",
        'admin_reject': "❌ Reject",
        'op_cancelled': "Operation cancelled. Returning to the main menu.",
        'select_language_prompt': "Please select your preferred language:", # <<< NEW KEY
        'language_updated': "Language has been updated to {lang_name}.", # <<< NEW KEY
        # Submission Flow
        'property_submission_start': "Let's submit a new property. First, what type is it?",
        'how_many_bedrooms': "How many bedrooms?",
        'how_many_bathrooms': "How many bathrooms?",
        'what_is_size': "What is the approximate size?", # <<< NEW KEY
        'what_is_floor': "What is the Floor Level? (Type the number, e.g., 5)", # <<< NEW KEY
        'has_title_deed': "Does it have a Title Deed?", # <<< NEW KEY
        'how_many_parking': "How many Parking Spaces? (Type the number, e.g., 2)", # <<< NEW KEY
        'what_is_condo_scheme': "What is the Condominium Scheme Type?", # <<< NEW KEY
        'what_is_price': "Please type the exact price in ETB.",
        'upload_images': "Please upload at least 3 images. When finished, press the button below.",
        'need_more_images': "You've only uploaded {count} image(s). Please upload at least 3 to continue.",
        'enter_description': "Great! Finally, please enter a short description for the property.",
        'submission_complete': "✅ Submission complete! Your property is pending admin approval.",
        # Notifications
        'property_approved_notification': "Your property submission has been approved and is now live!",
        'property_rejected_notification': "Your property submission was rejected. Reason: {reason}",
    },
    'am': {
        'welcome': "እንኳን ደህና መጡ, {name}! እባክዎ ሚናዎን ይምረጡ:",
        'main_menu_prompt': "ምን ማድረግ ይፈልጋሉ?",
        'browse_properties': "🔍 ንብረቶችን ያስሱ",
        'filter_properties': "📊 ንብረቶችን ያጣሩ",
        'submit_property': "➕ ንብረት ያስገቡ",
        'my_listings': "📋 የእኔ ዝርዝሮች",
        'admin_panel': "👑 የአስተዳዳሪ ፓነል",
        'language_select': "🌐 ቋንቋ",
        'back': "⬅️ ተመለስ",
        'cancel': "❌ ሰርዝ",
        'buyer_role': "ገዢ ነኝ",
        'broker_role': "ደላላ ነኝ",
        'admin_pending_listings': "⏳ በመጠባበቅ ላይ ያሉ ዝርዝሮች",
        'back_to_main_menu': "⬅️ ወደ ዋና ማውጫ ተመለስ",
        'admin_approve': "✅ አጽድቅ",
        'admin_reject': "❌ ውድቅ አድርግ",
        'op_cancelled': "ክንውኑ ተሰርዟል። ወደ ዋናው ምናሌ በመመለስ ላይ።",
        'select_language_prompt': "እባክዎ ተመራጭ ቋንቋዎን ይምረጡ:",
        'language_updated': "ቋንቋ ወደ {lang_name} ተቀይሯል።",
        # Submission Flow
        'property_submission_start': "አዲስ ንብረት እናስገባ። በመጀመሪያ፣ የንብረቱ አይነት ምንድን ነው?",
        'how_many_bedrooms': "ስንት መኝታ ክፍሎች አሉት?",
        'how_many_bathrooms': "ስንት ሽንት ቤት አሉት?",
        'what_is_size': "የቦታው ስፋት ስንት ነው?",
        'what_is_floor': "ስንተኛ ፎቅ ላይ ነው? (ቁጥሩን ያስገቡ, ለምሳሌ: 5)",
        'has_title_deed': "ካርታ አለው?",
        'how_many_parking': "ስንት የመኪና ማቆሚያ ቦታ አለው? (ቁጥሩን ያስገቡ, ለምሳሌ: 2)",
        'what_is_condo_scheme': "የኮንዶሚኒየም የክፍያ አይነት ምንድን ነው?",
        'what_is_price': "እባክዎ ትክክለኛውን ዋጋ በብር ያስገቡ።",
        'upload_images': "እባክዎ ቢያንስ 3 ፎቶዎችን ይስቀሉ። ሲጨርሱ ከታች ያለውን ቁልፍ ይጫኑ።",
        'need_more_images': "{count} ፎቶ(ዎች) ብቻ ነው የሰቀሉት። ለመቀጠል እባክዎ ቢያንስ 3 ይስቀሉ።",
        'enter_description': "በጣም ጥሩ! በመጨረሻም፣ እባክዎ ለንብረቱ አጭር መግለጫ ያስገቡ።",
        'submission_complete': "✅ ገብቷል! ያስገቡት ንብረት በአስተዳዳሪ እይታ ላይ ነው።",
        # Notifications
        'property_approved_notification': "ያስገቡት ንብረት ጸድቆ ገበያ ላይ ውሏል!",
        'property_rejected_notification': "ያስገቡት ንብረት ውድቅ ተደርጓል። ምክንያት: {reason}",
    }
}

# <<< MODIFIED FUNCTION
def t(key: str, lang: str = 'en', default: str = None, **kwargs) -> str:
    """
    Simple translator function. It now dynamically uses the provided language.
    If a key is not found in the target language, it falls back to English.
    If still not found, it returns the default or the key itself.
    """
    lang_dict = translations.get(lang, translations['en'])
    message = lang_dict.get(key)
    
    if message is None:
        message = translations['en'].get(key, default or key)
        
    return message.format(**kwargs)

# <<< NEW FUNCTION
def get_all_translations(key: str) -> list:
    """Returns a list of all available translations for a given key."""
    return [lang_dict.get(key) for lang_dict in translations.values() if lang_dict.get(key)]

def create_i18n_regex(key: str) -> str:
    """
    Creates a regex pattern that matches any translation of a given key.
    Example: create_i18n_regex('submit_property') -> '^(➕\\ Submit\\ a\\ Property|➕\\ ንብረት\\ ያስገቡ)$'
    """
    options = get_all_translations(key)
    # Use re.escape() to safely escape all special characters, including in emojis
    escaped_options = [re.escape(option) for option in options]
    pattern = "|".join(escaped_options)
    return f"^({pattern})$"