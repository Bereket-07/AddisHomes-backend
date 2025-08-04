import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from src.use_cases.property_use_cases import PropertyUseCases
from src.domain.models.property_models import PropertyFilter, PropertyType, CondoScheme
from src.domain.models.user_models import User
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *
from src.utils.display_utils import create_property_card_text
from .common_handlers import ensure_user_data, handle_exceptions

logger = logging.getLogger(__name__)

async def show_properties(update: Update, context: ContextTypes.DEFAULT_TYPE, filters: PropertyFilter):
    """
    A helper function to fetch and display properties.
    It no longer sends the final menu.
    """
    source_message = update.message or update.callback_query.message
    user: User = context.user_data.get('user')
    lang = user.language if user else 'en'

    await source_message.reply_text(
        t('searching', lang=lang, default="Searching for properties..."), 
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    properties = await prop_cases.find_properties(filters)
    
    if not properties:
        await source_message.reply_text(t('no_properties_found', lang=lang, default="No properties found matching your criteria."))
        return # Exit the function

    await source_message.reply_text(t(
        'found_properties', 
        lang=lang, 
        default="Found {count} matching properties:",
        count=len(properties)
    ))

    # Limit to first 10 results to avoid spamming the user
    for prop in properties[:10]:
        try:
            media_group = [InputMediaPhoto(media=url) for url in prop.image_urls]
            prop_details_card = create_property_card_text(prop, for_admin=False)

            await context.bot.send_media_group(chat_id=source_message.chat_id, media=media_group)
            await context.bot.send_message(
                chat_id=source_message.chat_id,
                text=prop_details_card,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send property card {prop.pid}: {e}")
            await context.bot.send_message(
                chat_id=source_message.chat_id,
                text=f"Error displaying a property (ID: {prop.pid[:8]}...). Continuing..."
            )
            
    if len(properties) > 10:
        await source_message.reply_text(t('showing_first_10', lang=lang, default="Showing the first 10 results. For more, please refine your search."))

# --- Filtering Conversation ---

# STEP 0: Entry Point
@handle_exceptions
@ensure_user_data
async def start_filtering(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['filters'] = {}
    user: User = context.user_data['user']
    await update.message.reply_text(
        text=t('select_property_type', lang=user.language),
        reply_markup=keyboards.get_property_type_keyboard(lang=user.language)
    )
    return STATE_FILTER_PROP_TYPE

# STEP 1: Receive Property Type, then branch
@handle_exceptions
@ensure_user_data
async def receive_filter_prop_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # --- UPDATED ---
    prop_type = PropertyType(update.message.text)
    context.user_data['filters']['property_type'] = prop_type
    user: User = context.user_data['user']
    
    if prop_type == PropertyType.CONDOMINIUM:
        await update.message.reply_text(t('select_condo_scheme', lang=user.language), reply_markup=keyboards.get_condo_scheme_keyboard(is_filter=True, lang=user.language))
        return STATE_FILTER_CONDO_SCHEME
    
    elif prop_type == PropertyType.APARTMENT:
        await update.message.reply_text(t('select_site_filter', lang=user.language, default="Filter by site/area:"), reply_markup=keyboards.get_site_keyboard(is_filter=True, lang=user.language))
        return STATE_FILTER_SITE

    # Existing logic for other types
    elif prop_type == PropertyType.BUILDING:
        await update.message.reply_text(t('ask_filter_is_commercial', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
        return STATE_FILTER_IS_COMMERCIAL
    elif prop_type == PropertyType.PENTHOUSE:
        await update.message.reply_text(t('ask_filter_has_rooftop', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
        return STATE_FILTER_HAS_ROOFTOP
    elif prop_type == PropertyType.DUPLEX:
        await update.message.reply_text(t('ask_filter_has_entrance', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
        return STATE_FILTER_HAS_ENTRANCE
    else: # Villa, etc. go to the price range
        await update.message.reply_text(t('select_price_range', lang=user.language), reply_markup=keyboards.get_price_range_keyboard(lang=user.language))
        return STATE_FILTER_PRICE_RANGE

# === BUILDING FILTER FLOW (Unchanged) ===
@handle_exceptions
@ensure_user_data
async def receive_filter_is_commercial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['filters']['filter_is_commercial'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(t('ask_filter_has_elevator', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
    return STATE_FILTER_HAS_ELEVATOR

@handle_exceptions
@ensure_user_data
async def receive_filter_has_elevator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['filters']['filter_has_elevator'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(t('select_price_range', lang=user.language), reply_markup=keyboards.get_price_range_keyboard(lang=user.language))
    return STATE_FILTER_PRICE_RANGE

# === PENTHOUSE FILTER FLOW (Unchanged) ===
@handle_exceptions
@ensure_user_data
async def receive_filter_has_rooftop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['filters']['filter_has_private_rooftop'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(t('ask_filter_is_two_story', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
    return STATE_FILTER_IS_TWO_STORY

@handle_exceptions
@ensure_user_data
async def receive_filter_is_two_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['filters']['filter_is_two_story_penthouse'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(t('select_price_range', lang=user.language), reply_markup=keyboards.get_price_range_keyboard(lang=user.language))
    return STATE_FILTER_PRICE_RANGE

# === DUPLEX FILTER FLOW (Unchanged) ===
@handle_exceptions
@ensure_user_data
async def receive_filter_has_entrance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['filters']['filter_has_private_entrance'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(t('select_price_range', lang=user.language), reply_markup=keyboards.get_price_range_keyboard(lang=user.language))
    return STATE_FILTER_PRICE_RANGE

# === COMMON & NEW FLOWS ===
@handle_exceptions
@ensure_user_data
async def receive_filter_condo_scheme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # --- UPDATED ---
    user: User = context.user_data['user']
    if update.message.text != t('any_scheme', lang=user.language):
        context.user_data['filters']['condominium_scheme'] = CondoScheme(update.message.text)
    # Now ask for the site
    await update.message.reply_text(t('select_site_filter', lang=user.language, default="Filter by site/area:"), reply_markup=keyboards.get_site_keyboard(is_filter=True, lang=user.language))
    return STATE_FILTER_SITE

# --- NEW HANDLER for Site filter ---
@handle_exceptions
@ensure_user_data
async def receive_filter_site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives site filter and handles 'Other' and 'Any'."""
    user_input = update.message.text
    user: User = context.user_data['user']
    other_option_text = t('other_option', lang=user.language, default=OTHER_OPTION_EN)
    any_option_text = t('any_option', lang=user.language)

    if user_input == other_option_text:
        await update.message.reply_text(t('type_specific_area', lang=user.language))
        return STATE_FILTER_OTHER_SITE
    
    if user_input != any_option_text:
        context.user_data['filters']['location_site'] = user_input
    
    # Move on to the next filter: price range
    await update.message.reply_text(t('select_price_range', lang=user.language), reply_markup=keyboards.get_price_range_keyboard(lang=user.language))
    return STATE_FILTER_PRICE_RANGE

# --- NEW HANDLER for "Other" site filter ---
@handle_exceptions
@ensure_user_data
async def receive_filter_other_site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives manually typed site filter."""
    user: User = context.user_data['user']
    user_input = update.message.text
    context.user_data['filters']['location_site'] = user_input
    
    # Move on to the next filter: price range
    await update.message.reply_text(t('select_price_range', lang=user.language), reply_markup=keyboards.get_price_range_keyboard(lang=user.language))
    return STATE_FILTER_PRICE_RANGE

@handle_exceptions
@ensure_user_data
async def receive_filter_price_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    if update.message.text != t('any_price', lang=user.language):
        price_value = keyboards.PRICE_RANGES_TEXT.get(update.message.text)
        if price_value:
            price_range = price_value.split('-')
            context.user_data['filters']['min_price'] = float(price_range[0])
            context.user_data['filters']['max_price'] = float(price_range[1])
            
    # --- UPDATED ---: Decide next step based on property type
    prop_type = context.user_data['filters'].get('property_type')
    
    if prop_type in [PropertyType.APARTMENT, PropertyType.CONDOMINIUM, PropertyType.PENTHOUSE, PropertyType.DUPLEX]:
         await update.message.reply_text(t('how_many_bedrooms', lang=user.language), reply_markup=keyboards.get_bedroom_keyboard(is_filter=True, lang=user.language))
         return STATE_FILTER_BEDROOMS
    elif prop_type == PropertyType.VILLA:
         await update.message.reply_text(t('select_region', lang=user.language), reply_markup=keyboards.get_region_keyboard(is_filter=True, lang=user.language))
         return STATE_FILTER_LOCATION_REGION
    else: # For Building type, we can end here
        return await end_filter_conversation(update, context)

@handle_exceptions
@ensure_user_data
async def receive_filter_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # This handler is now mostly for Villas
    user: User = context.user_data['user']
    if update.message.text != t('any_region', lang=user.language):
        context.user_data['filters']['location_region'] = update.message.text
        
    prop_type = context.user_data['filters'].get('property_type')
    if prop_type == PropertyType.VILLA:
        await update.message.reply_text(t('what_is_g_plus', lang=user.language), reply_markup=keyboards.get_g_plus_keyboard(is_filter=True, lang=user.language))
        return STATE_FILTER_VILLA_STRUCTURE
    else: # Fallback for other types if they reach here
        await update.message.reply_text(t('how_many_bedrooms', lang=user.language), reply_markup=keyboards.get_bedroom_keyboard(is_filter=True, lang=user.language))
        return STATE_FILTER_BEDROOMS

@handle_exceptions
@ensure_user_data
async def receive_filter_villa_structure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    if update.message.text != t('any_option', lang=user.language):
        numeric_part = update.message.text.upper().replace("G+", "").replace("+", "")
        try:
            context.user_data['filters']['min_floor_level'] = int(numeric_part)
        except (ValueError, TypeError):
            pass
    await update.message.reply_text(t('how_many_bedrooms', lang=user.language), reply_markup=keyboards.get_bedroom_keyboard(is_filter=True, lang=user.language))
    return STATE_FILTER_BEDROOMS

@handle_exceptions
@ensure_user_data
async def receive_filter_bedrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    if update.message.text != t('any_option', lang=user.language):
        min_bedrooms = int(update.message.text.replace('+', ''))
        context.user_data['filters']['min_bedrooms'] = min_bedrooms
    return await end_filter_conversation(update, context)

async def end_filter_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Helper function to finalize the filtering conversation."""
    user: User = context.user_data['user']
    final_filters = PropertyFilter(**context.user_data['filters'])
    await show_properties(update, context, final_filters)
    await update.message.reply_text(
        text=t('search_complete', lang=user.language),
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )
    context.user_data.pop('filters', None)
    return ConversationHandler.END

@handle_exceptions
@ensure_user_data
async def browse_all_properties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_properties(update, context, PropertyFilter())
    user = context.user_data.get('user')
    await update.message.reply_text(
        text=t('browse_complete', lang=user.language),
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )