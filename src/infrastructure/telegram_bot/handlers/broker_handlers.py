import logging
from telegram import Update , InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from src.use_cases.property_use_cases import PropertyUseCases
from src.use_cases.user_use_cases import UserUseCases
from src.domain.models.property_models import PropertyCreate, PropertyType, Location, FurnishingStatus, CondoScheme
from src.domain.models.user_models import User
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *
from .common_handlers import ensure_user_data
from src.utils.display_utils import create_property_card_text # <<< IMPORTED UTILITY

logger = logging.getLogger(__name__)

# --- Property Submission Conversation ---

@ensure_user_data
async def start_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data'] = {}
    await update.message.reply_text("Let's submit a new property. First, what type is it?", reply_markup=keyboards.get_property_type_keyboard())
    return STATE_SUBMIT_PROP_TYPE

async def receive_property_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['property_type'] = PropertyType(update.message.text)
    # For now, we assume Addis Ababa. This could be a question itself.
    context.user_data['submission_data']['location'] = {'region': 'Addis Ababa', 'city': 'Addis Ababa'}
    await update.message.reply_text("In which Sub-city is the property located?", reply_markup=keyboards.get_sub_city_keyboard())
    return STATE_SUBMIT_LOCATION_SUB_CITY

async def receive_sub_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    sub_city = update.message.text
    context.user_data['submission_data']['location']['sub_city'] = sub_city
    
    prop_type = context.user_data['submission_data']['property_type']
    if prop_type == PropertyType.CONDOMINIUM:
        keyboard = keyboards.get_condo_site_keyboard(sub_city)
        prompt = "Please select the Condominium Site name."
    else:
        keyboard = keyboards.get_neighborhood_keyboard(sub_city)
        prompt = "Please select the nearest neighborhood/area."

    if not keyboard.keyboard:
        prompt = "Could not find specific areas. Please type the specific area name."
        keyboard = keyboards.REMOVE_KEYBOARD

    await update.message.reply_text(prompt, reply_markup=keyboard)
    return STATE_SUBMIT_SPECIFIC_AREA

async def receive_specific_area(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['location']['specific_area'] = update.message.text
    await update.message.reply_text("How many bedrooms?", reply_markup=keyboards.get_numeric_keyboard(keyboards.BEDROOM_OPTIONS))
    return STATE_SUBMIT_BEDROOMS

async def receive_bedrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['bedrooms'] = int(update.message.text.replace('+', ''))
    await update.message.reply_text("How many bathrooms?", reply_markup=keyboards.get_numeric_keyboard(keyboards.BATHROOM_OPTIONS))
    return STATE_SUBMIT_BATHROOMS

async def receive_bathrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['bathrooms'] = int(update.message.text.replace('+', ''))
    await update.message.reply_text("What is the approximate size?", reply_markup=keyboards.get_size_range_keyboard())
    return STATE_SUBMIT_SIZE

async def receive_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    size_range = keyboards.SIZE_RANGES_TEXT[update.message.text].split('-')
    context.user_data['submission_data']['size_sqm'] = (int(size_range[0]) + int(size_range[1])) / 2
    await update.message.reply_text("What is the Floor Level? (Type the number, e.g., 5)", reply_markup=keyboards.REMOVE_KEYBOARD)
    return STATE_SUBMIT_FLOOR_LEVEL

async def receive_floor_level(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['floor_level'] = int(update.message.text)
    await update.message.reply_text("What is the Furnishing Status?", reply_markup=keyboards.get_furnishing_status_keyboard())
    return STATE_SUBMIT_FURNISHING_STATUS

async def receive_furnishing_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['furnishing_status'] = FurnishingStatus(update.message.text)
    await update.message.reply_text("Does it have a Title Deed?", reply_markup=keyboards.get_boolean_keyboard())
    return STATE_SUBMIT_TITLE_DEED

async def receive_title_deed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['title_deed'] = (update.message.text.lower() == "yes")
    await update.message.reply_text("How many Parking Spaces? (Type the number, e.g., 2)", reply_markup=keyboards.REMOVE_KEYBOARD)
    return STATE_SUBMIT_PARKING_SPACES

async def receive_parking_spaces(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['parking_spaces'] = int(update.message.text)
    prop_type = context.user_data['submission_data']['property_type']
    if prop_type == PropertyType.CONDOMINIUM:
        await update.message.reply_text("What is the Condominium Scheme Type?", reply_markup=keyboards.get_condo_scheme_keyboard())
        return STATE_SUBMIT_CONDO_SCHEME
    else:
        await update.message.reply_text("Please type the exact price in ETB.", reply_markup=keyboards.REMOVE_KEYBOARD)
        return STATE_SUBMIT_PRICE

async def receive_condo_scheme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['condominium_scheme'] = CondoScheme(update.message.text)
    await update.message.reply_text("Please type the exact price in ETB.", reply_markup=keyboards.REMOVE_KEYBOARD)
    return STATE_SUBMIT_PRICE

async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['submission_data']['price_etb'] = float(update.message.text)
        context.user_data['submission_data']['image_urls'] = []
        await update.message.reply_text("Please upload at least 3 images. When finished, press the button below.", reply_markup=keyboards.get_image_upload_keyboard())
        return STATE_SUBMIT_IMAGES
    except (ValueError, TypeError):
        await update.message.reply_text("Please enter a valid number for the price.")
        return STATE_SUBMIT_PRICE

async def receive_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text("That's not an image. Please send photos or click the 'Done' button.")
        return STATE_SUBMIT_IMAGES
    context.user_data['submission_data']['image_urls'].append(update.message.photo[-1].file_id)
    await update.message.reply_text(f"Image {len(context.user_data['submission_data']['image_urls'])} received. Send more or click 'Done Uploading'.")
    return STATE_SUBMIT_IMAGES

async def done_receiving_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    images = context.user_data.get('submission_data', {}).get('image_urls', [])
    if len(images) < 3:
        await update.message.reply_text(f"You've only uploaded {len(images)} image(s). Please upload at least 3 to continue.")
        return STATE_SUBMIT_IMAGES
    await update.message.reply_text("Great! Finally, please enter a short description for the property.", reply_markup=keyboards.REMOVE_KEYBOARD)
    return STATE_SUBMIT_DESCRIPTION

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
        await update.message.reply_text("✅ Submission complete! Your property is pending admin approval.", reply_markup=keyboards.get_main_menu_keyboard(user))
    except Exception as e:
        logger.error(f"Error during property submission: {e}", exc_info=True)
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