from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from src.domain.models.user_models import User, UserRole
from src.domain.models.property_models import PropertyType, CondoScheme
from src.utils.i18n import t
from src.utils.constants import ANY_OPTION, ANY_PRICE, ANY_REGION, ANY_SCHEME, CB_ADMIN_APPROVE, CB_ADMIN_REJECT

# A constant to remove the reply keyboard
REMOVE_KEYBOARD = ReplyKeyboardRemove()

# --- Data for Reply Keyboards ---
BEDROOM_OPTIONS = ["1", "2", "3", "4", "5", "6+"]
BATHROOM_OPTIONS = ["1", "2", "3", "4+"]
REGIONS = ["Addis Ababa", "Amhara", "Oromia", "Other"]
CONDO_SCHEMES = [cs.value for cs in CondoScheme]

# --- FIX: Added the missing size ranges ---
SIZE_RANGES_TEXT = {
    "Under 50 m²": "0-50",
    "50 - 100 m²": "50-100",
    "101 - 150 m²": "101-150",
    "151 - 250 m²": "151-250",
    "Above 250 m²": "250-9999",
}

PRICE_RANGES_TEXT = {
    "Under 5M": "0-5000000",
    "5M - 10M": "5000000-10000000",
    "10M - 20M": "10000000-20000000",
    "20M - 33M": "20000000-33000000",
    "Above 33M": "33000000-9999999999",
}

# --- Helper Function ---
def create_reply_options_keyboard(options: list, columns: int = 2, add_cancel=True) -> ReplyKeyboardMarkup:
    keyboard = [list(map(KeyboardButton, options[i:i + columns])) for i in range(0, len(options), columns)]
    if add_cancel:
        keyboard.append([KeyboardButton(t('cancel'))])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_main_menu_keyboard(user: User, lang: str = 'en') -> ReplyKeyboardMarkup:
    options = [t('browse_properties'), t('filter_properties')]
    if UserRole.BROKER in user.roles:
        options.extend([t('submit_property'), t('my_listings')])
    if UserRole.ADMIN in user.roles:
        options.append(t('admin_panel'))
    return create_reply_options_keyboard(options, columns=2, add_cancel=False)

def get_admin_panel_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup: # <<< NEW FUNCTION
    """Creates the keyboard for the admin sub-menu."""
    options = [
        t('admin_pending_listings'),
        # Add other admin buttons here in the future
        t('back_to_main_menu')
    ]
    return create_reply_options_keyboard(options, columns=1, add_cancel=False)

def get_role_selection_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard([t('buyer_role'), t('broker_role')], add_cancel=False)

# --- Submission & Filter Flow Keyboards ---
def get_property_type_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    options = [pt.value for pt in PropertyType]
    return create_reply_options_keyboard(options)

def get_bedroom_keyboard(is_filter: bool = False, lang: str = 'en') -> ReplyKeyboardMarkup:
    options = BEDROOM_OPTIONS
    if is_filter:
        options = options + [ANY_OPTION]
    return create_reply_options_keyboard(options, columns=4)

def get_bathroom_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard(BATHROOM_OPTIONS, columns=4)

# --- FIX: Added the missing keyboard function ---
def get_size_range_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard(list(SIZE_RANGES_TEXT.keys()), columns=2)

def get_price_range_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    options = list(PRICE_RANGES_TEXT.keys()) + [ANY_PRICE]
    return create_reply_options_keyboard(options, columns=2)

def get_region_keyboard(is_filter: bool = False, lang: str = 'en') -> ReplyKeyboardMarkup:
    options = REGIONS
    if is_filter:
        options = options + [ANY_REGION]
    return create_reply_options_keyboard(options)

def get_condo_scheme_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    options = CONDO_SCHEMES + [ANY_SCHEME]
    return create_reply_options_keyboard(options)

# --- Inline Keyboard for Admin Actions ---
def create_admin_approval_keyboard(prop_id: str, lang: str = 'en') -> InlineKeyboardMarkup:
    keyboard = [[
        InlineKeyboardButton(t('admin_approve', lang), callback_data=f"{CB_ADMIN_APPROVE}_{prop_id}"),
        InlineKeyboardButton(t('admin_reject', lang), callback_data=f"{CB_ADMIN_REJECT}_{prop_id}")
    ]]
    return InlineKeyboardMarkup(keyboard)