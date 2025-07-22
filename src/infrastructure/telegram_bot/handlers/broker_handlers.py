import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from src.use_cases.property_use_cases import PropertyUseCases
from src.use_cases.user_use_cases import UserUseCases
from src.domain.models.property_models import PropertyCreate, PropertyType, Location
from src.domain.models.user_models import User
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *

logger = logging.getLogger(__name__)

# --- Property Submission Conversation (Reply Keyboard Version) ---

async def start_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data'] = {}
    await update.message.reply_text(
        text=t('property_submission_start', default="Let's submit a new property. First, what type is it?"),
        reply_markup=keyboards.get_property_type_keyboard()
    )
    return STATE_SUBMIT_PROP_TYPE

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
            text=t('what_is_size', default="What is the approximate size?"),
            reply_markup=keyboards.get_size_range_keyboard()
        )
        return STATE_SUBMIT_SIZE
    except (ValueError, TypeError):
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_SUBMIT_BATHROOMS

async def receive_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    size_text = update.message.text
    size_value = next((v for k, v in keyboards.SIZE_RANGES.items() if k == size_text), None)
    if not size_value:
        await update.message.reply_text("Invalid choice. Please use the keyboard.")
        return STATE_SUBMIT_SIZE
        
    size_range = size_value.split('-')
    size_sqm = (int(size_range[0]) + int(size_range[1])) / 2
    context.user_data['submission_data']['size_sqm'] = size_sqm

    await update.message.reply_text(
        text=t('select_region', default="Which region?"),
        reply_markup=keyboards.get_region_keyboard()
    )
    return STATE_SUBMIT_LOCATION_REGION

async def receive_location_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    region = update.message.text
    context.user_data['submission_data']['location'] = Location(region=region, city="N/A")
    
    await update.message.reply_text(
        text="Please type the price in ETB (e.g., 15000000).",
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_SUBMIT_PRICE

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
        new_property = await prop_cases.submit_property(property_to_create)
        
        await update.message.reply_text(
            t('submission_complete', default="✅ Submission complete! Your property is pending admin approval."),
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        
        admin_telegram_id = await user_cases.get_admin_telegram_id()
        if admin_telegram_id:
            # ... admin notification logic ...
            pass
    except Exception as e:
        logger.error(f"Error during property submission: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
    
    context.user_data.pop('submission_data', None)
    return ConversationHandler.END

# --- "My Listings" Handler (Corrected) ---

async def my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for the 'My Listings' button. Triggered by a MessageHandler."""
    # --- FIX: No query object. We work with update.message. ---
    user: User = context.user_data['user']
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    
    listings = await prop_cases.get_properties_by_broker(user.uid)
    
    if not listings:
        await update.message.reply_text(
            "You have not submitted any properties yet.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        return
        
    response_text = "Your Submitted Properties:\n\n"
    for prop in listings:
        response_text += f"- {prop.property_type.value} in {prop.location.region} (**Status: {prop.status.value.title()}**)\n"
        
    await update.message.reply_text(response_text, reply_markup=keyboards.get_main_menu_keyboard(user))