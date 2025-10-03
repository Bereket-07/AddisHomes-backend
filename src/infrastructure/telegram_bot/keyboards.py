from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from src.domain.models.user_models import User, UserRole
from src.domain.models.property_models import PropertyType, CondoScheme, FurnishingStatus
from src.utils.i18n import t
from src.utils.constants import *
from src.utils.config import settings
# --- DEPRECATED: No longer need the complex data loader for locations ---
# from src.utils.data_loader import location_data 


# A constant to remove the reply keyboard
REMOVE_KEYBOARD = ReplyKeyboardRemove()

# --- Data for Reply Keyboards ---
BEDROOM_OPTIONS = ["1", "2", "3", "4", "5", "6+"]
BATHROOM_OPTIONS = ["1", "2", "3", "4+"]
REGIONS = ["Addis Ababa", "Amhara", "Oromia", "Other"]
FLOOR_LEVEL_OPTIONS = ["0 (Ground)", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10+"]
PARKING_SPACES_OPTIONS = ["0", "1", "2", "3", "4+"]
CONDO_SCHEMES = [cs.value for cs in CondoScheme]

G_PLUS_OPTIONS = ["G+0", "G+1", "G+2", "G+3", "G+4", "G+5+"]


SIZE_RANGES_TEXT = {
    "Under 50 m²": "0-50",
    "50 - 100 m²": "50-100",
    "101 - 150 m²": "101-150",
    "151 - 250 m²": "151-250",
    "Above 250 m²": "250-9999",
}

PRICE_RANGES_TEXT = {
    # Lower, more granular ranges
    "Under 2.5M": "0-2500000",
    "2.5M - 4M": "2500000-4000000",
    "4M - 6M": "4000000-6000000",
    "6M - 8M": "6000000-8000000",
    # Mid-range
    "8M - 11M": "8000000-11000000",
    "11M - 14M": "11000000-14000000",
    "14M - 17M": "14000000-17000000",
    # Higher-end ranges
    "17M - 22M": "17000000-22000000",
    "22M - 30M": "22000000-30000000",
    "Above 30M": "30000000-9999999999",
}

# --- Helper Function ---
def create_reply_options_keyboard(options: list, columns: int = 2, add_cancel=True, lang: str = 'en') -> ReplyKeyboardMarkup:
    keyboard = [list(map(KeyboardButton, options[i:i + columns])) for i in range(0, len(options), columns)]
    if add_cancel:
        keyboard.append([KeyboardButton(t('cancel', lang=lang))])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_main_menu_keyboard(user: User) -> ReplyKeyboardMarkup:
    lang = user.language
    options = [t('browse_properties', lang=lang), t('filter_properties', lang=lang)]
    if UserRole.BROKER in user.roles:
        options.extend([t('submit_property', lang=lang), t('my_listings', lang=lang)])
    if UserRole.ADMIN in user.roles:
        options.append(t('admin_panel', lang=lang))
    options.append(t('language_select', lang=lang))
    return create_reply_options_keyboard(options, columns=2, add_cancel=False, lang=lang)

def get_website_inline_keyboard() -> InlineKeyboardMarkup:
    """Global inline keyboard with a website link."""
    url = settings.WEB_APP_URL or "https://addishomess.com"
    keyboard = [[InlineKeyboardButton(text="🌐 Visit our website", url=url)]]
    return InlineKeyboardMarkup(keyboard)

def get_admin_panel_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    options = [
        t('admin_pending_listings', lang=lang),
        t('admin_manage_listings', lang=lang, default="🗂️ Manage Listings"), 
        t('admin_view_analytics', lang=lang, default="📊 View Analytics"), 
        t('back_to_main_menu', lang=lang)
    ]
    return create_reply_options_keyboard(options, columns=1, add_cancel=False, lang=lang)

def create_admin_management_keyboard(prop_id: str, lang: str = 'en') -> InlineKeyboardMarkup:
    """Keyboard for managing an existing approved property."""
    keyboard = [[
        InlineKeyboardButton(t('admin_mark_sold', lang=lang, default="💰 Mark as Sold"), callback_data=f"{CB_ADMIN_MARK_SOLD}_{prop_id}"),
        InlineKeyboardButton(t('admin_delete', lang=lang, default="🗑️ Delete"), callback_data=f"{CB_ADMIN_DELETE_CONFIRM}_{prop_id}")
    ]]
    return InlineKeyboardMarkup(keyboard)

def create_delete_confirmation_keyboard(prop_id: str, lang: str = 'en') -> InlineKeyboardMarkup:
    """Keyboard to confirm a permanent delete action."""
    keyboard = [[
        InlineKeyboardButton(t('admin_delete_confirm_yes', lang=lang, default="⚠️ YES, DELETE PERMANENTLY ⚠️"), callback_data=f"{CB_ADMIN_DELETE_EXECUTE}_{prop_id}"),
        InlineKeyboardButton(t('admin_delete_confirm_no', lang=lang, default="❌ No, Cancel"), callback_data=f"{CB_ADMIN_DELETE_CANCEL}_{prop_id}")
    ]]
    return InlineKeyboardMarkup(keyboard)

def get_role_selection_keyboard() -> ReplyKeyboardMarkup:
    # Use both languages for first-time selection
    options = [t('buyer_role', lang='en'), t('broker_role', lang='en'), t('buyer_role', lang='am'), t('broker_role', lang='am')]
    return create_reply_options_keyboard(options, add_cancel=False)

def get_language_selection_keyboard() -> ReplyKeyboardMarkup:
    """Creates a keyboard for selecting a language."""
    options = ["English 🇬🇧", "አማርኛ 🇪🇹"]
    return create_reply_options_keyboard(options, columns=2, add_cancel=True, lang='en')

# --- Submission & Filter Flow Keyboards ---
def get_property_type_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    """Creates a keyboard with translated property type names."""
    # Generate translated button text for each property type enum
    options = [t(f"prop_type_{pt.name.lower()}", lang=lang) for pt in PropertyType]
    return create_reply_options_keyboard(options, lang=lang)

# --- DEPRECATED KEYBOARDS ---
# def get_sub_city_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup: ...
# def get_neighborhood_keyboard(sub_city: str, lang: str = 'en') -> ReplyKeyboardMarkup: ...
# def get_condo_site_keyboard(sub_city: str, lang: str = 'en') -> ReplyKeyboardMarkup: ...

# --- NEW KEYBOARD for Apartment/Condo sites ---
def get_site_keyboard(is_filter: bool = False, lang: str = 'en') -> ReplyKeyboardMarkup:
    """Creates a dynamic keyboard for common sites in the user's language."""
    # Use the user's language to get the translated site names for the buttons
    # Falls back to English ('en') if the language key doesn't exist for some reason
    options = [site.get(lang, site['en']) for site in SUPPORTED_SITES]
    
    # Add special options (also translated)
    options.append(t('other_option', lang=lang))
    if is_filter:
        options.append(t('any_option', lang=lang))
        
    return create_reply_options_keyboard(options, columns=3, lang=lang)


def get_numeric_keyboard(options: list, lang: str = 'en') -> ReplyKeyboardMarkup:
    """Helper for numeric choice keyboards like bedrooms/bathrooms."""
    return create_reply_options_keyboard(options, columns=4, lang=lang)

def get_bedroom_keyboard(is_filter: bool = False, lang: str = 'en') -> ReplyKeyboardMarkup:
    options = [t('bedroom_count', lang=lang, count=i) for i in range(1, 6)]
    options.append(t('bedroom_plus', lang=lang, count=6))
    if is_filter:
        options.append(t('any_option', lang=lang))
    return create_reply_options_keyboard(options, columns=4, lang=lang)

def get_bathroom_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard(BATHROOM_OPTIONS, columns=4, lang=lang)

def get_size_range_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard(list(SIZE_RANGES_TEXT.keys()), columns=2, lang=lang)

def get_price_range_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    options = list(PRICE_RANGES_TEXT.keys())
    options.append(t('any_price', lang=lang))
    return create_reply_options_keyboard(options, columns=2, lang=lang)

def get_region_keyboard(is_filter: bool = False, lang: str = 'en') -> ReplyKeyboardMarkup:
    options = REGIONS[:] # Create a copy
    if is_filter:
        options.append(t('any_region', lang=lang))
    return create_reply_options_keyboard(options, lang=lang)

def get_furnishing_status_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard([fs.value for fs in FurnishingStatus], columns=3, lang=lang)

def get_boolean_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    """Creates a simple Yes/No keyboard."""
    options = [t('yes', lang=lang), t('no', lang=lang)]
    return create_reply_options_keyboard(options, columns=2, lang=lang)

def get_condo_scheme_keyboard(is_filter: bool = False, lang: str = 'en') -> ReplyKeyboardMarkup:
    options = CONDO_SCHEMES[:] # Create a copy
    if is_filter:
        options.append(t('any_scheme', lang=lang))
    return create_reply_options_keyboard(options, lang=lang)

def get_g_plus_keyboard(is_filter: bool = False, lang: str = 'en') -> ReplyKeyboardMarkup:
    """Creates a keyboard for Villa G+ options."""
    options = G_PLUS_OPTIONS[:] # Create a copy
    if is_filter:
        options.append(t('any_option', lang=lang))
    return create_reply_options_keyboard(options, columns=3, lang=lang)


def get_image_upload_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    """Creates a keyboard with a 'Done' button for image uploads."""
    keyboard = [[KeyboardButton(DONE_UPLOADING_TEXT)], [KeyboardButton(t('cancel', lang=lang))]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# --- Inline Keyboard for Admin Actions ---
def create_admin_approval_keyboard(prop_id: str, lang: str = 'en') -> InlineKeyboardMarkup:
    keyboard = [[
        InlineKeyboardButton(t('admin_approve', lang=lang), callback_data=f"{CB_ADMIN_APPROVE}_{prop_id}"),
        InlineKeyboardButton(t('admin_reject', lang=lang), callback_data=f"{CB_ADMIN_REJECT}_{prop_id}")
    ]]
    return InlineKeyboardMarkup(keyboard)