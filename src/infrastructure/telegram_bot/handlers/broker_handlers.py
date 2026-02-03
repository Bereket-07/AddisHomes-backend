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
from src.infrastructure.storage_utils import upload_telegram_photo_to_storage
from src.utils.config import settings

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
    """Receives translated property type and converts it back to the enum."""
    user_input = update.message.text
    user: User = context.user_data['user']
    lang = user.language
    selected_prop_type = None

    # --- NEW LOGIC: Reverse-translate the user's input to find the correct enum ---
    for pt in PropertyType:
        translated_name = t(f"prop_type_{pt.name.lower()}", lang=lang)
        if user_input == translated_name:
            selected_prop_type = pt
            break

    # If we couldn't find a match, something went wrong (user typed manually).
    # For now, we'll assume they use the keyboard. If not, this will gracefully fail.
    if not selected_prop_type:
        # You could optionally send an error message here
        return STATE_SUBMIT_PROP_TYPE

    context.user_data['submission_data']['property_type'] = selected_prop_type
    context.user_data['submission_data']['location'] = {'region': 'Addis Ababa', 'city': 'Addis Ababa'}

    if selected_prop_type == PropertyType.CONDOMINIUM:
        await update.message.reply_text(
            t('what_is_condo_scheme', lang=lang),
            reply_markup=keyboards.get_condo_scheme_keyboard(lang=lang)
        )
        return STATE_SUBMIT_CONDO_SCHEME
    
    elif selected_prop_type == PropertyType.APARTMENT:
        await update.message.reply_text(
            t('select_site', lang=lang, default="Please select the site/area."),
            reply_markup=keyboards.get_site_keyboard(lang=lang)
        )
        return STATE_SUBMIT_SITE
    
    elif selected_prop_type == PropertyType.BUILDING:
        await update.message.reply_text(
            t('is_commercial', lang=lang),
            reply_markup=keyboards.get_boolean_keyboard(lang=lang)
        )
        return STATE_SUBMIT_IS_COMMERCIAL
    else:
        await update.message.reply_text(
            t('how_many_bedrooms', lang=lang), 
            reply_markup=keyboards.get_bedroom_keyboard(lang=lang)
        )
        return STATE_SUBMIT_BEDROOMS

# --- DEPRECATED receive_sub_city ---
# --- DEPRECATED receive_specific_area ---

# --- NEW HANDLER for Condo scheme, now early in the flow ---
@handle_exceptions
@ensure_user_data
async def receive_condo_scheme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['condominium_scheme'] = CondoScheme(update.message.text)
    user: User = context.user_data['user']
    # After scheme, ask for the site
    await update.message.reply_text(
        t('select_site', lang=user.language, default="Great. Now, please select the Condominium's site/area."),
        reply_markup=keyboards.get_site_keyboard(lang=user.language)
    )
    return STATE_SUBMIT_SITE

# --- NEW HANDLER for Site selection ---
@handle_exceptions
@ensure_user_data
async def receive_site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the site selection, handles 'Other', and translates input."""
    user_input = update.message.text
    user: User = context.user_data['user']
    lang = user.language
    other_option_text = t('other_option', lang=lang)

    if user_input == other_option_text:
        await update.message.reply_text(
            t('type_specific_area', lang=lang),
            reply_markup=keyboards.REMOVE_KEYBOARD
        )
        return STATE_SUBMIT_OTHER_SITE
    else:
        # --- NEW LOGIC: Reverse translate the input to store a consistent value ---
        site_to_store = user_input # Default to the input itself
        # Find the English value corresponding to the Amharic input
        for site in SUPPORTED_SITES:
            if site.get(lang) == user_input:
                site_to_store = site['en']
                break
        
        # Store the standardized English site name and move on
        context.user_data['submission_data']['location']['site'] = site_to_store
        await update.message.reply_text(
            t('how_many_bedrooms', lang=lang), 
            reply_markup=keyboards.get_bedroom_keyboard(lang=lang)
        )
        return STATE_SUBMIT_BEDROOMS

# --- NEW HANDLER for "Other" Site input ---
@handle_exceptions
@ensure_user_data
async def receive_other_site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the manually typed site name."""
    user_input = update.message.text
    user: User = context.user_data['user']
    # Store the site and move on to bedrooms
    context.user_data['submission_data']['location']['site'] = user_input
    await update.message.reply_text(
        t('how_many_bedrooms', lang=user.language), 
        reply_markup=keyboards.get_bedroom_keyboard(lang=user.language)
    )
    return STATE_SUBMIT_BEDROOMS

# === BUILDING SUBMISSION FLOW (Unchanged) ===
@handle_exceptions
@ensure_user_data
async def receive_is_commercial(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['submission_data']['is_commercial'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(t('total_floors', lang=user.language), reply_markup=keyboards.REMOVE_KEYBOARD)
    return STATE_SUBMIT_TOTAL_FLOORS

@handle_exceptions
@ensure_user_data
async def receive_total_floors(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    try:
        context.user_data['submission_data']['total_floors'] = int(update.message.text)
        context.user_data['submission_data']['bedrooms'] = 0
        context.user_data['submission_data']['bathrooms'] = 0
        await update.message.reply_text(t('total_units', lang=user.language), reply_markup=keyboards.REMOVE_KEYBOARD)
        return STATE_SUBMIT_TOTAL_UNITS
    except (ValueError, TypeError):
        await update.message.reply_text(t('invalid_number', lang=user.language))
        return STATE_SUBMIT_TOTAL_FLOORS

@handle_exceptions
@ensure_user_data
async def receive_total_units(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    try:
        context.user_data['submission_data']['total_units'] = int(update.message.text)
        await update.message.reply_text(t('has_elevator', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
        return STATE_SUBMIT_HAS_ELEVATOR
    except (ValueError, TypeError):
        await update.message.reply_text(t('invalid_number', lang=user.language))
        return STATE_SUBMIT_TOTAL_UNITS

@handle_exceptions
@ensure_user_data
async def receive_has_elevator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['submission_data']['has_elevator'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(
        t('what_is_size', lang=user.language),
        reply_markup=keyboards.get_size_range_keyboard(lang=user.language)
    )
    return STATE_SUBMIT_SIZE

# === REGULAR RESIDENTIAL FLOW (Unchanged - The new flow merges into this) ===
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
            t('invalid_number', lang=user.language), 
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
            t('invalid_number', lang=user.language),
            reply_markup=keyboards.get_bathroom_keyboard(lang=user.language)
        )
        return STATE_SUBMIT_BATHROOMS

# === COMMON FLOW (Unchanged) ===
@handle_exceptions
@ensure_user_data
async def receive_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    size_range = keyboards.SIZE_RANGES_TEXT[update.message.text].split('-')
    context.user_data['submission_data']['size_sqm'] = (int(size_range[0]) + int(size_range[1])) / 2
    
    user: User = context.user_data['user']
    prop_type = context.user_data['submission_data']['property_type']
    
    if prop_type == PropertyType.VILLA:
        prompt = t('what_is_g_plus', lang=user.language)
        keyboard = keyboards.get_g_plus_keyboard(lang=user.language)
        next_state = STATE_SUBMIT_FLOOR_LEVEL
    elif prop_type in [PropertyType.APARTMENT, PropertyType.PENTHOUSE, PropertyType.DUPLEX, PropertyType.CONDOMINIUM]:
        prompt = t('what_is_floor', lang=user.language)
        keyboard = keyboards.REMOVE_KEYBOARD
        next_state = STATE_SUBMIT_FLOOR_LEVEL
    else: # Building
        prompt = t('what_is_furnishing', lang=user.language)
        keyboard = keyboards.get_furnishing_status_keyboard(lang=user.language)
        next_state = STATE_SUBMIT_FURNISHING_STATUS

    await update.message.reply_text(prompt, reply_markup=keyboard)
    return next_state

@handle_exceptions
@ensure_user_data
async def receive_floor_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    user_input = update.message.text.strip()
    
    try:
        numeric_part = user_input
        if "G+" in user_input.upper():
            numeric_part = user_input.upper().replace("G+", "")
        cleaned_text = numeric_part.split(' ')[0].replace('+', '')
        floor_value = int(cleaned_text)
        context.user_data['submission_data']['floor_level'] = floor_value
        
        await update.message.reply_text(
            t('what_is_furnishing', lang=user.language),
            reply_markup=keyboards.get_furnishing_status_keyboard(lang=user.language)
        )
        return STATE_SUBMIT_FURNISHING_STATUS
    except (ValueError, TypeError):
        await update.message.reply_text(t('invalid_number', lang=user.language))
        return STATE_SUBMIT_FLOOR_LEVEL

@handle_exceptions
@ensure_user_data
async def receive_furnishing_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['submission_data']['furnishing_status'] = FurnishingStatus(update.message.text)
    
    prop_type = context.user_data['submission_data']['property_type']

    if prop_type == PropertyType.PENTHOUSE:
        await update.message.reply_text(t('has_private_rooftop', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
        return STATE_SUBMIT_HAS_ROOFTOP
    elif prop_type == PropertyType.DUPLEX:
        await update.message.reply_text(t('has_private_entrance', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
        return STATE_SUBMIT_HAS_ENTRANCE
    else:
        await update.message.reply_text(t('has_title_deed', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
        return STATE_SUBMIT_TITLE_DEED

# === PENTHOUSE FLOW (Unchanged) ===
@handle_exceptions
@ensure_user_data
async def receive_has_rooftop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['submission_data']['has_private_rooftop'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(t('is_two_story_penthouse', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
    return STATE_SUBMIT_IS_TWO_STORY

@handle_exceptions
@ensure_user_data
async def receive_is_two_story(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['submission_data']['is_two_story_penthouse'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(t('has_title_deed', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
    return STATE_SUBMIT_TITLE_DEED

# === DUPLEX FLOW (Unchanged) ===
@handle_exceptions
@ensure_user_data
async def receive_has_entrance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user: User = context.user_data['user']
    context.user_data['submission_data']['has_private_entrance'] = (update.message.text.lower() == t('yes', lang=user.language).lower())
    await update.message.reply_text(t('has_title_deed', lang=user.language), reply_markup=keyboards.get_boolean_keyboard(lang=user.language))
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
        
        # --- UPDATED ---: The condo scheme question is now at the beginning of the flow.
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
    # Take the highest resolution version
    photo = update.message.photo[-1]
    file_id = photo.file_id

    # Upload to Firebase Storage and get permanent URL
    # Pass repo to ensure DB blob storage
    repo = context.bot_data.get("property_use_cases").repo if context.bot_data.get("property_use_cases") else None
    public_url = await upload_telegram_photo_to_storage(context.bot, file_id, repo=repo)

    # Store the permanent URL instead of file_id
    context.user_data['submission_data']['image_urls'].append(public_url)

    await update.message.reply_text(
        t('image_received', lang=user.language, default="Image {count} received. Send more or click 'Done Uploading'.", count=len(context.user_data['submission_data']['image_urls']))
    )
    return STATE_SUBMIT_IMAGES

@handle_exceptions
@ensure_user_data
async def done_receiving_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    images = context.user_data.get('submission_data', {}).get('image_urls', [])
    user: User = context.user_data['user']
    if len(images) < 3:
        await update.message.reply_text(
            t('need_more_images', lang=user.language, count=len(images))
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
        prop_cases.submit_property(property_to_create)
        await update.message.reply_text(
            t('submission_complete', lang=user.language),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    except Exception as e:
        logger.error(f"Error during property submission: {e}", exc_info=True)
        await update.message.reply_text(t('error_occurred', lang=user.language, default="An error occurred. Please try again."))
    
    context.user_data.pop('submission_data', None)
    return ConversationHandler.END

# --- "My Listings" Handler (Unchanged) ---    
@handle_exceptions
@ensure_user_data
async def my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the broker's own listings using the rich card format."""
    user: User = context.user_data['user']
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    
    listings = prop_cases.get_properties_by_broker(user.uid)
    
    if not listings:
        await update.message.reply_text(
            t('no_listings_yet', lang=user.language, default="You have not submitted any properties yet."),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        return
        
    await update.message.reply_text(t('displaying_your_listings', lang=user.language, default="Displaying your submitted properties:"))
    
    def _resolve_image_url(url: str) -> str:
        if url and (url.startswith('/uploads/') or url.startswith('/images/')):
            base = settings.SERVICE_URL or 'http://localhost:8000'
            return f"{base}{url}"
        return url

    for prop in listings:
        resolved_urls = [_resolve_image_url(url) for url in prop.image_urls]
        prop_details_card = create_property_card_text(prop, for_broker=True)

        try:
            if not resolved_urls:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=prop_details_card,
                    parse_mode='Markdown'
                )
            elif len(resolved_urls) == 1:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=resolved_urls[0]
                )
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=prop_details_card,
                    parse_mode='Markdown'
                )
            else:
                media_group = [InputMediaPhoto(media=url) for url in resolved_urls]
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