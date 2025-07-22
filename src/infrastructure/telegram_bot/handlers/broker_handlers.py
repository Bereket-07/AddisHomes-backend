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

# --- Property Submission Conversation ---
async def start_submission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data'] = {}
    await update.message.reply_text(
        text=t('property_submission_start'),
        reply_markup=keyboards.get_property_type_keyboard()
    )
    return STATE_SUBMIT_PROP_TYPE

async def receive_property_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # This handler now expects text from the reply keyboard
    # ... logic to process text, then...
    await update.message.reply_text(
        text=t('how_many_bedrooms'),
        reply_markup=keyboards.get_bedroom_keyboard()
    )
    return STATE_SUBMIT_BEDROOMS

async def receive_bedrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bedrooms = int(query.data.replace(CB_PREFIX_BEDROOMS, ""))
    context.user_data['submission_data']['bedrooms'] = bedrooms
    await query.edit_message_text(
        text=t('how_many_bathrooms'),
        reply_markup=keyboards.create_options_keyboard(keyboards.BATHROOM_OPTIONS, CB_PREFIX_BATHROOMS)
    )
    return STATE_SUBMIT_BATHROOMS

async def receive_bathrooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    bathrooms = int(query.data.replace(CB_PREFIX_BATHROOMS, ""))
    context.user_data['submission_data']['bathrooms'] = bathrooms
    await query.edit_message_text(
        text=t('what_is_size'),
        reply_markup=keyboards.create_dict_options_keyboard(keyboards.SIZE_RANGES, CB_PREFIX_SIZE)
    )
    return STATE_SUBMIT_SIZE

async def receive_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    size_range = query.data.replace(CB_PREFIX_SIZE, "").split('-')
    # We take the average for simplicity. Could also store the range.
    size_sqm = (int(size_range[0]) + int(size_range[1])) / 2
    context.user_data['submission_data']['size_sqm'] = size_sqm
    
    await query.edit_message_text(text=t('what_is_price'))
    return STATE_SUBMIT_PRICE

async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text)
        context.user_data['submission_data']['price_etb'] = price
        await update.message.reply_text(
            text=t('select_region'),
            reply_markup=keyboards.create_location_keyboard(CB_PREFIX_LOCATION, 'region')
        )
        return STATE_SUBMIT_LOCATION_REGION
    except (ValueError, TypeError):
        await update.message.reply_text("Please enter a valid number for the price.")
        return STATE_SUBMIT_PRICE

async def receive_location_region(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    region = query.data.replace(CB_PREFIX_LOCATION, "")
    # For now, we'll simplify and just use region. A full flow would continue to city.
    context.user_data['submission_data']['location'] = Location(region=region, city="N/A")
    context.user_data['submission_data']['image_urls'] = []
    await query.edit_message_text(text=t('upload_images'))
    return STATE_SUBMIT_IMAGES

async def receive_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message.photo:
        await update.message.reply_text("Please send an image or type 'done'.")
        return STATE_SUBMIT_IMAGES
        
    file_id = update.message.photo[-1].file_id
    context.user_data['submission_data']['image_urls'].append(file_id)
    await update.message.reply_text(text=t('image_received'))
    return STATE_SUBMIT_IMAGES

async def done_receiving_images(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    images = context.user_data['submission_data']['image_urls']
    if len(images) < 3:
        await update.message.reply_text(text=t('need_more_images'))
        return STATE_SUBMIT_IMAGES
    
    await update.message.reply_text(text=t('enter_description'))
    return STATE_SUBMIT_DESCRIPTION

async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['submission_data']['description'] = update.message.text
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]
    user: User = context.user_data['user']
    
    try:
        submission_data = context.user_data['submission_data']
        property_to_create = PropertyCreate(
            broker_id=user.uid,
            broker_name=user.display_name or "N/A",
            **submission_data
        )
        
        new_property = await prop_cases.submit_property(property_to_create)
        
        await update.message.reply_text(
            t('submission_complete'),
            reply_markup=keyboards.create_main_menu_keyboard(user)
        )
        
        admin_telegram_id = await user_cases.get_admin_telegram_id()
        if admin_telegram_id:
            admin_notification_text = t(
                'new_pending_property',
                type=new_property.property_type.value,
                broker_name=new_property.broker_name,
                price=f"{new_property.price_etb:,.0f}"
            )
            await context.bot.send_message(
                chat_id=admin_telegram_id,
                text=admin_notification_text,
                reply_markup=keyboards.create_admin_approval_keyboard(new_property.pid),
                parse_mode='Markdown'
            )
        else:
            logger.warning("Could not find a claimed admin account to send notification to.")
        
    except Exception as e:
        logger.error(f"Error during property submission: {e}")
        await update.message.reply_text("An error occurred. Please try again.")
    
    del context.user_data['submission_data']
    return ConversationHandler.END

async def my_listings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user: User = context.user_data['user']
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    
    listings = await prop_cases.get_properties_by_broker(user.uid)
    
    if not listings:
        await query.edit_message_text(
            "You have not submitted any properties yet.",
            reply_markup=keyboards.create_back_to_main_keyboard()
        )
        return STATE_MAIN
        
    response_text = "Your Submitted Properties:\n\n"
    for prop in listings:
        response_text += f"- {prop.property_type.value} in {prop.location.region} ({prop.status.value.title()})\n"
        
    await query.edit_message_text(response_text, reply_markup=keyboards.create_back_to_main_keyboard())
    return STATE_MAIN