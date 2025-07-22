from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from src.domain.models.user_models import User, UserRole
from src.domain.models.property_models import PropertyType, CondoScheme
from src.utils.i18n import t

# A constant to remove the reply keyboard
REMOVE_KEYBOARD = ReplyKeyboardRemove()

# --- Data for Reply Keyboards ---
BEDROOM_OPTIONS = ["1", "2", "3", "4", "5", "6+"]
BATHROOM_OPTIONS = ["1", "2", "3", "4+"]
PRICE_RANGES_TEXT = {
    "Under 5M": "0-5000000",
    "5M - 10M": "5000000-10000000",
    "10M - 20M": "10000000-20000000",
    "20M - 33M": "20000000-33000000",
    "Above 33M": "33000000-9999999999",
    "Any Price": "any"
}
REGIONS = ["Addis Ababa", "Amhara", "Oromia", "Other", "Any Region"]
CONDO_SCHEMES = [cs.value for cs in CondoScheme] + ["Any Scheme"]

# --- Helper Function ---
def create_reply_options_keyboard(options: list, columns: int = 2, add_cancel=True) -> ReplyKeyboardMarkup:
    keyboard = [list(map(KeyboardButton, options[i:i + columns])) for i in range(0, len(options), columns)]
    if add_cancel:
        keyboard.append([KeyboardButton(t('cancel'))])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# --- Role-Specific & Main Menu (These are correct) ---
def get_main_menu_keyboard(user: User, lang: str = 'en') -> ReplyKeyboardMarkup:
    options = [t('browse_properties'), t('filter_properties')]
    if UserRole.BROKER in user.roles:
        options.extend([t('submit_property'), t('my_listings')])
    if UserRole.ADMIN in user.roles:
        options.append(t('admin_panel'))
    return create_reply_options_keyboard(options, columns=2, add_cancel=False)

def get_role_selection_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard([t('buyer_role'), t('broker_role')], add_cancel=False)

# ... other keyboards like admin panel ...

# --- Filter Flow Keyboards ---
def get_property_type_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    options = [pt.value for pt in PropertyType]
    return create_reply_options_keyboard(options)

def get_bedroom_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    options = BEDROOM_OPTIONS + ["Any"]
    return create_reply_options_keyboard(options, columns=4)

def get_price_range_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard(list(PRICE_RANGES_TEXT.keys()), columns=2)

def get_region_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard(REGIONS)

def get_condo_scheme_keyboard(lang: str = 'en') -> ReplyKeyboardMarkup:
    return create_reply_options_keyboard(CONDO_SCHEMES)

# --- Inline Keyboard for Admin Actions ---
def create_admin_approval_keyboard(prop_id: str, lang: str = 'en') -> InlineKeyboardMarkup:
    keyboard = [[
        InlineKeyboardButton(t('admin_approve', lang), callback_data=f"admin_approve_{prop_id}"),
        InlineKeyboardButton(t('admin_reject', lang), callback_data=f"admin_reject_{prop_id}")
    ]]
    return InlineKeyboardMarkup(keyboard)