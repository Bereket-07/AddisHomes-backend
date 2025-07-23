import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler
from src.domain.models.property_models import Property
from src.use_cases.property_use_cases import PropertyUseCases
from src.use_cases.user_use_cases import UserUseCases
from .. import keyboards
from src.utils.i18n import t
from src.utils.constants import *
from src.utils.display_utils import create_property_card_text  # <<< IMPORTED UTILITY
from .common_handlers import ensure_user_data

logger = logging.getLogger(__name__)

@ensure_user_data
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shows the dedicated admin sub-menu."""
    await update.message.reply_text(
        text="👑 Admin Panel",
        reply_markup=keyboards.get_admin_panel_keyboard(),
    )

@ensure_user_data
async def view_pending_listings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Triggers display of pending properties using the rich card format."""
    logger.info("Admin requested to view pending listings.")
    
    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    pending_props = await prop_cases.get_pending_properties()
    
    logger.info(f"Found {len(pending_props)} pending properties in the database.")

    if not pending_props:
        await update.message.reply_text(
            "There are no pending properties for approval.",
            reply_markup=keyboards.get_admin_panel_keyboard()
        )
        return

    await update.message.reply_text(f"Found {len(pending_props)} pending listings. Please review them below:")
    
    for prop in pending_props:
        media_group = [InputMediaPhoto(media=url) for url in prop.image_urls]
        prop_details_card = create_property_card_text(prop, for_admin=True) # <<< USING UTILITY
        approval_keyboard = keyboards.create_admin_approval_keyboard(prop.pid)

        try:
            await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media_group)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=prop_details_card,
                parse_mode='Markdown',
                reply_markup=approval_keyboard
            )
        except Exception as e:
            logger.error(f"Failed to send rich card for pending property {prop.pid}: {e}.")
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Error displaying property {prop.pid}. Details:\n{prop_details_card}",
                parse_mode='Markdown',
                reply_markup=approval_keyboard
            )
    
    await update.message.reply_text(
        "End of pending list.",
        reply_markup=keyboards.get_admin_panel_keyboard()
    )

@ensure_user_data
async def approve_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the 'Approve' inline button click."""
    query = update.callback_query
    await query.answer()
    prop_id = query.data.split('_')[-1]

    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]

    approved_prop = await prop_cases.approve_property(prop_id)
    if approved_prop:
        broker = await user_cases.get_user_by_id(approved_prop.broker_id)
        if broker and broker.telegram_id:
            notification_text = t('property_approved_notification', default="Your property submission has been approved and is now live!")
            try:
                await context.bot.send_message(chat_id=broker.telegram_id, text=notification_text)
            except Exception as e:
                logger.error(f"Failed to send approval notification to broker {broker.uid}: {e}")
        
        await query.edit_message_text(
            text=f"✅ **ACTION TAKEN: APPROVED**\n\nProperty `{approved_prop.pid}` has been approved.",
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text("❌ This property might have been handled already.")

# --- REJECTION CONVERSATION ---
@ensure_user_data
async def reject_property_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the rejection conversation. Asks for a reason."""
    query = update.callback_query
    await query.answer()
    prop_id = query.data.split('_')[-1]
    context.user_data['prop_to_reject'] = prop_id

    await query.edit_message_text(
        text=f"⏳ **ACTION: REJECTING**\n\nProperty `{prop_id}`. Please provide a reason in the next message.",
        parse_mode='Markdown'
    )
    
    await query.message.reply_text(
        text="Please type the reason for rejection now:",
        reply_markup=keyboards.REMOVE_KEYBOARD
    )
    return STATE_ADMIN_REJECT_REASON_INPUT

@ensure_user_data
async def reject_property_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the text reason for rejection and finalizes the process."""
    reason = update.message.text
    prop_id = context.user_data.get('prop_to_reject')
    user = context.user_data.get('user')

    if not prop_id:
        await update.message.reply_text(
            "Error: Property ID not found in session. Please try again from the pending list.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
        return ConversationHandler.END

    prop_cases: PropertyUseCases = context.bot_data["property_use_cases"]
    user_cases: UserUseCases = context.bot_data["user_use_cases"]
    rejected_prop = await prop_cases.reject_property(prop_id, reason)

    if rejected_prop:
        broker = await user_cases.get_user_by_id(rejected_prop.broker_id)
        if broker and broker.telegram_id:
            notification_text = t('property_rejected_notification', reason=reason, default=f"Your property submission was rejected. Reason: {reason}")
            try:
                await context.bot.send_message(chat_id=broker.telegram_id, text=notification_text)
            except Exception as e:
                logger.error(f"Failed to send rejection notification to broker {broker.uid}: {e}")

        await update.message.reply_text(
            f"❌ Property {rejected_prop.pid[:8]}... has been rejected.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )
    else:
        await update.message.reply_text(
            "❌ Could not find or reject property. It might have been handled already.",
            reply_markup=keyboards.get_main_menu_keyboard(user)
        )

    context.user_data.pop('prop_to_reject', None)
    return ConversationHandler.END