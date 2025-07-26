import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from src.use_cases.property_use_cases import PropertyUseCases
from src.domain.models.property_models import PropertyCreate, PropertyType, Location, FurnishingStatus, CondoScheme
from src.domain.models.user_models import User
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *
from src.utils.display_utils import create_property_card_text
from .common_handlers import ensure_user_data, handle_exceptions

logger = logging.getLogger(__name__)

# --- Property Submission Conversation ---

@handle_exceptions
@ensure_user_data
async def start_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data'] = {}
    user: User = context.user_data['user']
    await update.message.reply_text(
        t('property_submission_start', lang=user.language),
        reply_markup=keyboards.get_property_type_keyboard(lang=user.language)
    )
    return STATE_SUBMIT_PROP_TYPE

@handle_exceptions
@ensure_user_data
async def receive_property_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['property_type'] = PropertyType(update.message.text)
    # For now, we assume Addis Ababa. This could be a question itself.
    context.user_data['submission_data']['location'] = {'region': 'Addis Ababa', 'city': 'Addis Ababa'}
    user: User = context.user_data['user']
    await update.message.reply_text(
        t('select_sub_city', lang=user.language, default="In which Sub-city is the property located?"),
        reply_markup=keyboards.get_sub_city_keyboard(lang=user.language)
    )
    return STATE_SUBMIT_LOCATION_SUB_CITY

@handle_exceptions
@ensure_user_data
async def receive_sub_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sub_city = update.message.text
    context.user_data['submission_data']['location']['sub_city'] = sub_city
    user: User = context.user_data['user']
    
    prop_type = context.user_data['submission_data']['property_type']
    if prop_type == PropertyType.CONDOMINIUM:
        keyboard = keyboards.get_condo_site_keyboard(sub_city, lang=user.language)
        prompt = t('select_condo_site', lang=user.language, default="Please select the Condominium Site name.")
    else:
        keyboard = keyboards.get_neighborhood_keyboard(sub_city, lang=user.language)
        prompt = t('select_neighborhood', lang=user.language, default="Please select the nearest neighborhood/area.")

    if not keyboard.keyboard:
        prompt = t('type_specific_area', lang=user.language, default="Could not find specific areas. Please type the specific area name.")
        keyboard = keyboards.REMOVE_KEYBOARD
    
    await update.message.reply_text(prompt, reply_markup=keyboard)
    return STATE_SUBMIT_SPECIFIC_AREA

@handle_exceptions
@ensure_user_data
async def receive_specific_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['location']['specific_area'] = update.message.text
    user: User = context.user_data['user']
    await update.message.reply_text(
        t('how_many_bedrooms', lang=user.language), 
        reply_markup=keyboards.get_bedroom_keyboard(lang=user.language)
    )
    return STATE_SUBMIT_BEDROOMS

@handle_exceptions
@ensure_user_data
async def receive_bedrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    try:
        cleaned_text = update.message.text.split(' ')[0].replace('+', '')
        context.user_data['submission_data']['bedrooms'] = int(cleaned_text)
        await update.message.reply_text(
            t('how_many_bathrooms', lang=user.language), 
            reply_markup=keyboards.get_bathroom_keyboard(lang=user.language)
        )
        return STATE_SUBMIT_BATHROOMS
    except (ValueError, TypeError):
        await update.message.reply_text(
            t('invalid_number', lang=user.language, default="That's not a valid number. Please use the buttons."), 
            reply_markup=keyboards.get_bedroom_keyboard(lang=user.language)
        )
        return STATE_SUBMIT_BEDROOMS

@handle_exceptions
@ensure_user_data
async def receive_bathrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    try:
        cleaned_text = update.message.text.replace('+', '')
        context.user_data['submission_data']['bathrooms'] = int(cleaned_text)
        await update.message.reply_text(
            t('what_is_size', lang=user.language),
            reply_markup=keyboards.get_size_range_keyboard(lang=user.language)
        )
        return STATE_SUBMIT_SIZE
    except (ValueError, TypeError):
        await update.message.reply_text(
            t('invalid_number', lang=user.language, default="That's not a valid number. Please use the buttons."),
            reply_markup=keyboards.get_bathroom_keyboard(lang=user.language)
        )
        return STATE_SUBMIT_BATHROOMS

@handle_exceptions
@ensure_user_data
async def receive_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # This function now asks the conditional question
    size_range = keyboards.SIZE_RANGES_TEXT[update.message.text].split('-')
    context.user_data['submission_data']['size_sqm'] = (int(size_range[0]) + int(size_range[1])) / 2
    
    user: User = context.user_data['user']
    prop_type = context.user_data['submission_data']['property_type']
    
    # --- MODIFIED LOGIC ---
    if prop_type == PropertyType.VILLA:
        prompt = t('what_is_g_plus', lang=user.language)
        keyboard = keyboards.get_g_plus_keyboard(lang=user.language)
    else:
        prompt = t('what_is_floor', lang=user.language)
        # For Apartments/Condos, we still want a free-text input for floor number
        keyboard = keyboards.REMOVE_KEYBOARD

    await update.message.reply_text(prompt, reply_markup=keyboard)
    return STATE_SUBMIT_FLOOR_LEVEL

@handle_exceptions
@ensure_user_data
async def receive_floor_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # This function now correctly parses both "5" and "G+2" style inputs
    user: User = context.user_data['user']
    user_input = update.message.text.strip()
    
    try:
        # --- MODIFIED LOGIC ---
        numeric_part = user_input
        if "G+" in user_input.upper():
            # Handles "G+1", "g+2", etc.
            numeric_part = user_input.upper().replace("G+", "")
        
        # Handles "0 (Ground)" -> "0"
        cleaned_text = numeric_part.split(' ')[0].replace('+', '')
        
        floor_value = int(cleaned_text)
        context.user_data['submission_data']['floor_level'] = floor_value
        # --- END MODIFIED LOGIC ---

        await update.message.reply_text(
            t('what_is_furnishing', lang=user.language, default="What is the Furnishing Status?"),
            reply_markup=keyboards.get_furnishing_status_keyboard(lang=user.language)
        )
        return STATE_SUBMIT_FURNISHING_STATUS
        
    except (ValueError, TypeError):
        await update.message.reply_text(
            t('invalid_number', lang=user.language, default="That's not a valid number. Please use the buttons or type a number.")
        )
        return STATE_SUBMIT_FLOOR_LEVEL

@handle_exceptions
@ensure_user_data
async def receive_furnishing_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['furnishing_status'] = FurnishingStatus(update.message.text)
    user: User = context.user_data['user']
    await update.message.reply_text(
        t('has_title_deed', lang=user.language),
        reply_markup=keyboards.get_boolean_keyboard(lang=user.language)
    )
    return STATE_SUBMIT_TITLE_DEED

@handle_exceptions
@ensure_user_data
async def receive_title_deed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['submission_data']['title_deed'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(
        t('how_many_parking', lang=user.language),
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_SUBMIT_PARKING_SPACES

@handle_exceptions
@ensure_user_data
async def receive_parking_spaces(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    try:
        cleaned_text = update.message.text.replace('+', '')
        context.user_data['submission_data']['parking_spaces'] = int(cleaned_text)
        
        prop_type = context.user_data['submission_data']['property_type']
        if prop_type == PropertyType.CONDOMINIUM:
            await update.message.reply_text(
                t('what_is_condo_scheme', lang=user.language),
                reply_markup=keyboards.get_condo_scheme_keyboard(lang=user.language)
            )
            return STATE_SUBMIT_CONDO_SCHEME
        else:
            await update.message.reply_text(
                t('what_is_price', lang=user.language), 
                reply_markup=keyboards.REMOVE_KEYBOARD
            )
            return STATE_SUBMIT_PRICE
    except (ValueError, TypeError):
        await update.message.reply_text(
            t('invalid_number', lang=user.language, default="That's not a valid number. Please use the buttons.")
        )
        return STATE_SUBMIT_PARKING_SPACES

@handle_exceptions
@ensure_user_data
async def receive_condo_scheme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['condominium_scheme'] = CondoScheme(update.message.text)
    user: User = context.user_data['user']
    await update.message.reply_text(
        t('what_is_price', lang=user.language), 
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_SUBMIT_PRICE

@handle_exceptions
@ensure_user_data
async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    try:
        context.user_data['submission_data']['price_etb'] = float(update.message.text)
        context.user_data['submission_data']['image_urls'] = []
        await update.message.reply_text(
            t('upload_images', lang=user.language),
            reply_markup=keyboards.get_image_upload_keyboard(lang=user.language)
        )
        return STATE_SUBMIT_IMAGES
    except (ValueError, TypeError):
        await update.message.reply_text(
            t('invalid_price', lang=user.language, default="Please enter a valid number for the price.")
        )
        return STATE_SUBMIT_PRICE

@handle_exceptions
@ensure_user_data
async def receive_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    if not update.message.photo:
        await update.message.reply_text(
            t('not_an_image', lang=user.language, default="That's not an image. Please send photos or click the 'Done' button.")
        )
        return STATE_SUBMIT_IMAGES
    context.user_data['submission_data']['image_urls'].append(update.message.photo[-1].file_id)
    await update.message.reply_text(
        t('image_received', lang=user.language, default="Image {count} received. Send more or click 'Done Uploading'.").format(count=len(context.user_data['submission_data']['image_urls']))
    )
    return STATE_SUBMIT_IMAGES

@handle_exceptions
@ensure_user_data
async def done_receiving_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    images = context.user_data.get('submission_data', {}).get('image_urls', [])
    user: User = context.user_data['user']
    if len(images) < 3:
        await update.message.reply_text(
            t('need_more_images', lang=user.language).format(count=len(images))
        )
        return STATE_SUBMIT_IMAGES
    await update.message.reply_text(
        t('enter_description', lang=user.language), 
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_SUBMIT_DESCRIPTION

@handle_exceptions
@ensure_user_data
async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['description'] = update.message.text
    user: User = context.user_data['user']
    
    # Finalize data before creation
    location_obj = Location(**context.user_data['submission_data'].pop('location'))
    context.user_data['submission_data']['location'] = location_obj
    
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    try:
        property_to_create = PropertyCreate(broker_id=user.uid, broker_name=user.display_name or "N/A", **context.user_data['submission_data'])
        await prop_cases.submit_property(property_to_create)
        await update.message.reply_text(
            t('submission_complete', lang=user.language),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    except Exception as e:
        logger.error(f"Error during property submission: {e}", exc_info=True)
        await update.message.reply_text(t('error_occurred', lang=user.language, default="An error occurred. Please try again."))
    
    context.user_data.pop('submission_data', None)
    return ConversationHandler.END

# --- "My Listings" Handler (UPDATED) ---    
@handle_exceptions
@ensure_user_data
async def my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the broker's own listings using the rich card format."""
    user: User = context.user_data['user']
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    
    listings = await prop_cases.get_properties_by_broker(user.uid)
    
    if not listings:
        await update.message.reply_text(
            t('no_listings_yet', lang=user.language, default="You have not submitted any properties yet."),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        return
        
    await update.message.reply_text(t('displaying_your_listings', lang=user.language, default="Displaying your submitted properties:"))
    
    for prop in listings:
        media_group = [InputMediaPhoto(media=url) for url in prop.image_urls]
        prop_details_card = create_property_card_text(prop, for_broker=True)

        try:
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_group)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prop_details_card,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Failed to send rich card for broker's property {prop.pid}: {e}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Error displaying property. Details:\n{prop_details_card}",
                parse_mode='Markdown'
            )
    
    await update.message.reply_text(
        t('end_of_listings', lang=user.language, default="End of your listings."),
        reply_markup=keyboards.get_main_menu_keyboard(user)
    )