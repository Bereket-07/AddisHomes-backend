# src/utils/i18n.py
import re
translations = {
    'en': {
        # General & Main Menu
        'welcome': "Welcome, {name}! Please choose your role:",
        'main_menu_prompt': "What would you like to do?",
        'browse_properties': "🔍 Browse Properties",
        'filter_properties': "📊 Filter Properties",
        'submit_property': "➕ Submit a Property",
        'my_listings': "📋 My Listings",
        'admin_panel': "👑 Admin Panel",
        'language_select': "🌐 Language",
        'what_is_g_plus': "What is the Villa's structure (e.g., G+1)?",
        'back': "⬅️ Back",
        'cancel': "❌ Cancel",
        'yes': "Yes",
        'no': "No",
        'buyer_role': "I'm a Buyer",
        'broker_role': "I'm a Broker",
        'op_cancelled': "Operation cancelled. Returning to the main menu.",
        'error_occurred': "An error occurred. Please try again.",

        # Language Selection
        'select_language_prompt': "Please select your preferred language:",
        'language_updated': "Language has been updated to {lang_name}.",

        # Admin Panel & Actions
        'admin_pending_listings': "⏳ View Pending Listings",
        'admin_manage_listings': "🗂️ Manage Listings",
        'admin_view_analytics': "📊 View Analytics",
        'back_to_main_menu': "⬅️ Back to Main Menu",
        'admin_approve': "✅ Approve",
        'admin_reject': "❌ Reject",
        'admin_mark_sold': "💰 Mark as Sold",
        'admin_delete': "🗑️ Delete",
        'admin_delete_confirm_yes': "⚠️ YES, DELETE PERMANENTLY ⚠️",
        'admin_delete_confirm_no': "❌ No, Cancel",
        
        # Property Filtering & Browsing Flow
        'searching': "Searching for properties...",
        'no_properties_found': "No properties found matching your criteria.",
        'found_properties': "Found {count} matching properties:",
        'showing_first_10': "Showing the first 10 results. For more, please refine your search.",
        'search_complete': "Search complete. Returning to the main menu.",
        'browse_complete': "Browse complete. Returning to the main menu.",
        'select_property_type': "First, select a property type:",
        'select_price_range': "Select a price range:",
        'select_region': "Which region?",
        'select_condo_scheme': "Select a Condominium scheme:",
        'any_option': "Any",
        'any_price': "Any Price",
        'any_region': "Any Region",
        'any_scheme': "Any Scheme",

        # Property Submission Flow
        'property_submission_start': "Let's submit a new property. First, what type is it?",
        'select_sub_city': "In which Sub-city is the property located?",
        'select_neighborhood': "Please select the nearest neighborhood/area.",
        'select_condo_site': "Please select the Condominium Site name.",
        'type_specific_area': "Could not find specific areas. Please type the specific area name.",
        'how_many_bedrooms': "How many bedrooms?",
        'how_many_bathrooms': "How many bathrooms?",
        'what_is_size': "What is the approximate size?",
        'what_is_floor': "What is the Floor Level? (Type the number, e.g., 5)",
        'what_is_furnishing': "What is the Furnishing Status?",
        'has_title_deed': "Does it have a Title Deed?",
        'how_many_parking': "How many Parking Spaces? (Type the number, e.g., 2)",
        'what_is_condo_scheme': "What is the Condominium Scheme Type?",
        'what_is_price': "Please type the exact price in ETB.",
        'upload_images': "Please upload at least 3 images. When finished, press the button below.",
        'image_received': "Image {count} received. Send more or click 'Done Uploading'.",
        'need_more_images': "You've only uploaded {count} image(s). Please upload at least 3 to continue.",
        'enter_description': "Great! Finally, please enter a short description for the property.",
        'submission_complete': "✅ Submission complete! Your property is pending admin approval.",
        'invalid_number': "That's not a valid number. Please use the buttons.",
        'invalid_price': "Please enter a valid number for the price.",
        'not_an_image': "That's not an image. Please send photos or click the 'Done' button.",

        # Broker Specific
        'no_listings_yet': "You have not submitted any properties yet.",
        'displaying_your_listings': "Displaying your submitted properties:",
        'end_of_listings': "End of your listings.",
        
        # Notifications
        'property_approved_notification': "Your property submission has been approved and is now live!",
        'property_rejected_notification': "Your property submission was rejected. Reason: {reason}",


        'is_commercial': "Is it a commercial or mixed-use building?",
        'total_floors': "How many floors does the building have?",
        'total_units': "How many total units (apartments/offices) are in the building?",
        'has_elevator': "Does the building have an elevator?",
        'has_private_rooftop': "Does the penthouse have a private rooftop terrace?",
        'is_two_story_penthouse': "Is it a two-story (duplex) penthouse?",
        'has_private_entrance': "Does the duplex have a private entrance?",

        # Filter prompts
        'ask_filter_is_commercial': "Show only commercial buildings?",
        'ask_filter_has_elevator': "Must have an elevator?",
        'ask_filter_has_rooftop': "Must have a private rooftop?",
        'ask_filter_is_two_story': "Show only two-story penthouses?",
        'ask_filter_has_entrance': "Must have a private entrance?",
    },
    'am': {
        # General & Main Menu
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
        'yes': "አዎ",
        'no': "አይደለም",
        'buyer_role': "ገዢ ነኝ",
        'broker_role': "ደላላ ነኝ",
        'op_cancelled': "ክንውኑ ተሰርዟል። ወደ ዋናው ምናሌ በመመለስ ላይ።",
        'error_occurred': "ስህተት አጋጥሟል። እባክዎ እንደገና ይሞክሩ።",
        'what_is_g_plus': "የቪላው አሰራር እንዴት ነው (ለምሳሌ፡ G+1)?",
        # Language Selection
        'select_language_prompt': "እባክዎ ተመራጭ ቋንቋዎን ይምረጡ:",
        'language_updated': "ቋንቋ ወደ {lang_name} ተቀይሯል።",

        # Admin Panel & Actions
        'admin_pending_listings': "⏳ በመጠባበቅ ላይ ያሉ ዝርዝሮች",
        'admin_manage_listings': "🗂️ ዝርዝሮችን ያስተዳድሩ",
        'admin_view_analytics': "📊 ትንታኔዎችን ይመልከቱ",
        'back_to_main_menu': "⬅️ ወደ ዋና ማውጫ ተመለስ",
        'admin_approve': "✅ አጽድቅ",
        'admin_reject': "❌ ውድቅ አድርግ",
        'admin_mark_sold': "💰 እንደተሸጠ ምልክት ያድርጉ",
        'admin_delete': "🗑️ ይሰርዙ",
        'admin_delete_confirm_yes': "⚠️ አዎ፣ እስከመጨረሻው ይሰረዝ ⚠️",
        'admin_delete_confirm_no': "❌ አይ፣ ይሰረዝ",

        # Property Filtering & Browsing Flow
        'searching': "ንብረቶችን በመፈለግ ላይ...",
        'no_properties_found': "ከፍለጋዎ ጋር የሚዛመድ ምንም ንብረት አልተገኘም።",
        'found_properties': "{count} ተዛማጅ ንብረቶች ተገኝተዋል:",
        'showing_first_10': "የመጀመሪያዎቹን 10 ውጤቶች በማሳየት ላይ። ለተጨማሪ፣ እባክዎ ፍለጋዎን ያጥቡ።",
        'search_complete': "ፍለጋ ተጠናቋል። ወደ ዋናው ማውጫ በመመለስ ላይ።",
        'browse_complete': "ማሰስ ተጠናቋል። ወደ ዋናው ማውጫ በመመለስ ላይ።",
        'select_property_type': "በመጀመሪያ የንብረቱን አይነት ይምረጡ:",
        'select_price_range': "የዋጋ ወሰን ይምረጡ:",
        'select_region': "በየትኛው ክልል?",
        'select_condo_scheme': "የኮንዶሚኒየም የክፍያ አይነት ይምረጡ:",
        'any_option': "ማንኛውም",
        'any_price': "ማንኛውም ዋጋ",
        'any_region': "ማንኛውም ክልል",
        'any_scheme': "ማንኛውም አይነት",

        # Property Submission Flow
        'property_submission_start': "አዲስ ንብረት እናስገባ። በመጀመሪያ፣ የንብረቱ አይነት ምንድን ነው?",
        'select_sub_city': "ንብረቱ በየትኛው ክፍለ ከተማ ነው የሚገኘው?",
        'select_neighborhood': "እባክዎ በአቅራቢያ የሚገኘውን ሰፈር/አካባቢ ይምረጡ።",
        'select_condo_site': "እባክዎ የኮንዶሚኒየም ሳይቱን ስም ይምረጡ።",
        'type_specific_area': "የተወሰኑ ቦታዎችን ማግኘት አልተቻለም። እባክዎ የአካባቢውን ስም ይጻፉ።",
        'how_many_bedrooms': "ስንት መኝታ ክፍሎች አሉት?",
        'how_many_bathrooms': "ስንት ሽንት ቤት አሉት?",
        'what_is_size': "የቦታው ስፋት ስንት ነው?",
        'what_is_floor': "ስንተኛ ፎቅ ላይ ነው? (ቁጥሩን ያስገቡ, ለምሳሌ: 5)",
        'what_is_furnishing': "የፈርኒቸር ሁኔታው ምንድን ነው?",
        'has_title_deed': "ካርታ አለው?",
        'how_many_parking': "ስንት የመኪና ማቆሚያ ቦታ አለው? (ቁጥሩን ያስገቡ, ለምሳሌ: 2)",
        'what_is_condo_scheme': "የኮንዶሚኒየም የክፍያ አይነት ምንድን ነው?",
        'what_is_price': "እባክዎ ትክክለኛውን ዋጋ በብር ያስገቡ።",
        'upload_images': "እባክዎ ቢያንስ 3 ፎቶዎችን ይስቀሉ። ሲጨርሱ ከታች ያለውን ቁልፍ ይጫኑ።",
        'image_received': "ፎቶ {count} ተቀብለናል። ተጨማሪ ይላኩ ወይም 'መስቀል ጨርሻለሁ' የሚለውን ይጫኑ።",
        'need_more_images': "{count} ፎቶ(ዎች) ብቻ ነው የሰቀሉት። ለመቀጠል እባክዎ ቢያንስ 3 ይስቀሉ።",
        'enter_description': "በጣም ጥሩ! በመጨረሻም፣ እባክዎ ለንብረቱ አጭር መግለጫ ያስገቡ።",
        'submission_complete': "✅ ገብቷል! ያስገቡት ንብረት በአስተዳዳሪ እይታ ላይ ነው።",
        'invalid_number': "ይህ ትክክለኛ ቁጥር አይደለም። እባክዎ ያሉትን ቁልፎች ይጠቀሙ።",
        'invalid_price': "እባክዎ ትክክለኛ የዋጋ ቁጥር ያስገቡ።",
        'not_an_image': "ይህ ፎቶ አይደለም። እባክዎ ፎቶ ይላኩ ወይም 'ጨርሻለሁ' የሚለውን ቁልፍ ይጫኑ።",

        # Broker Specific
        'no_listings_yet': "እስካሁን ምንም አይነት ንብረት አላስገቡም።",
        'displaying_your_listings': "ያስገቧቸውን ንብረቶች ዝርዝር:",
        'end_of_listings': "የዝርዝሮችዎ መጨረሻ።",

        # Notifications
        'property_approved_notification': "ያስገቡት ንብረት ጸድቆ ገበያ ላይ ውሏል!",
        'property_rejected_notification': "ያስገቡት ንብረት ውድቅ ተደርጓል። ምክንያት: {reason}",


        'is_commercial': "ሕንፃው ለንግድ ወይስ ለተቀላቀለ አገልግሎት ነው?",
        'total_floors': "ሕንፃው ስንት ፎቆች አሉት?",
        'total_units': "ሕንፃው በድምሩ ስንት ክፍሎች (አፓርታማዎች/ቢሮዎች) አሉት?",
        'has_elevator': "ሕንፃው ሊፍት (አሳንሰር) አለው?",
        'has_private_rooftop': "ፔንትሃውሱ የግል የጣራ ላይ እርከን አለው?",
        'is_two_story_penthouse': "ባለ ሁለት ፎቅ (ዱፕሌክስ) ፔንትሃውስ ነው?",
        'has_private_entrance': "ዱፕሌክሱ የግል መግቢያ በር አለው?",
        
        # Filter prompts
        'ask_filter_is_commercial': "የንግድ ሕንፃዎችን ብቻ አሳይ?",
        'ask_filter_has_elevator': "ሊፍት የግድ ሊኖረው ይገባል?",
        'ask_filter_has_rooftop': "የግል ጣራ የግድ ሊኖረው ይገባል?",
        'ask_filter_is_two_story': "ባለ ሁለት ፎቅ ፔንትሃውሶችን ብቻ አሳይ?",
        'ask_filter_has_entrance': "የግል መግቢያ የግድ ሊኖረው ይገባል?",
    }
}

def t(key: str, lang: str = 'en', default: str = None, **kwargs) -> str:
    """
    Simple translator function. It now dynamically uses the provided language.
    If a key is not found in the target language, it falls back to English.
    If still not found, it returns the default or the key itself.
    """
    lang_dict = translations.get(lang, translations['en'])
    message = lang_dict.get(key)
    
    if message is None:
        # Fallback to English if the key is not in the target language
        message = translations['en'].get(key)
    
    if message is None:
        # Fallback to the default value or the key itself if not in English either
        message = default or key
        # We don't format the key itself, only real messages
        return message

    return message.format(**kwargs)

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