import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from src.use_cases.property_use_cases import PropertyUseCases
from src.domain.models.property_models import PropertyFilter, PropertyType, CondoScheme
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *
from src.utils.display_utils import create_property_card_text # <<< IMPORTED UTILITY

logger = logging.getLogger(__name__)

async def show_properties(update: Update, context: ContextTypes.DEFAULT_TYPE, filters: PropertyFilter):
    """A helper function to fetch and display properties using rich cards."""
    source_message = update.message or update.callback_query.message
    await source_message.reply_text("Searching for properties...", reply_markup=keyboards.REMOVE_KEYBOARD)
    
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    properties = await prop_cases.find_properties(filters)
    
    user = context.user_data.get('user')
    main_menu_keyboard = keyboards.get_main_menu_keyboard(user) if user else None

    if not properties:
        await source_message.reply_text(
            "No properties found matching your criteria.",
            reply_markup=main_menu_keyboard
        )
        return

    await source_message.reply_text(f"Found {len(properties)} matching properties:")

    for prop in properties[:10]: # Limit to 10 to avoid spam
        media_group = [InputMediaPhoto(media=url) for url in prop.image_urls]
        prop_details_card = create_property_card_text(prop, for_admin=False) # <<< USING UTILITY

        try:
            await context.bot.send_media_group(chat_id=source_message.chat_id, media=media_group)
            await context.bot.send_message(
                chat_id=source_message.chat_id,
                text=prop_details_card,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send rich card for property {prop.pid}: {e}")
            await context.bot.send_message(
                chat_id=source_message.chat_id,
                text=f"Error displaying property {prop.pid}. Details:\n{prop_details_card}",
                parse_mode='Markdown'
            )
            
    if len(properties) > 10:
        await source_message.reply_text("Showing the first 10 results. For more, please refine your search.", reply_markup=main_menu_keyboard)
    else:
        await source_message.reply_text("End of results.", reply_markup=main_menu_keyboard)

# --- Filtering Conversation (This section remains unchanged) ---
async def start_filtering(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['filters'] = {}
    await update.message.reply_text(
        text=t('select_property_type', default="First, select a property type:"),
        reply_markup=keyboards.get_property_type_keyboard()
    )
    return STATE_FILTER_PROP_TYPE

async def receive_filter_prop_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        prop_type = PropertyType(update.message.text)
        context.user_data['filters']['property_type'] = prop_type
        await update.message.reply_text(
            text=t('how_many_bedrooms', default="How many bedrooms?"),
            reply_markup=keyboards.get_bedroom_keyboard(is_filter=True)
        )
        return STATE_FILTER_BEDROOMS
    except ValueError:
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_FILTER_PROP_TYPE

async def receive_filter_bedrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    bedrooms_text = update.message.text
    if bedrooms_text != ANY_OPTION:
        try:
            min_bedrooms = int(bedrooms_text.replace('+', ''))
            context.user_data['filters']['min_bedrooms'] = min_bedrooms
        except (ValueError, TypeError):
            await update.message.reply_text("Invalid choice. Please use the keyboard.")
            return STATE_FILTER_BEDROOMS
    
    await update.message.reply_text(
        text=t('select_region', default="Which region?"),
        reply_markup=keyboards.get_region_keyboard(is_filter=True)
    )
    return STATE_FILTER_LOCATION_REGION

async def receive_filter_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    region_text = update.message.text
    if region_text != ANY_REGION:
        context.user_data['filters']['location_region'] = region_text

    await update.message.reply_text(
        text=t('select_price_range', default="Select a price range:"),
        reply_markup=keyboards.get_price_range_keyboard()
    )
    return STATE_FILTER_PRICE_RANGE

async def receive_filter_price_range(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    price_text = update.message.text
    if price_text != ANY_PRICE:
        price_value = keyboards.PRICE_RANGES_TEXT.get(price_text)
        if not price_value:
            await update.message.reply_text("Invalid choice. Please use the keyboard.")
            return STATE_FILTER_PRICE_RANGE
        price_range = price_value.split('-')
        context.user_data['filters']['min_price'] = float(price_range[0])
        context.user_data['filters']['max_price'] = float(price_range[1])
    
    filters_so_far = context.user_data['filters']
    if filters_so_far.get('property_type') == PropertyType.CONDOMINIUM:
        await update.message.reply_text(
            text=t('select_condo_scheme', default="Select a Condominium scheme:"),
            reply_markup=keyboards.get_condo_scheme_keyboard()
        )
        return STATE_FILTER_CONDO_SCHEME

    final_filters = PropertyFilter(**filters_so_far)
    await show_properties(update, context, final_filters)
    context.user_data.pop('filters', None)
    return ConversationHandler.END

async def receive_filter_condo_scheme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    scheme_text = update.message.text
    if scheme_text != ANY_SCHEME:
        try:
            context.user_data['filters']['condominium_scheme'] = CondoScheme(scheme_text)
        except ValueError:
            await update.message.reply_text("Invalid choice. Please use the keyboard.")
            return STATE_FILTER_CONDO_SCHEME
            
    final_filters = PropertyFilter(**context.user_data['filters'])
    await show_properties(update, context, final_filters)
    context.user_data.pop('filters', None)
    return ConversationHandler.END

async def browse_all_properties(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for browsing all properties without filters."""
    await show_properties(update, context, PropertyFilter())
    return ConversationHandler.END