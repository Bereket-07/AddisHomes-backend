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

    # --- THIS IS THE FIX ---
    # Pass 'count' as a keyword argument directly to t()
    await source_message.reply_text(t(
        'found_properties', 
        lang=lang, 
        default="Found {count} matching properties:",
        count=len(properties)  # Pass count as a kwarg here
    ))
    # -----------------------

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

# --- Filtering Conversation (RE-ORDERED & FIXED) ---

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

# STEP 1: Receive Property Type, then ask for Scheme (if Condo) or Price (if not)
@handle_exceptions
@ensure_user_data
async def receive_filter_prop_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    prop_type = PropertyType(update.message.text)
    context.user_data['filters']['property_type'] = prop_type
    user: User = context.user_data['user']
    
    if prop_type == PropertyType.CONDOMINIUM:
        await update.message.reply_text(
            text=t('select_condo_scheme', lang=user.language),
            reply_markup=keyboards.get_condo_scheme_keyboard(is_filter=True, lang=user.language)
        )
        return STATE_FILTER_CONDO_SCHEME
    else:
        await update.message.reply_text(
            text=t('select_price_range', lang=user.language),
            reply_markup=keyboards.get_price_range_keyboard(lang=user.language)
        )
        return STATE_FILTER_PRICE_RANGE

# STEP 2 (Conditional): Receive Condo Scheme, then ask for Price
@handle_exceptions
@ensure_user_data
async def receive_filter_condo_scheme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    scheme_text = update.message.text
    user: User = context.user_data['user']
    if scheme_text != t('any_scheme', lang=user.language):
        context.user_data['filters']['condominium_scheme'] = CondoScheme(scheme_text)
            
    await update.message.reply_text(
        text=t('select_price_range', lang=user.language),
        reply_markup=keyboards.get_price_range_keyboard(lang=user.language)
    )
    return STATE_FILTER_PRICE_RANGE

# STEP 3: Receive Price Range, then ask for Region
@handle_exceptions
@ensure_user_data
async def receive_filter_price_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price_text = update.message.text
    user: User = context.user_data['user']
    if price_text != t('any_price', lang=user.language):
        # This assumes PRICE_RANGES_TEXT keys are not translated. If they are, this logic needs adjustment.
        price_value = keyboards.PRICE_RANGES_TEXT.get(price_text)
        if price_value:
            price_range = price_value.split('-')
            context.user_data['filters']['min_price'] = float(price_range[0])
            context.user_data['filters']['max_price'] = float(price_range[1])
    
    await update.message.reply_text(
        text=t('select_region', lang=user.language),
        reply_markup=keyboards.get_region_keyboard(is_filter=True, lang=user.language)
    )
    return STATE_FILTER_LOCATION_REGION

# STEP 4: Receive Region, then ask for Bedrooms
@handle_exceptions
@ensure_user_data
async def receive_filter_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    region_text = update.message.text
    user: User = context.user_data['user']
    
    if region_text != t('any_region', lang=user.language):
        context.user_data['filters']['location_region'] = region_text

    # --- MODIFIED LOGIC ---
    prop_type = context.user_data['filters'].get('property_type')
    
    if prop_type == PropertyType.VILLA:
        # If it's a villa, ask for G+ structure
        await update.message.reply_text(
            text=t('what_is_g_plus', lang=user.language),
            reply_markup=keyboards.get_g_plus_keyboard(is_filter=True, lang=user.language)
        )
        return STATE_FILTER_VILLA_STRUCTURE
    else:
        # For all other types, go to bedrooms
        await update.message.reply_text(
            text=t('how_many_bedrooms', lang=user.language),
            reply_markup=keyboards.get_bedroom_keyboard(is_filter=True, lang=user.language)
        )
        return STATE_FILTER_BEDROOMS
    # --- END MODIFIED LOGIC ---

# --- NEW HANDLER FOR VILLA STRUCTURE FILTER ---
# STEP 4.5 (Conditional): Receive Villa Structure, then ask for Bedrooms
@handle_exceptions
@ensure_user_data
async def receive_filter_villa_structure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    user_input = update.message.text.strip()
    
    if user_input != t('any_option', lang=user.language):
        # We will filter for "greater than or equal to"
        # "G+2" means we search for G+2, G+3, etc.
        numeric_part = user_input.upper().replace("G+", "").replace("+", "")
        try:
            # We don't have a specific filter for floor_level, so this will be a post-filter step.
            # For now, let's just store it. We'll add the actual filtering logic in firestore_repo.py
            context.user_data['filters']['min_floor_level'] = int(numeric_part)
        except (ValueError, TypeError):
            pass # Ignore if input is invalid, effectively treating it as "Any"
            
    # Now ask for bedrooms
    await update.message.reply_text(
        text=t('how_many_bedrooms', lang=user.language),
        reply_markup=keyboards.get_bedroom_keyboard(is_filter=True, lang=user.language)
    )
    return STATE_FILTER_BEDROOMS

# STEP 5 (FINAL): Receive Bedrooms, show results, AND send the final menu
@handle_exceptions
@ensure_user_data
async def receive_filter_bedrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bedrooms_text = update.message.text
    user: User = context.user_data['user']
    if bedrooms_text != t('any_option', lang=user.language):
        min_bedrooms = int(bedrooms_text.replace('+', ''))
        context.user_data['filters']['min_bedrooms'] = min_bedrooms
    
    # Build the filters from all collected data
    final_filters = PropertyFilter(**context.user_data['filters'])
    
    # Call the helper to display the properties
    await show_properties(update, context, final_filters)
    
    # After showing properties, send a final confirmation message WITH the main menu
    await update.message.reply_text(
        text=t('search_complete', lang=user.language, default="Search complete. Returning to the main menu."),
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )
    
    # Clean up and end the conversation
    context.user_data.pop('filters', None)
    return ConversationHandler.END


@handle_exceptions
@ensure_user_data
async def browse_all_properties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for browsing all properties without filters."""
    # We can reuse the final logic from the conversation for a consistent experience
    await show_properties(update, context, PropertyFilter())
    user = context.user_data.get('user')
    await update.message.reply_text(
        text=t('browse_complete', lang=user.language, default="Browse complete. Returning to the main menu."),
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )