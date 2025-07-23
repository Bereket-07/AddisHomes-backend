import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from src.use_cases.property_use_cases import PropertyUseCases
from src.use_cases.user_use_cases import UserUseCases
from src.domain.models.property_models import PropertyCreate, PropertyType, Location , FurnishingStatus, CondoScheme
from src.domain.models.user_models import User
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *
from src.utils.display_utils import create_property_card_text # <<< IMPORTED UTILITY
from .common_handlers import ensure_user_data

logger = logging.getLogger(__name__)

# --- Property Submission Conversation (This section remains unchanged) ---
@ensure_user_data
async def start_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (code for start_submission is correct)
    context.user_data['submission_data'] = {}
    await update.message.reply_text(
        text=t('property_submission_start', default="Let's submit a new property. First, what type is it?"),
        reply_markup=keyboards.get_property_type_keyboard()
    )
    return STATE_SUBMIT_PROP_TYPE

# ... (all other receive_* handlers for submission are correct and remain unchanged)
async def receive_property_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        prop_type = PropertyType(update.message.text)
        context.user_data['submission_data']['property_type'] = prop_type
        await update.message.reply_text(
            text=t('how_many_bedrooms', default="How many bedrooms?"),
            reply_markup=keyboards.get_bedroom_keyboard()
        )
        return STATE_SUBMIT_BEDROOMS
    except ValueError:
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_SUBMIT_PROP_TYPE

async def receive_bedrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        bedrooms = int(update.message.text.replace('+', ''))
        context.user_data['submission_data']['bedrooms'] = bedrooms
        await update.message.reply_text(
            text=t('how_many_bathrooms', default="How many bathrooms?"),
            reply_markup=keyboards.get_bathroom_keyboard()
        )
        return STATE_SUBMIT_BATHROOMS
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_SUBMIT_BEDROOMS

async def receive_bathrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        bathrooms = int(update.message.text.replace('+', ''))
        context.user_data['submission_data']['bathrooms'] = bathrooms
        await update.message.reply_text(
            text=t('what_is_size', default="What is the approximate size in square meters?"),
            reply_markup=keyboards.get_size_range_keyboard()
        )
        return STATE_SUBMIT_SIZE
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_SUBMIT_BATHROOMS

async def receive_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # ... (this function's logic is fine)
    size_text = update.message.text
    size_value = keyboards.SIZE_RANGES_TEXT.get(size_text)
    if not size_value:
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_SUBMIT_SIZE
    size_range = size_value.split('-')
    size_sqm = (int(size_range[0]) + int(size_range[1])) / 2
    context.user_data['submission_data']['size_sqm'] = size_sqm

    await update.message.reply_text(
        text=t('select_region', default="Which region?"),
        reply_markup=keyboards.get_region_keyboard(is_filter=False)
    )
    return STATE_SUBMIT_LOCATION_REGION # <<< FLOWS TO REGION

async def receive_location_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    region = update.message.text
    # Initialize the location object
    context.user_data['submission_data']['location'] = {'region': region}
    await update.message.reply_text(
        text="Now, please type the name of the **City** (e.g., Addis Ababa).",
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_SUBMIT_LOCATION_CITY # <<< FLOWS TO CITY

async def receive_location_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text
    context.user_data['submission_data']['location']['city'] = city
    await update.message.reply_text(
        text="Great. Type the **Sub-city** if applicable, or type 'skip'.",
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_SUBMIT_LOCATION_SUB_CITY # <<< FLOWS TO SUB-CITY

async def receive_location_sub_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sub_city = update.message.text
    if sub_city.lower() != 'skip':
        context.user_data['submission_data']['location']['sub_city'] = sub_city
    
    await update.message.reply_text(
        text="What is the **Floor Level**? (e.g., 5 for 5th floor, 0 for ground)",
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_SUBMIT_FLOOR_LEVEL # <<< FLOWS TO FLOOR LEVEL

async def receive_floor_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['submission_data']['floor_level'] = int(update.message.text)
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid number. Please enter the floor level (e.g., 5).")
        return STATE_SUBMIT_FLOOR_LEVEL
        
    await update.message.reply_text(
        text="What is the **Furnishing Status**?",
        reply_markup=keyboards.get_furnishing_status_keyboard()
    )
    return STATE_SUBMIT_FURNISHING_STATUS # <<< FLOWS TO FURNISHING

async def receive_furnishing_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        status = FurnishingStatus(update.message.text)
        context.user_data['submission_data']['furnishing_status'] = status
    except ValueError:
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_SUBMIT_FURNISHING_STATUS
        
    await update.message.reply_text(
        text="Does it have a **Title Deed**?",
        reply_markup=keyboards.get_boolean_keyboard()
    )
    return STATE_SUBMIT_TITLE_DEED # <<< FLOWS TO TITLE DEED

async def receive_title_deed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    answer = update.message.text.lower()
    if answer not in ["yes", "no"]:
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_SUBMIT_TITLE_DEED
        
    context.user_data['submission_data']['title_deed'] = (answer == "yes")
    
    await update.message.reply_text(
        text="How many **Parking Spaces** are available? (Enter 0 if none)",
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_SUBMIT_PARKING_SPACES # <<< FLOWS TO PARKING

async def receive_parking_spaces(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['submission_data']['parking_spaces'] = int(update.message.text)
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid number. Please enter the number of parking spaces (e.g., 2).")
        return STATE_SUBMIT_PARKING_SPACES

    # --- CONDITIONAL QUESTION ---
    prop_type = context.user_data['submission_data'].get('property_type')
    if prop_type == PropertyType.CONDOMINIUM:
        await update.message.reply_text(
            text="What is the **Condominium Scheme**?",
            reply_markup=keyboards.get_condo_scheme_keyboard() # Re-use existing keyboard
        )
        return STATE_SUBMIT_CONDO_SCHEME # <<< FLOWS TO CONDO (if needed)
    else:
        # If not a condo, skip to price
        await update.message.reply_text(
            text="Almost done! Please type the price in ETB (e.g., 15000000).",
            reply_markup=keyboards.REMOVE_KEYBOARD
        )
        return STATE_SUBMIT_PRICE # <<< SKIPS TO PRICE

async def receive_condo_scheme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        scheme = CondoScheme(update.message.text)
        context.user_data['submission_data']['condominium_scheme'] = scheme
    except ValueError:
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_SUBMIT_CONDO_SCHEME

    await update.message.reply_text(
        text="Almost done! Please type the price in ETB (e.g., 15000000).",
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_SUBMIT_PRICE # <<< FLOWS TO PRICE

async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text)
        context.user_data['submission_data']['price_etb'] = price
        context.user_data['submission_data']['image_urls'] = []
        await update.message.reply_text(text=t('upload_images', default="Please upload at least 3 images. Send them one by one, then type 'done' when finished."))
        return STATE_SUBMIT_IMAGES
    except (ValueError, TypeError):
        await update.message.reply_text("Please enter a valid number for the price.")
        return STATE_SUBMIT_PRICE

async def receive_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text("Please send an image or type 'done'.")
        return STATE_SUBMIT_IMAGES
    file_id = update.message.photo[-1].file_id
    context.user_data['submission_data']['image_urls'].append(file_id)
    await update.message.reply_text(text=t('image_received', default="Image received. Send more or type 'done'."))
    return STATE_SUBMIT_IMAGES

async def done_receiving_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    images = context.user_data.get('submission_data', {}).get('image_urls', [])
    if len(images) < 3:
        await update.message.reply_text(text=t('need_more_images', default="Please upload at least 3 images to continue."))
        return STATE_SUBMIT_IMAGES
    await update.message.reply_text(text=t('enter_description', default="Finally, please enter a short description."))
    return STATE_SUBMIT_DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['description'] = update.message.text
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]
    user: User = context.user_data['user']
    
    try:
        property_to_create = PropertyCreate(
            broker_id=user.uid,
            broker_name=user.display_name or "N/A",
            **context.user_data['submission_data']
        )
        await prop_cases.submit_property(property_to_create)
        
        await update.message.reply_text(
            t('submission_complete', default="✅ Submission complete! Your property is pending admin approval."),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        
        # Optional: Notify admin here
    except Exception as e:
        logger.error(f"Error during property submission: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
    
    context.user_data.pop('submission_data', None)
    return ConversationHandler.END

# --- "My Listings" Handler (UPDATED) ---
@ensure_user_data
async def my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the broker's own listings using the rich card format."""
    user: User = context.user_data['user']
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    
    listings = await prop_cases.get_properties_by_broker(user.uid)
    
    if not listings:
        await update.message.reply_text(
            "You have not submitted any properties yet.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        return
        
    await update.message.reply_text("Displaying your submitted properties:")
    
    for prop in listings:
        media_group = [InputMediaPhoto(media=url) for url in prop.image_urls]
        prop_details_card = create_property_card_text(prop, for_broker=True) # <<< USING UTILITY

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
    
    await update.message.reply_text("End of your listings.", reply_markup=keyboards.get_main_menu_keyboard(user))