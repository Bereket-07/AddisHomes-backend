import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from src.use_cases.property_use_cases import PropertyUseCases
from src.use_cases.user_use_cases import UserUseCases
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *

logger = logging.getLogger(__name__)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered by a text message from the main menu's reply keyboard."""
    await update.message.reply_text(
        text="👑 Admin Panel",
        reply_markup=keyboards.get_admin_panel_keyboard()
    )

async def view_pending_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggered by a text message from the admin panel keyboard."""
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    pending_props = await prop_cases.get_pending_properties()
    
    user = context.user_data['user']
    if not pending_props:
        await update.message.reply_text(
            "There are no pending properties for approval.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        return

    await update.message.reply_text("Processing pending listings...")
    
    chat_id = update.message.chat_id
    for prop in pending_props:
        prop_details = (
            f"**{prop.property_type.value} in {prop.location.region}**\n\n"
            f"**Price:** {prop.price_etb:,.0f} ETB\n"
            f"**Size:** {prop.size_sqm} sqm\n"
            f"**Bedrooms:** {prop.bedrooms}\n"
            f"**Bathrooms:** {prop.bathrooms}\n"
            f"**Broker:** {prop.broker_name}\n\n"
            f"_{prop.description}_"
        )
        
        try:
            media_group = [InputMediaPhoto(media=url) for url in prop.image_urls[:10]]
            await context.bot.send_media_group(chat_id=chat_id, media=media_group)
        except Exception as e:
            logger.error(f"Could not send media group for {prop.pid}: {e}. Sending first image only.")
            try:
                await context.bot.send_photo(chat_id=chat_id, photo=prop.image_urls[0])
            except Exception as e_photo:
                logger.error(f"Could not even send single photo for {prop.pid}: {e_photo}")

        await context.bot.send_message(
            chat_id=chat_id,
            text=prop_details,
            reply_markup=keyboards.create_admin_approval_keyboard(prop.pid),
            parse_mode='Markdown'
        )

# --- THESE HANDLERS ARE CORRECTLY TRIGGERED BY INLINE KEYBOARDS (CALLBACKQUERY) ---

async def approve_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    prop_id = query.data.split('_')[-1]
    
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]
    
    approved_prop = await prop_cases.approve_property(prop_id)
    if approved_prop:
        broker = await user_cases.get_user_by_id(approved_prop.broker_id)
        if broker:
            # Use a default text in case i18n key is missing
            notification_text = t('property_approved_notification', default="Your property submission has been approved and is now live!")
            await context.bot.send_message(chat_id=broker.telegram_id, text=notification_text)
        await query.edit_message_text(f"✅ Property {approved_prop.pid[:8]}... has been approved.")
    else:
        await query.edit_message_text("❌ Could not find or approve property.")

# --- REJECTION CONVERSATION ---

async def reject_property_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the rejection conversation. Asks for a reason."""
    query = update.callback_query
    await query.answer()
    
    prop_id = query.data.split('_')[-1]
    context.user_data['prop_to_reject'] = prop_id
    
    # We remove the inline keyboard from the original message
    await query.edit_message_reply_markup(reply_markup=None)
    # And send a new message asking for the reason
    await query.message.reply_text(
        text="Please provide a reason for rejecting this property:",
        reply_markup=keyboards.REMOVE_KEYBOARD # Use standard text input
    )
    
    return STATE_ADMIN_REJECT_REASON_INPUT

async def reject_property_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the text reason for rejection and finalizes the process."""
    reason = update.message.text
    prop_id = context.user_data.get('prop_to_reject')
    user = context.user_data.get('user')
    
    if not prop_id:
        await update.message.reply_text(
            "Error: Property ID not found. Please try again.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        return ConversationHandler.END
        
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]
    
    rejected_prop = await prop_cases.reject_property(prop_id, reason)
    
    if rejected_prop:
        broker = await user_cases.get_user_by_id(rejected_prop.broker_id)
        if broker:
            notification_text = t('property_rejected_notification', reason=reason, default=f"Your property submission was rejected. Reason: {reason}")
            await context.bot.send_message(chat_id=broker.telegram_id, text=notification_text)
        
        await update.message.reply_text(
            f"❌ Property {rejected_prop.pid[:8]}... has been rejected.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    else:
        await update.message.reply_text(
            "❌ Could not find or reject property.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    
    # Clean up and end the conversation
    context.user_data.pop('prop_to_reject', None)
    return ConversationHandler.END